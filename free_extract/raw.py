import fitz

#Function to extract raw text from PDF
def extract_raw_text(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Extract text and print it out for debugging
pdf_path = "/Volumes/my_space/VSCODE/LLM starting/invoice_extract_2/extract_free/INV-121_Jitesh Soni.pdf"  # Update this to your file path
with open(pdf_path, "rb") as f:
    raw_text = extract_raw_text(f)

# Print raw text for analysis
print(raw_text)
