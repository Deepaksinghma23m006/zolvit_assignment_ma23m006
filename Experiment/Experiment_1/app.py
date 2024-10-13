
import os
import json
import pandas as pd
import re
import io

from dotenv import load_dotenv
import streamlit as st

# Gemini-specific imports
import google.generativeai as genai
from pdf2image import convert_from_bytes
from PIL import Image

# Load environment variables from .env
load_dotenv()

# Configure API key for Gemini
GENIEMI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GENIEMI_API_KEY:
    st.error("Google API key not found in the environment variables.")
    st.stop()

genai.configure(api_key=GENIEMI_API_KEY)

# Function to convert PDF to images
def convert_pdf_to_images(uploaded_pdf):
    try:
        images = convert_from_bytes(uploaded_pdf.read())
        return images
    except Exception as e:
        st.error(f"Error converting PDF to images: {e}")
        return []

# Function to call the Gemini API
def call_gemini_api(image, prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([
            {
                "mime_type": "image/jpeg",
                "data": image  # Correct key: 'data' instead of 'content'
            },
            {
                "mime_type": "text/plain",
                "text": prompt  # Correct key: 'text' instead of 'content'
            }
        ])
        return response.text
    except Exception as e:
        st.error(f"Error during Gemini API call: {e}")
        return None

# Function to extract data from a single image using Gemini
def extract_data_from_image(image, prompt):
    # Convert PIL Image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    # Get Gemini response
    response = call_gemini_api(img_bytes, prompt)
    return response

# Function to process multiple PDF files and extract invoice data into a DataFrame
def create_docs(user_pdf_list):
    df = pd.DataFrame({
        'Invoice No.': pd.Series(dtype='str'),
        'Quantity': pd.Series(dtype='str'),
        'Date': pd.Series(dtype='str'),
        'Amount': pd.Series(dtype='float'),
        'Total': pd.Series(dtype='str'),
        'Email': pd.Series(dtype='str'),
        'Address': pd.Series(dtype='str'),
        'Taxable Value': pd.Series(dtype='float'),
        'SGST Amount': pd.Series(dtype='float'),
        'CGST Amount': pd.Series(dtype='float'),
        'IGST Amount': pd.Series(dtype='float'),
        'SGST Rate': pd.Series(dtype='float'),
        'CGST Rate': pd.Series(dtype='float'),
        'IGST Rate': pd.Series(dtype='float'),
        'Tax Amount': pd.Series(dtype='float'),
        'Tax Rate': pd.Series(dtype='float'),
        'Final Amount': pd.Series(dtype='float'),
        'Invoice Date': pd.Series(dtype='str'),
        'Place of Supply': pd.Series(dtype='str'),
        'Place of Origin': pd.Series(dtype='str'),
        'GSTIN Supplier': pd.Series(dtype='str'),
        'GSTIN Recipient': pd.Series(dtype='str'),
    })
    
    # Define the prompt for Gemini
    prompt_template = '''Extract the following fields from the invoice image:
- Invoice No.
- Quantity
- Date
- Amount
- Total
- Email
- Address
- Taxable Value
- SGST Amount
- CGST Amount
- IGST Amount
- SGST Rate
- CGST Rate
- IGST Rate
- Tax Amount
- Tax Rate
- Final Amount
- Invoice Date
- Place of Supply
- Place of Origin
- GSTIN Supplier
- GSTIN Recipient

Provide the output in JSON format.
'''
    
    for file in user_pdf_list:
        st.write(f"Processing {file.name}...")
        try:
            images = convert_pdf_to_images(file)
            if not images:
                st.warning(f"No images extracted from {file.name}. Skipping.")
                continue
            
            for page_number, image in enumerate(images, start=1):
                st.write(f"Processing page {page_number} of {file.name}...")
                
                llm_response = extract_data_from_image(image, prompt_template)
                if not llm_response:
                    st.error(f"Failed to extract data from page {page_number} of {file.name}.")
                    continue

                # Attempt to parse the JSON response
                try:
                    data_dict = json.loads(llm_response)
                    st.write(f"Extracted Data from page {page_number} of {file.name}: {data_dict}")
                except json.JSONDecodeError as e:
                    st.error(f"Error parsing JSON from page {page_number} of {file.name}: {e}")
                    continue

                # Add the extracted data to the DataFrame
                df = pd.concat([df, pd.DataFrame([data_dict])], ignore_index=True)
                st.write("*******DONE******")
        except Exception as e:
            st.error(f"An error occurred while processing {file.name}: {e}")

    # Save the DataFrame to an Excel file
    output_excel_file = "extracted_invoice_data.xlsx"
    try:
        df.to_excel(output_excel_file, index=False)
        st.download_button(
            "Download Extracted Data as Excel",
            data=open(output_excel_file, "rb").read(),
            file_name=output_excel_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Error saving Excel file: {e}")
    
    return df

# Streamlit app function
def main():
    st.set_page_config(page_title="Invoice Extraction Bot using Gemini")
    st.title("Invoice Extraction Bot using Gemini 🤖")
    st.subheader("I can help you in extracting invoice data from your PDF files.")
    
    # Upload the invoices (PDF files)
    pdf_files = st.file_uploader(
        "Upload invoices here, only PDF files allowed",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    if st.button("Extract Data"):
        if pdf_files:
            with st.spinner('Processing...'):
                df = create_docs(pdf_files)
                
                if not df.empty:
                    st.write("### Extracted Data:")
                    st.dataframe(df)
                    
                    # Allow downloading the extracted data as a CSV file
                    try:
                        data_as_csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download data as CSV", 
                            data_as_csv, 
                            "invoice_data.csv", 
                            "text/csv", 
                            key="download-invoice-csv"
                        )
                        st.success("Extraction complete! ✅")
                    except Exception as e:
                        st.error(f"Error generating CSV file: {e}")
                else:
                    st.warning("No data extracted from the uploaded PDFs.")
        else:
            st.error("Please upload at least one PDF file.")

# Run the app
if __name__ == "__main__":
    main()
