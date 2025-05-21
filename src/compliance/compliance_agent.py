import os
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re
from rule_generator import ComplianceRuleGenerator

class ComplianceAgent:
    def __init__(self):
        self.rule_generator = ComplianceRuleGenerator()
        self.rules = self.rule_generator.schema['rules']
        
    def evaluate_document(self, document_data: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
        """
        Evaluate a document against all applicable compliance rules.
        
        Args:
            document_data (Dict[str, Any]): Extracted document data
            doc_type (str): Type of document (invoice, purchase_order, goods_receipt)
            
        Returns:
            Dict[str, Any]: Evaluation results including violations and overall status
        """
        results = {
            "document_type": doc_type,
            "evaluation_time": datetime.now().isoformat(),
            "overall_status": "compliant",
            "violations": [],
            "warnings": [],
            "passed_rules": []
        }
        
        applicable_rules = [
            rule for rule in self.rules 
            if doc_type in rule['applicable_documents']
        ]
        
        for rule in applicable_rules:
            validation_result = self._validate_rule(rule, document_data)
            
            if validation_result['status'] == 'violation':
                results['violations'].append({
                    'rule_id': rule['rule_id'],
                    'rule_name': rule['name'],
                    'description': rule['description'],
                    'severity': rule['severity'],
                    'details': validation_result['details']
                })
                if rule['severity'] == 'high':
                    results['overall_status'] = 'non_compliant'
            elif validation_result['status'] == 'warning':
                results['warnings'].append({
                    'rule_id': rule['rule_id'],
                    'rule_name': rule['name'],
                    'description': rule['description'],
                    'details': validation_result['details']
                })
            else:
                results['passed_rules'].append({
                    'rule_id': rule['rule_id'],
                    'rule_name': rule['name']
                })
        
        return results
    
    def _validate_rule(self, rule: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single rule against document data.
        
        Args:
            rule (Dict[str, Any]): The rule to validate
            document_data (Dict[str, Any]): Document data to validate against
            
        Returns:
            Dict[str, Any]: Validation result
        """
        validation_type = rule['validation']['type']
        
        try:
            if validation_type == 'regex':
                return self._validate_regex(rule, document_data)
            elif validation_type == 'numeric':
                return self._validate_numeric(rule, document_data)
            elif validation_type == 'date_comparison':
                return self._validate_date_comparison(rule, document_data)
            elif validation_type == 'currency_consistency':
                return self._validate_currency_consistency(rule, document_data)
            elif validation_type == 'cross_reference':
                return self._validate_cross_reference(rule, document_data)
            elif validation_type == 'line_item_calculation':
                return self._validate_line_item_calculation(rule, document_data)
            elif validation_type == 'address_validation':
                return self._validate_address(rule, document_data)
            else:
                return {
                    'status': 'warning',
                    'details': f"Unknown validation type: {validation_type}"
                }
        except Exception as e:
            return {
                'status': 'warning',
                'details': f"Validation error: {str(e)}"
            }
    
    def _validate_regex(self, rule: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate using regex pattern."""
        pattern = rule['validation']['pattern']
        field = rule['validation'].get('field', 'invoice_number')  # Default field
        
        if field not in document_data:
            return {
                'status': 'violation',
                'details': f"Required field '{field}' not found in document"
            }
        
        value = str(document_data[field])
        if not re.match(pattern, value):
            return {
                'status': 'violation',
                'details': rule['validation']['error_message']
            }
        
        return {'status': 'compliant'}
    
    def _validate_numeric(self, rule: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate numeric conditions."""
        field = rule['validation']['field']
        operator = rule['validation']['operator']
        expected_value = rule['validation']['value']
        
        if field not in document_data:
            return {
                'status': 'violation',
                'details': f"Required field '{field}' not found in document"
            }
        
        try:
            actual_value = float(document_data[field])
        except (ValueError, TypeError):
            return {
                'status': 'violation',
                'details': f"Field '{field}' must be a numeric value"
            }
        
        is_valid = False
        if operator == '<=':
            is_valid = actual_value <= expected_value
        elif operator == '>=':
            is_valid = actual_value >= expected_value
        elif operator == '<':
            is_valid = actual_value < expected_value
        elif operator == '>':
            is_valid = actual_value > expected_value
        elif operator == '==':
            is_valid = actual_value == expected_value
        
        if not is_valid:
            return {
                'status': 'violation',
                'details': rule['validation']['error_message']
            }
        
        return {'status': 'compliant'}
    
    def _validate_date_comparison(self, rule: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate date comparisons."""
        fields = rule['validation']['fields']

        first_field = next(iter(fields.items()))
        field_name = first_field[0]
        operator = first_field[1]
        
        if field_name not in document_data:
            return {
                'status': 'violation',
                'details': f"Required field '{field_name}' not found in document"
            }
        
        try:
            date1 = datetime.strptime(document_data[field_name], "%Y-%m-%d")
        except ValueError:
            return {
                'status': 'violation',
                'details': f"Field '{field_name}' must be in YYYY-MM-DD format"
            }
        
        second_field = next((f for f in fields.items() if f[0] != field_name), None)
        if second_field:
            field2_name = second_field[0]
            if field2_name not in document_data:
                return {
                    'status': 'violation',
                    'details': f"Required field '{field2_name}' not found in document"
                }
            
            try:
                date2 = datetime.strptime(document_data[field2_name], "%Y-%m-%d")
            except ValueError:
                return {
                    'status': 'violation',
                    'details': f"Field '{field2_name}' must be in YYYY-MM-DD format"
                }
            
            is_valid = False
            if operator == '>':
                is_valid = date1 > date2
            elif operator == '<':
                is_valid = date1 < date2
            elif operator == '>=':
                is_valid = date1 >= date2
            elif operator == '<=':
                is_valid = date1 <= date2
            elif operator == '==':
                is_valid = date1 == date2
            
            if not is_valid:
                return {
                    'status': 'violation',
                    'details': rule['validation']['error_message']
                }
        
        return {'status': 'compliant'}

    def _validate_currency_consistency(self, rule: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate currency consistency across document fields.
        
        Args: 
            rule (Dict[str, Any]): The rule to validate
            document_data (Dict[str, Any]): Document data to validate against
        Returns:
            Dict[str, Any]: Validation result
        """

        currency_field = rule['validation']['currency_field']
        allowed_currencies = rule['validation']['allowed_currencies']
        
        if currency_field not in document_data:
            return {
                'status': 'violation',
                'details': f"Required currency field '{currency_field}' not found in document"
            }
        
        currency = document_data[currency_field]
        if currency not in allowed_currencies:
            return {
                'status': 'violation',
                'details': f"Currency '{currency}' is not in the allowed list: {', '.join(allowed_currencies)}"
            }
        
        if 'line_items' in document_data:
            for item in document_data['line_items']:
                if 'currency' in item and item['currency'] != currency:
                    return {
                        'status': 'violation',
                        'details': f"Line item currency '{item['currency']}' does not match document currency '{currency}'"
                    }
        
        return {'status': 'compliant'}

    def _validate_cross_reference(self, rule: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate cross-references between related documents.
        
        Args:
            rule (Dict[str, Any]): The rule to validate
            document_data (Dict[str, Any]): Document data to validate against
        Returns:
            Dict[str, Any]: Validation result
        """
        reference_field = rule['validation']['reference_field']
        reference_type = rule['validation']['reference_type']
        reference_format = rule['validation'].get('reference_format')
        
        if reference_field not in document_data:
            return {
                'status': 'violation',
                'details': f"Required reference field '{reference_field}' not found in document"
            }
        
        reference = document_data[reference_field]
        
        if reference_format and not re.match(reference_format, str(reference)):
            return {
                'status': 'violation',
                'details': f"Reference '{reference}' does not match required format"
            }
        
        return {'status': 'compliant'}

    def _validate_line_item_calculation(self, rule: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate line item calculations and totals.
        
        Args:
            rule (Dict[str, Any]): The rule to validate
            document_data (Dict[str, Any]): Document data to validate against
        Returns:
            Dict[str, Any]: Validation result
        """
        if 'line_items' not in document_data:
            return {
                'status': 'violation',
                'details': "Document must contain line items"
            }
        
        total_amount = 0
        for item in document_data['line_items']:
            if not all(k in item for k in ['quantity', 'unit_price']):
                return {
                    'status': 'violation',
                    'details': "Each line item must have quantity and unit price"
                }
            
            try:
                item_total = float(item['quantity']) * float(item['unit_price'])
                if 'total' in item and abs(float(item['total']) - item_total) > 0.01:
                    return {
                        'status': 'violation',
                        'details': f"Line item total {item['total']} does not match calculated total {item_total}"
                    }
                total_amount += item_total
            except (ValueError, TypeError):
                return {
                    'status': 'violation',
                    'details': "Invalid numeric values in line item"
                }
        
        if 'total_amount' in document_data:
            doc_total = float(document_data['total_amount'])
            if abs(doc_total - total_amount) > 0.01:
                return {
                    'status': 'violation',
                    'details': f"Document total {doc_total} does not match sum of line items {total_amount}"
                }
        
        return {'status': 'compliant'}

    def _validate_address(self, rule: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate address format and required components.
        
        Args:
            rule (Dict[str, Any]): The rule to validate
            document_data (Dict[str, Any]): Document data to validate against

        Returns:
            Dict[str, Any]: Validation result
        """
        address_field = rule['validation']['address_field']
        required_components = rule['validation']['required_components']
        
        if address_field not in document_data:
            return {
                'status': 'violation',
                'details': f"Required address field '{address_field}' not found in document"
            }
        
        address = document_data[address_field]
        
        if not isinstance(address, dict):
            return {
                'status': 'violation',
                'details': f"Address must be a structured object with components"
            }

        missing_components = [comp for comp in required_components if comp not in address]
        if missing_components:
            return {
                'status': 'violation',
                'details': f"Missing required address components: {', '.join(missing_components)}"
            }

        if 'postal_code_format' in rule['validation']:
            postal_code = address.get('postal_code', '')
            if not re.match(rule['validation']['postal_code_format'], postal_code):
                return {
                    'status': 'violation',
                    'details': f"Invalid postal code format: {postal_code}"
                }
        
        return {'status': 'compliant'}

