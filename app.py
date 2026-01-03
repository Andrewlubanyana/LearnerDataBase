import streamlit as st
import pandas as pd
import pdfplumber
from docx import Document
import io

st.set_page_config(page_title="Ultimate Data Analyzer", layout="wide")

# --- 1. DATA EXTRACTION FUNCTIONS ---
def process_file(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'csv': return pd.read_csv(file)
    if ext == 'xlsx': return pd.read_excel(file)
    if ext == 'pdf':
        with pdfplumber.open(file) as pdf:
            data = []
            for page in pdf.pages:
                table = page.extract_table()
                if table: data.extend(table)
            return pd.DataFrame(data[1:], columns=data[0]) if data else None
    if ext == 'docx':
        doc = Document(file)
        data = [[c.text.strip() for c in r.cells] for t in doc.tables for r in t.rows]
        return pd.DataFrame(data[1:], columns=data[0]) if data else None
    return None

# --- 2. THE APP INTERFACE ---
st.title("📊 Universal Student Data Analyzer")

# Create Tabs for Uploading vs. Pasting
tab1, tab2 = st.tabs(["📂 Upload File", "📋 Paste Data / CV Text"])

df = None

with tab1:
    uploaded_file = st.file_uploader("Upload CSV, Excel, PDF, or Word", type=['csv', 'xlsx', 'pdf', 'docx'])
    if uploaded_file:
        df = process_file(uploaded_file)

with tab2:
    st.write("Paste your CV data or list here. Ensure there is a space, comma, or tab between items.")
    raw_input = st.text_area("Paste data here:", height=200, placeholder="John Doe 85 Male\nJane Smith 90 Female")
    separator = st.selectbox("How is your data separated?", ["Auto-detect Space", "Comma (,)", "Tab"])
    
    if raw_input:
        lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
        if separator == "Comma (,)":
            data = [l.split(',') for l in lines]
        elif separator == "Tab":
            data = [l.split('\t') for l in lines]
        else:
            data = [l.split() for l in lines]
        df = pd.DataFrame(data)

# --- 3. ANALYSIS & SORTING ---
if df is not None:
    st.divider()
    # Clean-up: Remove empty rows
    df = df.dropna(how='all').fillna("")
    
    # Let user pick column names if they are missing
    if st.checkbox("Use first row as header?"):
        new_header = df.iloc[0]
        df = df[1:]
        df.columns = new_header

    # Sidebar Tools
    st.sidebar.header("Data Tools")
    target_col = st.sidebar.selectbox("Sort by:", df.columns)
    order = st.sidebar.radio("Direction:", ["Ascending", "Descending"])
    df = df.sort_values(by=target_col, ascending=(order == "Ascending"))

    # Main Display
    st.subheader("Final Analyzed Data")
    st.dataframe(df, use_container_width=True)

    # Automatic Mark Calculation
    mark_col = st.sidebar.selectbox("Which column contains the Marks?", df.columns)
    if mark_col:
        try:
            numeric_marks = pd.to_numeric(df[mark_col].astype(str).str.replace('%',''), errors='coerce')
            st.metric("Class Average", f"{numeric_marks.mean():.2f}%")
        except:
            st.sidebar.warning("Selected 'Mark' column is not numeric.")

else:
    st.info("Please upload a file or paste data in the tabs above to begin.")
