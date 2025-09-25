import streamlit as st
import json
from PIL import Image
import io
import pytesseract
import hashlib
from pdf2image import convert_from_bytes
import pandas as pd

# ---------------- OCR FUNCTION ----------------
def process_certificate_ocr(image):
    """
    Extracts important fields like name, roll number, and certificate ID
    from the given certificate image using Tesseract OCR.
    """
    try:
        text = pytesseract.image_to_string(image, config="--psm 6")  # Better layout detection

        extracted_data = {
            "name": "",
            "roll_no": "",
            "cert_id": ""
        }

        for line in text.split("\n"):
            line_clean = line.strip()
            if "Name" in line_clean:
                extracted_data["name"] = line_clean.split(":")[-1].strip()
            elif "Roll" in line_clean or "Roll No" in line_clean:
                extracted_data["roll_no"] = line_clean.split(":")[-1].strip()
            elif "Certificate ID" in line_clean or "Cert ID" in line_clean:
                extracted_data["cert_id"] = line_clean.split(":")[-1].strip()

        return {
            "extracted_data": extracted_data,
            "ocr_confidence": 85,  # Mock confidence
            "full_text": text
        }

    except Exception as e:
        return {
            "extracted_data": {},
            "ocr_confidence": 0,
            "full_text": "",
            "error": str(e)
        }

# ---------------- TEXT NORMALIZATION ----------------
def normalize_text(text):
    return text.strip().lower().replace(" ", "")

# ---------------- STREAMLIT FRONTEND ----------------
st.set_page_config(page_title="JACVS Verifier", layout="wide")

st.title("🛡️ JACVS - Jharkhand Academic Credential Verification System")
st.markdown("Upload a certificate (PDF/JPG/PNG) and a CSV file for verification.")

# Sidebar Instructions
with st.sidebar:
    st.header("How to Use")
    st.write("- Ensure the certificate is scanned clearly.")
    st.write("- Supported formats: PDF, JPG, JPEG, PNG")
    st.write("- Upload a CSV file with columns: name, roll_no, cert_id")
    st.write("- For institutions: Contact admin for bulk verification tools.")

# ---------------- CSV FILE UPLOAD ----------------
csv_file = st.file_uploader("Upload CSV file with student records", type=['csv'])
records_dict = {}
if csv_file:
    try:
        records_df = pd.read_csv(csv_file)
        if all(col in records_df.columns for col in ['name','roll_no','cert_id']):
            # Normalize all CSV data
            records_dict = {normalize_text(k): 
                            {"roll_no": normalize_text(v['roll_no']), "cert_id": normalize_text(v['cert_id'])} 
                            for k,v in records_df.set_index('name').T.to_dict('dict').items()}
            st.success(f"Loaded {len(records_dict)} records from CSV.")
        else:
            st.error("CSV must have columns: name, roll_no, cert_id")
    except Exception as e:
        st.error(f"Error reading CSV: {e}")

# ---------------- CERTIFICATE UPLOAD ----------------
uploaded_file = st.file_uploader("Choose a certificate file", type=['pdf', 'jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # Handle PDF
    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(uploaded_file.read(), poppler_path="/usr/bin")
        if len(images) == 0:
            st.error("No pages found in PDF.")
            st.stop()
    else:
        images = [Image.open(uploaded_file)]

    # Display all pages
    st.subheader("Uploaded Certificate Pages")
    for i, image in enumerate(images):
        st.image(image, caption=f"Page {i+1}", use_column_width=True)

    # Process OCR for all pages
    full_extracted_data = []
    for i, image in enumerate(images):
        with st.spinner(f"🔍 Processing page {i+1}..."):
            ocr_result = process_certificate_ocr(image)
            full_extracted_data.append(ocr_result)

    # Combine extracted data from all pages
    combined_data = {
        "name": "",
        "roll_no": "",
        "cert_id": "",
        "full_text": ""
    }

    for page_data in full_extracted_data:
        extracted = page_data.get("extracted_data", {})
        for key in ["name", "roll_no", "cert_id"]:
            if extracted.get(key):
                combined_data[key] = extracted[key]
        combined_data["full_text"] += page_data.get("full_text", "") + "\n"

    # Normalize extracted fields
    name_norm = normalize_text(combined_data.get("name", ""))
    roll_norm = normalize_text(combined_data.get("roll_no", ""))
    cert_norm = normalize_text(combined_data.get("cert_id", ""))

    # Generate hash of all pages
    img_bytes = io.BytesIO()
    for image in images:
        image.save(img_bytes, format='PNG')
    document_hash = hashlib.sha256(img_bytes.getvalue()).hexdigest()

    # ---------------- VERIFICATION LOGIC ----------------
    anomalies = []
    confidence_score = 85
    status = "Valid"
    recommendation = "Proceed with verification."

    if records_dict:
        if name_norm in records_dict:
            if (records_dict[name_norm]['roll_no'] != roll_norm or
                records_dict[name_norm]['cert_id'] != cert_norm):
                anomalies.append("Mismatch in Roll No or Certificate ID")
                status = "Caution"
                confidence_score = 60
                recommendation = "Manual review recommended."
            else:
                status = "Valid"
                confidence_score = 85
                recommendation = "Proceed with verification."
        else:
            anomalies.append("Name not found in records")
            status = "Forged"
            confidence_score = 30
            recommendation = "Document appears invalid."
    else:
        st.warning("No CSV records loaded. Verification not performed.")

    if any(page.get('ocr_confidence', 0) < 70 for page in full_extracted_data):
        anomalies.append("Low OCR confidence - blurry image?")

    # Final result
    result = {
        "status": status,
        "confidence_score": confidence_score,
        "recommendation": recommendation,
        "anomalies": anomalies,
        "extracted_data": combined_data,
        "document_hash": document_hash,
        "full_text": combined_data["full_text"]
    }

    # ---------------- DISPLAY RESULTS ----------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Verification Report")
        status_color = "🟢" if result["status"] == "Valid" else ("🟡" if result["status"] == "Caution" else "🔴")
        st.markdown(f"**Status:** {status_color} {result['status']} ({result['confidence_score']}% Confidence)")
        st.write("**Recommendation:**", result['recommendation'])

        if result['anomalies']:
            st.error("⚠️ Anomalies Detected:")
            for anomaly in result['anomalies']:
                st.write(f"- {anomaly}")
        else:
            st.success("✅ No issues found.")

    with col2:
        st.subheader("📄 Extracted Data")
        for key, value in result['extracted_data'].items():
            if key != "full_text" and value:
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

        st.write(f"**Document Hash:** {result['document_hash'][:16]}...")  # Show only first 16 chars

    # Download JSON report
    report_json = json.dumps(result, indent=2, ensure_ascii=False)
    st.download_button(
        "📥 Download Report (JSON)",
        report_json,
        file_name="jacvs_report.json",
        mime="application/json"
    )

# Footer
st.markdown("---")
st.markdown("Built for **Jharkhand Education** | **Privacy Notice:** No data is stored without consent.")
