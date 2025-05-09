import streamlit as st
import pandas as pd
import openai
from dotenv import load_dotenv
import datetime
import os
import toml
from mapping_questions import categorize_questions
from analyze_checklist import identify_unique_locations, analyze_selected_locations, generate_summary
import supabase
import io
import uuid

# Page configuration
st.set_page_config(page_title="Food Safety Analyzer", layout="wide", page_icon="🍽️")

# Load secrets from the local file
try:
    secrets_path = os.path.join(os.path.dirname(__file__), "secrets.toml")
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        # Make secrets available in st.secrets
        for section, values in secrets.items():
            if section not in st.secrets:
                st.secrets[section] = {}
            for key, value in values.items():
                st.secrets[section][key] = value
        print("Loaded secrets from local file")
    else:
        print("No local secrets file found, using Streamli  t's secrets if available")
except Exception as e:
    print(f"Error loading secrets: {e}")

# Set OpenAI API key using st.secrets
openai.api_key = st.secrets["openai"]["api_key"]

# Initialize Supabase client using st.secrets
supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["key"]
supabase_client = supabase.create_client(supabase_url, supabase_key)
# Initialize session state for maintaining data between reruns
if 'df' not in st.session_state:
    st.session_state.df = None
if 'categorized' not in st.session_state:
    st.session_state.categorized = False
if 'unique_cafes' not in st.session_state:
    st.session_state.unique_cafes = []
if 'unique_vendors' not in st.session_state:
    st.session_state.unique_vendors = []
if 'locations_output' not in st.session_state:
    st.session_state.locations_output = ""
if 'selected_cafes' not in st.session_state:
    st.session_state.selected_cafes = []
if 'selected_vendors' not in st.session_state:
    st.session_state.selected_vendors = []
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'analyzed_df' not in st.session_state:
    st.session_state.analyzed_df = None
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'analyzed_df' not in st.session_state:
    st.session_state.analyzed_df = None
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'entries_saved' not in st.session_state:
    st.session_state.entries_saved = 0
if 'all_entries_saved' not in st.session_state:
    st.session_state.all_entries_saved = False
if 'supabase_ids' not in st.session_state:
    st.session_state.supabase_ids = []

def reset_analysis():
    """Reset analysis-related session state"""
    st.session_state.analysis_complete = False
    st.session_state.analyzed_df = None
    st.session_state.summary = ""

def reset_all():
    """Reset all session state"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reinitialize
    st.session_state.df = None
    st.session_state.categorized = False
    st.session_state.unique_cafes = []
    st.session_state.unique_vendors = []
    st.session_state.locations_output = ""
    st.session_state.selected_cafes = []
    st.session_state.selected_vendors = []
    st.session_state.analysis_complete = False
    st.session_state.analyzed_df = None
    st.session_state.summary = ""
    st.session_state.entries_saved = 0
    st.session_state.all_entries_saved = False
    st.session_state.supabase_ids = []

def create_cafe_vendor_mapping(df):
    """Creates a mapping between cafes and their associated vendors based on vendor_name column"""
    cafe_vendor_mapping = {}
    
    # Check if required columns exist
    required_cols = ['location_name', 'checklist_type', 'vendor_name']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.warning(f"Missing required columns: {', '.join(missing_cols)}. Vendor mapping may be incomplete.")
        return {}
    
    # Get all cafe locations
    cafe_locations = df[df['checklist_type'] == 'cafe']['location_name'].unique()
    
    # For each cafe, find all vendors that serve there
    for cafe in cafe_locations:
        # Get all vendors associated with this cafe
        cafe_vendors_df = df[(df['checklist_type'] == 'vendor') & 
                           (df['location_name'] == cafe)]
        
        # If vendors exist for this cafe
        if not cafe_vendors_df.empty:
            # Get unique vendor names, excluding None/NaN values
            vendors = cafe_vendors_df['vendor_name'].dropna().unique()
            vendors = [v for v in vendors if v and str(v).lower() != 'none'] 
            
            if len(vendors) > 0:
                cafe_vendor_mapping[cafe] = sorted(list(vendors))
        
        # If the cafe has checklist entries where vendor_name is filled
        vendor_from_cafe_entries = df[(df['checklist_type'] == 'cafe') & 
                                    (df['location_name'] == cafe) & 
                                    (df['vendor_name'].notna())]
        
        if not vendor_from_cafe_entries.empty:
            # Get unique vendor names from cafe entries
            additional_vendors = vendor_from_cafe_entries['vendor_name'].dropna().unique()
            additional_vendors = [v for v in additional_vendors if v and str(v).lower() != 'none']
            
            # Add these vendors to the mapping
            if len(additional_vendors) > 0:
                if cafe in cafe_vendor_mapping:
                    # Add to existing vendors, avoiding duplicates
                    cafe_vendor_mapping[cafe] = sorted(list(set(cafe_vendor_mapping[cafe] + additional_vendors)))
                else:
                    cafe_vendor_mapping[cafe] = sorted(list(additional_vendors))
    
    # Also look for vendors with vendor_name not empty
    vendor_entries = df[(df['checklist_type'] == 'vendor') & (df['vendor_name'].notna())]
    
    for vendor_loc in vendor_entries['location_name'].unique():
        # Get vendors at this location
        vendors_at_loc = vendor_entries[vendor_entries['location_name'] == vendor_loc]['vendor_name'].dropna().unique()
        vendors_at_loc = [v for v in vendors_at_loc if v and str(v).lower() != 'none']
        
        if len(vendors_at_loc) > 0:
            if vendor_loc in cafe_vendor_mapping:
                # Add to existing vendors, avoiding duplicates
                cafe_vendor_mapping[vendor_loc] = sorted(list(set(cafe_vendor_mapping[vendor_loc] + list(vendors_at_loc))))
            else:
                cafe_vendor_mapping[vendor_loc] = sorted(list(vendors_at_loc))
    
    return cafe_vendor_mapping

# Add a helper function to get vendors with their café affiliations
def get_vendor_cafe_mapping(selected_cafes, selected_vendors, cafe_vendor_mapping):
    """Create a mapping of vendors to their serving cafés"""
    vendor_cafe_mapping = {}
    for vendor in selected_vendors:
        serving_cafes = []
        for cafe in selected_cafes:
            if cafe in cafe_vendor_mapping and vendor in cafe_vendor_mapping[cafe]:
                serving_cafes.append(cafe)
        vendor_cafe_mapping[vendor] = serving_cafes
    return vendor_cafe_mapping

def filter_data_for_analysis(df, selected_cafes, selected_vendors, vendors_only=False):
    """
    Filter data for analysis based on selected cafes and vendors
    
    If vendors_only is True:
      - Process ONLY rows where location_name is in selected_cafes AND vendor_name is in selected_vendors
    
    If vendors_only is False (analyze all cafe):
      - Process ALL rows where location_name is in selected_cafes
    """
    # Create a copy of the dataframe to avoid SettingWithCopyWarning
    filtered_df = df.copy()
    
    # Print diagnostic information
    st.write(f"Total rows in dataset: {len(filtered_df)}")
    st.write(f"Selected cafes: {selected_cafes}")
    st.write(f"Selected vendors: {selected_vendors}")
    
    if vendors_only and selected_vendors:
        # STRICT FILTER: Only rows that match BOTH selected cafes AND selected vendors
        # This is different from the previous logic - we only want exact matches
        mask = (
            filtered_df['location_name'].isin(selected_cafes) & 
            filtered_df['vendor_name'].isin(selected_vendors)
        )
        
        result_df = filtered_df[mask]
        
        # Count matches
        match_count = len(result_df)
        st.write(f"Rows matching both selected cafes AND selected vendors: {match_count}")
        
        # If no matches found with strict filtering, provide a clearer message
        if match_count == 0:
            st.error("No entries found with the selected vendors in these cafes.")
            st.write("This could be because:")
            st.write("1. The vendor_name field might be empty or have different values than expected")
            st.write("2. The selected vendors might not have entries in the selected cafes")
            
            # Show a sample of the data to help diagnose
            st.write("Sample vendor_name values in the dataset:")
            vendor_sample = filtered_df['vendor_name'].dropna().unique()[:10]
            st.write(vendor_sample)
            
            # Return empty DataFrame - DON'T use fallbacks as requested
            return pd.DataFrame()
    else:
        # Analyze all cafe entries: include all rows for selected cafes
        mask = filtered_df['location_name'].isin(selected_cafes)
        result_df = filtered_df[mask]
        st.write(f"Rows matching selected cafes (all entries): {len(result_df)}")
        
        if len(result_df) == 0:
            st.error("No entries found for the selected cafes.")
            # Return empty DataFrame - DON'T use fallbacks
            return pd.DataFrame()
    
    # Additional analysis to help debug
    if not result_df.empty:
        # Show rows with upload_links
        has_uploads = len(result_df[result_df['upload_links'].notna() & (result_df['upload_links'] != '')])
        st.write(f"Of these, {has_uploads} rows have images (upload_links)")
        
        # Show breakdown by cafe
        st.write("Rows per cafe:")
        for cafe in selected_cafes:
            cafe_rows = len(result_df[result_df['location_name'] == cafe])
            st.write(f"- {cafe}: {cafe_rows} rows")
        
        # If analyzing vendors, show breakdown by vendor
        if vendors_only and selected_vendors:
            st.write("Rows per vendor:")
            for vendor in selected_vendors:
                vendor_rows = len(result_df[result_df['vendor_name'] == vendor])
                st.write(f"- {vendor}: {vendor_rows} rows")
    
    return result_df

def direct_analyze(df, cafes, vendors, api_key, vendors_only=False):
    """Improved direct pass-through to analyze_selected_locations"""
    if df.empty:
        st.error("Empty dataframe provided for analysis")
        return pd.DataFrame()
    
    # Print diagnostic information
    st.write(f"Analysis details:")
    st.write(f"- Total rows provided: {len(df)}")
    st.write(f"- Selected cafes: {cafes}")
    st.write(f"- Selected vendors: {vendors}")
    st.write(f"- Analysis mode: {'Vendor-specific only' if vendors_only else 'Full cafe analysis'}")
    
    # Make a copy of the dataframe to avoid modifying the original
    analysis_df = df.copy()
    
    # CRITICAL: Make sure there are rows that match the filter criteria
    cafe_filter = analysis_df['location_name'].isin(cafes)
    cafe_rows = len(analysis_df[cafe_filter])
    st.write(f"- Rows matching selected cafes: {cafe_rows}")
    
    if vendors_only:
        # For vendor-specific analysis, we need to ensure there are 
        # matching rows with both location_name and vendor_name
        vendor_rows = len(analysis_df[
            cafe_filter & 
            analysis_df['vendor_name'].isin(vendors)
        ])
        st.write(f"- Rows matching both cafe and vendor filters: {vendor_rows}")
        
        if vendor_rows == 0:
            st.error("No rows match both cafe and vendor criteria in the original data")
            return pd.DataFrame()
    
    # Check for upload_links column
    if 'upload_links' not in analysis_df.columns:
        st.warning("No 'upload_links' column found. Adding empty column.")
        analysis_df['upload_links'] = ""
    
    # Check if any rows have images
    if vendors_only:
        rows_with_images = len(analysis_df[
            cafe_filter & 
            analysis_df['vendor_name'].isin(vendors) &
            analysis_df['upload_links'].notna() & 
            (analysis_df['upload_links'] != '')
        ])
    else:
        rows_with_images = len(analysis_df[
            cafe_filter & 
            analysis_df['upload_links'].notna() & 
            (analysis_df['upload_links'] != '')
        ])
    
    st.write(f"- Rows with images to analyze: {rows_with_images}")
    
    if rows_with_images == 0:
        st.warning("No rows with images found for processing. The analysis will likely return empty results.")
    
    try:
        # Track time to show progress
        start_time = datetime.datetime.now()
        st.write(f"Starting analysis at {start_time.strftime('%H:%M:%S')}")
        
        # Call analyze_selected_locations with the vendors_only parameter
        result = analyze_selected_locations(
            analysis_df, cafes, vendors, api_key, vendors_only
        )
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        st.write(f"Analysis completed in {duration:.1f} seconds")
        
        return result
    except Exception as e:
        st.error(f"Error in analyze_selected_locations: {str(e)}")
        st.exception(e)
        # Return original dataframe with error columns
        analysis_df['compliance_status'] = "Error"
        analysis_df['explanation'] = f"Analysis failed: {str(e)}"
        return analysis_df

def analyze_selected_locations_wrapper(df, cafes, vendors, api_key, vendors_only=False):
    """Modified wrapper to call analyze_selected_locations with the proper arguments"""
    # Clone dataframe to avoid modifying original
    analysis_df = df.copy()
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Call the original function but make sure to pass all rows
        # analyze_selected_locations will do its own filtering
        status_text.text("Running analysis...")
        result = analyze_selected_locations(analysis_df, cafes, vendors, api_key)
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        
        # Check results
        if isinstance(result, pd.DataFrame) and len(result) > 0:
            status_text.text(f"Analysis returned {len(result)} rows of results")
            return result
        else:
            st.warning("Analysis returned empty results. This might be an issue with the data or the analysis function.")
            # Return the original with a message
            analysis_df['compliance_status'] = "No results"
            analysis_df['explanation'] = "Analysis completed but returned no results"
            return analysis_df
            
    except Exception as e:
        st.error(f"Error in analyze_selected_locations: {str(e)}")
        # Return original dataframe with error columns
        analysis_df['compliance_status'] = "Error"
        analysis_df['explanation'] = f"Analysis failed: {str(e)}"
        return analysis_df

def main():
    # App header with styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #3498db;
    }
    .subheader {
        font-size: 1.5rem;
        color: #3498db;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
  
    }
       .step-container {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 2rem;
        background-color: #f8f9fa;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
       .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: black;
    }
    .stDataFrame {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: white;
        border: 1px solid #e0e0e0;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        color: white;
    }
      .info-box {
        background-color: #2c3e50;
        border-left: 4px solid #3498db;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 0.3rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #ffffff;
    }
    
    .info-box h4 {
        color: #ffffff;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        font-weight: 500;
    }
    }
                 .info-box p {
        color: #ecf0f1;
        margin: 1rem 0;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-header'>Food Safety Compliance Analyzer</h1>", unsafe_allow_html=True)
    
    with st.expander("📋 Instructions", expanded=False):
        st.markdown("""
        <div class='info-box'>
        <h4>How to use this app:</h4>
        <ol>
            <li>Upload a CSV or Excel file containing your questions</li>
            <li>The file should have a column named 'questions' or 'question'</li>
            <li>Click 'Start Categorization' to process the questions</li>
            <li>Select locations to analyze</li>
            <li>Click 'Run Analysis' to analyze the selected locations</li>
            <li>Review the analysis results and export as needed</li>
        </ol>
        
        <p>The questions will be categorized into the following categories:</p>
        <ul>
            <li>Hygiene & Cleanliness</li>
            <li>Inventory & Storage</li>
            <li>Food Safety Compliance</li>
            <li>Hardware (Assets) & Other Equipment</li>
            <li>Marketing</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # STEP 1: File Upload Section
    st.markdown("<div class='step-container'>", unsafe_allow_html=True)
    st.markdown("<h2 class='subheader'>Step 1: Upload Your Data</h2>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx'], 
                                     on_change=reset_all)
    
    if uploaded_file is not None:
        try:
            # Only read file if not already loaded
            if st.session_state.df is None:
                # Read the file based on its type
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Handle common column format issues
                
                # Fix company_name if it exists but has spaces or capitalization issues
                cols_lower = [col.lower().strip() for col in df.columns]
                if 'company_name' not in df.columns and 'company name' in cols_lower:
                    actual_col = df.columns[cols_lower.index('company name')]
                    df.rename(columns={actual_col: 'company_name'}, inplace=True)
                    
                # Similarly fix other important columns
                column_mappings = {
                    'company name': 'company_name',
                    'companyname': 'company_name',
                    'location name': 'location_name',
                    'locationname': 'location_name',
                    'checklist name': 'checklist_name',
                    'checklistname': 'checklist_name',
                    'checklist type': 'checklist_type',
                    'checklisttype': 'checklist_type',
                    'question': 'question',
                    'vendor name': 'vendor_name',
                    'vendorname': 'vendor_name',
                }
                
                # Apply mappings where needed
                for wrong_name, right_name in column_mappings.items():
                    if wrong_name in cols_lower and right_name not in df.columns:
                        actual_col = df.columns[cols_lower.index(wrong_name)]
                        df.rename(columns={actual_col: right_name}, inplace=True)
                
                # Store in session state
                st.session_state.df = df
            else:
                df = st.session_state.df
                
            # Display the first few rows of the uploaded data
            st.dataframe(df.head(), use_container_width=True)

            # Check if 'questions' column exists
            if 'question' in df.columns and 'questions' not in df.columns:
                df = df.rename(columns={'question': 'questions'})
                st.session_state.df = df
            
            if 'questions' not in df.columns:
                st.error("Column 'questions' not found in the uploaded file.")
                st.write("Available columns:", df.columns.tolist())
                return
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.exception(e)
            return
    else:
        st.info("Please upload a file to continue")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # STEP 2: Categorization Section
    st.markdown("<div class='step-container'>", unsafe_allow_html=True)
    st.markdown("<h2 class='subheader'>Step 2: Categorize Questions</h2>", unsafe_allow_html=True)
    
    if not st.session_state.categorized:
        if st.button("Start Categorization"):
            with st.spinner("Categorizing questions... This may take a few minutes."):
                try:
                    # Get unique questions for categorization
                    unique_questions = st.session_state.df[['questions']].drop_duplicates()
                    
                    # Process only unique questions
                    st.info(f"Found {len(unique_questions)} unique questions to categorize")
                    categorized_unique_df = categorize_questions(unique_questions)
                    
                    # Create a mapping dictionary from unique categorized questions
                    question_to_category = dict(zip(categorized_unique_df['questions'], 
                                                   categorized_unique_df['categorization']))
                    
                    # Apply the mapping to the original dataframe
                    st.session_state.df['categorization'] = st.session_state.df['questions'].map(question_to_category)
                    
                    # Ensure 'questions' column is renamed to 'question' if needed by analyze_checklist.py
                    if 'question' not in st.session_state.df.columns:
                        st.session_state.df['question'] = st.session_state.df['questions']
                    
                    # Modify here: Create a mapping between cafes and their vendors
                    st.session_state.cafe_vendor_mapping = create_cafe_vendor_mapping(st.session_state.df)
                    
                    # Continue with the existing code
                    unique_cafes, unique_vendors, locations_output = identify_unique_locations(st.session_state.df)
                    
                    st.session_state.unique_cafes = unique_cafes
                    st.session_state.unique_vendors = unique_vendors
                    st.session_state.locations_output = locations_output
                    st.session_state.categorized = True
                    
                    st.success("Categorization completed successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error during categorization: {str(e)}")
                    st.exception(e)
    else:
        st.success("Questions have been categorized!")
        
        # Option to view categorized data
        if st.checkbox("Show categorized data sample"):
            st.dataframe(st.session_state.df[['questions', 'categorization']].head(10), use_container_width=True)
            
        # Option to reset categorization
        if st.button("Reset Categorization"):
            st.session_state.categorized = False
            st.session_state.unique_cafes = []
            st.session_state.unique_vendors = []
            st.session_state.locations_output = ""
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # STEP 3: Location Selection (only shown after categorization)
    if st.session_state.categorized:
        st.markdown("<div class='step-container'>", unsafe_allow_html=True)
        st.markdown("<h2 class='subheader'>Step 3: Select Locations to Analyze</h2>", unsafe_allow_html=True)
        
        # Display the unique cafes and vendors 
        with st.expander("Show all identified locations", expanded=False):
            st.code(st.session_state.locations_output)
            
            # Add display of cafe-vendor relationships with better formatting
            if st.session_state.cafe_vendor_mapping:
                st.markdown("### Cafe-Vendor Relationships")
                
                # Create a table for better presentation
                relationship_data = []
                for cafe, vendors in st.session_state.cafe_vendor_mapping.items():
                    for vendor in vendors:
                        relationship_data.append({
                            "Cafe Location": cafe,
                            "Vendor": vendor
                        })
                
                if relationship_data:
                    st.dataframe(pd.DataFrame(relationship_data), use_container_width=True)
                else:
                    st.info("No vendor relationships found in the data")

        # Initialize cafe_vendor_mapping if not present
        if 'cafe_vendor_mapping' not in st.session_state:
            st.session_state.cafe_vendor_mapping = {}

        # Create columns for location selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Select Cafes (max 5)")
            cafe_options = [(i, cafe) for i, cafe in enumerate(st.session_state.unique_cafes)]
            
            # Use multiselect for better UX
            selected_cafes_names = st.multiselect(
                "Choose cafes:",
                options=[cafe for _, cafe in cafe_options],
                default=st.session_state.selected_cafes,
                key="cafe_selector"
            )
            
            st.session_state.selected_cafes = selected_cafes_names
            
            if len(selected_cafes_names) > 5:
                st.warning("You selected more than 5 cafes. Only the first 5 will be analyzed.")
                st.session_state.selected_cafes = selected_cafes_names[:5]

        with col2:
            st.markdown("#### Select Vendors (max 5)")
            
            # Get all vendors from selected cafes
            available_vendors = []
            vendor_to_cafe_map = {}
            
            for cafe in st.session_state.selected_cafes:
                if cafe in st.session_state.cafe_vendor_mapping:
                    for vendor in st.session_state.cafe_vendor_mapping[cafe]:
                        available_vendors.append(vendor)
                        if vendor in vendor_to_cafe_map:
                            vendor_to_cafe_map[vendor].append(cafe)
                        else:
                            vendor_to_cafe_map[vendor] = [cafe]
            
            # Remove duplicates but preserve ordering
            available_vendors = list(dict.fromkeys(available_vendors))
            
            if available_vendors:
                # Format options to show where each vendor serves
                vendor_options = []
                for vendor in available_vendors:
                    cafes = vendor_to_cafe_map[vendor]
                    if len(cafes) > 1:
                        vendor_options.append(f"{vendor} - Serves in: {', '.join(cafes)}")
                    else:
                        vendor_options.append(f"{vendor} - {cafes[0]}")
            
                # Use multiselect with the formatted options
                selected_vendor_options = st.multiselect(
                    "Choose vendors serving in the selected cafe(s):",
                    options=vendor_options,
                    default=[opt for opt in vendor_options if any(v in opt for v in st.session_state.selected_vendors)],
                    key="vendor_selector"
                )
                
                # Extract the actual vendor names from the options
                selected_vendors_names = [opt.split(" - ")[0] for opt in selected_vendor_options]
                
                st.session_state.selected_vendors = selected_vendors_names
                
                if len(selected_vendors_names) > 5:
                    st.warning("You selected more than 5 vendors. Only the first 5 will be analyzed.")
                    st.session_state.selected_vendors = selected_vendors_names[:5]
            else:
                st.info("No vendors available for the selected cafes.")
                st.session_state.selected_vendors = []

        # If no cafes are selected but vendors are, show guidance
        if not st.session_state.selected_cafes and st.session_state.selected_vendors:
            st.warning("Please select at least one cafe to analyze vendors within it.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # STEP 4: Analysis Section
        st.markdown("<div class='step-container'>", unsafe_allow_html=True)
        st.markdown("<h2 class='subheader'>Step 4: Run Analysis</h2>", unsafe_allow_html=True)
        
        if st.session_state.selected_cafes or st.session_state.selected_vendors:
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
            st.write("Selected locations for analysis:")
            
            if st.session_state.selected_cafes:
                st.write("### Selected Cafes:")
                for cafe in st.session_state.selected_cafes:
                    st.write(f"- {cafe}")
            
            if st.session_state.selected_vendors:
                st.write("### Selected Vendors:")
                # Group vendors by cafés
                vendor_to_cafes = {}
                for vendor in st.session_state.selected_vendors:
                    vendor_to_cafes[vendor] = []
                    for cafe in st.session_state.selected_cafes:
                        if cafe in st.session_state.cafe_vendor_mapping and vendor in st.session_state.cafe_vendor_mapping[cafe]:
                            vendor_to_cafes[vendor].append(cafe)
                
                for vendor, cafes in vendor_to_cafes.items():
                    if cafes:
                        cafe_list = ", ".join(cafes)
                        st.write(f"- {vendor} (serves in: {cafe_list})")
                    else:
                        st.write(f"- {vendor}")
            
            # Add an option to analyze entire cafes or just vendors
            analyze_entire_cafes = False
            if st.session_state.selected_vendors:
                analyze_entire_cafes = st.checkbox("Also analyze the entire cafes (not just the selected vendors)", value=False)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if not st.session_state.analysis_complete:
                if st.button("Run Analysis"):
                    with st.spinner("Analyzing selected locations... This may take several minutes."):
                        try:
                            # Make sure we have the 'question' column for analyze_checklist.py
                            if 'question' not in st.session_state.df.columns:
                                st.session_state.df['question'] = st.session_state.df['questions']
                            
                            # Show data summary header
                            st.subheader("Analysis Setup")
                            
                            # Prepare for analysis based on selection mode
                            vendors_only = st.session_state.selected_vendors and not analyze_entire_cafes
                            
                            if vendors_only:
                                st.write("Mode: Analyzing ONLY selected vendors within selected cafes")
                            else:
                                st.write("Mode: Analyzing ALL entries in selected cafes")
                            
                            # Pass the vendors_only parameter to direct_analyze
                            analyzed_df = direct_analyze(
                                st.session_state.df,
                                st.session_state.selected_cafes,
                                st.session_state.selected_vendors,
                                openai.api_key,
                                vendors_only
                            )
                            
                            # Check if analysis produced results
                            if analyzed_df.empty:
                                st.error("Analysis completed but no results were produced.")
                                return
                            
                            # Generate summary
                            summary = generate_summary(analyzed_df)
                            
                            # Store in session state
                            st.session_state.analyzed_df = analyzed_df
                            st.session_state.summary = summary
                            st.session_state.analysis_complete = True
                            st.session_state.analyzed_vendors_only = vendors_only
                            
                            st.success("Analysis completed successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error during analysis: {str(e)}")
                            st.exception(e)
            else:
                st.success("Analysis completed!")
                
                # Option to reset analysis
                if st.button("Run New Analysis"):
                    reset_analysis()
                    st.rerun()
        else:
            st.warning("Please select at least one location to analyze")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # STEP 5: Results Section (only shown after analysis)
        if st.session_state.analysis_complete:
            st.markdown("<div class='step-container'>", unsafe_allow_html=True)
            st.markdown("<h2 class='subheader'>Step 5: Review Results</h2>", unsafe_allow_html=True)
            
            # Display analysis mode
            if hasattr(st.session_state, 'analyzed_vendors_only') and st.session_state.analyzed_vendors_only:
                st.info("Analysis was performed on vendor-specific entries only.")
            else:
                st.info("Analysis was performed on all entries for the selected cafes and vendors.")
            
            # Display analysis results
            with st.expander("Analysis Summary", expanded=True):
                st.code(st.session_state.summary)
            
            # Show sample of analysis results
            with st.expander("Sample Analysis Results", expanded=False):
                if 'compliance_status' in st.session_state.analyzed_df.columns:
                    result_cols = ['location_name', 'question', 'compliance_status', 'severity_level', 'explanation']
                    available_cols = [col for col in result_cols if col in st.session_state.analyzed_df.columns]
                    st.dataframe(st.session_state.analyzed_df[available_cols].head(10), use_container_width=True)
                else:
                    st.dataframe(st.session_state.analyzed_df.head(10), use_container_width=True)
            
            # Export options
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                        # Export options
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
            st.markdown("#### Export Results")
            col1, col2 = st.columns(2)
            
            # Save to Supabase
          
                           # Save to Supabase
            if not st.session_state.all_entries_saved:
                if st.button("Save to Database"):
                    with st.spinner("Saving entries to database..."):
                        try:
                            # Get the valid columns from the database schema
                            valid_columns = [
                                'id', 'company_name', 'location_name', 'checklist_name', 'checklist_type',
                                'question', 'question_type', 'vendor_name', 'answer_type', 'can_upload',
                                'can_comment', 'is_upload_mandatory', 'answer', 'extra_comment', 'is_skipped',
                                'categorization', 'answer_date', 'upload_links', 'compliance_status',
                                'explanation', 'improvement_suggestions', 'severity_level', 'image_quality_issues',
                                'quality_assessment', 'analysis_tags', 'analysis_date', 'created_at', 'updated_at'
                            ]
                            
                            # Convert DataFrame to list of dictionaries for insertion
                            records = st.session_state.analyzed_df.to_dict('records')
                            clean_records = []
                            
                            # Filter out invalid columns and handle NaN values
                            for record in records:
                                clean_record = {}
                                for key, value in record.items():
                                    if key in valid_columns:
                                        # Replace NaN values with None
                                        if pd.isna(value):
                                            clean_record[key] = None
                                        else:
                                            clean_record[key] = value
                                
                                # Add timestamps
                                clean_record['analysis_date'] = datetime.datetime.now().isoformat()
                                clean_record['created_at'] = datetime.datetime.now().isoformat()
                                clean_record['updated_at'] = datetime.datetime.now().isoformat()
                                clean_records.append(clean_record)
                            
                            # Insert in batches
                            batch_size = 20
                            total_records = len(clean_records)
                            
                            for i in range(0, total_records, batch_size):
                                batch = clean_records[i:min(i+batch_size, total_records)]
                                response = supabase_client.table('compliance_analysis_dynamic_entries').insert(batch).execute()
                                
                                # Store IDs from response
                                if hasattr(response, 'data'):
                                    for item in response.data:
                                        if 'id' in item:
                                            st.session_state.supabase_ids.append(item['id'])
                                
                                st.session_state.entries_saved += len(batch)
                                
                                # Show preview after 5 entries
                                if st.session_state.entries_saved >= 5 and not st.session_state.all_entries_saved:
                                    st.success(f"Saved {st.session_state.entries_saved} entries so far")
                                    preview_df = st.session_state.analyzed_df.head(5)
                                    st.dataframe(preview_df, use_container_width=True) 
                            
                            st.session_state.all_entries_saved = True
                            st.success(f"All {total_records} entries saved to database!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving to database: {str(e)}")
                            st.exception(e)
            else:
                st.success(f"All {st.session_state.entries_saved} entries saved to database!")
            
            with col1:
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    st.session_state.analyzed_df.to_excel(writer, index=False, sheet_name='Analysis Results')
                output.seek(0)
                
                st.download_button(
                    label="Export All Results as Excel",
                    data=output,
                    file_name=f"full_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="export_all"
                )
            
            with col2:
                # Filter non-compliant items
                if 'compliance_status' in st.session_state.analyzed_df.columns:
                    non_compliant_df = st.session_state.analyzed_df[st.session_state.analyzed_df['compliance_status'] == 'No']
                    if not non_compliant_df.empty:
                        # Create Excel file in memory for non-compliant items
                        nc_output = io.BytesIO()
                        with pd.ExcelWriter(nc_output, engine='xlsxwriter') as writer:
                            non_compliant_df.to_excel(writer, index=False, sheet_name='Non-Compliant Items')
                        nc_output.seek(0)
                        
                        st.download_button(
                            label="Export Non-Compliant Items as Excel",
                            data=nc_output,
                            file_name=f"non_compliant_items_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="export_non_compliant"
                        )
                    else:
                        st.info("No non-compliant items found.")
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 