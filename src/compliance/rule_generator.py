import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, List
from datetime import datetime

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class ComplianceRuleGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the compliance rules schema."""
        schema_path = os.path.join(os.path.dirname(__file__), 'compliance_rules.json')
        with open(schema_path, 'r') as f:
            return json.load(f)
    
    def _generate_rule_id(self, category: str, existing_rules: List[Dict[str, Any]]) -> str:
        """Generate a unique rule ID based on category and existing rules."""
        prefix = {
            'invoice': 'INV',
            'purchase_order': 'PO',
            'goods_receipt': 'GRN'
        }.get(category, 'GEN')

        max_num = 0
        for rule in existing_rules:
            if rule['rule_id'].startswith(prefix):
                try:
                    num = int(rule['rule_id'].split('-')[1])
                    max_num = max(max_num, num)
                except (IndexError, ValueError):
                    continue
        
        return f"{prefix}-{max_num + 1:03d}"
    
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
        1. Generate a rule that strictly follows the schema structure
        2. Include all required fields
        3. Use appropriate validation types (regex, numeric, date_comparison)
        4. Set appropriate severity levels (high, medium, low)
        5. Specify correct enforcement actions (reject, flag_for_review, warning)
        6. Ensure the rule is applicable to the correct document types

        Natural Language Instruction:
        {natural_language_instruction}

        Return ONLY the rule object in JSON format, without any explanation or additional text.
        The response should be a valid JSON object that can be parsed by json.loads().
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
            
            # Print raw response for debugging
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
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {str(e)}")
                print("Failed to parse response text:")
                print(response_text)
                return None
            
            rule['rule_id'] = self._generate_rule_id(rule['category'], self.schema['rules'])
            self._validate_rule(rule)
            
            return rule
            
        except Exception as e:
            print(f"Error generating rule: {str(e)}")
            return None
    
    def _validate_rule(self, rule: Dict[str, Any]) -> bool:
        """Validate the generated rule against the schema."""
        required_fields = ['rule_id', 'category', 'name', 'description', 'severity', 
                         'validation', 'applicable_documents', 'enforcement']
        
        for field in required_fields:
            if field not in rule:
                raise ValueError(f"Missing required field: {field}")
        
        if rule['category'] not in self.schema['document_types']:
            raise ValueError(f"Invalid category: {rule['category']}")

        if rule['severity'] not in ['high', 'medium', 'low']:
            raise ValueError(f"Invalid severity: {rule['severity']}")
 
        if rule['enforcement']['action'] not in ['reject', 'flag_for_review', 'warning']:
            raise ValueError(f"Invalid enforcement action: {rule['enforcement']['action']}")
        
        return True
    
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

