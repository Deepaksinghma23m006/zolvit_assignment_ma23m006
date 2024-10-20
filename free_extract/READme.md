# Scalable Invoice Data Extraction using Streamlit and OCR

This project provides a **Streamlit** web application to extract data from **invoice PDFs** (regular, scanned, mixed text/image) and output the extracted information along with accuracy scores in an Excel file. The app uses **PyMuPDF** to extract text from regular PDFs and **Tesseract OCR** for scanned PDFs.

The project is **Dockerized** for easy deployment and scaling, and is packaged with all necessary dependencies.

## Features

- Extract data from both regular and scanned PDF invoices.
- Use **OCR** (Tesseract) for scanned documents.
- Provide detailed extracted information with accuracy scores.
- Export extracted data to Excel for download.
- Dockerized for easy deployment and scalability.

## Tech Stack

- **Streamlit**: Frontend and web server.
- **PyMuPDF**: Extract text from PDF.
- **Tesseract OCR**: Optical Character Recognition for scanned PDFs.
- **Pandas**: Data manipulation and export to Excel.
- **Docker**: Containerization of the entire app.

## Requirements

- **Docker** and **Docker Compose** (optional)
- **Tesseract-OCR** and **Poppler** libraries (will be installed in the Docker container).

## Project Structure

. ├── app.py # Main Streamlit app ├── utils.py # Helper functions for extracting and processing invoice data ├── requirements.txt # Python dependencies ├── Dockerfile # Docker setup ├── docker-compose.yml # Docker Compose setup (optional) ├── README.md # Project documentation └── .dockerignore # Files to ignore during Docker build

bash
Copy code

## Setup Instructions

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/invoice-extraction.git
cd invoice-extraction
Step 2: Build the Docker Image
Use the following command to build the Docker image:

bash
Copy code
docker build -t invoice-extractor .
Step 3: Run the Application
You can run the app either using Docker or Docker Compose.

Option 1: Run with Docker
Run the Docker container and expose it on port 8501:

bash
Copy code
docker run -p 8501:8501 invoice-extractor
Option 2: Run with Docker Compose (Optional)
If you prefer using Docker Compose, make sure you have docker-compose.yml in the project root. Then, run the following command:

bash
Copy code
docker-compose up
Step 4: Access the Application
Once the container is running, open your browser and go to:

arduino
Copy code
http://localhost:8501
You will see the Streamlit app where you can upload PDF invoices for extraction.

Step 5: Upload PDF and Extract Data
Upload one or more invoice PDFs through the app.
The app will extract data from the PDFs, displaying accuracy scores and performance metrics.
Download the extracted data in Excel format.
Step 6: Stop the Application
To stop the Docker container:

bash
Copy code
docker stop <container-id>
For Docker Compose:

bash
Copy code
docker-compose down
Troubleshooting
Issue: Tesseract not extracting text properly.
Make sure the PDF is of high enough quality for OCR.
Issue: Slow performance for large files.
OCR can be resource-intensive, especially for large or complex PDFs.
Future Improvements
Add support for multi-page invoices.
Enhance text extraction accuracy using advanced NLP techniques.
Scale horizontally using Kubernetes for large-scale processing.
License
This project is licensed under the MIT License.

Authors
Your Name - Initial Work
markdown
Copy code

### Instructions Recap:

1. **Clone the repository** using `git clone`.
2. **Build** the Docker image with `docker build`.
3. **Run** the application using either `docker run` or `docker-compose up`.
4. **Access** the app on `http://localhost:8501`.
5. **Upload PDF invoices** and extract data.
6. **Download** extracted data in Excel format.
7. **Stop** the container when done.

This should guide users through setting up and running your project.