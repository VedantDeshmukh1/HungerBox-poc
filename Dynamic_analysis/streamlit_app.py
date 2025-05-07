import streamlit as st
import pandas as pd
import openai
from dotenv import load_dotenv
import datetime
import os
from mapping_questions import categorize_questions
from analyze_checklist import identify_unique_locations, analyze_selected_locations, generate_summary
import supabase
import io
import uuid

# Page configuration
st.set_page_config(page_title="Food Safety Analyzer", layout="wide", page_icon="🍽️")
# Remove load_dotenv() since we'll use st.secrets
# load_dotenv()

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
                    
                    # Identify unique cafes and vendors
                    unique_cafes, unique_vendors, locations_output = identify_unique_locations(st.session_state.df)
                    
                    # Store in session state
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
            vendor_options = [(i, vendor) for i, vendor in enumerate(st.session_state.unique_vendors)]
            
            # Use multiselect for better UX
            selected_vendors_names = st.multiselect(
                "Choose vendors:",
                options=[vendor for _, vendor in vendor_options],
                default=st.session_state.selected_vendors,
                key="vendor_selector"
            )
            
            st.session_state.selected_vendors = selected_vendors_names
            
            if len(selected_vendors_names) > 5:
                st.warning("You selected more than 5 vendors. Only the first 5 will be analyzed.")
                st.session_state.selected_vendors = selected_vendors_names[:5]
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # STEP 4: Analysis Section
        st.markdown("<div class='step-container'>", unsafe_allow_html=True)
        st.markdown("<h2 class='subheader'>Step 4: Run Analysis</h2>", unsafe_allow_html=True)
        
        if st.session_state.selected_cafes or st.session_state.selected_vendors:
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
            st.write("Selected locations for analysis:")
            if st.session_state.selected_cafes:
                st.write("- Cafes: " + ", ".join(st.session_state.selected_cafes))
            if st.session_state.selected_vendors:
                st.write("- Vendors: " + ", ".join(st.session_state.selected_vendors))
            st.markdown("</div>", unsafe_allow_html=True)
            
            if not st.session_state.analysis_complete:
                if st.button("Run Analysis"):
                    with st.spinner("Analyzing selected locations... This may take several minutes."):
                        try:
                            # Make sure we have the 'question' column for analyze_checklist.py
                            if 'question' not in st.session_state.df.columns:
                                st.session_state.df['question'] = st.session_state.df['questions']
                            
                            # Run the analysis
                            analyzed_df = analyze_selected_locations(
                                st.session_state.df, 
                                st.session_state.selected_cafes, 
                                st.session_state.selected_vendors, 
                                openai.api_key
                            )
                            
                            # Generate summary
                            summary = generate_summary(analyzed_df)
                            
                            # Store in session state
                            st.session_state.analyzed_df = analyzed_df
                            st.session_state.summary = summary
                            st.session_state.analysis_complete = True
                            
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