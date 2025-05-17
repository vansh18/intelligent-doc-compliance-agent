from src.ingestion.document_loader import parse_scanned_pdf
from src.processing.gemini_processor import structure_document_text
from src.storage.db_manager import DatabaseManager
import uuid
import os
from dotenv import load_dotenv
load_dotenv()

def process_document(pdf_path: str) -> str:
    """
    Process a document through the complete pipeline:
    1. Extract text using OCR
    2. Structure the text using Gemini
    3. Store the structured data in PostgreSQL
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Document ID
    """

    document_id = str(uuid.uuid4())

    print("Extracting text from document...")
    extraction_result = parse_scanned_pdf(pdf_path)

    print("Structuring document using Gemini...")
    structured_data = structure_document_text(extraction_result["raw_text"])

    print("Storing structured data in database...")
    db_manager = DatabaseManager()
    try:
        doc_id = db_manager.save_document(
            document_id=document_id,
            raw_text=extraction_result["raw_text"],
            structured_data=structured_data
        )
        print(f"Document processed and stored with ID: {doc_id}")
        return doc_id
    finally:
        db_manager.close()

if __name__ == "__main__":
    required_vars = ["GEMINI_API_KEY", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    pdf_path = "data/invoice.pdf"
    doc_id = process_document(pdf_path)