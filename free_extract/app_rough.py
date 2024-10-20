import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from io import BytesIO
import re

# Function to extract text from PDF using PyMuPDF
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Function to apply OCR using Tesseract for scanned PDFs
def extract_text_from_image(pdf_file):
    images = convert_from_path(pdf_file, dpi=300)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

# Function to process extracted text into desired format
import re
import re

def process_invoice_text(text):
    # Function to safely convert strings to floats by removing commas and ₹ symbols
    def safe_float(value):
        try:
            return float(value.replace(',', '').replace('₹', '').strip())  # Remove commas and ₹ before converting to float
        except ValueError:
            return 0.0  # Fallback to 0.0 if conversion fails

    # Initialize variables
    taxable_value, sgst_amount, cgst_amount, igst_amount = 0, 0, 0, 0
    cgst_rates, sgst_rates, igst_rates = [], [], []
    invoice_number, invoice_date, due_date, place_of_supply, place_of_origin = "", "", "", "", ""
    mobile, email, customer_details, gstin, total_discount = "", "", "", "", 0

    # Extracting invoice number
    invoice_number_match = re.search(r"Invoice #:\s*([A-Za-z0-9\-]+)", text)
    if invoice_number_match:
        invoice_number = invoice_number_match.group(1).strip()

    # Extracting invoice date
    invoice_date_match = re.search(r"Invoice Date:\s*([0-9A-Za-z\s]+)\s*Due Date:", text)
    if invoice_date_match:
        invoice_date = invoice_date_match.group(1).strip()

    # Extracting due date
    due_date_match = re.search(r"Due Date:\s*([0-9A-Za-z\s]+)\s*Customer Details:", text)
    if due_date_match:
        due_date = due_date_match.group(1).strip()


    # Extracting place of origin (improved regular expression to handle line breaks and spaces)
    place_of_origin_match = re.search(r"(?:Shahdol,)\s*([A-Za-z\s]+),\s*[0-9]{6}", text, re.DOTALL)
    if place_of_origin_match:
        place_of_origin = place_of_origin_match.group(1).strip()

    # Extracting place of supply
    place_of_supply_match = re.search(r"Place of Supply:\s*([0-9A-Za-z\s\-]+)", text)
    if place_of_supply_match:
        place_of_supply = place_of_supply_match.group(1).strip()

    # Extracting mobile number
    mobile_match = re.search(r"Mobile\s*\+?\d*\s*([0-9]+)", text)
    if mobile_match:
        mobile = mobile_match.group(1).strip()

    # Extracting email
    email_match = re.search(r"Email\s*([A-Za-z0-9@.\-_]+)", text)
    if email_match:
        email = email_match.group(1).strip()

    # Extracting and cleaning customer details
    customer_details_match = re.search(r"Customer Details:\s*([A-Za-z\s]+)", text)
    if customer_details_match:
        customer_details = customer_details_match.group(1).strip()

    # Further cleaning the customer details to remove 'Place of Supply' or 'Ph' or any trailing characters
    customer_details_clean = re.sub(r"\b(Place of Supply|Ph)\b.*", '', customer_details).strip()

    # Extracting GSTIN
    gstin_match = re.search(r"GSTIN\s*([A-Za-z0-9]+)", text)
    if gstin_match:
        gstin = gstin_match.group(1).strip()

    # Extracting taxable value
    taxable_value_match = re.search(r"Taxable Amount\s*₹([0-9,]+\.\d{2})", text)
    if taxable_value_match:
        taxable_value = safe_float(taxable_value_match.group(1))

    # Extracting CGST amounts and rates
    cgst_matches = re.findall(r"CGST\s*(\d+\.?\d*)%?\s*₹([0-9,]+\.\d{2})", text)
    for match in cgst_matches:
        cgst_rates.append(float(match[0]))  # Append CGST rate
        cgst_amount += safe_float(match[1])  # Sum CGST amounts

    # Extracting SGST amounts and rates
    sgst_matches = re.findall(r"SGST\s*(\d+\.?\d*)%?\s*₹([0-9,]+\.\d{2})", text)
    for match in sgst_matches:
        sgst_rates.append(float(match[0]))  # Append SGST rate
        sgst_amount += safe_float(match[1])  # Sum SGST amounts

    # Extracting IGST amounts and rates
    igst_matches = re.findall(r"IGST\s*(\d+\.?\d*)%?\s*₹([0-9,]+\.\d{2})", text)
    if igst_matches:
        for match in igst_matches:
            igst_rates.append(float(match[0]))  # Append IGST rate
            igst_amount += safe_float(match[1])  # Sum IGST amounts
    else:
        igst_rates = [0]  # Default to [0] if no IGST found
        igst_amount = 0  # Set IGST amount to 0 if not found

    # Extracting final amount (total)
    final_amount_match = re.search(r"Total\s*₹([0-9,]+\.\d{2})", text)
    if final_amount_match:
        final_amount = safe_float(final_amount_match.group(1))

    # Extracting discount (if available)
    discount_match = re.search(r"Total Discount\s*-?\s*₹([0-9,]+\.\d{2})", text)
    if discount_match:
        total_discount = safe_float(discount_match.group(1))

    # Calculating total tax amount
    tax_amount = sgst_amount + cgst_amount + igst_amount

    # Return the parsed data as a dictionary
    return {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "mobile": mobile,
        "email": email,
        "customer_details": customer_details_clean,
        "place_of_origin": place_of_origin,
        "gstin": gstin,
        "place_of_supply": place_of_supply,
        "taxable_value": taxable_value,
        "sgst_amount": sgst_amount,
        "cgst_amount": cgst_amount,
        "igst_amount": igst_amount,
        "sgst_rates": sgst_rates if sgst_rates else [0],  # Default to [0] if no SGST found
        "cgst_rates": cgst_rates if cgst_rates else [0],  # Default to [0] if no CGST found
        "igst_rates": igst_rates if igst_rates else [0],  # Default to [0] if no IGST found
        "tax_amount": tax_amount,
        "total_discount": total_discount,
        "final_amount": final_amount,
    }

