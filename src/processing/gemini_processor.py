import google.generativeai as genai
import os
from typing import Dict, Any
import json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)


DOCUMENT_SCHEMA = {
    "document_type": "string",
    "document_id": "string",
    "dates": {
        "issue_date": "string",
        "due_date": "string",
        "delivery_date": "string"
    },
    "parties": {
        "sender": {
            "name": "string",
            "address": "string",
            "contact": "string"
        },
        "recipient": {
            "name": "string",
            "address": "string",
            "contact": "string"
        }
    },
    "financial": {
        "currency": "string",
        "subtotal": "number",
        "tax": "number",
        "total": "number"
    },
    "line_items": [
        {
            "description": "string",
            "quantity": "number",
            "unit_price": "number",
            "total": "number"
        }
    ]
}

def clean_json_response(text: str) -> str:
    """
    Clean and extract JSON from Gemini's response.
    Sometimes Gemini includes markdown formatting or extra text.
    """

    text = text.replace("```json", "").replace("```", "")
    start = text.find("{")
    end = text.rfind("}") + 1
    
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in response")
        
    return text[start:end]

def structure_document_text(raw_text: str) -> Dict[str, Any]:
    """
    Use Gemini to structure the extracted document text into a consistent format.
    
    Args:
        raw_text (str): The raw text extracted from the document
        
    Returns:
        Dict[str, Any]: Structured information from the document
    """
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    You are an expert document analysis system working for a compliance agent. Your task is to extract and structure information from documents into a consistent JSON format.

    IMPORTANT RULES:
    1. ALWAYS return a valid JSON object that strictly follows the schema below
    2. Use null for any fields where information is not found
    3. Maintain consistent data types (strings, numbers, arrays) as specified
    4. Do not add any fields outside the schema
    5. Do not include any explanatory text outside the JSON
    6. Wrap your response in a JSON code block using ```json and ``` markers

    REQUIRED JSON SCHEMA:
    {json.dumps(DOCUMENT_SCHEMA, indent=2)}

    EXAMPLE RESPONSE FORMAT:
    ```json
    {{
        "document_type": "invoice",
        "document_id": "INV-2024-001",
        "dates": {{
            "issue_date": "2024-03-15",
            "due_date": "2024-04-15",
            "delivery_date": null
        }},
        "parties": {{
            "sender": {{
                "name": "ABC Company",
                "address": "123 Business St",
                "contact": "contact@abc.com"
            }},
            "recipient": {{
                "name": "XYZ Corp",
                "address": "456 Corporate Ave",
                "contact": "billing@xyz.com"
            }}
        }},
        "financial": {{
            "currency": "USD",
            "subtotal": 1000.00,
            "tax": 100.00,
            "total": 1100.00
        }},
        "line_items": [
            {{
                "description": "Product A",
                "quantity": 2,
                "unit_price": 500.00,
                "total": 1000.00
            }}
        ]
    }}
    ```

    Document text to analyze:
    {raw_text}

    Remember: Return ONLY the JSON object wrapped in ```json and ``` markers, no other text or explanation.
    """

    try:
        # temperature=0 for maximum consistency
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=1,
                top_k=1,
                max_output_tokens=2048,
            )
        )
        
        # Debug: Print raw response
        print("Raw Gemini Response:")
        print(response.text)
        print("\n" + "="*50 + "\n")
        
        cleaned_json = clean_json_response(response.text)
        structured_data = json.loads(cleaned_json)
        
        if not isinstance(structured_data, dict):
            raise ValueError("Response is not a valid JSON object")
            
        required_keys = set(DOCUMENT_SCHEMA.keys())
        if not all(key in structured_data for key in required_keys):
            missing_keys = required_keys - set(structured_data.keys())
            raise ValueError(f"Missing required keys: {missing_keys}")
            
        return {"structured_data": structured_data}
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {str(e)}")
        print("Failed Response Text:")
        print(response.text)
        return {"error": f"Failed to parse JSON response: {str(e)}"}
    except Exception as e:
        print(f"General Error: {str(e)}")
        return {"error": f"Failed to structure document: {str(e)}"} 