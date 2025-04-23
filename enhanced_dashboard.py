import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
from wordcloud import WordCloud
import calendar
from supabase import create_client, Client
import io
import uuid

# Set page configuration
st.set_page_config(
    page_title="Food Safety Compliance Dashboard",
    page_icon="🍽️",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Global styles */
    .main {
        background-color: #f9f9f9;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1E3A8A;
    }
    
    h1 {
        text-align: center;
        padding-bottom: 10px;
        border-bottom: 2px solid #3B82F6;
    }
    
    h2 {
        padding-top: 20px;
        margin-bottom: 20px;
    }
    
    /* Dashboard cards */
 
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #4B5563;
    }
    
    /* Chart containers - Updated for better visibility */
 
    
    
    /* Status indicators */
    .status-good {
        color: #10B981;
        font-weight: bold;
    }
    
    .status-warning {
        color: #F59E0B;
        font-weight: bold;
    }
    
    .status-critical {
        color: #EF4444;
        font-weight: bold;
    }
    
    /* Filter section */
    .filter-container {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    /* Data table formatting */
    .dataframe {
        width: 100%;
        border-collapse: collapse;
    }
    
    .dataframe th {
        background-color: #DBEAFE;
        font-weight: bold;
        text-align: left;
        padding: 12px;
        color: #1E40AF;
    }
    
    .dataframe td {
        border-bottom: 1px solid #E5E7EB;
        padding: 12px;
        background-color: #FFFFFF;
    }
    
    .dataframe tr:hover {
        background-color: #F3F4F6;
    }
    
    /* Issue cards */
    .issue-card {
        margin-bottom: 15px;
        padding: 15px;
        border-left: 4px solid #EF4444;
        background-color: #FEF2F2;
        border-radius: 5px;
        color: #7F1D1D;
    }
    
    /* Category metrics box */
    .category-metrics {
        padding: 15px;
        background-color: #EFF6FF;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 4px solid #3B82F6;
        color: #1E3A8A;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Make expandables more visible */
    .streamlit-expanderHeader {
        background-color: #DBEAFE !important;
        border-radius: 5px !important;
        padding: 10px !important;
        font-weight: bold !important;
        color: #1E40AF !important;
    }
    
    .streamlit-expanderContent {
        background-color: #F9FAFB !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 0 0 5px 5px !important;
        padding: 15px !important;
    }
    
    /* Make info messages more visible */
    
    
    /* Make subheaders stand out */
    .stSubheader {
        color: #1E3A8A !important;
        font-weight: bold !important;
        border-bottom: 2px solid #BFDBFE !important;
        padding-bottom: 5px !important;
    }
    
    /* Fix tabs contrast */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #DBEAFE !important;
        border-radius: 10px 10px 0 0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #1E40AF !important;
        font-weight: bold !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #93C5FD !important;
        color: #1E3A8A !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase client
@st.cache_resource
def init_supabase():

    url = st.secrets["supabase"]["url"]
    key =  st.secrets["supabase"]["key"]
    return create_client(url, key)

# Function to load data from Supabase
@st.cache_data
def load_data_from_supabase():
    try:
        supabase = init_supabase()
        
        # Retrieve all records using paging
        all_records = []
        page_size = 1000  # Supabase recommended page size
        offset = 0
        
        while True:
            response = supabase.table("food_safety_records").select("*").range(offset, offset + page_size - 1).execute()
            
            if response.data:
                all_records.extend(response.data)  # Add fetched records to the list
                offset += page_size  # Move to the next set of records
                
                # Show progress if many records
                if offset % 3000 == 0:
                    st.info(f"Loading data... Retrieved {len(all_records)} records so far.")
            else:
                break  # Exit loop if no more records
        
        if not all_records:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_records)
        
        # Handle date columns with proper error handling
        if 'answer_date' in df.columns:
            # Force convert to datetime, coerce errors to NaT
            df['answer_date'] = pd.to_datetime(df['answer_date'], errors='coerce')
            # Create analysis_date column if it doesn't exist
            if 'analysis_date' not in df.columns:
                df['analysis_date'] = df['answer_date']
        
        if 'analysis_date' in df.columns:
            # Force convert to datetime, coerce errors to NaT
            df['analysis_date'] = pd.to_datetime(df['analysis_date'], errors='coerce')
        
        # Convert boolean columns
        bool_columns = ['can_upload', 'can_comment', 'is_upload_mandatory', 'is_skipped']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        
        return df
    except Exception as e:
        st.error(f"Error loading data from Supabase: {e}")
        return pd.DataFrame()

# Function to upload Excel file to Supabase
def upload_excel_to_supabase(uploaded_file):
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file)
        
        # Convert to records for insertion
        records = df.to_dict(orient='records')
        
        # Add created_at field to each record
        current_time = datetime.now().isoformat()
        for record in records:
            record['created_at'] = current_time
            # Convert any datetime objects to ISO strings
            for key, value in record.items():
                if isinstance(value, pd.Timestamp) or isinstance(value, datetime):
                    record[key] = value.isoformat()
                # Handle boolean values for proper PostgreSQL format
                elif isinstance(value, bool):
                    pass  # Keep as is, Supabase handles this correctly
                # Handle NaN values
                elif pd.isna(value):
                    record[key] = None
        
        # Get Supabase client
        supabase = init_supabase()
        
        # Insert records in batches to avoid payload limits
        batch_size = 100
        results = []
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            result = supabase.table("food_safety_records").insert(batch).execute()
            results.append(result)
            
        st.success(f"Successfully uploaded {len(records)} records to Supabase!")
        return True
    except Exception as e:
        st.error(f"Error uploading to Supabase: {e}")
        return False

