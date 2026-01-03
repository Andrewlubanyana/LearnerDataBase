import streamlit as st
import pandas as pd
import pdfplumber
from docx import Document
import io

st.set_page_config(page_title="Universal Data Fixer", layout="wide")

# --- 1. THE DATA ENGINE ---
def get_data(file):
    ext = file.name.split('.')[-1].lower()
    
    # EXCEL / CSV: High Accuracy
    if ext == 'csv': return pd.read_csv(file)
    if ext == 'xlsx': return pd.read_excel(file)
    
    # PDF: Extracting Tables or Text
    if ext == 'pdf':
        with pdfplumber.open(file) as pdf:
            all_rows = []
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    all_rows.extend(table)
            if all_rows:
                return pd.DataFrame(all_rows[1:], columns=all_rows[0])
            # Fallback to lines if no table
            text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
            lines = [line.split() for line in text.split('\n') if line.strip()]
            return pd.DataFrame(lines)

    # WORD: Extracting Tables or Text
    if ext == 'docx':
        doc = Document(file)
        if doc.tables:
            table = doc.tables[0]
            data = [[c.text.strip() for c in r.cells] for r in table.rows]
            return pd.DataFrame(data[1:], columns=data[0])
        lines = [p.text.split() for p in doc.paragraphs if p.text.strip()]
        return pd.DataFrame(lines)
    
    return None

# --- 2. THE INTERACTIVE INTERFACE ---
st.title("📂 Flexible Data Analyzer")
st.info("Upload any document. If the columns look wrong, use the sidebar to re-map them.")

uploaded_file = st.file_uploader("Upload Document", type=['csv', 'xlsx', 'pdf', 'docx'])

if uploaded_file:
    df = get_data(uploaded_file)
    
    if df is not None:
        # Clean up: remove empty columns/rows
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        # Reset headers to be simple strings
        df.columns = [f"Column {i} ({str(c)})" for i, c in enumerate(df.columns)]

        # --- SIDEBAR: FLEXIBLE MAPPING ---
        st.sidebar.header("🛠️ Fix Your Data")
        st.sidebar.write("If the data is scrambled, pick the correct columns below:")
        
        name_col = st.sidebar.selectbox("Which column is 'Name'?", df.columns, index=0)
        mark_col = st.sidebar.selectbox("Which column is 'Mark'?", df.columns, index=min(1, len(df.columns)-1))
        
        sort_by = st.sidebar.selectbox("Sort Table By:", df.columns)
        order = st.sidebar.radio("Order:", ["Ascending", "Descending"])

        # Apply Sorting
        df = df.sort_values(by=sort_by, ascending=(order == "Ascending"))

        # --- DISPLAY ---
        st.subheader("Your Extracted Database")
        st.dataframe(df, use_container_width=True)

        # --- ANALYSIS ---
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 🔍 Column Focus")
            # Show a clean version of just the chosen columns
            clean_df = df[[name_col, mark_col]].copy()
            clean_df.columns = ["Student Name", "Mark"]
            st.table(clean_df.head(10))

        with col2:
            st.write("### 📈 Quick Stats")
            try:
                # Force the chosen Mark column to be a number for calculation
                numeric_marks = pd.to_numeric(df[mark_col].astype(str).str.replace('%',''), errors='coerce')
                avg = numeric_marks.mean()
                st.metric("Calculated Average", f"{avg:.2f}%")
            except:
                st.warning("Could not calculate average. Please ensure the 'Mark' column only contains numbers.")

    else:
        st.error("No readable data found in this file.")
