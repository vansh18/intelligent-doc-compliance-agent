import os
import google.generativeai as genai
from typing import Dict, Any
from pdf_parser import parse_pdf

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
    
def doc_handler(path: str) -> Dict[str, Any]:
    """
    Handle document based on its extension and content.
    
    Args:
        path (str): Path to the document file.
        
    Returns:
        Dict[str, Any]: Dictionary containing:
            - raw_text: Extracted text from the document
            - doc_type: Classified document type
            - metadata: Additional information about the processing
    """
    try:
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        
        result = {
            "raw_text": "",
            "doc_type": "unknown",
            "metadata": {
                "file_path": path,
                "file_extension": ext,
                "success": False,
                "error": None
            }
        }

        if ext == '.pdf':
            parsed_result = parse_pdf(path)
            result["raw_text"] = parsed_result["raw_text"]
            result["metadata"].update(parsed_result["metadata"])
            
            if parsed_result["metadata"]["success"]:
                result["doc_type"] = doc_classifer(parsed_result["raw_text"])
                result["metadata"]["success"] = True
                
        elif ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            from .gcloud_ocr import ocr_image
            result["raw_text"] = ocr_image(path)
            result["metadata"].update({
                "source": "OCR",
                "success": True
            })
            result["doc_type"] = doc_classifer(result["raw_text"])
            
        else:
            result["metadata"]["error"] = f"Unsupported file type: {ext}"
            return result
            
        return result
        
    except Exception as e:
        error_msg = f"Error processing document: {str(e)}"
        print(error_msg)
        return {
            "raw_text": "",
            "doc_type": "unknown",
            "metadata": {
                "file_path": path,
                "file_extension": ext if 'ext' in locals() else None,
                "success": False,
                "error": error_msg
            }
        }
    
