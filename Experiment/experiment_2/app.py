import os
import streamlit as st
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import tempfile
import re
import json
from llama_cpp import Llama

# Set page configuration
st.set_page_config(page_title="Invoice Data Extraction", layout="wide")

# Initialize LLaMA model
@st.cache_resource
def load_llama_model():
    model_path = os.path.join("llama_model", "llama-2-7b-chat.Q5_K_M.gguf")
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_batch=512,
        use_mlock=True
    )
    return llm

llm = load_llama_model()

# Helper functions
def extract_text_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""
    return text

def extract_text_via_ocr(file):
    text = ""
    with tempfile.TemporaryDirectory() as path:
        try:
            images = convert_from_path(file, output_folder=path)
        except Exception as e:
            st.error(f"Error converting PDF to images: {e}")
            return ""
        for img in images:
            try:
                text += pytesseract.image_to_string(img) + "\n"
            except Exception as e:
                st.error(f"Error with OCR on image: {e}")
                return ""
    return text

def preprocess_text(text):
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_invoice_data(text):
    prompt = f"""
You are a model designed to extract invoice information. Please strictly extract and return the invoice information in the following JSON format, and nothing else:

JSON Format:
{{
    "Invoice Number": "",
    "Invoice Date": "",
    "Due Date": "",
    "Total Amount": "",
    "Vendor Name": "",
    "Vendor Address": "",
    "Buyer Name": "",
    "Buyer Address": "",
    "GSTIN Number": "",
    "Bank Details": {{
        "Name": "",
        "Account Number": "",
        "IFSC Code": ""
    }},
    "Payment Terms": ""
}}

Extract the information strictly from the invoice text provided below:

\"\"\" 
{text} 
\"\"\"

Ensure that the JSON is valid and strictly adheres to the format. Return no additional explanations.
"""
    response = llm(
        prompt,
        max_tokens=1024,
        temperature=0.0,
        stop=["\"\"\""]
    )
    return response

def parse_json(text):
    try:
        # Use regex to find the first JSON-like structure
        json_text_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_text_match:
            json_text = json_text_match.group()
            # Try loading the JSON
            data = json.loads(json_text)
            return data
        else:
            raise ValueError("No valid JSON found in the text.")
    except json.JSONDecodeError as e:
        st.error(f"JSON decode error: {e}")
        return None
    except Exception as e:
        st.error(f"Failed to parse JSON: {e}")
        return None

# Streamlit App
st.title("📄 Invoice Data Extraction")
st.write("Upload your invoice PDFs (Regular, Scanned, or Mixed) to extract relevant information.")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Processing..."):
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name

        # Attempt to extract text directly
        text = extract_text_from_pdf(tmp_file_path)

        # If no text found, perform OCR
        if not text.strip():
            text = extract_text_via_ocr(tmp_file_path)

        text = preprocess_text(text)

        if not text.strip():
            st.error("Failed to extract text from the PDF.")
        else:
            st.subheader("Extracted Text")
            st.text_area("Raw Extracted Text", text, height=300)

            # Extract structured data using LLaMA model
            model_response = extract_invoice_data(text)

            if model_response is None:
                st.error("Model inference failed.")
            else:
                # Debugging: Display the raw model response
                st.subheader("Model Response (Debug)")
                st.text_area("Raw Model Response", str(model_response), height=300)

                # Check if response is a dictionary with choices
                if isinstance(model_response, dict) and 'choices' in model_response:
                    if len(model_response['choices']) > 0:
                        extracted_text = model_response['choices'][0]['text'].strip()
                        extracted_data = parse_json(extracted_text)
                    else:
                        st.error("No choices available in the model response.")
                        extracted_data = None
                else:
                    st.error("Unexpected response format from the model.")
                    extracted_data = None

                if extracted_data:
                    st.subheader("Extracted Invoice Data")
                    st.json(extracted_data)

    # Optionally, display the PDF
    st.subheader("Uploaded PDF")
    st.info("Note: For privacy reasons, the PDF is not displayed here.")
