import os
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
import re
from decimal import Decimal

class ComplianceAgent:
    def __init__(self):
        self.rules = self._load_rules()
        
    def _load_rules(self) -> Dict[str, Any]:
        """Load compliance rules from JSON file."""
        try:
            rules_path = os.path.join(os.path.dirname(__file__), 'compliance_rules.json')
            with open(rules_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading rules: {str(e)}")
            return {"rules": []}
    
    def clear_rules(self) -> None:
        """Clear all rules from the compliance rules file."""
        try:
            rules_path = os.path.join(os.path.dirname(__file__), 'compliance_rules.json')
            empty_rules = {
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
            with open(rules_path, 'w') as f:
                json.dump(empty_rules, f, indent=4)
            self.rules = empty_rules
            print("Rules cleared successfully")
        except Exception as e:
            print(f"Error clearing rules: {str(e)}")
    
    def validate_documents(self, documents: List[Dict[str, Any]], document_type: str) -> Dict[str, Any]:
        """
        Validate multiple documents against applicable rules.
        
        Args:
            documents (List[Dict[str, Any]]): List of structured document data
            document_type (str): Type of document (invoice, purchase_order, goods_receipt)
            
        Returns:
            Dict[str, Any]: Combined validation results for all documents
        """
        all_results = []
        
        for idx, document_data in enumerate(documents, 1):
            print(f"\nValidating Document {idx}:")
            print(f"Document Data: {json.dumps(document_data, indent=2)}")
            
            document_results = self.validate_document(document_data, document_type)
            all_results.append({
                'document_index': idx,
                'document_data': document_data,
                'validation_results': document_results,
                'summary': self.get_validation_summary(document_results)
            })
        
        return {
            'total_documents': len(documents),
            'document_results': all_results,
            'overall_summary': self._get_overall_summary(all_results)
        }
    
    def _get_overall_summary(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate overall summary for multiple documents."""
        total_rules = sum(len(doc['validation_results']) for doc in all_results)
        total_passed = sum(doc['summary']['passed'] for doc in all_results)
        total_failed = sum(doc['summary']['failed'] for doc in all_results)
        total_errors = sum(doc['summary']['errors'] for doc in all_results)
        total_high_severity = sum(doc['summary']['high_severity_failures'] for doc in all_results)
        
        return {
            'total_documents': len(all_results),
            'total_rules_checked': total_rules,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_errors': total_errors,
            'total_high_severity_failures': total_high_severity,
            'timestamp': datetime.now().isoformat()
        }
    
    def validate_document(self, document_data: Dict[str, Any], document_type: str) -> List[Dict[str, Any]]:
        """
        Validate a document against all applicable rules.
        
        Args:
            document_data (Dict[str, Any]): Structured document data
            document_type (str): Type of document (invoice, purchase_order, goods_receipt)
            
        Returns:
            List[Dict[str, Any]]: List of validation results
        """
        validation_results = []
        
        for rule in self.rules.get('rules', []):
            if document_type not in rule.get('applicable_documents', []):
                continue
                
            result = self._validate_rule(rule, document_data)
            validation_results.append(result)
            
        return validation_results
    
    def _validate_rule(self, rule: Dict[str, Any], document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single rule against document data.
        
        Args:
            rule (Dict[str, Any]): Rule to validate
            document_data (Dict[str, Any]): Document data to validate against
            
        Returns:
            Dict[str, Any]: Validation result
        """
        field = rule.get('field')
        validation = rule.get('validation', {})
        validation_type = validation.get('type')
        
        if field not in document_data:
            return {
                'rule_id': rule['rule_id'],
                'name': rule['name'],
                'status': 'failed',
                'message': f"Field '{field}' not found in document",
                'severity': rule['severity'],
                'timestamp': datetime.now().isoformat()
            }
        
        value = document_data[field]
        parameters = validation.get('parameters', {})
        
        try:
            is_valid = False
            error_message = validation.get('error_message', 'Validation failed')
            
            if validation_type == 'numeric':
                is_valid = self._validate_numeric(value, parameters)
            elif validation_type == 'regex':
                is_valid = self._validate_regex(value, parameters)
            elif validation_type == 'date_comparison':
                is_valid = self._validate_date_comparison(value, parameters)
            else:
                is_valid = True  # Custom validation types are handled by the agent
                
            return {
                'rule_id': rule['rule_id'],
                'name': rule['name'],
                'status': 'passed' if is_valid else 'failed',
                'message': None if is_valid else error_message,
                'severity': rule['severity'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'rule_id': rule['rule_id'],
                'name': rule['name'],
                'status': 'error',
                'message': f"Validation error: {str(e)}",
                'severity': rule['severity'],
                'timestamp': datetime.now().isoformat()
            }
    
    def _validate_numeric(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate numeric values."""
        try:
            if not isinstance(value, (int, float, Decimal)):
                value = Decimal(str(value))
                
            data_type = parameters.get('data_type', 'decimal')
            if data_type == 'decimal':
                if 'min_value' in parameters and value < Decimal(str(parameters['min_value'])):
                    return False
                if 'max_value' in parameters and value > Decimal(str(parameters['max_value'])):
                    return False
                if 'expected_value' in parameters:
                    expected = Decimal(str(parameters['expected_value']))
                    return abs(value - expected) < Decimal('0.01')
                    
            return True
            
        except (ValueError, TypeError, ArithmeticError):
            return False
    
    def _validate_regex(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate using regex pattern."""
        try:
            if not isinstance(value, str):
                value = str(value)
                
            pattern = parameters.get('pattern', '')
            case_sensitive = parameters.get('case_sensitive', True)
            
            if not case_sensitive:
                pattern = f"(?i){pattern}"
                
            return bool(re.match(pattern, value))
            
        except (re.error, TypeError):
            return False
    
    def _validate_date_comparison(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate date comparisons."""
        try:
            if not isinstance(value, str):
                value = str(value)
                
            date_value = datetime.fromisoformat(value)
            comparison_type = parameters.get('comparison_type', 'equals')
            comparison_date = datetime.fromisoformat(parameters.get('comparison_date', ''))
            
            if comparison_type == 'equals':
                return date_value == comparison_date
            elif comparison_type == 'before':
                return date_value < comparison_date
            elif comparison_type == 'after':
                return date_value > comparison_date
            elif comparison_type == 'between':
                start_date = datetime.fromisoformat(parameters.get('start_date', ''))
                end_date = datetime.fromisoformat(parameters.get('end_date', ''))
                return start_date <= date_value <= end_date
                
            return False
            
        except (ValueError, TypeError):
            return False
    
    def get_validation_summary(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of validation results.
        
        Args:
            validation_results (List[Dict[str, Any]]): List of validation results
            
        Returns:
            Dict[str, Any]: Summary of validation results
        """
        total = len(validation_results)
        passed = sum(1 for r in validation_results if r['status'] == 'passed')
        failed = sum(1 for r in validation_results if r['status'] == 'failed')
        errors = sum(1 for r in validation_results if r['status'] == 'error')
        
        high_severity_failures = [
            r for r in validation_results 
            if r['status'] == 'failed' and r['severity'] == 'high'
        ]
        
        return {
            'total_rules': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'high_severity_failures': len(high_severity_failures),
            'timestamp': datetime.now().isoformat()
        }

