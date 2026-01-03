import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="CSV Data Aligner", layout="wide")

st.title("🛠️ CSV Database & Aligner")
st.write("If your CSV looks messy, use the **Delimiter** and **Header** settings below to fix the arrangement.")

# --- 1. UPLOAD WITH ADVANCED SETTINGS ---
with st.expander("Settings: Fix CSV Alignment", expanded=True):
    col1, col2, col3 = st.columns(3)
    sep = col1.selectbox("Separator (Delimiter):", [",", ";", "Tab", "Space", "|"], help="What separates your words?")
    encoding = col2.selectbox("File Encoding:", ["utf-8", "latin1", "cp1252"])
    skip_rows = col3.number_input("Skip first X rows:", min_value=0, value=0)

uploaded_file = st.file_uploader("Upload your CSV file", type=['csv', 'txt'])

if uploaded_file:
    try:
        # Read the CSV with the user-defined settings
        df = pd.read_csv(
            uploaded_file, 
            sep=sep, 
            encoding=encoding, 
            skiprows=skip_rows,
            on_bad_lines='warn', # Don't crash on messy lines
            engine='python'
        )

        if not df.empty:
            # Clean column names
            df.columns = [str(c).strip() for c in df.columns]

            # --- 2. INTERACTIVE DATA CLEANING ---
            st.sidebar.header("Filter & Sort")
            
            # Search Bar
            search_query = st.sidebar.text_input("🔍 Search Name/Surname:")
            if search_query:
                mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                df = df[mask]

            # Column Selection (In case CSV has too many random columns)
            to_keep = st.sidebar.multiselect("Keep these columns:", df.columns, default=list(df.columns))
            if to_keep:
                df = df[to_keep]

            # Sorting
            sort_target = st.sidebar.selectbox("Sort data by:", df.columns)
            order = st.sidebar.radio("Order:", ["Ascending", "Descending"])
            df = df.sort_values(by=sort_target, ascending=(order == "Ascending"))

            # --- 3. DISPLAY ---
            st.subheader("Corrected Database View")
            st.dataframe(df, use_container_width=True)

            # --- 4. ANALYSIS ---
            st.divider()
            st.subheader("📊 Statistics")
            
            # Find the mark column
            mark_col = next((c for c in df.columns if 'mark' in c.lower() or 'score' in c.lower() or 'grade' in c.lower()), None)
            
            if mark_col:
                # Convert to numeric, stripping strings like '%'
                df[mark_col] = pd.to_numeric(df[mark_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
                valid_marks = df[mark_col].dropna()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Average Mark", f"{valid_marks.mean():.2f}%")
                c2.metric("Highest", f"{valid_marks.max()}%")
                c3.metric("Total Students", len(df))
            else:
                st.info("To see mark analysis, ensure your CSV has a column header named 'Mark' or 'Score'.")

    except Exception as e:
        st.error(f"Error reading CSV: {e}. Try changing the Separator or Encoding settings above.")
else:
    st.info("Upload a CSV to begin. Use the 'Settings' box above if the data appears in one single column.")
