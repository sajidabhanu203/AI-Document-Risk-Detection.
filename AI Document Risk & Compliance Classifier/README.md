# DocuShield — AI Document Risk & Compliance Classifier

## Project Overview
DocuShield is a document-screening prototype that identifies predefined risk indicators in text extracted from PDF, DOCX, and TXT documents.

## Features
- PDF, DOCX, and TXT upload
- Rule-based risk classification
- Risk dashboard and charts
- Filterable findings table
- CSV export

## Technologies
- Python
- Streamlit
- Pandas
- PyPDF
- python-docx
- Plotly
- Regular expressions

## Installation
1. Install Python.
2. Open this folder in VS Code.
3. Run: `python -m pip install -r requirements.txt`
4. Run: `python -m streamlit run app.py`

## Important Limitation
This prototype uses predefined patterns, not a trained machine-learning model. Its findings are preliminary and require human review. It does not certify legal or regulatory compliance.