# Function to generate SQL script for data insertion
def generate_insert_sql(uploaded_file):
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file)
        
        # Convert DataFrame to SQL INSERT statements
        table_name = "food_safety_records"
        
        # Start SQL script
        sql_script = f"-- SQL Script to insert food safety records\n\n"
        
        # Get column names
        columns = df.columns.tolist()
        columns_str = ", ".join([f'"{col}"' for col in columns])
        
        # Add created_at column
        columns_str += ', "created_at"'
        
        # Create INSERT statements for each row
        for _, row in df.iterrows():
            values = []
            for col in columns:
                val = row[col]
                # Handle different data types
                if pd.isna(val):
                    values.append("NULL")
                elif isinstance(val, bool):
                    values.append(str(val).lower())  # Convert to lowercase true/false for PostgreSQL
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                elif isinstance(val, (datetime, pd.Timestamp)):
                    values.append(f"'{val.isoformat()}'")
                else:
                    # Escape single quotes in strings
                    values.append(f"'{str(val).replace('\'', '\'\'')}'")
            
            # Add current timestamp for created_at
            values.append(f"'{datetime.now().isoformat()}'")
            
            values_str = ", ".join(values)
            sql_script += f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});\n"
        
        return sql_script
    except Exception as e:
        st.error(f"Error generating SQL script: {e}")
        return None

# Function to extract most common issues from explanation and improvements
def extract_common_issues(df):
    # Combine explanations and improvements for text analysis
    text_data = pd.Series(' '.join(df['explanation'].fillna('') + ' ' + df['improvement_suggestions'].fillna('')))
    
    # List of common food safety issue keywords
    issue_keywords = {
        'Cleanliness': ['dirt', 'clean', 'sanitize', 'hygiene', 'washing'],
        'Temperature': ['temperature', 'hot', 'cold', 'frozen', 'refrigerat', 'cooling'],
        'Storage': ['storage', 'shelf', 'container', 'store', 'stock'],
        'Cross-contamination': ['cross-contamination', 'separate', 'raw', 'cooked'],
        'Equipment': ['equipment', 'utensil', 'machine', 'tools', 'maintenance'],
        'Personal Hygiene': ['hair', 'gloves', 'uniform', 'handwashing', 'nail'],
        'Documentation': ['label', 'document', 'record', 'log', 'checklist'],
        'Pests': ['pest', 'insect', 'rodent', 'fly', 'cockroach'],
        'Expiry': ['expir', 'date', 'shelf life', 'outdated', 'spoil'],
        'Training': ['training', 'knowledge', 'awareness', 'education', 'procedure']
    }
    
    # Count occurrences of each issue type
    issue_counts = {}
    
    for issue, keywords in issue_keywords.items():
        count = 0
        for keyword in keywords:
            count += text_data.str.count(keyword).sum()
        issue_counts[issue] = count
    
    # Convert to dataframe for visualization
    issues_df = pd.DataFrame(list(issue_counts.items()), columns=['Issue', 'Count'])
    issues_df = issues_df.sort_values('Count', ascending=False)
    
    return issues_df

# Function to create a severity breakdown chart
def create_severity_chart(df):
    if 'severity_level' not in df.columns or df['severity_level'].isna().all():
        # Create a default chart with empty data
        empty_df = pd.DataFrame({'Severity': ['Critical', 'Major', 'Minor', 'None'], 'Count': [0, 0, 0, 0]})
        fig = px.bar(
            empty_df, 
            x='Severity', 
            y='Count',
            title='Breakdown by Severity Level (No Data)',
            color='Severity'
        )
        return fig
        
    severity_counts = df['severity_level'].value_counts().reset_index()
    severity_counts.columns = ['Severity', 'Count']
    
    # Define severity order and colors
    severity_order = ['Critical', 'Major', 'Minor', 'None']
    severity_colors = {'Critical': '#EF4444', 'Major': '#F59E0B', 'Minor': '#3B82F6', 'None': '#10B981'}
    
    # Create ordered categories
    severity_counts['Severity'] = pd.Categorical(
        severity_counts['Severity'], 
        categories=severity_order,
        ordered=True
    )
    
    # Sort by the ordered category
    severity_counts = severity_counts.sort_values('Severity')
    
    # Create a color list based on our severity values
    colors = [severity_colors.get(severity, '#6B7280') for severity in severity_counts['Severity']]
    
    fig = px.bar(
        severity_counts, 
        x='Severity', 
        y='Count',
        title='Breakdown by Severity Level',
        color='Severity',
        color_discrete_map=severity_colors,
        category_orders={"Severity": severity_order}
    )
    
    fig.update_layout(
        xaxis_title='Severity Level',
        yaxis_title='Number of Findings',
        height=400,
        margin=dict(l=40, r=40, t=50, b=40)
    )
    
    return fig

