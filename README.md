# Intelligent Document Compliance Agent

An AI-powered document compliance checking system that automates the validation of business documents against configurable compliance rules.

## Overview

The Intelligent Document Compliance Agent is designed to streamline document compliance checking processes by leveraging AI and machine learning to automatically validate documents against configurable rules. It supports various document types including invoices, purchase orders, and receipts.

### Key Features

- 📄 Multi-document type support (PDF, JPG, PNG)
- 🤖 AI-powered document processing and validation
- ⚡ Real-time compliance checking
- 📊 Detailed compliance reports

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Document Input │────▶│  Document       │────▶│  Structured     │-────│
│  (PDF/JPG/PNG)  │     │  Processing     │     │      JSON       │     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     │     
                                                                        │
                                                                        │
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     │
│  NL Rules       │────▶│  Rule           │────▶│  Structured     │     │
│                 │     │  Generator      │     │  Rules          │     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     │
                                                         │              │
                                                         ▼              │
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     │
│  Generated      │◀────│  Validation     │◀────│  Compliance     │◀────│
│  Report         │     │  Summary        │     │  Agent          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Components

1. **Document Processing**
   - OCR using Google Cloud Vision API
   - Text extraction and structuring
   - Document type classification

2. **Rule Generation**
   - Natural language rule processing
   - Rule structure validation
   - Rule storage and management

3. **Compliance Engine**
   - Rule-based validation
   - Cross-document consistency checks
   - Severity-based reporting

4. **Report Generation**
   - HTML-based report generation
   - Detailed validation results
   - Downloadable reports

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Google Cloud Vision API credentials
- Gemini API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/intelligent-doc-compliance-agent.git
   cd intelligent-doc-compliance-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/gcloud-credentials.json
   GEMINI_API_KEY=your_gemini_api_key
   ```

## Usage

1. Start the application:
   ```bash
   streamlit run src/app.py
   ```

2. Access the web interface at `http://localhost:8501`

3. Upload documents and configure compliance rules:
   - Upload documents (PDF, JPG, PNG)
   - Define compliance rules in natural language
   - Run compliance checks
   - Generate and download reports

## Implementation Details

### Document Processing

- Uses Google Cloud Vision API for OCR
- Implements document type classification
- Extracts structured data from documents

### Compliance Validation

- Configurable rule engine
- Cross-document consistency checks
- Severity-based validation results

### Report Generation

- HTML-based report generation
- Detailed validation results
- Downloadable reports

## Limitations and Assumptions

### Current Limitations

1. **Document Types**
   - Limited to PDF, JPG, and PNG formats
   - Maximum file size: 10MB per document

2. **Processing**
   - OCR accuracy depends on document quality
   - Longer processing time for documents

3. **Rules**
   - Rules must be defined in natural language
   - Limited to predefined validation types

### Assumptions

1. **Document Structure**
   - Documents follow standard business formats
   - Text is machine-readable

2. **Data Consistency**
   - Related documents share common identifiers
   - Document types are correctly identified

