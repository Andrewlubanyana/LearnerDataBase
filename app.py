import streamlit as st
import pandas as pd
import pdfplumber
from docx import Document
import plotly.express as px

st.set_page_config(page_title="Universal Student Database", layout="wide")

# --- 1. FILE HELPERS ---
def extract_pdf_table(file):
    with pdfplumber.open(file) as pdf:
        table = pdf.pages[0].extract_table()
        if table:
            return pd.DataFrame(table[1:], columns=table[0])
    return None

def extract_docx_table(file):
    doc = Document(file)
    if doc.tables:
        data = [[cell.text.strip() for cell in row.cells] for row in doc.tables[0].rows]
        if data:
            return pd.DataFrame(data[1:], columns=data[0])
    return None

# --- 2. APP UI ---
st.title("📊 Universal Student Database")
uploaded_file = st.file_uploader("Upload CSV, Excel, PDF, or Word", type=['csv', 'xlsx', 'pdf', 'docx'])

# Define df as None initially so the app doesn't crash
df = None

if uploaded_file:
    ext = uploaded_file.name.split('.')[-1].lower()
    try:
        if ext == 'csv':
            df = pd.read_csv(uploaded_file)
        elif ext == 'xlsx':
            df = pd.read_excel(uploaded_file)
        elif ext == 'pdf':
            df = extract_pdf_table(uploaded_file)
        elif ext == 'docx':
            df = extract_docx_table(uploaded_file)
        
        # --- THE CORRECTED INDENTATION BLOCK ---
        if df is not None:
            # CLEANING
            df = df.dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            
            # --- 3. SORTING & FILTERING ---
            st.sidebar.header("Settings")
            sort_by = st.sidebar.selectbox("Sort data by:", df.columns)
            order = st.sidebar.radio("Order:", ["Ascending", "Descending"])
            df = df.sort_values(by=sort_by, ascending=(order == "Ascending"))

            # --- 4. DISPLAY & ANALYZE ---
            st.subheader("Data Preview")
            st.dataframe(df, use_container_width=True)

            # Look for a "Mark" column
            mark_col = next((c for c in df.columns if 'mark' in c.lower() or 'score' in c.lower()), None)
            if mark_col:
                df[mark_col] = pd.to_numeric(df[mark_col], errors='coerce')
                st.metric("Class Average", f"{df[mark_col].mean():.1f}%")
        else:
            st.warning("No table detected in this file. Please ensure data is in a table format.")

    except Exception as e:
        st.error(f"Error loading file: {e}")
else:
    st.info("👋 Welcome! Please upload a file to see the database and sorting options.")