# Example usage:
invoice_text = """
TA X  I N V O I C E
ORIGINAL FOR RECIPIENT
UNCUE DERMACARE PRIVATE LIMITED
GSTIN 23AADCU2395N1ZY    
C/o KARUNA GUPTA KURELE, 1st Floor
S.P Bungalow Ke Pichhe, Shoagpur Shahdol, Shahdol
Shahdol, MADHYA PRADESH, 484001
Mobile +91 8585960963   Email ruhi@dermaq.in
Invoice #: INV-124
Invoice Date: 10 Feb 2024
Due Date: 10 Feb 2024
Customer Details:
Ankita Sattva
Place of Supply: 
23-MADHYA PRADESH
#
Item
Rate / Item
Qty
Taxable Value
Tax Amount
Amount
1
Arachitol Nano (60k) 4*5ml  
340.43
3 BTL
1,021.29
122.55 (12%)
1,143.84
2
Neurobion Forte - 30 tablets   
34.75
3 STRP
104.24
18.76 (18%)
123.00
Taxable Amount
₹1,125.52
CGST 6.0%
₹61.28
SGST 6.0%
₹61.28
CGST 9.0%
₹9.38
SGST 9.0%
₹9.38
IGST 12.0%
₹34.72
IGST 18.0%
₹104.68Discount
- ₹ 152.02
Round Off
0.18
Total
₹1,115.00
Total Discount
₹152.02
Total Items / Qty : 2 / 6.000 
Total amount (in words): INR One Thousand, One Hundred And Fifteen Rupees Only.
Amount Paid
Pay using UPI: 
Bank Details:
Bank:
"""

parsed_data = process_invoice_text(invoice_text)
print(parsed_data)


# Streamlit app
st.title("Invoice Data Extraction")
st.write("Upload multiple invoices (PDFs) and get the extracted data displayed here and downloadable in Excel format.")

uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    extracted_data = []

    for pdf_file in uploaded_files:
        try:
            extracted_text = extract_text_from_pdf(pdf_file)
        except:
            extracted_text = extract_text_from_image(pdf_file)

        invoice_data = process_invoice_text(extracted_text)
        extracted_data.append(invoice_data)

    # Convert extracted data to a DataFrame
    df = pd.DataFrame(extracted_data)

    # Display the DataFrame in Streamlit
    st.write("Extracted Data:")
    st.dataframe(df)

    # Export to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    # Provide a download button for the Excel file
    st.download_button(
        label="Download Excel file",
        data=output.getvalue(),
        file_name="extracted_invoices.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
