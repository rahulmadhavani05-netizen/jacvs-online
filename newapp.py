import streamlit as st
import pandas as pd
from datetime import datetime

# -----------------------
# Title
# -----------------------
st.title("Certificate Verification System")

# -----------------------
# Upload Dataset
# -----------------------
st.subheader("Upload Dataset (CSV)")
dataset_file = st.file_uploader("Upload CSV dataset", type=["csv"])
df = pd.DataFrame()
if dataset_file:
    try:
        df = pd.read_csv(dataset_file)
        st.success("Dataset loaded successfully!")
        st.info("CSV columns: name, rollNumber, certificateId, institution, issueDate, course, grades")
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")

# -----------------------
# Upload Certificate
# -----------------------
st.subheader("Upload Certificate")
cert_file = st.file_uploader("Upload certificate file (image or PDF)", type=["png", "jpg", "jpeg", "pdf"])

# -----------------------
# Process Certificate
# -----------------------
if cert_file and not df.empty:
    st.info("Processing certificate...")

    # Simulated OCR: for testing, ask user to input certificate ID
    extracted_cert_id = st.text_input("Enter certificate ID (simulate OCR extraction)")

    if extracted_cert_id:
        # Check dataset
        match = df[df['certificateId'].astype(str) == str(extracted_cert_id)]
        if not match.empty:
            st.success("Certificate is Authentic ✅")
            record = match.to_dict(orient="records")[0]
            st.json(record)
        else:
            st.warning("Data Not Available ❌")
            st.json({
                "name": "Unknown",
                "rollNumber": "Unknown",
                "certificateId": extracted_cert_id,
                "institution": "Unknown",
                "course": "Unknown",
                "grades": "Unknown",
                "issueDate": datetime.now().strftime("%Y-%m-%d")
            })
elif cert_file and df.empty:
    st.warning("Please upload a dataset first!")
