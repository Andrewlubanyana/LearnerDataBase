import streamlit as st
import pandas as pd
import pdfplumber
from docx import Document
import re

st.set_page_config(page_title="Smart Student Database", layout="wide")

# --- 1. IMPROVED HEURISTIC SCANNER ---
def extract_from_plain_text(text):
    lines = text.split('\n')
    extracted_data = []

    for line in lines:
        line = line.strip()
        if not line: continue

        # 1. Look for Marks (1 to 3 digit numbers, often followed by %)
        mark_match = re.search(r'\b(\d{1,3})\b(?:\s*%)?', line)
        mark = mark_match.group(1) if mark_match else None

        # 2. Look for Gender
        gender_match = re.search(r'\b(Male|Female|M|F)\b', line, re.IGNORECASE)
        gender = gender_match.group(1).capitalize() if gender_match else "N/A"

        # 3. Look for Names (Captalized words that aren't 'Male' or 'Female')
        # We look for 1 or 2 capitalized words at the start of segments
        names = re.findall(r'\b([A-Z][a-z]+)\b', line)
        # Filter out "Male" or "Female" from being picked up as names
        names = [n for n in names if n.lower() not in ['male', 'female']]
        
        full_name = " ".join(names[:2]) if names else "Unknown"

        # Only add if we found at least a Name and a Mark
        if names or mark:
            extracted_data.append({
                "Full Name": full_name,
                "Mark": mark if mark else "0",
                "Gender": gender
            })

    if extracted_data:
        return pd.DataFrame(extracted_data)
    return None

# --- 2. DATA PROCESSING ENGINE ---
def process_upload(file):
    ext = file.name.split('.')[-1].lower()
    raw_text = ""

    # A. Tables first (High Accuracy)
    if ext == 'csv': return pd.read_csv(file)
    if ext == 'xlsx': return pd.read_excel(file)
    
    if ext == 'pdf':
        with pdfplumber.open(file) as pdf:
            # Check for tables on any page
            for page in pdf.pages:
                table = page.extract_table()
                if table: return pd.DataFrame(table[1:], columns=table[0])
            # If no tables, get all text
            raw_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
            
    elif ext == 'docx':
        doc = Document(file)
        if doc.tables:
            table = doc.tables[0]
            data = [[c.text.strip() for c in r.cells] for r in table.rows]
            return pd.DataFrame(data[1:], columns=data[0])
        raw_text = "\n".join([p.text for p in doc.paragraphs])

    # B. Plain Text Heuristics (Fall-back)
    if raw_text:
        return extract_from_plain_text(raw_text)
    return None

# --- 3. APP UI ---
st.title("📊 High-Accuracy Student Analyzer")
uploaded_file = st.file_uploader("Upload Document (Table or Plain Text)", type=['csv', 'xlsx', 'pdf', 'docx'])

if uploaded_file:
    df = process_upload(uploaded_file)
    
    if df is not None:
        # Final Clean-up
        df = df.dropna(subset=['Full Name']) if 'Full Name' in df.columns else df
        df.columns = [str(c).strip() for c in df.columns]

        # Sorting Sidebar
        st.sidebar.header("Sort Settings")
        sort_by = st.sidebar.selectbox("Sort by:", df.columns)
        df = df.sort_values(by=sort_by)

        st.subheader("Final Result")
        st.dataframe(df, use_container_width=True)
        
        # Math Analysis
        mark_col = next((c for c in df.columns if 'mark' in c.lower() or 'score' in c.lower()), None)
        if mark_col:
            df[mark_col] = pd.to_numeric(df[mark_col], errors='coerce')
            st.info(f"Class Average: {df[mark_col].mean():.2f}%")
    else:
        st.error("Could not extract data. Please ensure names and marks are clearly typed.")
