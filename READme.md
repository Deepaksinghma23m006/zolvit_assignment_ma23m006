# 📄 Invoice Extraction Bot

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

## Video Demo


For a visual demonstration of the application, watch this video: Invoice Extraction Bot Demo

## Contributing
Contributions are welcome! Please create an issue or submit a pull request if you have suggestions or improvements.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.



### Notes

- **Repository URL**: https://github.com/Deepaksinghma23m006/zolvit_assignment_ma23m006
- **Screenshots**:
- **Video Link**: https://youtu.be/537Y0lKko04








