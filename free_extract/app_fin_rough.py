import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from io import BytesIO
import re
from typing import Dict, Tuple, List, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import json
from difflib import SequenceMatcher
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Stores extraction results with accuracy metrics"""
    value: Any
    confidence_score: float
    extraction_method: str
    validation_status: str
    cross_validation_score: float = 0.0
    
    @property
    def is_trusted(self) -> bool:
        return (self.confidence_score > 0.9 and 
                self.cross_validation_score > 0.8 and 
                self.validation_status == "VALID")

class AccuracyVerifier:
    """Handles accuracy verification and trust determination"""
    
    @staticmethod
    def verify_number_format(value: str, expected_format: str) -> float:
        """Verify if a number matches expected format"""
        try:
            if re.match(expected_format, value):
                return 1.0
            return 0.0
        except:
            return 0.0
    
    @staticmethod
    def verify_date_format(date_str: str) -> float:
        """Verify if a date string matches common formats"""
        date_patterns = [
            r'\d{2}[-/]\d{2}[-/]\d{4}',
            r'\d{1,2}\s[A-Za-z]{3}\s\d{4}'
        ]
        return any(re.match(pattern, date_str) for pattern in date_patterns)
    
    @staticmethod
    def cross_validate_amount(amount: float, line_items: List[Dict]) -> float:
        """Cross-validate total amount against line items"""
        try:
            calculated_total = sum(item.get('amount', 0) for item in line_items)
            difference = abs(amount - calculated_total)
            return 1.0 - (difference / amount) if amount else 0.0
        except:
            return 0.0

class EnhancedInvoiceExtractor:
    """Enhanced text extraction with multiple methods and validation"""
    
    def __init__(self):
        self.accuracy_verifier = AccuracyVerifier()
        self.extraction_metrics = defaultdict(list)
    
    def extract_with_confidence(self, pdf_file) -> Tuple[str, Dict[str, float]]:
        """Extract text using multiple methods and combine results"""
        methods = {
            'pymupdf': self._extract_pymupdf,
            'tesseract': self._extract_tesseract,
        }
        
        results = {}
        confidences = {}
        
        for method_name, method_func in methods.items():
            try:
                start_time = time.time()
                text = method_func(pdf_file)
                duration = time.time() - start_time
                
                confidence = self._calculate_confidence(text, method_name, duration)
                
                results[method_name] = text
                confidences[method_name] = confidence
                
                self.extraction_metrics[method_name].append({
                    'duration': duration,
                    'confidence': confidence,
                    'success': True
                })
            except Exception as e:
                logger.error(f"Extraction failed for method {method_name}: {str(e)}")
                self.extraction_metrics[method_name].append({
                    'duration': 0,
                    'confidence': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Use the result with highest confidence
        best_method = max(confidences.items(), key=lambda x: x[1])[0]
        return results[best_method], confidences

    def _extract_pymupdf(self, pdf_file) -> str:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        return " ".join(page.get_text() for page in doc)
    
    def _extract_tesseract(self, pdf_file) -> str:
        images = convert_from_path(pdf_file, dpi=300)
        return " ".join(pytesseract.image_to_string(img) for img in images)
    
    def _calculate_confidence(self, text: str, method: str, duration: float) -> float:
        """Calculate confidence score based on various factors"""
        factors = {
            'text_length': min(len(text) / 1000, 1.0),  # Normalize text length
            'processing_speed': 1.0 / (1.0 + duration),  # Faster processing suggests better quality
            'expected_patterns': self._check_expected_patterns(text)
        }
        return sum(factors.values()) / len(factors)
    
    def _check_expected_patterns(self, text: str) -> float:
        """Check if text contains expected invoice patterns"""
        expected_patterns = [
            r'invoice',
            r'total',
            r'amount',
            r'date',
            r'customer'
        ]
        matches = sum(1 for pattern in expected_patterns 
                     if re.search(pattern, text.lower()))
        return matches / len(expected_patterns)
import re
import tempfile
import numpy as np
from typing import Dict, Any
from pdf2image import convert_from_path
import pytesseract


class EnhancedInvoiceParser:

    def parse(self, pdf_file) -> Dict[str, Any]:
        """Main parsing function that handles extraction."""
        try:
            # Assuming PDF to Text conversion is being done using Tesseract
            text = self._extract_tesseract(pdf_file)

            # Extracting fields from the converted text
            basic_fields = self._extract_basic_fields(text)
            financial_details = self._extract_financial_details(text)
            line_items = self._extract_line_items(text)

            # Returning all extracted information in a single dictionary
            return {
                'basic_fields': basic_fields,
                'financial_details': financial_details,
                'line_items': line_items
            }

        except Exception as e:
            print(f"ERROR: {str(e)}")
            return {}

    def _extract_tesseract(self, pdf_file) -> str:
        """Extract text from a PDF file using Tesseract OCR."""
        try:
            # Create a temporary file for the uploaded PDF file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(pdf_file.read())
                temp_pdf_path = temp_pdf.name

            # Convert PDF to image using pdf2image and then run OCR using pytesseract
            images = convert_from_path(temp_pdf_path, dpi=300)
            text = " ".join(pytesseract.image_to_string(img) for img in images)
            return text
        except Exception as e:
            print(f"Extraction failed for method tesseract: {e}")
            return ""

    def _extract_basic_fields(self, text: str) -> Dict[str, Any]:
        """Extract basic fields such as invoice number, date, and other metadata."""
        try:
            invoice_number_match = re.search(r'Invoice Number:\s*(\w+)', text)
            invoice_number = invoice_number_match.group(1) if invoice_number_match else 'Unknown'

            invoice_date_match = re.search(r'Invoice Date:\s*([\d/-]+)', text)
            invoice_date = invoice_date_match.group(1) if invoice_date_match else 'Unknown'

            return {
                'invoice_number': invoice_number,
                'invoice_date': invoice_date
            }
        except Exception as e:
            print(f"Parsing failed: {e}")
            return {}

    def _extract_financial_details(self, text: str) -> Dict[str, Any]:
        """Extract financial details such as amounts and taxes."""
        try:
            taxable_value_match = re.search(r'Taxable Value:\s*([\d,.]+)', text)
            taxable_value = taxable_value_match.group(1) if taxable_value_match else '0.0'

            tax_amount_match = re.search(r'Tax Amount:\s*([\d,.]+)', text)
            tax_amount = tax_amount_match.group(1) if tax_amount_match else '0.0'

            return {
                'taxable_value': taxable_value,
                'tax_amount': tax_amount
            }
        except Exception as e:
            print(f"Parsing failed: {e}")
            return {}

    def _extract_line_items(self, text: str) -> Dict[str, Any]:
        """Extract line items from the invoice."""
        try:
            # Example regex for extracting line items (customize for your data)
            line_items = re.findall(r'Item:\s*(\w+)\s*Quantity:\s*(\d+)\s*Price:\s*([\d,.]+)', text)

            return {'line_items': line_items} if line_items else {'line_items': []}
        except Exception as e:
            print(f"Parsing failed: {e}")
            return {'line_items': []}

    def calculate_mean_confidence(self, metrics: Dict[str, Any]) -> float:
        """Calculate the mean confidence score for extracted fields."""
        try:
            avg_confidence = np.mean([
                np.mean([m['confidence'] for m in field_metrics])
                for field_metrics in metrics.values()
                if field_metrics  # Ensure there are metrics
            ]) if metrics else 0.0

            return avg_confidence
        except Exception as e:
            print(f"Confidence calculation failed: {e}")
            return 0.0

    def calculate_trusted_rate(self, metrics: Dict[str, Any]) -> float:
        """Calculate the trusted rate of extracted data."""
        try:
            trusted_rate = np.mean([
                np.mean([m['trusted'] for m in field_metrics]) 
                for field_metrics in metrics.values()
                if field_metrics  # Ensure there are metrics
            ]) if metrics else 0.0

            return trusted_rate
        except Exception as e:
            print(f"Trusted rate calculation failed: {e}")
            return 0.0

class StreamlitDashboard:
    """Enhanced Streamlit interface with detailed metrics and reporting"""
    
    def __init__(self):
        self.extractor = EnhancedInvoiceExtractor()
        self.parser = EnhancedInvoiceParser()
    
    def run(self):
        st.title("Advanced Invoice Data Extraction")
        st.write("Upload invoices for processing with accuracy assessment")
        
        uploaded_files = st.file_uploader(
            "Upload PDF files", 
            type="pdf", 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            self.process_files(uploaded_files)
    
    def process_files(self, files):
        results = []
        metrics = defaultdict(list)
        
        with st.spinner("Processing invoices..."):
            for pdf_file in files:
                try:
                    # Extract and parse
                    text, confidences = self.extractor.extract_with_confidence(pdf_file)
                    parsed_data = self.parser.parse_with_verification(text)
                    
                    # Collect results and metrics
                    results.append(parsed_data)
                    for field, result in parsed_data.items():
                        metrics[field].append({
                            'confidence': result.confidence_score,
                            'trusted': result.is_trusted
                        })
                
                except Exception as e:
                    st.error(f"Error processing {pdf_file.name}: {str(e)}")
        
        self.display_results(results, metrics)
    
    def display_results(self, results, metrics):
        """Display results with detailed metrics"""
        
        # Display overall metrics
        st.subheader("Processing Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            trusted_rate = np.mean([
                np.mean([m['trusted'] for m in field_metrics])
                for field_metrics in metrics.values()
            ])
            st.metric("Trust Rate", f"{trusted_rate:.1%}")
        
        with col2:
            avg_confidence = np.mean([
                np.mean([m['confidence'] for m in field_metrics])
                for field_metrics in metrics.values()
            ])
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
        with col3:
            st.metric("Processed Files", len(results))
        
        # Display detailed results
        st.subheader("Extracted Data")
        df = pd.DataFrame([
            {field: result.value for field, result in invoice_data.items()}
            for invoice_data in results
        ])
        
        # Add confidence indicators
        df_confidence = pd.DataFrame([
            {field: result.confidence_score for field, result in invoice_data.items()}
            for invoice_data in results
        ])
        
        st.dataframe(df.style.background_gradient(
            cmap='RdYlGn',
            subset=df.columns,
            vmin=0,
            vmax=1,
            gmap=df_confidence
        ))
        
        # Export options
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Extracted Data', index=False)
            pd.DataFrame(metrics).to_excel(writer, sheet_name='Metrics', index=False)
        
        st.download_button(
            label="Download Results (Excel)",
            data=output.getvalue(),
            file_name="invoice_extraction_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    dashboard = StreamlitDashboard()
    dashboard.run()