# Function to create compliance trend chart
def create_compliance_trend(df, date_column='analysis_date'):
    # Make sure we have date data
    if date_column not in df.columns or df[date_column].isna().all():
        return None
    
    # Group by date and calculate compliance rate
    df['Date'] = df[date_column].dt.date
    daily_stats = df.groupby('Date').agg(
        Compliant=('compliance_status', lambda x: (x == 'Yes').sum()),
        Total=('compliance_status', 'count')
    ).reset_index()
    
    daily_stats['Compliance_Rate'] = (daily_stats['Compliant'] / daily_stats['Total'] * 100).round(1)
    
    # Sort by date
    daily_stats = daily_stats.sort_values('Date')
    
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=daily_stats['Date'],
        y=daily_stats['Compliance_Rate'],
        mode='lines+markers',
        name='Compliance Rate',
        line=dict(color='#3B82F6', width=3),
        marker=dict(size=8)
    ))
    
    # Add a target line at 90%
    fig.add_trace(go.Scatter(
        x=[daily_stats['Date'].min(), daily_stats['Date'].max()],
        y=[90, 90],
        mode='lines',
        name='Target (90%)',
        line=dict(color='#10B981', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='Compliance Rate Trend Over Time',
        xaxis_title='Date',
        yaxis_title='Compliance Rate (%)',
        height=400,
        margin=dict(l=40, r=40, t=50, b=40),
        yaxis=dict(range=[0, 105]),
        hovermode='x unified'
    )
    
    return fig

# Function to create location comparison chart
def create_location_comparison(df, location_type):
    if location_type == 'All':
        location_df = df
        title = 'Compliance Rate by Location'
    else:
        location_df = df[df['checklist_type'] == location_type.lower()]
        title = f'Compliance Rate by {location_type} Location'
    
    if location_df.empty:
        return None
    
    # Calculate compliance rate by location
    location_stats = location_df.groupby('location_name').agg(
        Compliant=('compliance_status', lambda x: (x == 'Yes').sum()),
        Non_Compliant=('compliance_status', lambda x: (x == 'No').sum()),
        Error=('compliance_status', lambda x: ((x != 'Yes') & (x != 'No')).sum()),
        Total=('compliance_status', 'count')
    ).reset_index()
    
    location_stats['Compliance_Rate'] = (location_stats['Compliant'] / location_stats['Total'] * 100).round(1)
    
    # Sort by compliance rate
    location_stats = location_stats.sort_values('Compliance_Rate')
    
    # Create a stacked bar chart
    fig = go.Figure()
    
    # Add bars for compliant, non-compliant, and error
    fig.add_trace(go.Bar(
        x=location_stats['location_name'],
        y=location_stats['Compliant'],
        name='Compliant',
        marker_color='#10B981'
    ))
    
    fig.add_trace(go.Bar(
        x=location_stats['location_name'],
        y=location_stats['Non_Compliant'],
        name='Non-Compliant',
        marker_color='#EF4444'
    ))
    
    fig.add_trace(go.Bar(
        x=location_stats['location_name'],
        y=location_stats['Error'],
        name='Unable to Determine',
        marker_color='#9CA3AF'
    ))
    
    # Add a line for compliance rate
    fig.add_trace(go.Scatter(
        x=location_stats['location_name'],
        y=location_stats['Compliance_Rate'],
        mode='lines+markers',
        name='Compliance Rate (%)',
        yaxis='y2',
        line=dict(color='#3B82F6', width=3),
        marker=dict(size=10)
    ))
    
    # Update layout with dual axis
    fig.update_layout(
        title=title,
        xaxis_title='Location',
        yaxis=dict(
            title='Number of Findings',
            side='left'
        ),
        yaxis2=dict(
            title='Compliance Rate (%)',
            side='right',
            overlaying='y',
            range=[0, 100]
        ),
        barmode='stack',
        height=500,
        margin=dict(l=40, r=40, t=50, b=150),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x unified'
    )
    
    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=-45)
    
    return fig

# Function to create a category comparison chart
def create_category_comparison(df):
    # Extract categories from JSON-like string if needed
    if 'categorization' in df.columns:
        # First try to extract categories
        all_categories = []
        
        for cat_str in df['categorization'].dropna():
            try:
                if isinstance(cat_str, str):
                    # Try to extract from bracket format [Cat1, Cat2]
                    match = re.search(r'\[(.*?)\]', cat_str)
                    if match:
                        categories = [c.strip() for c in match.group(1).split(',')]
                        all_categories.extend(categories)
                    else:
                        all_categories.append(cat_str.strip())
                elif isinstance(cat_str, list):
                    all_categories.extend(cat_str)
            except:
                pass
        
        # Count occurrences of each category
        category_counts = pd.Series(all_categories).value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']
        
        # Sort by count
        category_counts = category_counts.sort_values('Count', ascending=False)
        
        fig = px.bar(
            category_counts,
            x='Category',
            y='Count',
            title='Findings by Category',
            color='Count',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_title='Category',
            yaxis_title='Number of Findings',
            height=400,
            margin=dict(l=40, r=40, t=50, b=100)
        )
        
        # Rotate x-axis labels for better readability
        fig.update_xaxes(tickangle=-45)
        
        return fig
    
    return None

# Function to create tag chart
def create_tag_chart(df):
    if 'analysis_tags' not in df.columns or df['analysis_tags'].isna().all():
        return None
    
    # Combine all tags
    all_tags = []
    for tags_str in df['analysis_tags'].dropna():
        if isinstance(tags_str, str):
            tags = [tag.strip() for tag in tags_str.split(',')]
            all_tags.extend(tags)
    
    # Count occurrences
    tag_counts = pd.Series(all_tags).value_counts().reset_index()
    tag_counts.columns = ['Tag', 'Count']
    
    # Keep only top 15 tags
    tag_counts = tag_counts.head(15)
    
    if tag_counts.empty:
        return None
    
    # Create horizontal bar chart
    fig = px.bar(
        tag_counts,
        y='Tag',
        x='Count',
        orientation='h',
        title='Top 15 Most Common Tags',
        color='Count',
        color_continuous_scale='Viridis',
        height=400
    )
    
    fig.update_layout(
        xaxis_title='Count',
        yaxis_title='',
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    return fig

# Function to create compliance by checklist type chart
def create_checklist_comparison(df):
    # Calculate compliance rate by checklist type
    checklist_stats = df.groupby('checklist_name').agg(
        Compliant=('compliance_status', lambda x: (x == 'Yes').sum()),
        Non_Compliant=('compliance_status', lambda x: (x == 'No').sum()),
        Error=('compliance_status', lambda x: ((x != 'Yes') & (x != 'No')).sum()),
        Total=('compliance_status', 'count')
    ).reset_index()
    
    checklist_stats['Compliance_Rate'] = (checklist_stats['Compliant'] / checklist_stats['Total'] * 100).round(1)
    
    # Sort by total count
    checklist_stats = checklist_stats.sort_values('Total', ascending=False)
    
    # Use only top N checklists to avoid overcrowding
    top_n = min(10, len(checklist_stats))
    checklist_stats = checklist_stats.head(top_n)
    
    fig = px.bar(
        checklist_stats,
        x='checklist_name',
        y='Compliance_Rate',
        title=f'Compliance Rate by Checklist Type (Top {top_n})',
        color='Compliance_Rate',
        color_continuous_scale='RdYlGn',
        text='Compliance_Rate'
    )
    
    fig.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside'
    )
    
    fig.update_layout(
        xaxis_title='Checklist Type',
        yaxis_title='Compliance Rate (%)',
        yaxis=dict(range=[0, 100]),
        height=450,
        margin=dict(l=40, r=40, t=50, b=150)
    )
    
    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=-45)
    
    return fig

