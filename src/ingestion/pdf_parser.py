import os
import tempfile
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from typing import Dict, Any
from pdf2image import convert_from_path
from gcloud_ocr import ocr_image

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def parse_pdf(path: str) -> Dict[str, Any]:
    """
    Parse PDF using PyPDFLoader with LLM fallback for better text extraction.
    
    Args:
        path (str): Path to the PDF file
        
    Returns:
        Dict[str, Any]: Dictionary containing extracted text and metadata
    """
    try:
        loader = PyPDFLoader(path)
        documents = loader.load()
        
        combined_text = "\n".join([doc.page_content for doc in documents])
        
        if len(combined_text.strip()) > 100:
            return {
                "raw_text": combined_text,
                "metadata": {
                    "source": "PyPDFLoader",
                    "pages": len(documents),
                    "success": True
                }
            }

        return parse_with_llm(path)
        
    except Exception as e:
        print(f"PyPDFLoader failed: {str(e)}")
        return parse_with_llm(path)

def parse_with_llm(path: str) -> Dict[str, Any]:
    """
    Parse PDF using OCR and LLM for better text extraction.
    
    Args:
        path (str): Path to the PDF file
        
    Returns:
        Dict[str, Any]: Dictionary containing extracted text and metadata
    """
    try:
        full_text = ""
        with tempfile.TemporaryDirectory() as tmpdir:
            images = convert_from_path(path, dpi=300, output_folder=tmpdir)
            for i, image in enumerate(images):
                image_path = os.path.join(tmpdir, f"page_{i}.png")
                image.save(image_path)
                text = ocr_image(image_path)
                full_text += f"\n--- Page {i+1} ---\n{text}"
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        You are an expert document parser. Your task is to clean and structure the extracted text from a document.
        
        Rules:
        1. Remove any OCR artifacts or noise
        2. Fix any obvious text recognition errors
        3. Maintain the logical structure of the document
        4. Preserve important formatting like line breaks where they make sense
        5. Keep all numerical values and dates exactly as they appear
        6. Do not add any information that wasn't in the original text
        
        Document text to clean:
        {full_text}
        
        Return the cleaned text without any additional explanation or formatting.
        """
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=1,
                top_k=1,
                max_output_tokens=2048,
            )
        )
        
        cleaned_text = response.text.strip()
        
        return {
            "raw_text": cleaned_text,
            "metadata": {
                "source": "LLM_OCR",
                "pages": len(images),
                "success": True
            }
        }
        
    except Exception as e:
        print(f"LLM parsing failed: {str(e)}")
        return {
            "raw_text": "",
            "metadata": {
                "source": "failed",
                "error": str(e),
                "success": False
            }
        }