import pandas as pd
import streamlit as st
import requests
import numpy as np
from bs4 import BeautifulSoup

df_tender = None

# Add a text input for the user to enter the URL of the HTML table
st.sidebar.header("Upload Options")
url = st.text_input("Enter URL", "")
if url:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')

        df_tender = pd.read_html(str(tables[0]))[0]
    except requests.exceptions.RequestException as e:
        st.error(f"Request Exception:{e}")
    except ValueError as e:
        st.error(f"ValueError: {e}")

if df_tender is not None:
    # %% [markdown]
    # ## Data Cleaning

    # %%
    # Define the new column headers
    new_columns = ['Hospital', 'Tender Reference', 'Subject', 
                'Tendering Procedure', 'Contractor(s) & Address(es)', 
                'Item', 'Contract Period', 'Estimated Contract Amount', 
                'Date of Award']

    # Set the new column headers
    df_tender.columns = new_columns

    # Set the first row as headers, then reset the DataFrame without that row
    df_tender.columns = df_tender.iloc[0]  # Set the first row as header
    df_tender = df_tender[1:].reset_index(drop=True)  # Remove the first row and reset the index

    # Rename columns to the desired header names if needed
    df_tender.columns = new_columns

    df_tender = df_tender.drop(index=range(0, 6)).reset_index(drop=True)
    df_tender = df_tender.dropna(subset=['Subject'])
    df_tender = df_tender[~df_tender['Item'].str.contains('item', case=False, na=False)].reset_index(drop=True)

    # Extract Hospital, Subject, Tendering Procedure, Contractor, contract Period and Estimated Contract Amount columns
    df2 = df_tender[['Hospital','Subject','Tendering Procedure','Contractor(s) & Address(es)','Contract Period', 'Estimated Contract Amount']]

    # Define keywords and corresponding categories in alphabetical order, including within each condition
    conditions = [
        
    df2['Subject'].str.contains('bags|bottle|containers|consumables|dressing|disposable|gloves|mask|patches|paper|scrub|sharp box|sponges|syringes|'
                                    'swabstick|tape|tap|wax|wipes|wristbands', case=False, na=False),
    df2['Subject'].str.contains('Bromide|Granules|Linctus|Suspension|capsule|capsules|Cetirizine|cream|drops|enema|eye|flexpens|gel|inhaler|insulin|lozenge|'
                                'lozenges|mixture|ointment|oral|pencil|powder|potassium|prefilled|Sirolimus|sodium|spray|syrup|tablet|Tablet'
                                'Risdiplam|Peritoneal|Levetiracetam|Levocarnitine|Bisacodyl', case=False, na=False), 
    df2['Subject'].str.contains('injection|infusion', case=False, na=False),
    df2['Subject'].str.contains('implant|implants', case=False, na=False),    
    df2['Subject'].str.contains('Computed Tomography-based|Endoscope|Endoscopic|Endoscopy|Microscopes|Radiographic|Radiography|scanning|Spectrometers|Stereotactic', case=False, na=False), 
    df2['Subject'].str.contains('Analyzers|Bicart Select Combi-Pak|Hemodialysis|Immunostainers|Processors|cytometers|indicator|Heart-Lung Support|\bRadiotherapy Systems\b|\bunit\b|\bUnits\b|\bUnits,\b', case=False, na=False),    
    df2['Subject'].str.contains('Laboratory|Point-Of-Care|test|testing, assay', case=False, na=False),
    df2['Subject'].str.contains('vaccine|vaccines', case=False, na=False),
    ]
    # Define corresponding categories in alphabetical order
    choices = [
        'Consumable', 'Pharma','Injection & Infusion','Implants','Imaging','Device', 'Testing','Vaccine'] 
    # Use np.select to create the 'category' column with multiple conditions
    df2['category'] = np.select(conditions, choices, default='Others')

    # %%
    # Filter rows where the 'category' column is 'Pharma'
    df_pharma = df2[df2['category'] == 'Pharma'].reset_index(drop=True)
    df_pharma = df_pharma.drop(index=245).reset_index(drop=True)
    df_device = df2[df2['category'] == 'Device'].reset_index(drop=True)
    df_In = df2[df2['category'] == 'Injection & Infusion'].reset_index(drop=True)
    df_imaging = df2[df2['category'] == 'Imaging'].reset_index(drop=True)
    df_testing = df2[df2["category"] == 'Testing'].reset_index(drop=True)

    df_testing

    # %% [markdown]
    # ## Streamlit Dash

    # %%
    st.title(":hospital: HK HA Tender Award App")
    st.write(
        "2024 HK HA Tender Award List"
    )
    # Streamlit Title and Description
    st.title("Contractor List")
    st.write("This is a list of contractors involved in hospital tenders. You can filter by various fields to view specific contractors.")

    # Sidebar Filters
    st.sidebar.header("Filter Contractors")
    hospital_filter = st.sidebar.multiselect("Select Hospital", options=df2["Hospital"].unique())
    category_filter = st.sidebar.multiselect("Select Category", options=df2["Category"].unique())

    # Filter the DataFrame
    filtered_df = df2
    if hospital_filter:
        filtered_df = filtered_df[filtered_df["Hospital"].isin(hospital_filter)]
    if category_filter:
        filtered_df = filtered_df[filtered_df["Category"].isin(category_filter)]

    # Display filtered contractor list
    st.subheader("Contractor List")
    st.write(f"Total Contractors: {len(filtered_df)}")
    st.dataframe(filtered_df[["Contractor(s) & Address(es)","Subject", "Hospital", "Category", "Estimated Contract Amount"]])

    # Download Button for Filtered Contractor List
    st.download_button(
        label="Download Contractor List as CSV",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_contractor_list.csv",
        mime="text/csv"
    )

    # %% [markdown]
    # ### Chart

    # %%
    # Barchart of the filtered contractor 
    contractor_count = filtered_df.groupby('Contractor(s) & Address(es)').size().reset_index(name = 'Counts')
    # Function to truncate labels to the first 4 words
    def truncate_label(label):
        words = label.split()
        return ' '.join(words[:4])  # Join the first 4 words

    # Apply the function to the 'Contractor(s) & Address(es)' column
    contractor_count['Truncated Contractor'] = contractor_count['Contractor(s) & Address(es)'].apply(truncate_label)

    # Barchart of the filtered contractor 
    fig1 = px.bar(contractor_count, x='Truncated Contractor', y='Counts',
                title="Contractor Distribution")

    # Update layout to rotate x-axis labels
    fig1.update_layout(
        xaxis_tickangle=-40  # Rotate x-axis labels by -40 degrees
    )

    st.plotly_chart(fig1)


