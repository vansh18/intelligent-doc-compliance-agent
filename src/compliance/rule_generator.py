import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, List
from datetime import datetime
import time

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class ComplianceRuleGenerator:
    def __init__(self):
        """Initialize the compliance rule generator."""
        self.rules_file = os.path.join(os.path.dirname(__file__), 'compliance_rules.json')
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the compliance rules schema from JSON file."""
        try:
            with open(self.rules_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default_schema = {
                "version": "1.0",
                "metadata": {
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "author": "Compliance Agent",
                    "description": "Structured compliance rules for document validation"
                },
                "document_types": [
                    "invoice",
                    "purchase_order",
                    "goods_receipt"
                ],
                "rules": []
            }
            with open(self.rules_file, 'w') as f:
                json.dump(default_schema, f, indent=4)
            return default_schema
        except json.JSONDecodeError:
            print("Error: Invalid JSON in compliance rules file")
            return {"rules": []}
    
    def _generate_rule_id(self, category: str, existing_rules: List[Dict[str, Any]]) -> str:
        """Generate a unique rule ID based on category and existing rules."""
        try:
            if not isinstance(existing_rules, list):
                existing_rules = []
                
            prefix = {
                'invoice': 'INV',
                'purchase_order': 'PO',
                'goods_receipt': 'GRN',
                'general': 'GEN'
            }.get(category, 'GEN')

            max_num = 0
            for rule in existing_rules:
                if isinstance(rule, dict) and 'rule_id' in rule and rule['rule_id'].startswith(prefix):
                    try:
                        num = int(rule['rule_id'].split('-')[1])
                        max_num = max(max_num, num)
                    except (IndexError, ValueError):
                        continue
            
            return f"{prefix}-{max_num + 1:03d}"
            
        except Exception as e:
            print(f"Error generating rule ID: {str(e)}")
            return f"GEN-{int(time.time())}" 
    
    def generate_rule(self, rule_text: str) -> Dict[str, Any]:
        """
        Generate a compliance rule from natural language text.
        
        Args:
            rule_text (str): Natural language description of the rule
            
        Returns:
            Dict[str, Any]: Generated rule structure
        """
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = f"""
            Generate a structured compliance rule from the following natural language description.
            Return the rule in JSON format with these required fields:
            - rule_id: Unique identifier (format: CATEGORY-XXX where CATEGORY is based on the rule type)
            - name: Short descriptive name
            - description: Detailed description
            - category: Rule category (e.g., amount, date, vendor, etc.)
            - field: Document field to validate
            - validation: Dictionary containing:
                - type: Validation type (numeric, regex, date_comparison, cross_document_consistency)
                - parameters: Validation parameters
                - error_message: Custom error message
            - severity: Severity level (high, medium, low)
            - applicable_documents: List of document types this rule applies to
            - enforcement: Dictionary containing:
                - action: Enforcement action (block, warn, notify)
                - notification: Boolean indicating if notification is required

            Rule description: {rule_text}

            Return ONLY the JSON object, no additional text.
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
            try:
                rule = json.loads(response.text.strip())
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    rule = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse rule from response")
                
            required_fields = [
                'rule_id', 'name', 'description', 'category', 'field',
                'validation', 'severity', 'applicable_documents', 'enforcement'
            ]
            
            for field in required_fields:
                if field not in rule:
                    raise ValueError(f"Missing required field: {field}")
            
            self.schema['rules'].append(rule)
            self.schema['metadata']['last_updated'] = datetime.now().strftime("%Y-%m-%d")

            with open(self.rules_file, 'w') as f:
                json.dump(self.schema, f, indent=4)
        
            
            return rule
            
        except Exception as e:
            print(f"[DEBUG] Error generating rule: {str(e)}")
            raise
    
    def clear_rules(self) -> None:
        """Clear all rules from the compliance rules file."""
        try:
            self.schema['rules'] = []
            self.schema['metadata']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
            
            with open(self.rules_file, 'w') as f:
                json.dump(self.schema, f, indent=4)
                
            
            
        except Exception as e:
            print(f"[DEBUG] Error clearing rules: {str(e)}")
            raise
