import streamlit as st
import pandas as pd
import pdfplumber
from docx import Document
import re

st.set_page_config(page_title="Universal Student Database", layout="wide")

# --- 1. NEW PLAIN TEXT SCANNER ---
def extract_from_plain_text(text):
    """
    Scans raw text for patterns like 'John Doe 85 Male' 
    or 'Name: Sarah, Mark: 90'
    """
    # This pattern looks for: [Name/Surname] [Number/Mark] [Gender]
    # It's flexible to handle different orderings
    pattern = r"([A-Z][a-z]+)\s+([A-Z][a-z]+)?\s*(\d{1,3})?\s*(Male|Female|M|F)?"
    
    matches = re.findall(pattern, text)
    if matches:
        # Convert matches into a structured list
        data = []
        for m in matches:
            data.append({
                "Name": m[0],
                "Surname": m[1] if m[1] else "N/A",
                "Mark": m[2] if m[2] else "0",
                "Gender": m[3] if m[3] else "N/A"
            })
        return pd.DataFrame(data)
    return None

# --- 2. FILE HELPERS ---
def process_upload(file):
    ext = file.name.split('.')[-1].lower()
    df = None
    raw_text = ""

    if ext == 'csv':
        return pd.read_csv(file)
    elif ext == 'xlsx':
        return pd.read_excel(file)
    
    # For PDF and Word, we first try to find tables. 
    # If no tables exist, we extract raw text.
    if ext == 'pdf':
        with pdfplumber.open(file) as pdf:
            # Try table extraction first
            table = pdf.pages[0].extract_table()
            if table:
                return pd.DataFrame(table[1:], columns=table[0])
            # If no table, get raw text
            raw_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            
    elif ext == 'docx':
        doc = Document(file)
        if doc.tables:
            data = [[cell.text.strip() for cell in row.cells] for row in doc.tables[0].rows]
            return pd.DataFrame(data[1:], columns=data[0])
        # If no table, get raw text
        raw_text = "\n".join([para.text for para in doc.paragraphs])

    if raw_text:
        return extract_from_plain_text(raw_text)
    return None

# --- 3. APP UI ---
st.title("📊 Universal Student Database")
st.write("Upload any file. I will look for tables first, then scan plain text for student data.")

uploaded_file = st.file_uploader("Upload Document", type=['csv', 'xlsx', 'pdf', 'docx'])

if uploaded_file:
    try:
        df = process_upload(uploaded_file)
        
        if df is not None:
            # Clean up the data
            df = df.dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            
            # SIDEBAR
            st.sidebar.header("Sort & Filter")
            sort_by = st.sidebar.selectbox("Sort by:", df.columns)
            order = st.sidebar.radio("Direction:", ["Ascending", "Descending"])
            df = df.sort_values(by=sort_by, ascending=(order == "Ascending"))

            # DISPLAY
            st.subheader("Extracted Database")
            st.dataframe(df, use_container_width=True)

            # ANALYSIS
            mark_col = next((c for c in df.columns if 'mark' in c.lower() or 'score' in c.lower()), None)
            if mark_col:
                df[mark_col] = pd.to_numeric(df[mark_col], errors='coerce')
                avg = df[mark_col].mean()
                st.metric("Detected Average Mark", f"{avg:.1f}%")
        else:
            st.error("Could not find any student data or tables in this document.")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please upload a file to begin.")
