import streamlit as st
import json
from PIL import Image
import io
import pytesseract
import hashlib
from pdf2image import convert_from_bytes
import pandas as pd
import cv2
import numpy as np
import re  # For better field extraction

# Set Tesseract path (update for Windows if needed; remove if in PATH)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows path; comment out for macOS/Linux

# ---------------- ENHANCED OCR FUNCTION ----------------
def preprocess_image(image):
    """Enhance image for better OCR: Grayscale, contrast, denoise, threshold."""
    # Convert PIL to OpenCV
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Grayscale
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Denoise
    denoised = cv2.medianBlur(enhanced, 3)
    
    # Resize if small
    height, width = denoised.shape
    if height < 1000 or width < 1000:
        scale = 2.0
        denoised = cv2.resize(denoised, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Adaptive threshold for clean text
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Back to PIL
    processed_image = Image.fromarray(thresh)
    return processed_image

def process_certificate_ocr(image):
    """
    Enhanced OCR: Preprocess + Tesseract with real confidence and regex extraction.
    """
    try:
        # Preprocess for better accuracy
        processed = preprocess_image(image)
        
        # Tesseract with config for certificates
        custom_config = r'--oem 3 --psm 6'  # PSM 6 for uniform block text
        text = pytesseract.image_to_string(processed, config=custom_config, lang='eng')  # Add '+hin' for Hindi
        
        # Real confidence: Average word confidence
        data = pytesseract.image_to_data(processed, config=custom_config, output_type=pytesseract.Output.DICT)
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        ocr_confidence = np.mean(confidences) if confidences else 0
        
        # Extract fields with regex (more robust)
        extracted_data = {
            "name": "",
            "roll_no": "",
            "cert_id": ""
        }
        
        # Name (flexible: "Name:", "नाम:", etc.)
        name_match = re.search(r'(?:Name|नाम)[:\s]*([A-Za-z\s]+?)(?=\n|$|Roll|Certificate)', text, re.IGNORECASE | re.DOTALL)
        extracted_data["name"] = name_match.group(1).strip() if name_match else ""
        
        # Roll No
        roll_match = re.search(r'(?:Roll\s*(?:Number|No)[:\s]*)([A-Z0-9/]+)', text, re.IGNORECASE)
        extracted_data["roll_no"] = roll_match.group(1).strip() if roll_match else ""
        
        # Cert ID
        cert_match = re.search(r'(?:Certificate\s*(?:ID|No)|Cert\s*ID|ID[:\s]*)([A-Z0-9/]+)', text, re.IGNORECASE)
        extracted_data["cert_id"] = cert_match.group(1).strip() if cert_match else ""
        
        result = {
            "extracted_data": extracted_data,
            "ocr_confidence": ocr_confidence,
            "full_text": text
        }
        
        # Debug print (visible in terminal)
        if st.session_state.get('debug', False):
            print(f"=== OCR DEBUG ===\nFull Text: {text[:200]}...\nExtracted: {extracted_data}\nConfidence: {ocr_confidence:.1f}%\n================")
        
        return result

    except Exception as e:
        return {
            "extracted_data": {},
            "ocr_confidence": 0,
            "full_text": "",
            "error": str(e)
        }

# ---------------- TEXT NORMALIZATION ----------------
def normalize_text(text):
    """Normalize for matching: lower, remove spaces/punctuation."""
    return re.sub(r'[^\w]', '', text.lower().strip())  # Remove non-alphanumeric

# ---------------- STREAMLIT FRONTEND ----------------
st.set_page_config(page_title="JACVS Verifier", layout="wide")

st.title("🛡️ JACVS - Jharkhand Academic Credential Verification System")
st.markdown("Upload a certificate (PDF/JPG/PNG) and a CSV file for verification.")

# Sidebar: Instructions + Debug Toggle
with st.sidebar:
    st.header("How to Use")
    st.write("- Ensure the certificate is scanned clearly.")
    st.write("- Supported formats: PDF, JPG, JPEG, PNG")
    st.write("- Upload a CSV file with columns: name, roll_no, cert_id")
    st.write("- For institutions: Contact admin for bulk verification tools.")
    
    # Debug toggle
    debug = st.checkbox("Enable Debug Mode (shows raw OCR in terminal/browser)")
    if debug:
        st.session_state.debug = True
    else:
        st.session_state.debug = False

# ---------------- CSV FILE UPLOAD ----------------
csv_file = st.file_uploader("Upload CSV file with student records", type=['csv'])
records_dict = {}
if csv_file:
    try:
        records_df = pd.read_csv(csv_file)
        if all(col in records_df.columns for col in ['name', 'roll_no', 'cert_id']):
            # Normalize CSV data for matching (keys and values)
            records_dict = {
                normalize_text(row['name']): {
                    "roll_no": normalize_text(row['roll_no']),
                    "cert_id": normalize_text(row['cert_id'])
                }
                for _, row in records_df.iterrows()
            }
            st.success(f"Loaded {len(records_dict)} records from CSV.")
            
            # Show sample (for debug)
            if debug:
                st.write("**Sample Normalized Records:**")
                for name_norm, data in list(records_dict.items())[:3]:
                    st.write(f"- {name_norm}: Roll={data['roll_no']}, Cert={data['cert_id']}")
        else:
            st.error("CSV must have columns: name, roll_no, cert_id")
    except Exception as e:
        st.error(f"Error reading CSV: {e}")

# ---------------- CERTIFICATE UPLOAD ----------------
uploaded_file = st.file_uploader("Choose a certificate file", type=['pdf', 'jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # Read file content once
    file_content = uploaded_file.read()
    uploaded_file.seek(0)  # Reset for display if needed
    
    # Handle PDF (no hardcoded path; assumes Poppler in PATH)
    if uploaded_file.type == "application/pdf":
        try:
            images = convert_from_bytes(file_content)
            if len(images) == 0:
                st.error("No pages found in PDF. Ensure Poppler is installed and in PATH.")
                st.stop()
        except Exception as e:
            st.error(f"PDF processing error: {e}. Install Poppler and add to PATH.")
            st.stop()
    else:
        image = Image.open(io.BytesIO(file_content))
        images = [image]

    # Display all pages
    st.subheader("Uploaded Certificate Pages")
    for i, image in enumerate(images):
        st.image(image, caption=f"Page {i+1}", use_column_width=True)

    # Process OCR for all pages
    full_extracted_data = []
    for i, image in enumerate(images):
        with st.spinner(f"🔍 Processing page {i+1}..."):
            # Ensure RGB for OCR
            if image.mode != 'RGB':
                image = image.convert('RGB')
            ocr_result = process_certificate_ocr(image)
            full_extracted_data.append(ocr_result)
            
            # Show per-page debug if enabled
            if debug:
                st.write(f"**Page {i+1} Debug:** Confidence: {ocr_result.get('ocr_confidence', 0):.1f}% | Name: '{ocr_result.get('extracted_data', {}).get('name', 'Not found')}'")

    # Combine extracted data from all pages (take best non-empty)
    combined_data = {
        "name": "",
        "roll_no": "",
        "cert_id": "",
        "full_text": ""
    }
    for page_data in full_extracted_data:
        extracted = page_data.get("extracted_data", {})
        for key in ["name", "roll_no", "cert_id"]:
            if extracted.get(key) and not combined_data[key]:  # Take first non-empty
                combined_data[key] = extracted[key]
        combined_data["full_text"] += page_data.get("full_text", "") + "\n"

    # Normalize extracted fields for matching
    name_norm = normalize_text(combined_data.get("name", ""))
    roll_norm = normalize_text(combined_data.get("roll_no", ""))
    cert_norm = normalize_text(combined_data.get("cert_id", ""))

    # Show normalized for debug
    if debug:
        st.write(f"**Normalized Extracted:** Name='{name_norm}', Roll='{roll_norm}', Cert='{cert_norm}'")

    # Generate hash of all pages
    img_bytes = io.BytesIO()
    for image in images:
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        img_bytes.truncate(0)  # Reset for next
    img_bytes.seek(0)
    all_pages_bytes = io.BytesIO()
    for image in images:
        img_temp = io.BytesIO()
        image.save(img_temp, format='PNG')
        all_pages_bytes.write(img_temp.getvalue())
    document_hash = hashlib.sha256(all_pages_bytes.getvalue()).hexdigest()

    # ---------------- VERIFICATION LOGIC ----------------
    anomalies = []
    avg_confidence = np.mean([page.get('ocr_confidence', 0) for page in full_extracted_data])
    confidence_score = int(avg_confidence)  # Start with real OCR avg
    status = "Valid"
    recommendation = "Proceed with verification."

    if records_dict:
        if name_norm in records_dict:
            db_roll = records_dict[name_norm].get('roll_no', '')
            db_cert = records_dict[name_norm].get('cert_id', '')
            if roll_norm != db_roll or cert_norm != db_cert:
                anomalies.append("Mismatch in Roll No or Certificate ID")
                status = "Caution"
                confidence_score = min(confidence_score, 60)
                recommendation = "Manual review recommended."
            else:
                status = "Valid"
                confidence_score = max(confidence_score, 85)
                recommendation = "Proceed with verification."
        else:
            anomalies.append("Name not found in records")
            status = "Forged"
            confidence_score = min(confidence_score, 30)
            recommendation = "Document appears invalid."
    else:
        st.warning("No CSV records loaded. Skipping database match (using OCR only).")
        status = "OCR Processed"  # Neutral if no CSV

    # Confidence anomaly (only if truly low)
    if avg_confidence < 70:
        anomalies.append("Low OCR confidence - blurry image? Improve scan quality.")
        confidence_score = min(confidence_score, 30)

    # Boost if no anomalies
    if not anomalies and avg_confidence > 80:
        confidence_score = 95

    # Final result
    result = {
        "status": status,
        "confidence_score": confidence_score,
        "recommendation": recommendation,
        "anomalies": anomalies,
        "extracted_data": combined_data,
        "document_hash": document_hash,
        "full_text": combined_data["full_text"],
        "avg_ocr_confidence": avg_confidence
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

        st.write(f"**Document Hash:** {result['document_hash'][:16]}...")
        
        if debug:
            st.write("**Raw Full Text (First 200 chars):**")
            st.text(result['full_text'][:200])

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
