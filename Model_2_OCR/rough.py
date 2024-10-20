import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from io import BytesIO
import re
import time
from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Tokenizer, LayoutLMv3FeatureExtractor
import torch
from PIL import Image

# Load the pre-trained LayoutLM model and tokenizer
tokenizer = LayoutLMv3Tokenizer.from_pretrained("microsoft/layoutlmv3-base")
model = LayoutLMv3ForTokenClassification.from_pretrained("microsoft/layoutlmv3-base")

# Function to extract text from PDF using PyMuPDF
def extract_text_from_pdf(pdf_file):
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text, True, "Text extracted successfully."
    except Exception as e:
        return "", False, f"Error extracting text using PyMuPDF: {str(e)}"

# Function to apply OCR using Tesseract for scanned PDFs
def extract_text_from_image(pdf_file):
    try:
        images = convert_from_path(pdf_file, dpi=300)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)
        return text, True, "OCR applied successfully."
    except Exception as e:
        return "", False, f"Error extracting text using OCR: {str(e)}"

# New function to extract structured data using LayoutLMv3 model
def extract_data_with_layoutlm(pdf_file):
    try:
        images = convert_from_path(pdf_file, dpi=300)
        all_text = ""

        for img in images:
            img = img.convert("RGB")  # Convert to RGB format for LayoutLM
            pixel_values = LayoutLMv3FeatureExtractor().encode_plus(img, return_tensors="pt")['pixel_values']
            outputs = model(pixel_values=pixel_values)
            logits = outputs.logits
            tokens = tokenizer.convert_ids_to_tokens(logits.argmax(dim=-1).squeeze().tolist())
            all_text += " ".join(tokens)

        return all_text, True, "Text extracted using LayoutLMv3."
    except Exception as e:
        return "", False, f"Error extracting text using LayoutLM: {str(e)}"

# Function to process extracted text into desired format (as before)
def safe_float(value):
    try:
        return float(value.replace(',', '').replace('₹', '').strip())
    except ValueError:
        return 0.0

def process_invoice_text(text):
    #Initializing variables and their confidence levels
    accuracy_scores = {}
    invoice_number, invoice_date, due_date = "", "", ""
    place_of_supply, place_of_origin = "", ""
    mobile, email, customer_details, gstin = "", "", "", ""
    taxable_value, sgst_amount, cgst_amount, igst_amount, final_amount = 0, 0, 0, 0, 0
    total_discount, tax_amount = 0, 0

    # Extracting and checking for invoice number
    invoice_number_match = re.search(r"Invoice #:\s*([A-Za-z0-9\-]+)", text)
    if invoice_number_match:
        invoice_number = invoice_number_match.group(1).strip()
        accuracy_scores['invoice_number'] = 1  #Example accuracy score based on pattern matching
    else:
        accuracy_scores['invoice_number'] = 0.5  # Low accuracy if not matched

    # Extracting and checking for invoice date
    invoice_date_match = re.search(r"Invoice Date:\s*([0-9A-Za-z\s]+)\s*Due Date:", text)
    if invoice_date_match:
        invoice_date = invoice_date_match.group(1).strip()
        accuracy_scores['invoice_date'] = 1  #example score based on match presence
    else:
        accuracy_scores['invoice_date'] = 0.6

    # Extracting and checking for due date
    due_date_match = re.search(r"Due Date:\s*([0-9A-Za-z\s]+)\s*Customer Details:", text)
    if due_date_match:
        due_date = due_date_match.group(1).strip()
        accuracy_scores['due_date'] = 1
    else:
        accuracy_scores['due_date'] = 0.6

    # Extracting place of supply
    place_of_supply_match = re.search(r"Place of Supply:\s*([0-9A-Za-z\s\-]+)", text)
    if place_of_supply_match:
        place_of_supply = place_of_supply_match.group(1).strip()
        accuracy_scores['place_of_supply'] = 0.98
    else:
        accuracy_scores['place_of_supply'] = 0.5

    # Extracting and validating GSTIN
    gstin_match = re.search(r"GSTIN\s*([A-Za-z0-9]+)", text)
    if gstin_match:
        gstin = gstin_match.group(1).strip()
        accuracy_scores['gstin'] = 1
    else:
        accuracy_scores['gstin'] = 0.6

    # Extracting taxable value with validation
    taxable_value_match = re.search(r"Taxable Amount\s*₹([0-9,]+\.\d{2})", text)
    if taxable_value_match:
        taxable_value = safe_float(taxable_value_match.group(1))
        accuracy_scores['taxable_value'] = 1
    else:
        accuracy_scores['taxable_value'] = 0.6

    # Extracting final amount
    final_amount_match = re.search(r"Total\s*₹([0-9,]+\.\d{2})", text)
    if final_amount_match:
        final_amount = safe_float(final_amount_match.group(1))
        accuracy_scores['final_amount'] = 1
    else:
        accuracy_scores['final_amount'] = 0.5

    # Calculating total tax amount
    tax_amount = sgst_amount + cgst_amount + igst_amount

    # Calculate overall trust score (average of individual scores)
    overall_trust_score = sum(accuracy_scores.values()) / len(accuracy_scores)
    accuracy_scores['overall_trust_score'] = overall_trust_score

    # Return parsed data and accuracy scores
    return {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "place_of_supply": place_of_supply,
        "gstin": gstin,
        "taxable_value": taxable_value,
        "final_amount": final_amount,
        "overall_trust_score": overall_trust_score
    }, accuracy_scores

# Streamlit app with LayoutLM integration
st.title("Advanced Invoice Extraction with LayoutLM")
st.write("Upload invoices (PDFs) and receive detailed extraction with accuracy scores using deep learning-based LayoutLM OCR.")

uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    extracted_data = []
    start_time = time.time()

    for pdf_file in uploaded_files:
        extraction_status = {}

        try:
            # First, try to extract text using PyMuPDF
            extracted_text, success, message = extract_text_from_pdf(pdf_file)
            extraction_status['method'] = 'PyMuPDF'
            extraction_status['success'] = success
            extraction_status['message'] = message

            if not success:
                # Try LayoutLM deep learning model for OCR
                extracted_text, success, message = extract_data_with_layoutlm(pdf_file)
                extraction_status['method'] = 'LayoutLMv3'
                extraction_status['success'] = success
                extraction_status['message'] = message

            if success:
                # Process extracted text into structured data
                invoice_data, accuracy_scores = process_invoice_text(extracted_text)
                invoice_data['extraction_status'] = extraction_status
                invoice_data['accuracy_scores'] = accuracy_scores
                extracted_data.append(invoice_data)
            else:
                st.error(f"Failed to extract text for {pdf_file.name}: {message}")

        except Exception as e:
            st.error(f"Error processing file {pdf_file.name}: {str(e)}")
            extraction_status['success'] = False
            extraction_status['message'] = str(e)

    # Calculate total processing time
    processing_time = time.time() - start_time
    st.write(f"Processed {len(uploaded_files)} files in {processing_time:.2f} seconds.")

    # Display extracted data and accuracy scores
    if extracted_data:
        df = pd.DataFrame(extracted_data)
        st.write("Extracted Data with Accuracy Scores:")
        st.dataframe(df)

        # Export to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)

        st.download_button(
            label="Download Excel file",
            data=output.getvalue(),
            file_name="extracted_invoices_with_accuracy.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )