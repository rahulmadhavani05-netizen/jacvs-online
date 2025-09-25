import streamlit as st
import pandas as pd
import random
import datetime

st.set_page_config(page_title="Jharkhand Degree Verifier", layout="wide")

# -------------------------
# Helper Functions
# -------------------------

def generate_mock_verification(file_name):
    status = random.choices(
        ["Authentic", "Suspicious", "Invalid"], weights=[0.85, 0.10, 0.05], k=1
    )[0]
    confidence = round(random.uniform(80, 99.9), 1)
    anomalies = []
    if status == "Suspicious":
        anomalies.append("Mismatch in certificate ID")
    elif status == "Invalid":
        anomalies.append("Document tampered")
    extracted_data = {
        "Name": "Rajesh Kumar",
        "Roll Number": "2021CS101",
        "Certificate ID": "JHARKHAND2021CS101",
        "Institution": "Ranchi University",
        "Course": "Bachelor of Computer Science",
        "Grades": "A+",
        "Issue Date": "2024-05-15"
    }
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return status, confidence, anomalies, extracted_data, timestamp

# -------------------------
# Sidebar Navigation
# -------------------------
st.sidebar.title("Jharkhand Degree Verifier")
menu = st.sidebar.radio("Go to", ["Home", "Verify Certificate", "Admin Portal", "Institution Portal"])

# -------------------------
# Home Page
# -------------------------
if menu == "Home":
    st.markdown("# 🛡️ Secure Certificate Verification")
    st.markdown(
        "Protect academic integrity with our advanced fake degree detection system. "
        "Fast, reliable verification for employers, institutions, and government bodies."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Verify Certificate"):
            menu = "Verify Certificate"
    with col2:
        if st.button("🏫 Institution Login"):
            menu = "Institution Portal"

    st.markdown("### Features")
    st.markdown("**AI-Powered Verification:** Advanced OCR and machine learning algorithms to detect tampered documents and forged signatures")
    st.markdown("**Blockchain Security:** Digital watermarking and cryptographic validation for newly issued certificates")
    st.markdown("**Real-time Monitoring:** Comprehensive admin dashboard with fraud detection analytics and alert systems")
    
    st.markdown("### Trusted by Institutions")
    st.metric("Universities", "50+")
    st.metric("Colleges", "500+")
    st.metric("Certificates Verified", "1M+")
    st.metric("Accuracy Rate", "99.8%")

# -------------------------
# Verify Certificate Page
# -------------------------
elif menu == "Verify Certificate":
    st.markdown("# 🔍 Verify Certificate Authenticity")
    uploaded_file = st.file_uploader("Upload a certificate (PDF or image)", type=["pdf","png","jpg","jpeg"])
    
    if uploaded_file:
        with st.spinner("Analyzing document..."):
            status, confidence, anomalies, data, timestamp = generate_mock_verification(uploaded_file.name)
        st.success(f"✅ Verification Complete: **{status}**")
        st.info(f"Confidence: {confidence}%  •  Timestamp: {timestamp}")

        st.markdown("### Extracted Data")
        st.table(data)

        if anomalies:
            st.warning("⚠️ Detected Anomalies")
            for a in anomalies:
                st.write(f"- {a}")

        st.download_button(
            "📄 Download Verification Report",
            data=str({**data, "status": status, "confidence": confidence, "anomalies": anomalies, "timestamp": timestamp}),
            file_name=f"verification_report_{data['Roll Number']}.txt"
        )

# -------------------------
# Admin Portal
# -------------------------
elif menu == "Admin Portal":
    st.markdown("# 🛠️ Admin Dashboard")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        if username == "admin" and password == "admin123":
            st.success("✅ Logged in successfully")
            
            st.markdown("### Overview")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Verifications", "12,457")
            col2.metric("Authentic", "11,823")
            col3.metric("Suspicious", "489")
            col4.metric("Invalid", "145")

            st.markdown("### Top Institutions")
            st.table(pd.DataFrame([
                {"Institution": "Ranchi University", "Verifications": 4567},
                {"Institution": "BIT Mesra", "Verifications": 3124},
                {"Institution": "Jharkhand Technical University", "Verifications": 1987},
            ]))
        else:
            st.error("❌ Invalid credentials")

# -------------------------
# Institution Portal
# -------------------------
elif menu == "Institution Portal":
    st.markdown("# 🏫 Institution Portal")
    institution_id = st.text_input("Institution ID")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        st.success("✅ Logged in successfully")

        st.markdown("### Bulk Certificate Upload")
        uploaded_csv = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_csv:
            df = pd.read_csv(uploaded_csv)
            st.success(f"Uploaded {len(df)} records")
            st.dataframe(df)
            st.info("All data will be encrypted and secured")

        st.markdown("### Records")
        st.table(pd.DataFrame([{
            "Name": "Amit Kumar",
            "Roll Number": "2021CS101",
            "Certificate ID": "JHARKHAND2021CS101",
            "Status": "Verified"
        }]))
