import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# Set page config
st.set_page_config(
    page_title="חיפוש במערכת",
    page_icon="🔍",
    layout="wide"
)

# Add RTL CSS styling
st.markdown("""
<style>
    /* RTL for entire app */
    .stApp {
        direction: rtl;
        text-align: right;
        background: #ffffff;
    }
    
    /* Minimal spacing */
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    
    /* Main title styling */
    h1 {
        color: #2c3e50;
        font-size: 1.5rem !important;
        font-weight: bold !important;
        text-align: center !important;
        padding: 0.3rem 0;
        margin: 0 !important;
    }
    
    h2, h3, h4 {
        margin: 0.2rem 0 !important;
        padding: 0 !important;
    }
    
    /* RTL for all text elements */
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, label, div {
        direction: rtl;
        text-align: right;
    }
    
    /* Remove extra margins and padding */
    p {
        margin: 0.2rem 0 !important;
    }
    
    /* RTL for input fields - compact and square */
    .stTextInput > div > div > input {
        direction: rtl;
        text-align: right;
        border-radius: 2px;
        border: 1px solid #3498db;
        padding: 0.3rem 0.5rem;
        font-size: 0.85rem;
        height: 2rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2980b9;
        box-shadow: none;
    }
    
    .stTextInput > label {
        font-size: 0.8rem !important;
        margin-bottom: 0.1rem !important;
    }
    
    .stTextInput {
        margin-bottom: 0.2rem !important;
    }
    
    /* RTL for selectbox - compact and square */
    .stSelectbox > div > div > div {
        direction: rtl;
        text-align: right;
        border-radius: 2px;
    }
    
    .stSelectbox [data-baseweb="select"] {
        border-radius: 2px;
        border: 1px solid #3498db;
        min-height: 2rem !important;
    }
    
    .stSelectbox > label {
        font-size: 0.8rem !important;
        margin-bottom: 0.1rem !important;
    }
    
    .stSelectbox {
        margin-bottom: 0.2rem !important;
    }
    
    /* Buttons styling - compact and square */
    .stButton > button {
        direction: rtl;
        border-radius: 2px;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 0.3rem 0.6rem;
        height: 2rem;
        border: none;
        transition: opacity 0.2s;
    }
    
    .stButton > button:hover {
        opacity: 0.85;
    }
    
    /* Primary button - solid blue */
    .stButton > button[kind="primary"] {
        background: #3498db;
        color: white;
    }
    
    /* Secondary button - solid red */
    .stButton > button[kind="secondary"] {
        background: #e74c3c;
        color: white;
    }
    
    /* Default button - solid gray */
    .stButton > button {
        background: #95a5a6;
        color: white;
    }
    
    /* Success/Error/Warning messages - compact */
    .stAlert {
        direction: rtl;
        text-align: right;
        border-radius: 2px;
        padding: 0.3rem;
        margin: 0.2rem 0;
        font-size: 0.85rem;
    }
    
    /* Success message - solid green */
    .stSuccess {
        background: #27ae60;
        color: white;
        border: none;
    }
    
    /* Warning message - solid orange */
    .stWarning {
        background: #f39c12;
        color: white;
        border: none;
    }
    
    /* Error message - solid red */
    .stError {
        background: #e74c3c;
        color: white;
        border: none;
    }
    
    /* Info boxes - solid blue */
    .stInfo {
        direction: rtl;
        text-align: right;
        border-radius: 2px;
        background: #3498db;
        color: white;
        border: none;
        padding: 0.3rem;
        margin: 0.2rem 0;
        font-size: 0.85rem;
    }
    
    /* Divider - simple line */
    hr {
        margin: 0.3rem 0;
        border: none;
        height: 1px;
        background: #bdc3c7;
    }
    
    /* Fix selectbox dropdown */
    [data-baseweb="select"] {
        direction: rtl;
    }
    
    /* Remove column gaps */
    .row-widget {
        gap: 0.2rem !important;
    }
    
    /* Minimal sections */
    .element-container {
        margin: 0.1rem 0 !important;
    }
    
    /* Reduce vertical space between elements */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets configuration
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

@st.cache_resource
def get_google_client():
    """Initialize Google Sheets client"""
    try:
        # Try to load credentials from Streamlit secrets
        if 'gcp_service_account' in st.secrets:
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=SCOPES
            )
        else:
            # Load from file
            credentials = Credentials.from_service_account_file(
                'credentials.json',
                scopes=SCOPES
            )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-Google Sheets: {str(e)}")
        return None

def get_sheet_url():
    """Get Google Sheet URL from secrets"""
    if 'google_sheet_url' in st.secrets:
        return st.secrets['google_sheet_url']
    else:
        st.error("⚠️ לא נמצא URL של Google Sheet ב-secrets")
        st.info("""
        אנא הוסף את ה-URL ב-secrets:
        
        1. צור תיקייה: `.streamlit`
        2. צור קובץ: `secrets.toml`
        3. הוסף את השורה:
        ```
        google_sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
        ```
        """)
        return None

@st.cache_data(ttl=10)
def load_data_from_sheet(_client, sheet_url):
    """Load data from Google Sheet and automatically delete expired rows"""
    try:
        # Open the sheet by URL
        sheet = _client.open_by_url(sheet_url)
        worksheet = sheet.get_worksheet(0)  # First sheet
        
        # Get all values
        data = worksheet.get_all_values()
        
        # Convert to DataFrame
        if len(data) > 0:
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Automatically delete expired rows
            rows_to_delete = []
            for idx, row in df.iterrows():
                expiration_date = parse_date(row.get('תוקף', ''))
                if expiration_date and is_expired(expiration_date):
                    rows_to_delete.append(idx)
            
            # Delete expired rows from sheet (in reverse order)
            if rows_to_delete:
                for idx in sorted(rows_to_delete, reverse=True):
                    try:
                        # +2 because: +1 for header, +1 for 1-indexing
                        worksheet.delete_rows(idx + 2)
                    except:
                        pass
                
                # Reload data after deletion
                data = worksheet.get_all_values()
                if len(data) > 0:
                    df = pd.DataFrame(data[1:], columns=data[0])
            
            return df, worksheet
        return None, None
    except Exception as e:
        st.error(f"שגיאה בטעינת הנתונים: {str(e)}")
        return None, None

def parse_date(date_str):
    """Parse date string in DD/MM/YYYY format"""
    try:
        if pd.isna(date_str) or date_str == '':
            return None
        if isinstance(date_str, datetime):
            return date_str
        return datetime.strptime(str(date_str), "%d/%m/%Y")
    except:
        return None

def is_expired(expiration_date):
    """Check if the date has passed"""
    if expiration_date is None:
        return False
    current_date = datetime.now()
    return expiration_date < current_date

def search_person(df, search_term, search_column):
    """Search for a person in a specific column"""
    search_term = str(search_term).strip()
    
    # Map display names to actual column names
    column_mapping = {
        'שם מלא': 'שם מלא',
        'מספר אישי': 'מספר אישי',
        'תעודת זהות': 'תז',
        'מספר רכב': 'מספר רכב'
    }
    
    actual_column = column_mapping.get(search_column, search_column)
    
    # Search only in the selected column
    if actual_column in df.columns:
        mask = df[actual_column].astype(str).str.contains(search_term, case=False, na=False)
        return df[mask]
    else:
        return pd.DataFrame()  # Return empty dataframe if column not found

def display_person_details(row):
    """Display person details in a compact format"""
    # Check if expired for color coding
    expiration_date = parse_date(row['תוקף'])
    is_expired_flag = expiration_date and is_expired(expiration_date)
    status_color = "#e74c3c" if is_expired_flag else "#27ae60"
    bg_color = "#ecf0f1"
    text_color = "#2c3e50"  # Dark text for readability
    
    st.markdown(f"""
    <div style='background: {bg_color}; padding: 0.5rem; border-radius: 2px; margin: 0.3rem 0; border-right: 4px solid {status_color};'>
        <table style='width: 100%; border-collapse: collapse; color: {text_color};'>
            <tr>
                <td style='padding: 0.2rem; width: 50%; vertical-align: top; font-size: 0.9rem;'>
                    <div><strong>שם מלא:</strong> {row['שם מלא']}</div>
                    <div><strong>תעודת זהות:</strong> {row['תז']}</div>
                    <div><strong>מספר אישי:</strong> {row['מספר אישי']}</div>
                    <div><strong>תפקיד:</strong> {row['תפקיד']}</div>
                </td>
                <td style='padding: 0.2rem; width: 50%; vertical-align: top; font-size: 0.9rem;'>
                    <div><strong>מספר רכב:</strong> {row['מספר רכב']}</div>
                    <div><strong>סוג רכב:</strong> {row['סוג רכב']}</div>
                    <div><strong>תוקף:</strong> <span style='color: {status_color}; font-weight: bold;'>{row['תוקף']}</span></div>
                </td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

# Main app
def main():
    st.title("אישורי כניסה")
    st.markdown("---")
    
    # Initialize Google client
    client = get_google_client()
    
    if client is None:
        st.error("⚠️ לא ניתן להתחבר ל-Google Sheets")
        st.info("""
        אנא ודא ש:
        1. קובץ credentials.json קיים באותה תיקייה
        2. או שהגדרת את credentials ב-Streamlit secrets
        """)
        return
    
    # Get sheet URL
    sheet_url = get_sheet_url()
    
    if sheet_url is None:
        return
    
    # Load data
    df, worksheet = load_data_from_sheet(client, sheet_url)
    
    if df is None:
        st.error("לא ניתן לטעון נתונים מה-Google Sheet")
        return
    
    # Search input with column selection
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        search_column = st.selectbox(
            "עמודה:",
            options=['שם מלא', 'מספר אישי', 'תעודת זהות', 'מספר רכב'],
            index=0
        )
    
    with col2:
        search_term = st.text_input(
            "חיפוש:",
            placeholder=f"חפש לפי {search_column}...",
            key="search_input"
        )
    
    with col3:
        search_button = st.button("🔍 חפש", type="primary", use_container_width=True)
    
    with col4:
        refresh_button = st.button("🔄 רענן", use_container_width=True)
    
    if refresh_button:
        st.cache_data.clear()
        st.rerun()
    
    # Perform search
    if search_button and search_term:
        results = search_person(df, search_term, search_column)
        
        if len(results) == 0:
            st.markdown("""
            <div style='text-align: center; padding: 0.4rem; background: #95a5a6; border-radius: 2px; margin: 0.2rem 0; color: white; font-size: 0.85rem;'>
                לא נמצאו תוצאות
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='text-align: center; padding: 0.4rem; background: #27ae60; border-radius: 2px; margin: 0.2rem 0; color: white; font-size: 0.85rem;'>
                נמצאו {len(results)} תוצאות
            </div>
            """, unsafe_allow_html=True)
            
            # Display all results (expired rows already deleted automatically)
            for idx, row in results.iterrows():
                display_person_details(row)

if __name__ == "__main__":
    main()
