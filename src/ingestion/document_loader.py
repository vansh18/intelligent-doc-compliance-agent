import os
import google.generativeai as genai
from typing import Dict, Any, List
from .pdf_parser import parse_pdf
import json
import time

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)


def doc_classifer(text):
    """
    Classify document type(invoice, purchase order, GRN or unknown) based on its content.
    
    Args:
        text (str): The text content of the document
        
    Returns:
        str: Document type classification ("invoice", "purchase order", "GRN", or "unknown")
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        You are an expert document classifier. Your task is to classify the given document text into one of these categories:
        - invoice
        - purchase order
        - GRN (Goods Receipt Note)
        - unknown

        Rules:
        1. Return ONLY one of these exact words: "invoice", "purchase order", "GRN", or "unknown"
        2. Do not include any explanation or additional text
        3. If you're not confident about the classification, return "unknown"
        4. Look for key indicators like:
           - Invoice: invoice number, billing details, payment terms
           - Purchase Order: PO number, order details, terms and conditions
           - GRN: goods receipt, delivery confirmation, acceptance of goods

        Document text to classify:
        {text}
        """

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=1,
                top_k=1,
                max_output_tokens=10,
            )
        )
        
        classification = response.text.strip().lower()

        valid_classifications = ["invoice", "purchase order", "grn", "unknown"]
        if classification not in valid_classifications:
            return "unknown"
            
        return classification
        
    except Exception as e:
        print(f"Error in document classification: {str(e)}")
        return "unknown"
    
def detect_vendor(text: str) -> Dict[str, Any]:
    """
    Detect vendor information from document text.
    
    Args:
        text (str): The text content of the document
        
    Returns:
        Dict[str, Any]: Dictionary containing vendor information:
            - name: Vendor name
            - address: Vendor address details
            - contact: Contact information
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        Extract vendor information from the following document text. Return the information in JSON format with these fields:
        - name: The vendor's company name
        - address: A dictionary containing street_address, city, state, postal_code, country
        - contact: A dictionary containing phone, email

        If any field is not found, set its value to null.
        Return ONLY the JSON object, no additional text.
        Make sure the response is valid JSON format.

        Document text:
        {text}
        """

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=1,
                top_k=1,
                max_output_tokens=500,
            )
        )
        
        response_text = response.text.strip()
        try:
            vendor_info = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    vendor_info = json.loads(json_match.group())
                except json.JSONDecodeError:
                    vendor_info = {
                        "name": None,
                        "address": None,
                        "contact": None
                    }
            else:
                vendor_info = {
                    "name": None,
                    "address": None,
                    "contact": None
                }
        
        if not isinstance(vendor_info, dict):
            vendor_info = {
                "name": None,
                "address": None,
                "contact": None
            }
        
        return vendor_info
        
    except Exception as e:
        print(f"Error in vendor detection: {str(e)}")
        return {
            "name": None,
            "address": None,
            "contact": None,
        }

def extract_document_fields(text: str, doc_type: str) -> Dict[str, Any]:
    """
    Extract relevant fields from document based on its type.
    
    Args:
        text (str): The text content of the document
        doc_type (str): Type of document ("invoice", "purchase order", "GRN")
        
    Returns:
        Dict[str, Any]: Dictionary containing extracted fields
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        fields_prompt = {
            "invoice": """
                Extract the following fields from the invoice:
                - invoice_number: The unique invoice identifier
                - issue_date: Date when invoice was issued (YYYY-MM-DD)
                - due_date: Payment due date (YYYY-MM-DD)
                - total_amount: Total amount to be paid
                - currency: Currency code
                - payment_terms: Payment terms and conditions
                - line_items: List of items with description, quantity, unit_price, total
                - po_reference: Reference to related purchase order
                - shipping_details: Shipping information
                - tax_details: Tax information
            """,
            "purchase order": """
                Extract the following fields from the purchase order:
                - po_number: The unique purchase order identifier
                - issue_date: Date when PO was issued (YYYY-MM-DD)
                - delivery_date: Expected delivery date (YYYY-MM-DD)
                - total_amount: Total order amount
                - currency: Currency code
                - terms_and_conditions: PO terms and conditions
                - line_items: List of items with description, quantity, unit_price, total
                - shipping_address: Delivery address
                - billing_address: Billing address
            """,
            "grn": """
                Extract the following fields from the goods receipt note:
                - grn_number: The unique GRN identifier
                - receipt_date: Date when goods were received (YYYY-MM-DD)
                - po_reference: Reference to related purchase order
                - delivery_note: Delivery note number
                - received_by: Name of person who received goods
                - line_items: List of received items with description, quantity, condition
                - inspection_notes: Any inspection or quality notes
                - discrepancies: Any discrepancies found
            """
        }
        
        prompt = f"""
        Extract information from the following {doc_type} text. Return the information in JSON format.
        {fields_prompt.get(doc_type, '')}
        
        If any field is not found, set its value to null.
        Return ONLY the JSON object, no additional text.
        Make sure the response is valid JSON format.

        Document text:
        {text}
        """

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=1,
                top_k=1,
                max_output_tokens=1000,
            )
        )
        

        response_text = response.text.strip()
        try:
            extracted_fields = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    extracted_fields = json.loads(json_match.group())
                except json.JSONDecodeError:
                    extracted_fields = {}
            else:
                extracted_fields = {}
        
        if not isinstance(extracted_fields, dict):
            extracted_fields = {}
            
        return extracted_fields
        
    except Exception as e:
        print(f"Error in field extraction: {str(e)}")
        return {}

def match_documents(doc1: Dict[str, Any], doc2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Match and compare two related documents (e.g., invoice and PO).
    
    Args:
        doc1 (Dict[str, Any]): First document data
        doc2 (Dict[str, Any]): Second document data
        
    Returns:
        Dict[str, Any]: Dictionary containing:
            - match_score: Overall match score (0-100)
            - matches: List of matching fields
            - discrepancies: List of discrepancies found
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        Compare these two documents and identify matches and discrepancies.
        Return the analysis in JSON format with these fields:
        - match_score: Overall match score (0-100)
        - matches: List of matching fields with their values
        - discrepancies: List of discrepancies found

        Document 1:
        {json.dumps(doc1, indent=2)}

        Document 2:
        {json.dumps(doc2, indent=2)}
        """

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=1,
                top_k=1,
                max_output_tokens=1000,
            )
        )
        
        match_results = json.loads(response.text.strip())
        return match_results
        
    except Exception as e:
        print(f"Error in document matching: {str(e)}")
        return {
            "match_score": 0,
            "matches": [],
            "discrepancies": [f"Error during matching: {str(e)}"]
        }
    
