import streamlit as st
import pandas as pd
import fitz 
from pdf2image import convert_from_path
import pytesseract
from io import BytesIO
import re
import time
from utils import extract_text_from_pdf,extract_text_from_image, safe_float, process_invoice_text



# Streamlit app 
st.title("Scalable Invoice Data Extraction")
st.write("Upload invoices (PDFs) and receive detailed extraction with accuracy scores and performance metrics.")

uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    extracted_data = []
    start_time = time.time()

    for pdf_file in uploaded_files:
        extraction_status = {}
        try:
            extracted_text, success, message = extract_text_from_pdf(pdf_file)
            extraction_status['method'] = 'PyMuPDF'
            extraction_status['success'] = success
            extraction_status['message'] = message

            if not success:
                extracted_text, success, message = extract_text_from_image(pdf_file)
                extraction_status['method'] = 'OCR'
                extraction_status['success'] = success
                extraction_status['message'] = message

            if success:
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

    #Calculating total processing time
    processing_time = time.time() - start_time
    st.write(f"Processed {len(uploaded_files)} files in {processing_time:.2f} seconds.")

    #Displaying extracted data and accuracy scores
    if extracted_data:
        df = pd.DataFrame(extracted_data)
        st.write("Extracted Data with Accuracy Scores:")
        st.dataframe(df)

        #Export to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)

        st.download_button(
            label="Download Excel file",
            data=output.getvalue(),
            file_name="extracted_invoices_with_accuracy.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
