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
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the compliance rules schema."""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'compliance_rules.json')
            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"Schema file not found at {schema_path}")
                
            with open(schema_path, 'r') as f:
                schema = json.load(f)
                
            # Validate schema structure
            if not isinstance(schema, dict):
                raise ValueError("Schema must be a dictionary")
            if 'rules' not in schema:
                raise ValueError("Schema must contain 'rules' key")
            if 'document_types' not in schema:
                raise ValueError("Schema must contain 'document_types' key")
            if 'metadata' not in schema:
                raise ValueError("Schema must contain 'metadata' key")
                
            return schema
            
        except Exception as e:
            print(f"Error loading schema: {str(e)}")
            # Return a default schema structure
            return {
                "version": "1.0",
                "metadata": {
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "author": "Compliance Agent",
                    "description": "Default schema structure"
                },
                "document_types": ["invoice", "purchase_order", "goods_receipt"],
                "rules": []
            }
    
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
            return f"GEN-{int(time.time())}"  # Fallback to timestamp-based ID
    
    def generate_rule(self, natural_language_instruction: str) -> Dict[str, Any]:
        """
        Convert natural language compliance instruction into a structured rule.
        
        Args:
            natural_language_instruction (str): Natural language description of the compliance rule
            
        Returns:
            Dict[str, Any]: Structured compliance rule
        """
        prompt = f"""
        You are an expert compliance rule generator. Your task is to convert natural language compliance instructions into structured JSON rules.

        SCHEMA:
        {json.dumps(self.schema, indent=2)}

        RULES:
        1. Generate a rule that follows the schema structure
        2. Include all required fields:
           - rule_id (will be generated automatically)
           - name
           - description
           - category (one of: {', '.join(self.schema['document_types'] + ['general'])})
           - field (the field to validate)
           - validation (with type, parameters, and error_message)
           - severity (high, medium, low)
           - applicable_documents (list of document types)
           - enforcement (with action and notification)
        3. Use appropriate validation types (regex, numeric, date_comparison)
        4. Set appropriate severity levels (high, medium, low)
        5. Leave enforcement.action as "to_be_decided_by_agent"
        6. The response must be a valid JSON object that can be parsed by json.loads()
        7. Do not include any markdown formatting or code blocks

        Natural Language Instruction:
        {natural_language_instruction}

        Return ONLY the rule object in JSON format, without any explanation or additional text.
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    top_p=1,
                    top_k=1,
                    max_output_tokens=1024,
                )
            )
            
            print("Raw response from Gemini:")
            print(response.text)
            print("\n" + "="*50 + "\n")
            
            response_text = response.text.strip()
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            try:
                rule = json.loads(response_text)
                
                if 'enforcement' not in rule:
                    rule['enforcement'] = {"action": "to_be_decided_by_agent", "notification": True}
                else:
                    rule['enforcement']['action'] = "to_be_decided_by_agent"
                    if 'notification' not in rule['enforcement']:
                        rule['enforcement']['notification'] = True
                
                rule['rule_id'] = self._generate_rule_id(rule.get('category', 'general'), self.schema['rules'])
                return rule
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {str(e)}")
                print("Failed to parse response text:")
                print(response_text)
                return self._create_default_rule(natural_language_instruction, "Failed to generate specific validation rule")
            
        except Exception as e:
            print(f"Error generating rule: {str(e)}")
            return self._create_default_rule(natural_language_instruction, f"Error generating rule: {str(e)}")
    
    def _create_default_rule(self, description: str, error_message: str) -> Dict[str, Any]:
        """Create a default rule with the given description and error message."""
        return {
            "rule_id": "GEN-001",
            "name": "Default Rule",
            "description": description,
            "category": "general",
            "field": "unknown",
            "validation": {
                "type": "custom",
                "parameters": {},
                "error_message": error_message
            },
            "severity": "medium",
            "applicable_documents": ["invoice", "purchase_order", "goods_receipt"],
            "enforcement": {
                "action": "to_be_decided_by_agent",
                "notification": True
            }
        }
    
    def update_compliance_rules(self, new_rule: Dict[str, Any]) -> bool:
        """
        Add a new rule to the compliance rules file.
        
        Args:
            new_rule (Dict[str, Any]): The new rule to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.schema['rules'].append(new_rule)
            self.schema['metadata']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
            
            schema_path = os.path.join(os.path.dirname(__file__), 'compliance_rules.json')
            with open(schema_path, 'w') as f:
                json.dump(self.schema, f, indent=4)
            
            return True
            
        except Exception as e:
            print(f"Error updating compliance rules: {str(e)}")
            return False

if __name__ == "__main__":
    generator = ComplianceRuleGenerator()
    json_rule = generator.generate_rule("Verify the vendor name across all documents is same.")
    if json_rule:
        print("Generated Rule:", json.dumps(json_rule, indent=2))
        if generator.update_compliance_rules(json_rule):
            print("Rule updated successfully")
    else:
        print("Failed to generate rule")