def doc_handler(path: str) -> Dict[str, Any]:
    """
    Handle document based on its extension and content.
    
    Args:
        path (str): Path to the document file.
        
    Returns:
        Dict[str, Any]: Dictionary containing:
            - document_type: Classified document type
            - vendor_info: Extracted vendor information
            - extracted_fields: Document-specific fields
            - metadata: Additional information about the processing
            - matches: Document matching results (if applicable)
    """
    try:
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        
        result = {
            "document_type": "unknown",
            "vendor_info": None,
            "extracted_fields": {},
            "metadata": {
                "file_path": path,
                "file_extension": ext,
                "success": False,
                "error": None,
                "processing_time": None
            },
            "matches": None
        }

        start_time = time.time()

        if ext == '.pdf':
            parsed_result = parse_pdf(path)
            raw_text = parsed_result["raw_text"]
            result["metadata"].update(parsed_result["metadata"])
            
            if parsed_result["metadata"]["success"]:
                doc_type = doc_classifer(raw_text)
                result["document_type"] = doc_type
                result["vendor_info"] = detect_vendor(raw_text)
                result["extracted_fields"] = extract_document_fields(raw_text, doc_type)
                
                if doc_type in ["invoice", "grn"] and "po_reference" in result["extracted_fields"]:
                    result["matches"] = {
                        "status": "pending",
                        "message": "PO matching requires implementation of PO lookup functionality"
                    }
                
                result["metadata"]["success"] = True
                
        elif ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            from .gcloud_ocr import ocr_image
            raw_text = ocr_image(path)
            result["metadata"].update({
                "source": "OCR",
                "success": True
            })

            doc_type = doc_classifer(raw_text)
            result["document_type"] = doc_type
            result["vendor_info"] = detect_vendor(raw_text)
            result["extracted_fields"] = extract_document_fields(raw_text, doc_type)
            
            if doc_type in ["invoice", "grn"] and "po_reference" in result["extracted_fields"]:
                result["matches"] = {
                    "status": "pending",
                    "message": "PO matching requires implementation of PO lookup functionality"
                }
            
        else:
            result["metadata"]["error"] = f"Unsupported file type: {ext}"
            return result

        result["metadata"]["processing_time"] = time.time() - start_time
        return result
        
    except Exception as e:
        error_msg = f"Error processing document: {str(e)}"
        print(error_msg)
        return {
            "document_type": "unknown",
            "vendor_info": None,
            "extracted_fields": {},
            "metadata": {
                "file_path": path,
                "file_extension": ext if 'ext' in locals() else None,
                "success": False,
                "error": error_msg,
                "processing_time": None
            },
            "matches": None
        }
    
def process_multiple_documents(paths: List[str]) -> List[Dict[str, Any]]:
    """
    Process multiple documents and return their combined data.
    
    Args:
        paths (List[str]): List of paths to document files.
        
    Returns:
        List[Dict[str, Any]]: List of processed documents, each containing:
            - document_type: Classified document type
            - vendor_info: Extracted vendor information
            - extracted_fields: Document-specific fields
            - metadata: Additional information about the processing
            - matches: Document matching results (if applicable)
    """
    processed_docs = []
    
    for path in paths:
        try:
            doc_result = doc_handler(path)
            processed_docs.append(doc_result)
        except Exception as e:
            print(f"Error processing document {path}: {str(e)}")
            processed_docs.append({
                "document_type": "unknown",
                "vendor_info": None,
                "extracted_fields": {},
                "metadata": {
                    "file_path": path,
                    "file_extension": os.path.splitext(path)[1].lower() if path else None,
                    "success": False,
                    "error": str(e),
                    "processing_time": None
                },
                "matches": None
            })
    
    return processed_docs
