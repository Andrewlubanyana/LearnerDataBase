import streamlit as st
import pandas as pd
import pdfplumber
from docx import Document
import io

# 1. Update the uploader to explicitly allow these extensions
uploaded_file = st.file_uploader(
    "Upload Student Data", 
    type=['csv', 'xlsx', 'pdf', 'docx']
)

if uploaded_file is not None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    df = None

    try:
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        
        elif file_extension == 'xlsx':
            df = pd.read_excel(uploaded_file)
        
        elif file_extension == 'pdf':
            with pdfplumber.open(uploaded_file) as pdf:
                # Extracting table from the first page
                table = pdf.pages[0].extract_table()
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])
                else:
                    st.error("No clear table found in this PDF.")

        elif file_extension == 'docx':
            doc = Document(uploaded_file)
            data = []
            # Looks for the first table in the Word Doc
            if doc.tables:
                table = doc.tables[0]
                for row in table.rows:
                    data.append([cell.text.strip() for cell in row.cells])
                df = pd.DataFrame(data[1:], columns=data[0])
            else:
                st.error("No table found in this Word document.")

        # If data was successfully loaded into 'df'
        if df is not None:
            st.success(f"Successfully loaded: {uploaded_file.name}")
            # Clean column names (remove hidden spaces)
            df.columns = [str(c).strip() for c in df.columns]
            st.dataframe(df)
            
            # --- Analysis Logic Here ---
            
    except Exception as e:
        st.error(f"Error processing file: {e}")
        # --- (Continue with the Sorting and Charting code from before) ---
        # Note: The rest of the sorting/charting code remains the same!
        st.dataframe(df)
    else:
        st.error("Could not find a valid table inside this file.")

        # --- 2. DATA CLEANING (Standardizing Column Names) ---
        # This makes the app "smart" by finding columns even if they are lowercase
        df.columns = [c.strip() for c in df.columns] 
        
        # --- 3. SIDEBAR CONTROLS ---
        st.sidebar.header("Filter & Sort")
        
        # Sorting
        sort_by = st.sidebar.selectbox("Sort data by:", df.columns)
        order = st.sidebar.radio("Direction:", ["Ascending", "Descending"])
        
        df = df.sort_values(by=sort_by, ascending=(order == "Ascending"))

        # --- 4. ANALYSIS CALCULATIONS ---
        # We look for a column with 'mark' or 'score' in the name
        mark_col = next((c for c in df.columns if 'mark' in c.lower() or 'score' in c.lower()), None)

        if mark_col:
            avg_score = df[mark_col].mean()
            max_score = df[mark_col].max()
            min_score = df[mark_col].min()

            # Display "Metric" boxes at the top
            m1, m2, m3 = st.columns(3)
            m1.metric("Average Mark", f"{avg_score:.1f}%")
            m2.metric("Highest Mark", f"{max_score}%")
            m3.metric("Lowest Mark", f"{min_score}%")

        # --- 5. INTERACTIVE DATABASE TABLE ---
        st.subheader("Interactive Data Table")
        # Add a search bar for names
        search_term = st.text_input("Search by Name or Surname:")
        if search_term:
            # Filters the dataframe if the search term is in any column
            df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
        
        st.dataframe(df, use_container_width=True)

        # --- 6. VISUAL CHARTS ---
        st.subheader("Data Visualizations")
        c1, c2 = st.columns(2)

        with c1:
            # Chart 1: Gender split (if column exists)
            gender_col = next((c for c in df.columns if 'gender' in c.lower()), None)
            if gender_col:
                fig1 = px.pie(df, names=gender_col, title="Gender Distribution", hole=0.4)
                st.plotly_chart(fig1)

        with c2:
            # Chart 2: Performance distribution
            if mark_col:
                fig2 = px.histogram(df, x=mark_col, title="Grade Spread", color_discrete_sequence=['#636EFA'])
                st.plotly_chart(fig2)

    except Exception as e:
        st.error(f"Error: {e}. Please ensure your file has correct headers.")

else:
    st.info("Waiting for a file to be uploaded...")
