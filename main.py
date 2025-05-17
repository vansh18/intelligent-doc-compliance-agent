from src.ingestion.document_loader import parse_scanned_pdf
from src.processing.gemini_processor import structure_document_text
from src.processing.document_grouper import DocumentGrouper
from src.storage.db_manager import DatabaseManager
import uuid
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import glob

load_dotenv()

def process_document(pdf_path: str) -> Dict[str, Any]:
    """
    Process a single document through the pipeline.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        Dict[str, Any]: Processed document data
    """
    document_id = str(uuid.uuid4())

    print(f"Processing document: {pdf_path}")
    print("Extracting text from document...")
    extraction_result = parse_scanned_pdf(pdf_path)

    print("Structuring document using Gemini...")
    structured_data = structure_document_text(extraction_result["raw_text"])

    return {
        "id": document_id,
        "raw_text": extraction_result["raw_text"],
        "structured_data": structured_data["structured_data"]
    }

def process_documents(pdf_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Process multiple documents and identify relationships.
    
    Args:
        pdf_paths (List[str]): List of paths to PDF files
        
    Returns:
        List[Dict[str, Any]]: List of processed documents with relationships
    """

    processed_docs = []
    for pdf_path in pdf_paths:
        try:
            doc_data = process_document(pdf_path)
            processed_docs.append(doc_data)
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
            continue

    grouper = DocumentGrouper()
    docs_with_relationships = grouper.find_related_documents(processed_docs)
    db_manager = DatabaseManager()
    try:
        for doc in docs_with_relationships:
            db_manager.save_document(
                document_id=doc["id"],
                raw_text=doc["raw_text"],
                structured_data=doc["structured_data"]
            )

        all_relationships = []
        for doc in docs_with_relationships:
            all_relationships.extend(doc["relationships"])
        db_manager.save_relationships(all_relationships)
        
    finally:
        db_manager.close()
    
    return docs_with_relationships

def get_document_group(document_id: str) -> Dict[str, Any]:
    """
    Get a document and all its related documents.
    
    Args:
        document_id (str): ID of the document to get
        
    Returns:
        Dict[str, Any]: Document and its related documents
    """
    db_manager = DatabaseManager()
    try:
        main_doc = db_manager.get_document(document_id)
        related_docs = db_manager.get_related_documents(document_id)
        
        return {
            "main_document": main_doc,
            "related_documents": related_docs
        }
    finally:
        db_manager.close()

if __name__ == "__main__":
    required_vars = ["GEMINI_API_KEY", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    pdf_paths = glob.glob("data/test-data/*.pdf")
    if not pdf_paths:
        print("No PDF files found in data directory")
        exit(1)
        
    print(f"Found {len(pdf_paths)} PDF files to process")
    processed_docs = process_documents(pdf_paths)
    
    print("\nProcessing complete!")
    print(f"Successfully processed {len(processed_docs)} documents")
    
    for doc in processed_docs:
        if doc["relationships"]:
            print(f"\nDocument {doc['id']} has {len(doc['relationships'])} relationships:")
            for rel in doc["relationships"]:
                print(f"- Related to {rel['doc2_id']} via {rel['relationship_type']} (confidence: {rel['confidence']:.2f})")