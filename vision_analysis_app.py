import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import requests
from io import BytesIO
from collections import Counter
import os
import base64
from datetime import datetime
from openai import OpenAI
from supabase import create_client
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="HungerBox Analytics Platform",
    page_icon="🍽️",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
<style>
    /* Main headers and text */
    .main-header {
        color: #1565C0;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .sub-header {
        color: #424242;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }

    /* Containers and boxes */
    .metric-box {
        background-color: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(25, 118, 210, 0.2);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .metric-box:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }

    .info-box {
        background-color: rgba(25, 118, 210, 0.08);
        border-left: 4px solid #1976D2;
        padding: 1.2rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    .info-box:hover {
        background-color: rgba(25, 118, 210, 0.12);
    }

    /* Severity indicators */
    .severity-critical { color: #D32F2F !important; font-weight: bold; }
    .severity-major { color: #F57C00 !important; font-weight: bold; }
    .severity-minor { color: #FFA726 !important; font-weight: bold; }
    .severity-none { color: #2E7D32 !important; font-weight: bold; }

    /* Tags styling */
    .tag-pill {
        background-color: rgba(25, 118, 210, 0.1);
        padding: 6px 12px;
        border-radius: 15px;
        margin-right: 6px;
        font-size: 0.85em;
        display: inline-block;
        margin-bottom: 6px;
        color: #1565C0;
        border: 1px solid rgba(25, 118, 210, 0.2);
        transition: all 0.2s ease;
    }
    .tag-pill:hover {
        background-color: rgba(25, 118, 210, 0.15);
        transform: translateY(-1px);
    }

    /* Dark theme for form inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1E1E1E !important;
        border: 1px solid rgba(25, 118, 210, 0.3) !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        color: #FFFFFF !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #1976D2 !important;
        box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2) !important;
        background-color: #2D2D2D !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #888888 !important;
    }

    /* Dark theme for file uploader */
    .stFileUploader > div {
        background-color: #1E1E1E !important;
        border: 2px dashed rgba(25, 118, 210, 0.3) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        color: #FFFFFF !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader > div:hover {
        border-color: #1976D2 !important;
        background-color: #2D2D2D !important;
    }

    /* Dark theme for select boxes */
    .stSelectbox > div > div > div {
        background-color: #1E1E1E !important;
        border: 1px solid rgba(25, 118, 210, 0.3) !important;
        color: #FFFFFF !important;
    }

    .stSelectbox > div > div > div:hover {
        border-color: #1976D2 !important;
        background-color: #2D2D2D !important;
    }

    /* Form container for Visual Analyzer */
    [data-testid="stForm"] {
        background-color: rgba(30, 30, 30, 0.7) !important;
        padding: 2rem !important;
        border-radius: 10px !important;
        border: 1px solid rgba(25, 118, 210, 0.2) !important;
    }

    /* Labels for form inputs */
    .stTextInput label, .stTextArea label, .stFileUploader label {
        color: #E0E0E0 !important;
        font-weight: 500 !important;
    }

    /* Help text */
    .stTextInput .help-text, .stTextArea .help-text, .stFileUploader .help-text {
        color: #BBBBBB !important;
    }

    /* Button styling */
    .stButton > button {
        background-color: #1976D2 !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    .stButton > button:hover {
        background-color: #1565C0 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        transform: translateY(-1px) !important;
    }

    /* Section headers */
    .section-header {
        background: linear-gradient(to right, rgba(25, 118, 210, 0.08), rgba(25, 118, 210, 0.02));
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid rgba(25, 118, 210, 0.1);
        transition: all 0.3s ease;
    }
    .section-header:hover {
        background: linear-gradient(to right, rgba(25, 118, 210, 0.12), rgba(25, 118, 210, 0.04));
    }
    .section-header h2 {
        color: #1565C0;
        margin: 0;
        font-size: 1.5rem;
        font-weight: 600;
    }
    .section-header p {
        color: #424242;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }

    /* Expander styling */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(25, 118, 210, 0.2);
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    .streamlit-expanderHeader {
        background-color: rgba(25, 118, 210, 0.05);
        border-radius: 8px 8px 0 0;
        padding: 1rem;
        transition: all 0.2s ease;
    }
    .streamlit-expanderHeader:hover {
        background-color: rgba(25, 118, 210, 0.08);
    }

    /* Metrics styling */
    div[data-testid="stMetricValue"] {
        color: #1565C0;
        font-weight: 600;
    }
    div[data-testid="stMetricDelta"] {
        color: #2E7D32;
    }

    /* Radio buttons */
    .stRadio > div {
        background-color: transparent !important;
        border-radius: 8px;
        padding: 0.5rem;
    }
    .stRadio > div > div {
        background-color: rgba(25, 118, 210, 0.05);
        border-radius: 8px;
        padding: 0.5rem;
        transition: all 0.2s ease;
    }
    .stRadio > div > div:hover {
        background-color: rgba(25, 118, 210, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# Supabase configuration from secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to load data for dashboard
@st.cache_data
def load_data():
    try:
        # Initialize an empty list to hold all records
        all_records = []
        limit = 1000  # Number of records to fetch per request
        offset = 0  # Start from the first record

        while True:
            # Fetch records with pagination
            response = supabase.table('analysis_results').select("*").range(offset, offset + limit - 1).execute()
            
            if response.data:
                all_records.extend(response.data)  # Add fetched records to the list
                offset += limit  # Move to the next set of records
            else:
                break  # Exit loop if no more records are found

        # Convert to pandas DataFrame
        df = pd.DataFrame(all_records)
        return df

    except Exception as e:
        st.error(f"Error loading data from Supabase: {e}")
        return pd.DataFrame()

# Add this function to handle image upload to Supabase storage
def upload_image_to_supabase(image_data, file_name):
    try:
        # Create images bucket if it doesn't exist
        try:
            supabase.storage.create_bucket("images", {"public": True})
        except Exception as e:
            if "already exists" not in str(e):
                raise e

        # Upload the image to Supabase storage
        file_path = f"cafeteria_images/{file_name}"
        supabase.storage.from_("images").upload(
            path=file_path,
            file=image_data,
            file_options={"content-type": "image/png"}
        )

        # Get the public URL
        image_url = supabase.storage.from_("images").get_public_url(file_path)
        return image_url

    except Exception as e:
        st.error(f"Error uploading image to storage: {str(e)}")
        return None

# Update the feedback and upload functions with better logging
def upload_feedback_image_to_supabase(image_data, file_name):
    try:
        logger.info(f"Attempting to upload feedback image: {file_name}")
        
        # Check if feedback_images bucket exists first
        try:
            logger.info("Checking if feedback_images bucket exists")
            buckets = supabase.storage.list_buckets()
            logger.info(f"Available buckets: {buckets}")
            
            bucket_exists = any(bucket['name'] == 'feedback_images' for bucket in buckets)
            
            if not bucket_exists:
                logger.info("Creating feedback_images bucket")
                supabase.storage.create_bucket('feedback_images', {'public': True})
                logger.info("Created feedback_images bucket successfully")
            else:
                logger.info("Bucket feedback_images already exists")
                
        except Exception as e:
            logger.error(f"Error checking/creating bucket: {str(e)}")
            # If we can't create a bucket, try to use an existing bucket
            logger.info("Attempting to use images bucket as fallback")

        # Try to upload to feedback_images bucket, if it fails, try the images bucket
        try:
            # Upload the image to feedback_images bucket
            file_path = f"feedback/{file_name}"
            logger.info(f"Uploading image to path: {file_path} in feedback_images bucket")
            
            upload_result = supabase.storage.from_("feedback_images").upload(
                path=file_path,
                file=image_data,
                file_options={"content-type": "image/png"}
            )
            
            # Get the public URL
            image_url = supabase.storage.from_("feedback_images").get_public_url(file_path)
            logger.info(f"Generated public URL: {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"Error uploading to feedback_images bucket: {str(e)}")
            logger.info("Trying fallback to images bucket")
            
            # Fallback to images bucket
            file_path = f"feedback/{file_name}"
            upload_result = supabase.storage.from_("images").upload(
                path=file_path,
                file=image_data,
                file_options={"content-type": "image/png"}
            )
            
            # Get the public URL
            image_url = supabase.storage.from_("images").get_public_url(file_path)
            logger.info(f"Generated public URL from images bucket: {image_url}")
            return image_url

    except Exception as e:
        logger.error(f"Error uploading feedback image: {str(e)}")
        st.error(f"Error uploading feedback image to storage: {str(e)}")
        return None

# Update the display_image function to handle both base64 and URL images
def display_image(url_data):
    try:
        # Check if it's a base64 string
        if isinstance(url_data, str) and url_data.startswith('data:image'):
            # Handle base64 image
            img_data = base64.b64decode(url_data.split(',')[1])
            img = Image.open(BytesIO(img_data))
            return img
        
        # Check if it's a JSON string containing URLs
        elif isinstance(url_data, str) and url_data.startswith('['):
            urls = json.loads(url_data)
            if isinstance(urls, list) and urls:
                url = urls[0]
                response = requests.get(url)
                img = Image.open(BytesIO(response.content))
                return img
        
        # Direct URL
        else:
            response = requests.get(url_data)
            img = Image.open(BytesIO(response.content))
            return img
            
    except Exception as e:
        st.warning(f"Could not load image: {e}")
        return None

# Function to display results for Vision Analysis
def display_vision_results(result, cafeteria_name, question, analysis_date):
    # Severity color mapping
    severity_color = {
        "Critical": "severity-critical",
        "Major": "severity-major",
        "Minor": "severity-minor",
        "None": "severity-none"
    }

    # Main metrics
    with st.container():
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.markdown("## 📋 Compliance Report")
        
        col1, col2, col3 = st.columns([1,1,2])
        
        with col1:
            st.markdown(f"**Cafeteria:** {cafeteria_name}")
            st.markdown(f"**Analysis Date:** {analysis_date}")
            
        with col2:
            status = result.get('criteria_met', 'Unknown')
            status_icon = "✅" if status == "Yes" else "❌" if status == "No" else "❓"
            st.markdown(f"**Compliance Status:** {status_icon} {status}")
            
            severity = result.get('severity', 'Unknown')
            color_class = severity_color.get(severity, "")
            st.markdown(f"**Severity Level:** <span class='{color_class}'>{severity}</span>", 
                      unsafe_allow_html=True)
        
        with col3:
            tags = result.get('tags', [])
            if isinstance(tags, list):
                tags_html = ""
                for tag in tags:
                    tags_html += f'<span class="tag-pill">{tag}</span>'
                st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)
            else:
                tags_list = [tag.strip() for tag in tags.split(',')]
                tags_html = ""
                for tag in tags_list:
                    tags_html += f'<span class="tag-pill">{tag}</span>'
                st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Quality Assessment
    with st.expander("📸 Image Quality Analysis", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            issues = result.get('image_quality_issues', ['none'])
            if issues == ['none'] or (isinstance(issues, str) and issues.lower() == 'none'):
                st.success("✅ No quality issues detected")
            else:
                if isinstance(issues, list):
                    issues_text = ', '.join(issues)
                else:
                    issues_text = issues
                st.error(f"⚠️ Detected issues: {issues_text}")
        
        with col2:
            st.info(f"Quality Impact Assessment: {result.get('quality_assessment', '')}")

    # Detailed Analysis
    with st.expander("🔍 Detailed Compliance Analysis", expanded=True):
        st.markdown(f"**Assessment Question:** {question}")
        st.markdown("### Explanation")
        st.write(result.get('explanation', 'No explanation provided'))
        
        improvements = result.get('improvements', '')
        if improvements:
            st.markdown("### 🛠️ Improvement Suggestions")
            st.write(improvements)
        else:
            st.success("🌟 No improvements needed - all standards met")

# Main function to run the dashboard
def main():
    # Sidebar
    with st.sidebar:
        st.title("🍽️ HungerBox Analytics")
        st.markdown("---")
        st.markdown("""
        <div style='color: #34495E; padding: 10px;'>
        Connected to Supabase Database
        </div>
        """, unsafe_allow_html=True)

    # Load data from Supabase
    df = load_data()
    
    if df.empty:
        st.error("Could not load data from the database. Please check your connection.")
        return
        
    # Main tabs
    tab1, tab2 = st.tabs(["📊 Restaurant Analysis", "🔍 Visual Analyzer"])
    
    # Tab 1: Restaurant Analysis Dashboard
    with tab1:
        st.markdown('<div class="main-header">Restaurant Compliance Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Comprehensive analysis of food safety compliance across all cafeterias</div>', unsafe_allow_html=True)
        
        # Show data info
        st.caption(f"Loaded {len(df)} records from {len(df['cafeteria name'].unique())} restaurants")
        
        # Sub navigation for analysis dashboard
        dashboard_nav = st.radio(
            "Select Dashboard View:",
            ["Overview", "Restaurant Analysis", "Individual Records"],
            horizontal=True,
            key="dashboard_nav",
            help="Choose the type of analysis view you want to see"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing

        # Dashboard Overview
        if dashboard_nav == "Overview":
            st.markdown("""
            <div class="section-header">
                <h2>Overall Compliance Summary</h2>
                <p>Comprehensive overview of food safety compliance metrics</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Overall compliance counts
                compliance_counts = df['compliance_status'].value_counts()
                fig = px.pie(
                    names=compliance_counts.index,
                    values=compliance_counts.values,
                    title="Overall Compliance Status",
                    color_discrete_sequence=px.colors.qualitative.Bold,
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                # Severity levels
                if 'severity_level' in df.columns:
                    severity_counts = df['severity_level'].value_counts()
                    fig = px.bar(
                        x=severity_counts.index,
                        y=severity_counts.values,
                        title="Severity Levels Distribution",
                        labels={'x': 'Severity', 'y': 'Count'},
                        color=severity_counts.index,
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Severity level data not available")
            
            # Image quality issues
            if 'image_quality_issues' in df.columns:
                st.subheader("Image Quality Issues")
                
                # Extract all quality issues
                all_issues = []
                for issues in df['image_quality_issues'].dropna():
                    if isinstance(issues, str):
                        all_issues.extend([issue.strip() for issue in issues.split(',')])
                
                issues_count = Counter(all_issues)
                
                if issues_count:
                    fig = px.bar(
                        x=list(issues_count.keys()),
                        y=list(issues_count.values()),
                        labels={'x': 'Issue Type', 'y': 'Count'},
                        title="Image Quality Issues",
                        color=list(issues_count.keys()),
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No image quality issues found in the data")
            
            # Top tags visualization
            if 'tags' in df.columns:
                st.subheader("Most Common Tags")
                
                # Extract all tags
                all_tags = []
                for tag_str in df['tags'].dropna():
                    if isinstance(tag_str, str):
                        all_tags.extend([tag.strip() for tag in tag_str.split(',')])
                
                if all_tags:
                    tags_count = Counter(all_tags).most_common(10)
                    tags_df = pd.DataFrame(tags_count, columns=['Tag', 'Count'])
                    
                    fig = px.bar(
                        tags_df,
                        x='Count', 
                        y='Tag',
                        orientation='h',
                        title="Top 10 Tags",
                        color='Count',
                        color_continuous_scale=px.colors.sequential.Viridis
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No tags found in the data")
            
            # Compliance over time if dates vary
            if 'analysis_date' in df.columns and len(df['analysis_date'].unique()) > 1:
                st.subheader("Compliance Trend Over Time")
                
                time_data = df.groupby(['analysis_date', 'compliance_status']).size().reset_index(name='count')
                fig = px.line(
                    time_data, 
                    x='analysis_date', 
                    y='count', 
                    color='compliance_status',
                    title="Compliance Status Over Time",
                    labels={'analysis_date': 'Date', 'count': 'Number of Records'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Restaurant Analysis View
        elif dashboard_nav == "Restaurant Analysis":
            st.header("Restaurant-Specific Analysis")
            
            # Select restaurant
            restaurants = sorted(df['cafeteria name'].unique())
            selected_restaurant = st.selectbox("Select a Restaurant", restaurants)
            
            # Filter data for selected restaurant
            restaurant_df = df[df['cafeteria name'] == selected_restaurant]
            
            st.subheader(f"Analysis for {selected_restaurant}")
            
            # Restaurant stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", len(restaurant_df))
            
            with col2:
                compliant_count = len(restaurant_df[restaurant_df['compliance_status'] == 'Yes'])
                compliance_percentage = (compliant_count / len(restaurant_df)) * 100 if len(restaurant_df) > 0 else 0
                st.metric("Compliance Rate", f"{compliance_percentage:.1f}%")
            
            with col3:
                if 'severity_level' in df.columns:
                    critical_count = len(restaurant_df[restaurant_df['severity_level'] == 'Critical'])
                    st.metric("Critical Issues", critical_count)
                else:
                    st.metric("Critical Issues", "N/A")
            
            # Compliance visualization
            col1, col2 = st.columns(2)
            
            with col1:
                compliance_counts = restaurant_df['compliance_status'].value_counts()
                fig = px.pie(
                    names=compliance_counts.index,
                    values=compliance_counts.values,
                    title="Compliance Status",
                    color_discrete_sequence=px.colors.qualitative.Bold,
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'severity_level' in df.columns:
                    severity_counts = restaurant_df['severity_level'].value_counts()
                    fig = px.bar(
                        x=severity_counts.index,
                        y=severity_counts.values,
                        title="Severity Levels",
                        labels={'x': 'Severity', 'y': 'Count'},
                        color=severity_counts.index,
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Severity level data not available")
            
            # Image quality issues for this restaurant
            if 'image_quality_issues' in df.columns:
                st.subheader("Image Quality Issues")
                
                if restaurant_df['image_quality_issues'].dropna().empty:
                    st.info("No image quality data for this restaurant")
                else:
                    quality_counts = restaurant_df['image_quality_issues'].str.split(',').explode().str.strip().value_counts()
                    
                    fig = px.bar(
                        x=quality_counts.index,
                        y=quality_counts.values,
                        title="Image Quality Issues",
                        labels={'x': 'Issue Type', 'y': 'Count'},
                        color=quality_counts.index
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Top tags for this restaurant
            if 'tags' in df.columns:
                st.subheader("Top Tags")
                
                # Extract all tags for this restaurant
                rest_tags = []
                for tag_str in restaurant_df['tags'].dropna():
                    if isinstance(tag_str, str):
                        rest_tags.extend([tag.strip() for tag in tag_str.split(',')])
                
                if rest_tags:
                    tags_count = Counter(rest_tags).most_common(10)
                    tags_df = pd.DataFrame(tags_count, columns=['Tag', 'Count'])
                    
                    fig = px.bar(
                        tags_df,
                        x='Tag', 
                        y='Count',
                        title="Top 10 Tags",
                        color='Tag'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No tags data available for this restaurant")
            
            # Table of non-compliant items
            st.subheader("Non-Compliant Items")
            
            non_compliant = restaurant_df[restaurant_df['compliance_status'] == 'No']
            if not non_compliant.empty:
                display_columns = ['question', 'explanation']
                if 'severity_level' in df.columns:
                    display_columns.insert(1, 'severity_level')
                if 'improvement_suggestions' in df.columns:
                    display_columns.append('improvement_suggestions')
                    
                st.dataframe(non_compliant[display_columns], use_container_width=True)
            else:
                st.success("No non-compliant items found for this restaurant!")
        
        # Individual Records View
        elif dashboard_nav == "Individual Records":
            st.header("Individual Inspection Records")
            
            # Filters 
            st.subheader("Filter Records")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Restaurant filter
                restaurants = sorted(df['cafeteria name'].unique())
                selected_restaurant = st.selectbox("Restaurant", ["All"] + list(restaurants))
            
            with col2:
                # Compliance status filter
                compliance_options = ["All"] + sorted([status for status in df['compliance_status'].dropna().unique().tolist()])
                selected_compliance = st.selectbox("Compliance Status", compliance_options)
            
            with col3:
                # Severity filter if available
                if 'severity_level' in df.columns:
                    severity_options = ["All"] + sorted([severity for severity in df['severity_level'].dropna().unique().tolist()])
                    selected_severity = st.selectbox("Severity Level", severity_options)
                else:
                    selected_severity = "All"
            
            with col4:
                # Image quality filter if available
                if 'image_quality_issues' in df.columns:
                    quality_options = ["All", "Has Issues", "No Issues"]
                    selected_quality = st.selectbox("Image Quality", quality_options)
                else:
                    selected_quality = "All"
            
            # Apply filters
            filtered_df = df.copy()
            
            if selected_restaurant != "All":
                filtered_df = filtered_df[filtered_df['cafeteria name'] == selected_restaurant]
            
            if selected_compliance != "All":
                filtered_df = filtered_df[filtered_df['compliance_status'] == selected_compliance]
            
            if selected_severity != "All" and 'severity_level' in df.columns:
                filtered_df = filtered_df[filtered_df['severity_level'] == selected_severity]
            
            if selected_quality == "Has Issues" and 'image_quality_issues' in df.columns:
                filtered_df = filtered_df[filtered_df['image_quality_issues'].str.contains('too_dark|too_blurry', na=False)]
            elif selected_quality == "No Issues" and 'image_quality_issues' in df.columns:
                filtered_df = filtered_df[~filtered_df['image_quality_issues'].str.contains('too_dark|too_blurry', na=False)]
            
            st.markdown(f"**Showing {len(filtered_df)} records**")
            
            # Display individual records
            for idx, row in filtered_df.iterrows():
                question_preview = row['question']
                if len(question_preview) > 60:
                    question_preview = question_preview[:60] + "..."
                
                with st.expander(f"{row['cafeteria name']} - {question_preview}"):
                    cols = st.columns([1, 2])
                    
                    with cols[0]:
                        st.subheader("Image")
                        if 'upload_links (images)' in row and row['upload_links (images)']:
                            img = display_image(row['upload_links (images)'])
                            if img:
                                st.image(img, use_container_width=True)
                            else:
                                st.info("No image available or could not be loaded")
                        else:
                            st.info("No image available")
                    
                    with cols[1]:
                        st.subheader("Analysis Results")
                        
                        status_color = "green" if row['compliance_status'] == 'Yes' else "red" if row['compliance_status'] == 'No' else "orange"
                        st.markdown(f"**Compliance Status:** <span style='color:{status_color};'>{row['compliance_status']}</span>", unsafe_allow_html=True)
                        
                        if 'severity_level' in row and pd.notna(row['severity_level']):
                            severity_color = "red" if row['severity_level'] == 'Critical' else "orange" if row['severity_level'] == 'Major' else "yellow" if row['severity_level'] == 'Minor' else "green"
                            st.markdown(f"**Severity Level:** <span style='color:{severity_color};'>{row['severity_level']}</span>", unsafe_allow_html=True)
                        
                        st.markdown(f"**Question:** {row['question']}")
                        
                        if 'explanation' in row and pd.notna(row['explanation']):
                            st.markdown(f"**Explanation:** {row['explanation']}")
                        
                        if 'improvement_suggestions' in row and pd.notna(row['improvement_suggestions']):
                            st.markdown(f"**Improvement Suggestions:** {row['improvement_suggestions']}")
                        
                        if 'image_quality_issues' in row and pd.notna(row['image_quality_issues']) and row['image_quality_issues'] != 'none':
                            st.markdown(f"**Image Quality Issues:** {row['image_quality_issues']}")
                        
                        if 'quality_assessment' in row and pd.notna(row['quality_assessment']):
                            st.markdown(f"**Quality Assessment:** {row['quality_assessment']}")
                        
                        if 'tags' in row and pd.notna(row['tags']):
                            tags = [tag.strip() for tag in row['tags'].split(',')]
                            st.markdown("**Tags:**")
                            # Display tags as pills
                            tags_html = ""
                            for tag in tags:
                                tags_html += f'<span class="tag-pill">{tag}</span>'
                            st.markdown(tags_html, unsafe_allow_html=True)
                        
                        if 'analysis_date' in row and pd.notna(row['analysis_date']):
                            st.markdown(f"**Analysis Date:** {row['analysis_date']}")
    
    # Tab 2: Visual Analyzer
    with tab2:
        st.markdown('<div class="main-header">Food Safety Visual Analyzer</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">AI-powered compliance assessment for cafeteria operations</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="info-box">Upload a cafeteria image and enter a food safety question to receive an AI-powered compliance analysis.</div>', unsafe_allow_html=True)
        
        # Input Section
        with st.form("vision_input_form", clear_on_submit=False):
            st.markdown("""
            <div class="section-header">
                <h2>Image Analysis Input</h2>
                <p>Fill in the details below to analyze your cafeteria image</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Use API key from secrets
                api_key = st.secrets["openai"]["api_key"]
                cafeteria_name = st.text_input("Cafeteria Name", 
                                             placeholder="Enter cafeteria name...")
                question = st.text_area("Assessment Question", 
                                      placeholder="Enter your food safety question...",
                                      height=120)
                
            with col2:
                uploaded_image = st.file_uploader("Upload Cafeteria Image", 
                                               type=["jpg", "jpeg", "png"],
                                               help="Upload a clear image of the area to assess")
                if uploaded_image:
                    image = Image.open(uploaded_image)
                    st.image(image, caption="Preview of Uploaded Image", use_container_width=True)

            # Add some visual separation
            st.markdown("---")
            submitted = st.form_submit_button("Analyze Compliance", use_container_width=True)

        # Analysis Logic - Store results in session state to persist between interactions
        if submitted:
            if not all([api_key, cafeteria_name, question, uploaded_image]):
                st.error("⚠️ Please fill all required fields and upload an image")
            else:
                try:
                    with st.spinner("🔍 Analyzing image and preparing report..."):
                        # Convert image to base64
                        buffered = BytesIO()
                        image.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()
                        
                        # Save image in session state to persist after form submission
                        if 'image' not in st.session_state:
                            st.session_state.image = image
                        
                        # Create OpenAI client
                        client = OpenAI(api_key=api_key)
                        
                        # Construct analysis prompt
                        prompt = f"""
                        You are a food safety manager analyzing a cafeteria image for compliance with food safety standards.
                        Question to evaluate: {question}

                        INSTRUCTIONS:
                        1. Assess image quality (e.g., too dark, too blurry) and note its impact on your evaluation.
                        2. If the question explicitly requires a blank, empty, or clean area (e.g., "Take a blank photo if not applicable" or "Is the area clear?") and the image shows this, mark as "Yes" (compliant).
                        3. Dark or blurry images are compliant ONLY if:
                           - The question requires documentation of an empty, vacant, or clear area, AND
                           - Quality issues do not prevent confirming compliance.
                        4. Otherwise, dark or blurry images without context are non-compliant ("No").

                        OUTPUT:
                        Return a JSON object with:
                        - "criteria_met": "Yes" (compliant), "No" (non-compliant), or "Unable to determine" (quality prevents assessment)
                        - "explanation": 2-3 sentences explaining your assessment
                        - "improvements": Actionable recommendations if issues are found (empty string if none)
                        - "severity": "Critical" (immediate health risk), "Major" (significant violation), "Minor" (small issue), or "None" (compliant)
                        - "image_quality_issues": List of issues (e.g., ["too_dark", "too_blurry"], ["none"] if no issues)
                        - "quality_assessment": Brief comment on how image quality affected your evaluation
                        - "tags": List of 3-5 descriptive tags (e.g., kitchen, storage, cleanliness, etc.)
                        """

                        # API Call with logging
                        logger.info("Making OpenAI API call")
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", 
                                     "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                                    }
                                ]
                            }],
                            response_format={"type": "json_object"}
                        )
                        logger.info("OpenAI API call completed successfully")

                        # Process response
                        result = json.loads(response.choices[0].message.content)
                        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Store results in session state
                        st.session_state.result = result
                        st.session_state.cafeteria_name = cafeteria_name
                        st.session_state.question = question
                        st.session_state.analysis_date = analysis_date
                        st.session_state.has_analysis = True
                        
                        logger.info(f"Analysis complete: {result}")

                except Exception as e:
                    logger.error(f"Analysis failed: {str(e)}")
                    st.error(f"Analysis failed: {str(e)}")
                    st.session_state.has_analysis = False

        # Check if we have analysis results in session state and display them
        # This section is outside the form to prevent refreshing
        if 'has_analysis' in st.session_state and st.session_state.has_analysis:
            # Display Results
            st.success("✅ Analysis Complete!")
            display_vision_results(
                st.session_state.result, 
                st.session_state.cafeteria_name, 
                st.session_state.question, 
                st.session_state.analysis_date
            )
            
            # Add feedback section - outside the form to prevent refresh
            st.markdown("---")
            st.subheader("📝 Provide Feedback")
            st.markdown("Your feedback helps us improve our analysis quality.")
            
            feedback_col1, feedback_col2 = st.columns(2)
            
            with feedback_col1:
                satisfied = st.radio("Are you satisfied with this analysis?", ["Yes", "No"], key="feedback_satisfied")
            
            with feedback_col2:
                feedback_text = st.text_area(
                    "Additional feedback (optional)", 
                    placeholder="Please share any thoughts about the analysis...",
                    height=100,
                    key="feedback_text"
                )
            
            if st.button("Submit Feedback", key="submit_feedback"):
                try:
                    logger.info("Attempting to submit feedback")
                    
                    # Check if feedback table exists
                    try:
                        # First check if the table exists
                        logger.info("Checking if feedback table exists")
                        # We'll try a basic operation that should succeed if the table exists
                        test_query = supabase.table('feedback').select('count', count='exact').execute()
                        logger.info("Feedback table exists")
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"Error checking feedback table: {error_msg}")
                        
                        if "does not exist" in error_msg:
                            st.error("The feedback table does not exist in the database. Please create it first.")
                            st.code("""
CREATE TABLE IF NOT EXISTS public.feedback (
  id SERIAL PRIMARY KEY,
  analysis_id INTEGER REFERENCES public.analysis_results(id),
  satisfied BOOLEAN NOT NULL,
  feedback_text TEXT,
  image_url TEXT,
  cafeteria_name TEXT NOT NULL,
  question TEXT NOT NULL,
  compliance_status TEXT,
  explanation TEXT,
  improvement_suggestions TEXT,
  severity_level TEXT,
  image_quality_issues TEXT,
  quality_assessment TEXT,
  analysis_date DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
                            """, language="sql")
                            return
                        
                    # Upload a copy of the image for feedback
                    buffered = BytesIO()
                    st.session_state.image.save(buffered, format="PNG")
                    image_data = buffered.getvalue()
                    
                    # Generate a unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    feedback_file_name = f"feedback_{st.session_state.cafeteria_name.replace(' ', '_')}_{timestamp}.png"
                    
                    # Upload image to Supabase feedback bucket with logging
                    logger.info(f"Uploading feedback image: {feedback_file_name}")
                    feedback_image_url = upload_feedback_image_to_supabase(image_data, feedback_file_name)
                    
                    if feedback_image_url:
                        logger.info(f"Feedback image uploaded successfully: {feedback_image_url}")
                        
                        # Prepare feedback data with analysis results
                        feedback_data = {
                            'satisfied': True if satisfied == "Yes" else False,
                            'feedback_text': feedback_text,
                            'image_url': feedback_image_url,
                            'cafeteria_name': st.session_state.cafeteria_name,
                            'question': st.session_state.question,
                            'compliance_status': st.session_state.result.get('criteria_met', 'Unknown'),
                            'explanation': st.session_state.result.get('explanation', ''),
                            'improvement_suggestions': st.session_state.result.get('improvements', ''),
                            'severity_level': st.session_state.result.get('severity', 'Unknown'),
                            'image_quality_issues': ', '.join(st.session_state.result.get('image_quality_issues', ['none'])) if isinstance(st.session_state.result.get('image_quality_issues'), list) else st.session_state.result.get('image_quality_issues', 'none'),
                            'quality_assessment': st.session_state.result.get('quality_assessment', ''),
                            'analysis_date': datetime.now().date().isoformat()
                        }
                        
                        # If we have an analysis_id (if analysis was saved), include it
                        if 'analysis_id' in st.session_state:
                            feedback_data['analysis_id'] = st.session_state.analysis_id
                        
                        # Insert feedback into Supabase with logging
                        logger.info(f"Inserting feedback data into Supabase: {feedback_data}")
                        feedback_response = supabase.table('feedback').insert(feedback_data).execute()
                        
                        if hasattr(feedback_response, 'data') and feedback_response.data:
                            logger.info(f"Feedback submitted successfully: {feedback_response.data}")
                            st.success("✅ Thank you for your feedback!")
                        else:
                            error_msg = "Failed to submit feedback - no data returned"
                            if hasattr(feedback_response, 'error'):
                                error_msg += f": {feedback_response.error}"
                            logger.error(error_msg)
                            st.error(error_msg)
                    else:
                        logger.error("Failed to upload feedback image")
                        st.error("Failed to upload feedback image")
                        
                except Exception as e:
                    logger.error(f"Error submitting feedback: {str(e)}")
                    st.error(f"Error submitting feedback: {str(e)}")
                    import traceback
                    trace = traceback.format_exc()
                    logger.error(f"Full error trace:\n{trace}")
                    st.error(f"Full error trace:\n{trace}")
            
            # Option to save results - outside the form to prevent refresh
            st.markdown("---")
            save_col1, save_col2 = st.columns([3, 1])
            
            # with save_col1:
            #     st.info("Would you like to add this analysis to your records?")
            
            # with save_col2:
            #     if st.button("Save Analysis", key="save_analysis"):
            #         try:
            #             logger.info("Attempting to save analysis to database")
            #             # First, handle the image upload
            #             buffered = BytesIO()
            #             st.session_state.image.save(buffered, format="PNG")
            #             image_data = buffered.getvalue()
                        
            #             # Generate a unique filename
            #             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            #             file_name = f"{st.session_state.cafeteria_name.replace(' ', '_')}_{timestamp}.png"
                        
            #             # Upload image to Supabase storage with logging
            #             logger.info(f"Uploading analysis image: {file_name}")
            #             image_url = upload_image_to_supabase(image_data, file_name)
                        
            #             if image_url:
            #                 logger.info(f"Analysis image uploaded successfully: {image_url}")
                            
            #                 # Create a new row for the analysis
            #                 new_data = {
            #                     'question': st.session_state.question,
            #                     'upload_links (images)': json.dumps([image_url]),  # Store the public URL
            #                     'answer_type': 'boolean',
            #                     'cafeteria name': st.session_state.cafeteria_name,  # Space in column name preserved
            #                     'compliance_status': st.session_state.result.get('criteria_met', 'Unknown'),
            #                     'explanation': st.session_state.result.get('explanation', ''),
            #                     'improvement_suggestions': st.session_state.result.get('improvements', ''),
            #                     'severity_level': st.session_state.result.get('severity', 'Unknown'),
            #                     'image_quality_issues': ', '.join(st.session_state.result.get('image_quality_issues', ['none'])) if isinstance(st.session_state.result.get('image_quality_issues'), list) else st.session_state.result.get('image_quality_issues', 'none'),
            #                     'quality_assessment': st.session_state.result.get('quality_assessment', ''),
            #                     'tags': ', '.join(st.session_state.result.get('tags', [])) if isinstance(st.session_state.result.get('tags'), list) else st.session_state.result.get('tags', ''),
            #                     'analysis_date': datetime.now().date().isoformat()
            #                 }

            #                 # Log the data being saved
            #                 logger.info(f"Saving analysis data to Supabase: {new_data}")
            #                 st.write("Attempting to save the following data:")
            #                 st.json(new_data)

            #                 try:
            #                     # Insert data into Supabase with error handling
            #                     logger.info("Executing Supabase insert operation")
            #                     response = supabase.table('analysis_results').insert(new_data).execute()
                                
            #                     if hasattr(response, 'data') and response.data:
            #                         logger.info(f"Analysis saved successfully: {response.data}")
            #                         st.success("✅ Analysis saved to database successfully!")
                                    
            #                         # Show saved record ID and image URL
            #                         record_id = response.data[0].get('id')
            #                         # Store analysis_id in session state for feedback reference
            #                         st.session_state.analysis_id = record_id
                                    
            #                         st.info(f"""
            #                         Record saved with ID: {record_id}
            #                         Image URL: {image_url}
            #                         """)

            #                         # Option to export to Excel
            #                         if st.button("Export to Excel", key="export_excel"):
            #                             # Fetch updated data
            #                             df = load_data()
            #                             if not df.empty:
            #                                 # Save to Excel
            #                                 temp_file = f"analysis_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            #                                 df.to_excel(temp_file, index=False)
                                            
            #                                 with open(temp_file, 'rb') as f:
            #                                     st.download_button(
            #                                         label="Download Excel Export",
            #                                         data=f,
            #                                         file_name=temp_file,
            #                                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            #                                     )
            #                     else:
            #                         error_msg = "Failed to save analysis to database - no data returned"
            #                         if hasattr(response, 'error'):
            #                             error_msg += f": {response.error}"
            #                         logger.error(error_msg)
            #                         st.error(error_msg)
                                    
            #                 except Exception as e:
            #                     logger.error(f"Database error: {str(e)}")
            #                     st.error(f"Database error: {str(e)}")
            #                     import traceback
            #                     trace = traceback.format_exc()
            #                     logger.error(f"Full error trace:\n{trace}")
            #                     st.error(f"Full error trace:\n{trace}")
            #             else:
            #                 logger.error("Failed to upload image to storage")
            #                 st.error("Failed to upload image to storage")
                        
            #         except Exception as e:
            #             logger.error(f"Error preparing data: {str(e)}")
            #             st.error(f"Error preparing data: {str(e)}")

# Add footer
st.markdown("---")
st.markdown("© 2025 A platfrom for HungerBox Analytics")

# Main entry point
if __name__ == "__main__":
    main()