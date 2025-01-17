# 📄 Invoice Extraction Bot


### MODEL 1-  Pytesseract/OCR

### MODEL 2 -  Llama 3

### MODEL 3 -  OpenAI 



# Model 1 (check above folder)

```
streamlit run app.py
```

# Model 2 (check above folder )

It will run on kaggle with free subscription of llama 3 



# Model 3


## Description

The **Invoice Extraction Bot** is a Streamlit application designed to extract and validate invoice data from PDF files. It utilizes OpenAI's GPT-4 model to intelligently parse and organize critical information from invoices, such as invoice numbers, dates, amounts, and various tax-related fields.

## Features

- Upload invoice PDFs (supports regular, scanned, and mixed PDFs).
- Automatically extracts data fields including:
  - Invoice No.
  - Quantity
  - Date
  - Amount
  - Total
  - Email
  - GSTINs (Supplier and Recipient)
- Validation of extracted data with confidence levels.
- Provides detailed metrics on extraction performance.
- Download extracted data in Excel and CSV formats.

## Prerequisites

Before running the application, ensure you have the following installed:

- Docker (for containerization)
- Python 3.9 or later (if running locally)
- An OpenAI GPT-4 API key

## Installation and Setup

1. **Clone the Repository:**

   ```bash
   git clone <repository-url>
   cd <repository-directory>


2. **Create a .env File:**
Create a .env file in the root directory and add your OpenAI API key and endpoint:

GPT4V_KEY=your_openai_api_key
GPT4V_ENDPOINT=your_openai_api_endpoint

3. **Build the Docker Image:**
Ensure you are in the root directory where the Dockerfile is located, then build the Docker image:

  ```bash
  docker build -t invoice-extraction-app .
  ```

  
4. **Run the Docker Container:**
Run the container with the following command:

 ```bash
 docker run -p 8501:8501 invoice-extraction-app
 ```

5. **Access the Application:**

Open your web browser and navigate to http://localhost:8501 to access the Invoice Extraction Bot.


## screenshots

 Streamlit web interface PDF: https://drive.google.com/file/d/151xP1QKk7OcybJwiRxpxcUv0fo5WSlIQ/view?usp=drive_link

 
 Output file (Model 1,2 and 3 ) : [https://docs.google.com/spreadsheets/d/1SQZWM307DQXIXhgm7CGiuMsz9YkMhy62/edit?usp=drive_link&ouid=101059314479765340537&rtpof=true&sd=true](https://drive.google.com/drive/folders/1CohZue3YVLkZlrlihnKL0j8QA0_O1Jqv?usp=drive_link)
 
## Video Demo

[![Watch the video](https://img.youtube.com/vi/537Y0lKko04/maxresdefault.jpg)](https://www.youtube.com/watch?v=537Y0lKko04)



For a visual demonstration of the application, watch this video: Invoice Extraction Bot Demo

## Contributing
Contributions are welcome! Please create an issue or submit a pull request if you have suggestions or improvements.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.



### Notes

- **Repository URL**: https://github.com/Deepaksinghma23m006/zolvit_assignment_ma23m006
- **Video Link**: https://youtu.be/537Y0lKko04