# Main application
def main():
    st.title("🍽️ Food Safety Compliance Dashboard")
    
    # Create tabs for different actions
    main_tabs = st.tabs(["Dashboard", "Data Upload"])
    
    # Tab 1: Dashboard
    with main_tabs[0]:
        # Load data from Supabase
        df = load_data_from_supabase()
        
        if df.empty:
            st.warning("No data found in the database. Please use the Data Upload tab to add records.")
            return
        
        # Display basic info
        st.markdown(f"### Analysis Overview")
        st.info(f"Loaded {len(df)} records from Supabase")
        
        # Create sidebar filters
        st.sidebar.header("Filters")
        
        # Determine available filters based on data
        available_companies = sorted([c for c in df['company_name'].unique() if c is not None]) if 'company_name' in df.columns else []
        available_locations = sorted([l for l in df['location_name'].unique() if l is not None]) if 'location_name' in df.columns else []
        available_vendors = sorted([v for v in df['vendor_name'].unique() if v is not None]) if 'vendor_name' in df.columns else []
        available_categories = []
        
        # Extract unique categories from the categorization field
        if 'categorization' in df.columns:
            for cat_str in df['categorization'].dropna().unique():
                try:
                    if isinstance(cat_str, str):
                        # Try to extract from bracket format [Cat1, Cat2]
                        match = re.search(r'\[(.*?)\]', cat_str)
                        if match:
                            categories = [c.strip() for c in match.group(1).split(',')]
                            available_categories.extend(categories)
                        else:
                            available_categories.append(cat_str.strip())
                except:
                    pass
            available_categories = sorted(list(set(available_categories)))
        
        # Compliance status filter
        selected_compliance = st.sidebar.multiselect(
            "Compliance Status",
            options=["Yes", "No", "Unable to determine", "Error"],
            default=["Yes", "No", "Unable to determine", "Error"]
        )
        
        # Location type filter
        selected_location_type = st.sidebar.radio(
            "Location Type",
            options=["All", "Cafe", "Vendor"],
            index=0
        )
        
        # Company filter
        selected_company = st.sidebar.selectbox(
            "Company",
            options=["All"] + available_companies,
            index=0
        )
        
        # Vendor filter
        if available_vendors:
            selected_vendor = st.sidebar.selectbox(
                "Vendor",
                options=["All"] + available_vendors,
                index=0
            )
        else:
            selected_vendor = "All"
        
        # Category filter
        if available_categories:
            selected_category = st.sidebar.selectbox(
                "Category",
                options=["All"] + available_categories,
                index=0
            )
        else:
            selected_category = "All"
        
        # Location filter based on location type
        if selected_location_type == "All":
            location_options = ["All"] + available_locations
        else:
            location_options = ["All"] + list(df[df['checklist_type'] == selected_location_type.lower()]['location_name'].unique())
        
        selected_location = st.sidebar.selectbox(
            "Location",
            options=location_options,
            index=0
        )
        
        # Date range filter based on available date columns
        has_answer_date = 'answer_date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['answer_date']) and not df['answer_date'].isna().all()
        has_analysis_date = 'analysis_date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['analysis_date']) and not df['analysis_date'].isna().all()

        # Determine which date column to use for filtering
        date_filter_options = []
        if has_answer_date:
            date_filter_options.append("Answer Date")
        if has_analysis_date:
            date_filter_options.append("Analysis Date")

        # Initialize date variables
        start_date = None
        end_date = None
        date_column = None

        if date_filter_options:
            # Let user select which date to filter by
            selected_date_type = st.sidebar.radio(
                "Filter by Date",
                options=date_filter_options,
                index=0
            )
            
            # Set the date column to use based on user selection
            date_column = 'answer_date' if selected_date_type == "Answer Date" else 'analysis_date'
            
            try:
                # Get valid date range, handling potential errors
                valid_dates = df[date_column].dropna()
                if len(valid_dates) > 0:
                    min_date = valid_dates.min().date()
                    max_date = valid_dates.max().date()
                    
                    # Add option for single day or range selection
                    date_selection_mode = st.sidebar.radio(
                        "Date Selection Mode",
                        options=["Range", "Single Day"],
                        index=0
                    )
                    
                    if date_selection_mode == "Range":
                        selected_date_range = st.sidebar.date_input(
                            f"{selected_date_type} Range",
                            value=(min_date, max_date),
                            min_value=min_date,
                            max_value=max_date
                        )
                        
                        if len(selected_date_range) == 2:
                            start_date, end_date = selected_date_range
                        else:
                            start_date = selected_date_range[0]
                            end_date = selected_date_range[0]
                    else:  # Single Day mode
                        single_date = st.sidebar.date_input(
                            f"Select {selected_date_type}",
                            value=min_date,
                            min_value=min_date,
                            max_value=max_date
                        )
                        start_date = single_date
                        end_date = single_date
                    
                    # Show currently selected date range in sidebar
                    if start_date == end_date:
                        st.sidebar.info(f"Showing data for: {start_date.strftime('%b %d, %Y')}")
                    else:
                        st.sidebar.info(f"Date range: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")
                    
                else:
                    st.sidebar.warning(f"No valid dates found in {selected_date_type} column")
            except Exception as e:
                st.sidebar.warning(f"Error filtering by date: {str(e)}")
        
        # Initialize the filtered dataframe
        filtered_df = df.copy()

        # Apply date filter if date selection is active
        if date_filter_options and start_date is not None and end_date is not None and date_column is not None:
            filtered_df = filtered_df[(filtered_df[date_column].dt.date >= start_date) & 
                                     (filtered_df[date_column].dt.date <= end_date)]

        # Apply other filters
        if selected_compliance:
            filtered_df = filtered_df[filtered_df['compliance_status'].isin(selected_compliance)]

        if selected_location_type != "All":
            filtered_df = filtered_df[filtered_df['checklist_type'] == selected_location_type.lower()]

        if selected_company != "All" and 'company_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['company_name'] == selected_company]
            
        if selected_vendor != "All" and 'vendor_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['vendor_name'] == selected_vendor]

        if selected_location != "All":
            filtered_df = filtered_df[filtered_df['location_name'] == selected_location]
            
        # Category filter
        if selected_category != "All" and 'categorization' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['categorization'].apply(
                lambda x: selected_category in str(x) if not pd.isna(x) else False
            )]

        # Display filtered data summary
        st.markdown(f"Showing {len(filtered_df)} records after filtering")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Location Analysis", "Category Analysis", "Data Table"])
        
        # TAB 1: Overview
        with tab1:
            # Top metrics
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate key metrics
            total_entries = len(filtered_df)
            compliance_rate = (filtered_df['compliance_status'] == 'Yes').sum() / total_entries * 100 if total_entries > 0 else 0
            non_compliance = (filtered_df['compliance_status'] == 'No').sum()
            
            if 'severity_level' in filtered_df.columns:
                critical_issues = filtered_df[filtered_df['severity_level'] == 'Critical'].shape[0]
            else:
                critical_issues = 0
            
            # Display metrics
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{total_entries}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Total Inspections</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                compliance_color = "#10B981" if compliance_rate >= 90 else "#F59E0B" if compliance_rate >= 70 else "#EF4444"
                st.markdown(f'<div class="metric-value" style="color:{compliance_color}">{compliance_rate:.1f}%</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Compliance Rate</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value" style="color:#F59E0B">{non_compliance}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Non-Compliant Items</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value" style="color:#EF4444">{critical_issues}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Critical Issues</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Compliance trend chart
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            if date_filter_options:
                trend_chart = create_compliance_trend(filtered_df, date_column)
            else:
                # Try analysis_date as fallback, or don't show chart if no valid dates
                if has_analysis_date:
                    trend_chart = create_compliance_trend(filtered_df, 'analysis_date')
                else:
                    trend_chart = None
            
            if trend_chart:
                st.plotly_chart(trend_chart, use_container_width=True)
            else:
                st.info("Not enough date information to show compliance trend.")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Two columns for severity and category charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                severity_chart = create_severity_chart(filtered_df)
                st.plotly_chart(severity_chart, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                category_chart = create_category_comparison(filtered_df)
                if category_chart:
                    st.plotly_chart(category_chart, use_container_width=True)
                else:
                    st.info("No category data available.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Common issues and tags
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader("Common Issues")
                issues_df = extract_common_issues(filtered_df)
                fig = px.bar(
                    issues_df.head(10),
                    x='Count',
                    y='Issue',
                    orientation='h',
                    title='Top 10 Issue Types',
                    color='Count',
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader("Top Tags")
                tag_chart = create_tag_chart(filtered_df)
                if tag_chart:
                    st.plotly_chart(tag_chart, use_container_width=True)
                else:
                    st.info("No tag data available.")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # TAB 2: Location Analysis
        with tab2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            location_chart = create_location_comparison(filtered_df, selected_location_type)
            if location_chart:
                st.plotly_chart(location_chart, use_container_width=True)
            else:
                st.info(f"No location data available for the selected filters.")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Checklist compliance by type
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            checklist_chart = create_checklist_comparison(filtered_df)
            st.plotly_chart(checklist_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Location type breakdown
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("Compliance by Location Type")
            
            type_stats = filtered_df.groupby('checklist_type').agg(
                Compliant=('compliance_status', lambda x: (x == 'Yes').sum()),
                Non_Compliant=('compliance_status', lambda x: (x == 'No').sum()),
                Total=('compliance_status', 'count')
            ).reset_index()
            
            type_stats['Compliance_Rate'] = (type_stats['Compliant'] / type_stats['Total'] * 100).round(1)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    type_stats,
                    values='Total',
                    names='checklist_type',
                    title='Distribution of Checks by Location Type',
                    color='checklist_type',
                    color_discrete_map={'cafe': '#3B82F6', 'vendor': '#10B981'},
                    hole=0.4
                )
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    type_stats,
                    x='checklist_type',
                    y=['Compliant', 'Non_Compliant'],
                    title='Compliance Status by Location Type',
                    barmode='group',
                    color_discrete_map={'Compliant': '#10B981', 'Non_Compliant': '#EF4444'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # TAB 3: Category Analysis
        with tab3:
            # Categorization by compliance status
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("Category Compliance Analysis")
            
            # Extract categories if available
            if 'categorization' in filtered_df.columns:
                # Extract categories
                all_category_records = []
                
                for idx, row in filtered_df.iterrows():
                    if pd.isna(row['categorization']):
                        continue
                        
                    cat_str = row['categorization']
                    cats = []
                    
                    try:
                        if isinstance(cat_str, str):
                            # Try to extract from bracket format [Cat1, Cat2]
                            match = re.search(r'\[(.*?)\]', cat_str)
                            if match:
                                cats = [c.strip() for c in match.group(1).split(',')]
                            else:
                                cats = [cat_str.strip()]
                        elif isinstance(cat_str, list):
                            cats = cat_str
                    except:
                        continue
                    
                    for cat in cats:
                        all_category_records.append({
                            'category': cat,
                            'compliance_status': row['compliance_status'],
                            'severity_level': row.get('severity_level', 'Unknown')
                        })
                
                if all_category_records:
                    cat_df = pd.DataFrame(all_category_records)
                    
                    # Compliance by category
                    cat_compliance = cat_df.groupby('category').agg(
                        Compliant=('compliance_status', lambda x: (x == 'Yes').sum()),
                        Non_Compliant=('compliance_status', lambda x: (x == 'No').sum()),
                        Total=('compliance_status', 'count')
                    ).reset_index()
                    
                    cat_compliance['Compliance_Rate'] = (cat_compliance['Compliant'] / cat_compliance['Total'] * 100).round(1)
                    cat_compliance = cat_compliance.sort_values('Compliance_Rate')
                    
                    # Create visualization
                    fig = px.bar(
                        cat_compliance,
                        x='category',
                        y='Compliance_Rate',
                        title='Compliance Rate by Category',
                        color='Compliance_Rate',
                        color_continuous_scale='RdYlGn',
                        text='Compliance_Rate'
                    )
                    
                    fig.update_traces(
                        texttemplate='%{text:.1f}%',
                        textposition='outside'
                    )
                    
                    fig.update_layout(
                        xaxis_title='Category',
                        yaxis_title='Compliance Rate (%)',
                        yaxis=dict(range=[0, 100]),
                        height=450,
                        margin=dict(l=40, r=40, t=50, b=150)
                    )
                    
                    # Rotate x-axis labels for better readability
                    fig.update_xaxes(tickangle=-45)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Severity levels by category
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Category distribution pie chart
                        cat_counts = cat_df['category'].value_counts().reset_index()
                        cat_counts.columns = ['Category', 'Count']
                        
                        fig = px.pie(
                            cat_counts,
                            values='Count',
                            names='Category',
                            title='Distribution of Categories',
                            hole=0.4
                        )
                        
                        fig.update_traces(textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Critical findings by category
                        if 'severity_level' in cat_df.columns:
                            severe_cats = cat_df[cat_df['severity_level'].isin(['Critical', 'Major'])].groupby('category').size().reset_index()
                            severe_cats.columns = ['Category', 'Count']
                            severe_cats = severe_cats.sort_values('Count', ascending=False)
                            
                            fig = px.bar(
                                severe_cats,
                                x='Category',
                                y='Count',
                                title='Critical and Major Findings by Category',
                                color='Count',
                                color_continuous_scale='Reds'
                            )
                            
                            fig.update_layout(
                                xaxis_title='Category',
                                yaxis_title='Count of Critical/Major Issues',
                                height=400,
                                margin=dict(l=40, r=40, t=50, b=150)
                            )
                            
                            fig.update_xaxes(tickangle=-45)
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No severity data available by category.")
                else:
                    st.info("No category data found for analysis.")
            else:
                st.info("No categorization information available in the dataset.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Common issues by category
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("Common Issues by Category")
            
            # Create a dropdown to select a specific category
            if 'categorization' in filtered_df.columns:
                # Extract all unique categories
                all_cats = set()
                for cat_str in filtered_df['categorization'].dropna():
                    try:
                        if isinstance(cat_str, str):
                            match = re.search(r'\[(.*?)\]', cat_str)
                            if match:
                                cats = [c.strip() for c in match.group(1).split(',')]
                                all_cats.update(cats)
                            else:
                                all_cats.add(cat_str.strip())
                        elif isinstance(cat_str, list):
                            all_cats.update(cat_str)
                    except:
                        continue
                
                if all_cats:
                    selected_category = st.selectbox(
                        "Select Category for Detailed Analysis",
                        options=sorted(list(all_cats))
                    )
                    
                    # Filter data for the selected category
                    cat_filtered_df = filtered_df[filtered_df['categorization'].apply(
                        lambda x: selected_category in str(x) if not pd.isna(x) else False
                    )]
                    
                    if not cat_filtered_df.empty:
                        # Display category-specific metrics
                        cat_compliance_rate = (cat_filtered_df['compliance_status'] == 'Yes').sum() / len(cat_filtered_df) * 100
                        
                        st.markdown(f"""
                        <div class="category-metrics">
                            <h4 style='margin-top: 0;'>Category: {selected_category}</h4>
                            <p>Number of checks: <b>{len(cat_filtered_df)}</b></p>
                            <p>Compliance rate: <b style='color: {"#10B981" if cat_compliance_rate >= 90 else "#F59E0B" if cat_compliance_rate >= 70 else "#EF4444"}'>{cat_compliance_rate:.1f}%</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Extract common issues for this category
                        issues_df = extract_common_issues(cat_filtered_df)
                        
                        if not issues_df.empty:
                            fig = px.bar(
                                issues_df.head(10),
                                x='Count',
                                y='Issue',
                                orientation='h',
                                title=f'Top Issues in {selected_category} Category',
                                color='Count',
                                color_continuous_scale='Oranges'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No issue data available for this category.")
                        
                        # Display some example non-compliant items
                        non_compliant = cat_filtered_df[cat_filtered_df['compliance_status'] == 'No']
                        if not non_compliant.empty:
                            st.subheader(f"Example Non-Compliant Items in {selected_category}")
                            for i, (idx, row) in enumerate(non_compliant.head(3).iterrows()):
                                with st.expander(f"Issue {i+1}: {row['question'][:80]}..."):
                                    st.markdown(f"""
                                    <div class="issue-card">
                                        <h4 style='margin:0; color:#991B1B;'>{i+1}. {row['question']}</h4>
                                        <p style='margin:5px 0;'><b>Severity:</b> {row.get('severity_level', 'Unknown')}</p>
                                        <p style='margin:5px 0;'><b>Analysis Date:</b> {row.get('analysis_date', 'Unknown')}</p>
                                        <p style='margin:5px 0;'><b>Explanation:</b> {row.get('explanation', 'No explanation provided')}</p>
                                        <p style='margin:5px 0;'><b>Improvements:</b> {row.get('improvement_suggestions', 'No suggestions provided')}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.success(f"Great job! No non-compliant items found in {selected_category} category.")
                    else:
                        st.info(f"No records found for category: {selected_category}")
                else:
                    st.info("No category data available for analysis.")
            else:
                st.info("No categorization information available in the dataset.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # TAB 4: Data Table
        with tab4:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("Filtered Data Records")
            
            # Let user choose which columns to display
            all_columns = filtered_df.columns.tolist()
            
            # Default columns to show
            default_columns = [
                'company_name', 'location_name', 'checklist_name', 
                'question', 'compliance_status', 'severity_level',
                'analysis_date'
            ]
            
            # Only include columns that exist in the dataframe
            default_columns = [col for col in default_columns if col in all_columns]
            
            # Let user select columns to display
            selected_columns = st.multiselect(
                "Select columns to display",
                options=all_columns,
                default=default_columns
            )
            
            # Row filtering options
            st.markdown("### Filter Table Rows")
            
            filter_options = st.columns(4)
            
            with filter_options[0]:
                show_compliant = st.checkbox("Show Compliant", value=True)
            
            with filter_options[1]:
                show_non_compliant = st.checkbox("Show Non-Compliant", value=True)
            
            with filter_options[2]:
                show_critical = st.checkbox("Show Critical Issues", value=True)
            
            with filter_options[3]:
                sort_by = st.selectbox(
                    "Sort By",
                    options=["Default", "Date (Newest)", "Date (Oldest)", "Severity (High to Low)"]
                )
            
            # Apply row filters
            display_df = filtered_df.copy()
            
            # Compliance filter
            compliance_filter = []
            if show_compliant:
                compliance_filter.append("Yes")
            if show_non_compliant:
                compliance_filter.append("No")
            
            if compliance_filter:
                display_df = display_df[display_df['compliance_status'].isin(compliance_filter)]
            
            # Severity filter
            if 'severity_level' in display_df.columns and not show_critical:
                display_df = display_df[display_df['severity_level'] != 'Critical']
            
            # Apply sorting
            if sort_by == "Date (Newest)" and 'analysis_date' in display_df.columns:
                display_df = display_df.sort_values('analysis_date', ascending=False)
            elif sort_by == "Date (Oldest)" and 'analysis_date' in display_df.columns:
                display_df = display_df.sort_values('analysis_date', ascending=True)
            elif sort_by == "Severity (High to Low)" and 'severity_level' in display_df.columns:
                severity_order = {'Critical': 0, 'Major': 1, 'Minor': 2, 'None': 3}
                display_df['severity_order'] = display_df['severity_level'].map(lambda x: severity_order.get(x, 4))
                display_df = display_df.sort_values('severity_order')
                display_df = display_df.drop(columns=['severity_order'])
            
            # Show the filtered dataframe
            if selected_columns:
                st.dataframe(display_df[selected_columns], use_container_width=True)
            else:
                st.dataframe(display_df, use_container_width=True)
            
            # Download button for filtered data
            csv = display_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="Download filtered data as CSV",
                data=csv,
                file_name=f"food_safety_compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display non-compliant highlights
            non_compliant = display_df[display_df['compliance_status'] == 'No']
            
            if not non_compliant.empty:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader("Non-Compliant Items Highlights")
                
                # Group by location
                location_groups = non_compliant.groupby('location_name')
                
                for location, group in location_groups:
                    with st.expander(f"{location} ({len(group)} non-compliant items)"):
                        for i, (idx, row) in enumerate(group.iterrows()):
                            st.markdown(f"""
                            <div class="issue-card">
                                <h4 style='margin:0; color:#991B1B;'>{i+1}. {row['question']}</h4>
                                <p style='margin:5px 0;'><b>Severity:</b> {row.get('severity_level', 'Unknown')}</p>
                                <p style='margin:5px 0;'><b>Analysis Date:</b> {row.get('analysis_date', 'Unknown')}</p>
                                <p style='margin:5px 0;'><b>Explanation:</b> {row.get('explanation', 'No explanation provided')}</p>
                                <p style='margin:5px 0;'><b>Improvements:</b> {row.get('improvement_suggestions', 'No suggestions provided')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

    # Tab 2: Data Upload
    with main_tabs[1]:
        st.header("Upload Data to Supabase")
        
        upload_option = st.radio(
            "Upload Option",
            options=["Upload Excel File", "Generate SQL Script"],
            index=0
        )
        
        uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            # Preview the data
            preview_df = pd.read_excel(uploaded_file)
            
            # Check if necessary columns exist
            required_columns = ["question", "question_type", "vendor_name", "answer_type", 
                               "can_upload", "can_comment", "is_upload_mandatory", 
                               "answer", "extra_comment", "is_skipped", "categorization"]
            
            missing_columns = [col for col in required_columns if col not in preview_df.columns]
            
            if missing_columns:
                st.warning(f"Missing required columns: {', '.join(missing_columns)}")
            
            st.write("Data Preview:")
            st.dataframe(preview_df.head(5))
            
            if upload_option == "Upload Excel File":
                # Add upload button
                if st.button("Upload to Supabase"):
                    with st.spinner("Uploading data to Supabase..."):
                        success = upload_excel_to_supabase(uploaded_file)
                        if success:
                            # Clear the cache to refresh data
                            load_data_from_supabase.clear()
            
            else:  # Generate SQL Script
                if st.button("Generate SQL Script"):
                    with st.spinner("Generating SQL script..."):
                        sql_script = generate_insert_sql(uploaded_file)
                        if sql_script:
                            st.code(sql_script, language="sql")
                            
                            # Add download button
                            sql_file = io.BytesIO(sql_script.encode())
                            st.download_button(
                                label="Download SQL Script",
                                data=sql_file,
                                file_name=f"food_safety_insert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                                mime="text/plain"
                            )

# Run the app
if __name__ == '__main__':
    main()
