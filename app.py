import streamlit as st
import pandas as pd
import pdfplumber
from docx import Document

st.set_page_config(page_title="High-Precision Database", layout="wide")

def reconstruct_from_coordinates(file):
    """
    This is the most accurate way to read messy PDFs. 
    It groups words by their vertical position (y-axis).
    """
    all_data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            # Extract words with their location data
            words = page.extract_words(x_tolerance=3, y_tolerance=3)
            if not words: continue
            
            # Sort words: first by top position (row), then by left position (column)
            words.sort(key=lambda w: (w['top'], w['x0']))
            
            # Group words that are on the same line (within 3 pixels of each other)
            lines = []
            if words:
                current_line = [words[0]]
                for i in range(1, len(words)):
                    # If this word is roughly at the same height as the previous word
                    if abs(words[i]['top'] - current_line[-1]['top']) < 3:
                        current_line.append(words[i])
                    else:
                        lines.append(current_line)
                        current_line = [words[i]]
                lines.append(current_line)
            
            # Convert word groups into strings
            for line in lines:
                line_text = [w['text'] for w in line]
                all_data.append(line_text)
    
    # Create a DataFrame where columns are just numbered 0, 1, 2...
    return pd.DataFrame(all_data)

def process_any_file(file):
    ext = file.name.split('.')[-1].lower()
    
    if ext == 'csv': return pd.read_csv(file)
    if ext == 'xlsx': return pd.read_excel(file)
    
    if ext == 'pdf':
        # Try precision coordinate reconstruction first
        return reconstruct_from_coordinates(file)
            
    if ext == 'docx':
        doc = Document(file)
        data = []
        # Try tables first
        for table in doc.tables:
            for row in table.rows:
                data.append([cell.text.strip() for cell in row.cells])
        # If no tables, use paragraph lines
        if not data:
            data = [p.text.split() for p in doc.paragraphs if p.text.strip()]
        return pd.DataFrame(data)

st.title("🎯 High-Precision Student Database")
st.write("This version uses **Coordinate Mapping** to keep your data aligned.")

uploaded_file = st.file_uploader("Upload Document", type=['csv', 'xlsx', 'pdf', 'docx'])

if uploaded_file:
    df = process_any_file(uploaded_file)
    
    if df is not None:
        # 1. Clean up columns that are entirely empty
        df = df.dropna(axis=1, how='all').fillna("")
        
        # 2. Sidebar Controls
        st.sidebar.header("Data Alignment")
        st.sidebar.info("If the data is shifted, use the sorting tools below.")
        
        # Allow user to pick which column to sort by
        sort_col = st.sidebar.selectbox("Sort by Column:", df.columns)
        order = st.sidebar.radio("Order:", ["Ascending", "Descending"])
        df = df.sort_values(by=sort_col, ascending=(order == "Ascending"))

        # 3. Interactive View
        st.subheader("Extracted Table")
        st.dataframe(df, use_container_width=True)
        
        # 4. Analysis
        st.divider()
        st.write("### 📊 Search & Filter")
        search = st.text_input("Search for a specific Name or Mark:")
        if search:
            mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            st.table(df[mask])
            
    else:
        st.error("No data could be extracted from this file format.")
