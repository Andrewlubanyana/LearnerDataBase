import streamlit as st
import pandas as pd
import plotly.express as px

# Setup the page appearance
st.set_page_config(page_title="Data Analyzer", layout="wide")

# Title and Instructions
st.title("📂 Interactive Student Database")
st.markdown("Upload your file (CSV or Excel) to analyze marks and sort data.")

# --- 1. FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload your document here", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Load the data automatically
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success("File uploaded successfully!")

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
