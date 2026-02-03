import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

# Set page config
st.set_page_config(
    page_title="אישורי כניסה",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add RTL CSS styling with ultra-compact design
st.markdown("""
<style>
    /* RTL for entire app */
    .stApp {
        direction: rtl;
        text-align: right;
        background: #ffffff;
    }
    
    /* Ultra-minimal spacing */
    .block-container {
        padding-top: 0.2rem;
        padding-bottom: 0rem;
        padding-left: 0.3rem;
        padding-right: 0.3rem;
        max-width: 100%;
    }
    
    /* Hide title completely */
    h1, h2, h3 {
        display: none !important;
    }
    
    /* RTL for all text elements */
    .stMarkdown, .stText, p, label, div {
        direction: rtl;
        text-align: right;
    }
    
    /* Minimal margins */
    p {
        margin: 0.1rem 0 !important;
    }
    
    /* Ultra-compact input fields */
    .stTextInput > div > div > input {
        direction: rtl;
        text-align: right;
        border-radius: 2px;
        border: 1px solid #3498db;
        padding: 0.25rem 0.4rem;
        font-size: 0.85rem;
        height: 1.8rem;
    }
    
    .stTextInput > label {
        font-size: 0.75rem !important;
        margin-bottom: 0.05rem !important;
    }
    
    .stTextInput {
        margin-bottom: 0.1rem !important;
    }
    
    /* Ultra-compact selectbox */
    .stSelectbox [data-baseweb="select"] {
        border-radius: 2px;
        border: 1px solid #3498db;
        min-height: 1.8rem !important;
    }
    
    .stSelectbox > label {
        font-size: 0.75rem !important;
        margin-bottom: 0.05rem !important;
    }
    
    .stSelectbox {
        margin-bottom: 0.1rem !important;
    }
    
    /* Ultra-compact square buttons */
    .stButton > button {
        direction: rtl;
        border-radius: 2px;
        font-weight: 600;
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        height: 1.8rem;
        border: none;
    }
    
    /* Primary button */
    .stButton > button[kind="primary"] {
        background: #3498db;
        color: white;
    }
    
    /* Secondary button */
    .stButton > button[kind="secondary"] {
        background: #e74c3c;
        color: white;
    }
    
    /* Default button */
    .stButton > button {
        background: #95a5a6;
        color: white;
    }
    
    /* Ultra-compact messages */
    .stAlert {
        direction: rtl;
        text-align: right;
        border-radius: 2px;
        padding: 0.25rem;
        margin: 0.15rem 0;
        font-size: 0.8rem;
    }
    
    /* Minimal divider */
    hr {
        margin: 0.2rem 0;
        border: none;
        height: 1px;
        background: #bdc3c7;
    }
    
    /* Fix selectbox dropdown */
    [data-baseweb="select"] {
        direction: rtl;
    }
    
    /* Ultra-minimal spacing between elements */
    .element-container {
        margin: 0.05rem 0 !important;
    }
    
    .row-widget {
        gap: 0.15rem !important;
    }
    
    /* Remove vertical gaps */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.1rem !important;
    }
    
    /* Hide Streamlit branding and menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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
    """Get Google Sheet URL from secrets or user input"""
    if 'google_sheet_url' in st.secrets:
        return st.secrets['google_sheet_url']
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

def delete_row_from_sheet(worksheet, row_number):
    """Delete a specific row from Google Sheet"""
    try:
        # Row number is 1-indexed and includes header
        worksheet.delete_rows(row_number + 2)  # +2 because: +1 for header, +1 for 1-indexing
        return True
    except Exception as e:
        st.error(f"שגיאה במחיקת השורה: {str(e)}")
        return False

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

def search_person(df, search_term):
    """Search for a person by name or vehicle number"""
    search_term = str(search_term).strip()
    
    # Search in relevant columns - removed תז and מספר אישי
    mask = (
        df['שם מלא'].astype(str).str.contains(search_term, case=False, na=False) |
        df['מספר רכב'].astype(str).str.contains(search_term, case=False, na=False)
    )
    
    return df[mask]

def display_person_details(row):
    """Display person details in ultra-compact format"""
    # Check if expired for color coding
    expiration_date = parse_date(row.get('תוקף', ''))
    is_expired_flag = expiration_date and is_expired(expiration_date)
    status_color = "#e74c3c" if is_expired_flag else "#27ae60"
    bg_color = "#ecf0f1"
    text_color = "#2c3e50"
    
    st.markdown(f"""
    <div style='background: {bg_color}; padding: 0.3rem; border-radius: 2px; margin: 0.2rem 0; border-right: 3px solid {status_color};'>
        <table style='width: 100%; border-collapse: collapse; color: {text_color};'>
            <tr>
                <td style='padding: 0.15rem; width: 50%; vertical-align: top; font-size: 0.8rem;'>
                    <div><strong>שם:</strong> {row['שם מלא']}</div>
                    <div><strong>תפקיד:</strong> {row['תפקיד']}</div>
                </td>
                <td style='padding: 0.15rem; width: 50%; vertical-align: top; font-size: 0.8rem;'>
                    <div><strong>רכב:</strong> {row['מספר רכב']}</div>
                    <div><strong>סוג:</strong> {row['סוג רכב']}</div>
                    <div><strong>תוקף:</strong> <span style='color: {status_color}; font-weight: bold;'>{row['תוקף']}</span></div>
                </td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

# Main app
def main():
    # No title - saves space and avoids cutoff issues
    
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
        st.warning("⚠️ לא הוגדר URL של Google Sheet")
        sheet_url = st.text_input(
            "הזן את כתובת ה-Google Sheet:",
            placeholder="https://docs.google.com/spreadsheets/d/..."
        )
        
        if not sheet_url:
            st.info("💡 הזן את כתובת ה-Google Sheet כדי להמשיך")
            return
    
    # Load data
    df, worksheet = load_data_from_sheet(client, sheet_url)
    
    if df is None:
        st.error("לא ניתן לטעון נתונים מה-Google Sheet")
        return
    
    # Search input - compact design
    col1, col2 = st.columns([4, 1])
    
    with col1:
        search_term = st.text_input(
            "חיפוש:",
            placeholder="שם או מספר רכב...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍 חפש", type="primary", use_container_width=True)
    
    if not search_button and not search_term:
        refresh_button = st.button("🔄 רענן", use_container_width=True)
        if refresh_button:
            st.cache_data.clear()
            st.rerun()
    
    # Perform search
    if search_button and search_term:
        results = search_person(df, search_term)
        
        if len(results) == 0:
            st.warning("לא נמצאו תוצאות")
        else:
            st.success(f"נמצאו {len(results)} תוצאות")
            
            # Check each result for expiration
            rows_to_delete = []
            
            for idx, row in results.iterrows():
                expiration_date = parse_date(row['תוקף'])
                
                # Check if expired
                if expiration_date and is_expired(expiration_date):
                    st.error("⚠️ התוקף פג - הרשומה תימחק")
                    rows_to_delete.append((idx, row))
                    
                    # Show the expired record before deletion
                    st.markdown("### פרטי הרשומה שפג תוקפה:")
                    display_person_details(row)
                else:
                    # Show valid record
                    st.markdown("### פרטי האדם:")
                    display_person_details(row)
            
            # Delete expired rows
            if rows_to_delete:
                if st.button(f"🗑️ אשר מחיקת {len(rows_to_delete)} רשומות שפג תוקפן", type="secondary"):
                    deleted_count = 0
                    # Sort in reverse order to delete from bottom to top (preserves row numbers)
                    for idx, row in sorted(rows_to_delete, reverse=True):
                        if delete_row_from_sheet(worksheet, idx):
                            deleted_count += 1
                    
                    if deleted_count > 0:
                        st.success(f"✅ נמחקו {deleted_count} רשומות שפג תוקפן")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ לא הצלחנו למחוק את הרשומות")

if __name__ == "__main__":
    main()
