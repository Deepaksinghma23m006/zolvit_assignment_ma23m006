import os
import json
import re
import logging
import requests
import time
import pandas as pd
from pypdf import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
import streamlit as st
import yaml

# Load prompt template from YAML file
def load_prompts():
    with open('prompts.yaml') as file:
        return yaml.safe_load(file)

prompts = load_prompts()

def get_pdf_text(pdf_doc):
    """
    Extracts text from a PDF file, handling regular and scanned PDFs.
    
    Parameters:
        pdf_doc (UploadedFile): The uploaded PDF file.
    
    Returns:
        str: The extracted text from the PDF.
    """
    text = ""
    try:
        pdf_reader = PdfReader(pdf_doc)
        num_pages = len(pdf_reader.pages)
        for page_number, page in enumerate(pdf_reader.pages, start=1):
            extracted_text = page.extract_text()
            if extracted_text and len(extracted_text.strip()) > 50:
                text += extracted_text + "\n"
                logging.info(f"Text extracted from page {page_number} using PdfReader.")
            else:
                logging.info(f"Insufficient text on page {page_number}. Applying OCR.")
                pdf_doc.seek(0)
                pdf_bytes = pdf_doc.read()
                images = convert_from_bytes(pdf_bytes, first_page=page_number, last_page=page_number)
                for image in images:
                    ocr_text = pytesseract.image_to_string(image, config='--psm 6')
                    if ocr_text and len(ocr_text.strip()) > 10:
                        text += ocr_text + "\n"
                        logging.info(f"OCR text extracted from page {page_number}.")
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        st.error(f"Error extracting text from PDF: {e}")
    return text

def call_openai_api(pages_data):
    """
    Calls the OpenAI GPT-4 API to extract invoice data in JSON format.
    
    Parameters:
        pages_data (str): The extracted text from the PDF.
    
    Returns:
        str or None: The raw extracted data from the API if successful; otherwise, None.
    """
    GPT4V_KEY = os.getenv("GPT4V_KEY")
    GPT4V_ENDPOINT = os.getenv("GPT4V_ENDPOINT")
    
    headers = {
        "Content-Type": "application/json",
        "api-key": GPT4V_KEY,
    }

    prompt = prompts['invoice_extraction_prompt'].format(pages=pages_data)

    data = {
        "messages": [
            {"role": "system", "content": "You are a helpful and accurate assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.3
    }

    try:
        response = requests.post(GPT4V_ENDPOINT, headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            llm_extracted_data = response_json.get("choices", [])[0].get("message", {}).get("content", "")
            logging.info(f"Raw API response for data extraction: {llm_extracted_data}")
            return llm_extracted_data
        elif response.status_code == 429:
            logging.warning("Rate limit exceeded. Retrying after 10 seconds...")
            st.warning("Rate limit exceeded. Retrying after 10 seconds...")
            time.sleep(10)
            return call_openai_api(pages_data)
        else:
            logging.error(f"API call failed: {response.status_code} - {response.text}")
            st.error(f"Error during API call: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"Exception during API call: {e}")
        st.error(f"An error occurred during API call: {e}")
        return None

def validate_data(field, value):
    """
    Validates the extracted data fields using regex patterns and assigns confidence levels.
    
    Parameters:
        field (str): The name of the field.
        value (str): The extracted value of the field.
    
    Returns:
        tuple: (is_valid (bool), confidence (str))
    """
    patterns = {
        'Invoice No.': r'^[A-Za-z0-9\-]+$',
        'Quantity': r'^\d+(\.\d+)?$',
        'Date': r'^\d{2}/\d{2}/\d{4}$',
        'Amount': r'^\d+(\.\d+)?$',
        'Total': r'^\d+(\.\d+)?$',
        'Email': r'^[\w\.-]+@[\w\.-]+\.\w+$',
        'GSTIN Supplier': r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$',
        'GSTIN Recipient': r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$',
    }

    if field in patterns:
        if re.match(patterns[field], str(value).strip()):
            return True, "High Confidence"
        else:
            return False, "Low Confidence"
    else:
        if str(value).strip():
            return True, "Medium Confidence"
        else:
            return False, "Low Confidence"

def extract_json(raw_text):
    """
    Extracts the first JSON object found in the raw text.
    
    Parameters:
        raw_text (str): The raw text containing JSON.
    
    Returns:
        str or None: The extracted JSON string if found; otherwise, None.
    """
    pattern = r'\{.*\}'
    match = re.search(pattern, raw_text, re.DOTALL)
    if match:
        return match.group(0)
    else:
        return None

def create_docs(user_pdf_list):
    """
    Processes multiple PDF files to extract invoice data and compile it into a DataFrame.
    
    Parameters:
        user_pdf_list (list): List of uploaded PDF files.
    
    Returns:
        pd.DataFrame: DataFrame containing all extracted invoice data.
    """
    df = pd.DataFrame(columns=[
        'Invoice No.', 'Quantity', 'Date', 'Amount', 'Total',
        'Email', 'Address', 'Taxable Value', 'SGST Amount',
        'CGST Amount', 'IGST Amount', 'SGST Rate', 'CGST Rate',
        'IGST Rate', 'Tax Amount', 'Tax Rate', 'Final Amount',
        'Invoice Date', 'Place of Supply', 'Place of Origin',
        'GSTIN Supplier', 'GSTIN Recipient',
        'Confidence', 'Trust'
    ])
    
    metrics = {
        'total_files': 0,
        'successful_extractions': 0,
        'field_accuracy': {field: {'correct': 0, 'total': 0} for field in df.columns if field not in ['Confidence', 'Trust']}
    }
    
    for pdf_file in user_pdf_list:
        pdf_file.seek(0)
        pages_data = get_pdf_text(pdf_file)

        # Call the API to extract structured data
        raw_response = call_openai_api(pages_data)

        if raw_response:
            json_data = extract_json(raw_response)

            if json_data:
                try:
                    extracted_data = json.loads(json_data)
                    metrics['total_files'] += 1

                    row_data = {}
                    for field in df.columns[:-2]:  # Exclude Confidence and Trust
                        value = extracted_data.get(field, "")
                        is_valid, confidence = validate_data(field, value)
                        row_data[field] = value
                        df.at[len(df)] = row_data
                        metrics['field_accuracy'][field]['total'] += 1
                        if is_valid:
                            metrics['field_accuracy'][field]['correct'] += 1
                    
                    # Update metrics for confidence and trust
                    df.at[len(df) - 1, 'Confidence'] = "High Confidence"  # Example, set appropriately
                    df.at[len(df) - 1, 'Trust'] = "Trusted"  # Example, set appropriately
                    
                    metrics['successful_extractions'] += 1

                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error: {e}")

    # Log extraction metrics
    logging.info(f"Total files processed: {metrics['total_files']}")
    logging.info(f"Successful extractions: {metrics['successful_extractions']}")
    for field, accuracy in metrics['field_accuracy'].items():
        logging.info(f"Field '{field}' accuracy: {accuracy['correct']}/{accuracy['total']}")

    return df
