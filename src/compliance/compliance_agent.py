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
    
    def validate_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate multiple documents against applicable rules.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents to validate, each containing:
                - document_type: Type of document (invoice, purchase_order, goods_receipt)
                - extracted_fields: Dictionary of extracted fields
                - vendor_info: Dictionary of vendor information
                - metadata: Dictionary of document metadata
            
        Returns:
            Dict[str, Any]: Validation results for all documents
        """
        print(f"\n[DEBUG] Starting validation of {len(documents)} documents")
        print(f"[DEBUG] Available rules: {len(self.rules.get('rules', []))}")
        
        all_results = []
        processed_docs = []
        
        for idx, doc in enumerate(documents, 1):
            print(f"\n[DEBUG] Processing document {idx}")
            document_type = doc.get('document_type')
            if not document_type:
                print(f"[DEBUG] Warning: Document {idx} missing document_type")
                continue
                
            print(f"[DEBUG] Document type: {document_type}")
            
            document_data = {
                **doc.get('extracted_fields', {}),
                'vendor_name': doc.get('vendor_info', {}).get('name'),
                'vendor_address': doc.get('vendor_info', {}).get('address', {}),
                'vendor_contact': doc.get('vendor_info', {}).get('contact', {})
            }
            
            print(f"[DEBUG] Document data fields: {list(document_data.keys())}")
            
            validation_results = []
            applicable_rules = [r for r in self.rules.get('rules', []) 
                              if document_type in r.get('applicable_documents', [])]
            
            print(f"[DEBUG] Found {len(applicable_rules)} applicable rules for {document_type}")
            
            for rule in applicable_rules:
                print(f"\n[DEBUG] Validating rule: {rule.get('rule_id')} - {rule.get('name')}")
                if rule.get('validation', {}).get('type') == 'cross_document_consistency':
                    is_valid, message = self._validate_cross_document_consistency(rule, document_data, processed_docs)
                    result = {
                        'rule_id': rule['rule_id'],
                        'name': rule['name'],
                        'status': 'passed' if is_valid else 'failed',
                        'message': message,
                        'severity': rule['severity'],
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    result = self._validate_rule(rule, document_data)
                print(f"[DEBUG] Rule validation result: {result['status']}")
                validation_results.append(result)
            
            processed_docs.append({
                'document_type': document_type,
                'document_data': document_data,
                'status': 'processed'
            })
            
            summary = self.get_validation_summary(validation_results)
            print(f"[DEBUG] Document summary: {summary}")

            all_results.append({
                'document_index': idx,
                'document_type': document_type,
                'document_data': document_data,
                'validation_results': validation_results,
                'summary': summary
            })
        
        overall_summary = self._get_overall_summary(all_results)
        print(f"\n[DEBUG] Overall summary: {overall_summary}")
        
        return {
            'total_documents': len(documents),
            'document_results': all_results,
            'overall_summary': overall_summary
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
                return {
                    'rule_id': rule['rule_id'],
                    'name': rule['name'],
                    'status': 'error',
                    'message': f"Unknown validation type: {validation_type}",
                    'severity': rule['severity'],
                    'timestamp': datetime.now().isoformat()
                }
                
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
            if isinstance(value, str):
                value = value.replace(',', '')
                
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

    def _validate_cross_document_consistency(self, rule: Dict[str, Any], current_doc: Dict[str, Any], processed_docs: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate consistency of a field across multiple documents.
        
        Args:
            rule (Dict[str, Any]): The rule to validate against
            current_doc (Dict[str, Any]): Current document being validated
            processed_docs (List[Dict[str, Any]]): List of previously processed documents
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            field = rule['field']
            validation = rule['validation']
            validation_type = validation.get('type', 'exact_match')
            
            # Get current document's value
            current_value = current_doc.get(field)
            if current_value is None:
                return False, f"Field '{field}' not found in current document"
            
            # For string values, normalize them
            if isinstance(current_value, str):
                current_value = current_value.strip().lower()
            
            # Find matching documents
            matching_docs = []
            for doc in processed_docs:
                if doc.get('status') == 'pending':
                    continue
                    
                doc_value = doc.get(field)
                if doc_value is None:
                    continue
                    
                # Normalize string values
                if isinstance(doc_value, str):
                    doc_value = doc_value.strip().lower()
                
                matching_docs.append((doc, doc_value))
            
            if not matching_docs:
                return True, ""  # No previous documents to compare against
            
            # Validate based on type
            if validation_type == 'exact_match':
                # For strings, do case-insensitive comparison
                if isinstance(current_value, str):
                    for doc, value in matching_docs:
                        if current_value != value:
                            return False, f"Value '{current_doc.get(field)}' does not match previous document value '{doc.get(field)}' (case-insensitive comparison)"
                else:
                    for doc, value in matching_docs:
                        if current_value != value:
                            return False, f"Value '{current_value}' does not match previous document value '{value}'"
                            
            elif validation_type == 'numeric_consistency':
                try:
                    current_decimal = self._convert_to_decimal(current_value)
                    tolerance = Decimal(str(validation.get('tolerance', 0.01)))
                    
                    for doc, value in matching_docs:
                        try:
                            doc_decimal = self._convert_to_decimal(value)
                            if abs(current_decimal - doc_decimal) > tolerance:
                                return False, f"Value '{current_value}' differs from previous document value '{value}' by more than {tolerance}"
                        except (ValueError, TypeError):
                            continue
                            
                except (ValueError, TypeError):
                    return False, f"Value '{current_value}' is not a valid number"
                    
            elif validation_type == 'date_consistency':
                try:
                    current_date = self._parse_date(current_value)
                    allowed_days = int(validation.get('allowed_days', 1))
                    
                    for doc, value in matching_docs:
                        try:
                            doc_date = self._parse_date(value)
                            if abs((current_date - doc_date).days) > allowed_days:
                                return False, f"Date '{current_value}' differs from previous document date '{value}' by more than {allowed_days} days"
                        except (ValueError, TypeError):
                            continue
                            
                except (ValueError, TypeError):
                    return False, f"Value '{current_value}' is not a valid date"
            
            return True, ""
            
        except Exception as e:
            print(f"[DEBUG] Error in cross-document validation: {str(e)}")
            return False, f"Error in cross-document validation: {str(e)}"
    
    def _convert_to_decimal(self, value: Any) -> Decimal:
        """Convert a value to Decimal, handling currency strings."""
        try:
            if isinstance(value, str):
                value = value.replace(',', '')
            return Decimal(str(value))
        except (ValueError, TypeError):
            raise ValueError(f"Could not convert value '{value}' to decimal")

