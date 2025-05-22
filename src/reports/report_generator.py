import os
from datetime import datetime
from typing import Dict, Any, List

class ComplianceReportGenerator:
    def __init__(self):
        """Initialize the compliance report generator."""
        self.css = """
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .summary { background: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin: 20px 0; }
        .document { background: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin: 20px 0; }
        .rule { padding: 10px; margin: 10px 0; border-left: 4px solid #ccc; }
        .rule.passed { border-left-color: #28a745; background: #d4edda; }
        .rule.failed { border-left-color: #dc3545; background: #f8d7da; }
        .rule.error { border-left-color: #ffc107; background: #fff3cd; }
        .status { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; }
        .status.passed { background: #28a745; }
        .status.failed { background: #dc3545; }
        .status.error { background: #ffc107; color: black; }
        .data { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        """

    def _format_document_section(self, doc: Dict[str, Any], index: int) -> str:
        """Format a single document section."""
        doc_type = doc.get('document_type', 'Unknown')
        summary = doc.get('summary', {})
        
        if summary.get('failed', 0) > 0:
            status = 'failed'
        elif summary.get('errors', 0) > 0:
            status = 'error'
        else:
            status = 'passed'
        
        data_html = []
        for key, value in doc.get('document_data', {}).items():
            data_html.append(f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>")
        
        rules_html = []
        for rule in doc.get('validation_results', []):
            rule_status = rule.get('status', 'unknown')
            rules_html.append(f"""
                <div class="rule {rule_status}">
                    <div class="status {rule_status}">{rule_status.upper()}</div>
                    <h4>{rule.get('name', 'Unknown Rule')}</h4>
                    <p><strong>Field:</strong> {rule.get('field', 'Unknown')}</p>
                    <p><strong>Message:</strong> {rule.get('message', 'No message')}</p>
                </div>
            """)
        
        return f"""
            <div class="document">
                <h3>Document {index}: {doc_type}</h3>
                <div class="status {status}">{status.upper()}</div>
                
                <div class="data">
                    <table>
                        {"".join(data_html)}
                    </table>
                </div>
                
                <h4>Validation Results</h4>
                {"".join(rules_html)}
                
                <div class="summary">
                    <p><strong>Total Rules:</strong> {summary.get('total_rules', 0)}</p>
                    <p><strong>Passed:</strong> {summary.get('passed', 0)}</p>
                    <p><strong>Failed:</strong> {summary.get('failed', 0)}</p>
                    <p><strong>Errors:</strong> {summary.get('errors', 0)}</p>
                </div>
            </div>
        """

    def generate_report(self, validation_results: Dict[str, Any]) -> str:
        """
        Generate a compliance validation report.
        
        Args:
            validation_results (Dict[str, Any]): Validation results from ComplianceAgent
            
        Returns:
            str: HTML report
        """
        
        documents = validation_results.get('document_results', [])
        
        total_docs = len(documents)
        passed_docs = sum(1 for doc in documents if doc.get('summary', {}).get('failed', 0) == 0)
        failed_docs = sum(1 for doc in documents if doc.get('summary', {}).get('failed', 0) > 0)
        error_docs = sum(1 for doc in documents if doc.get('summary', {}).get('errors', 0) > 0)
        total_rules = sum(len(doc.get('validation_results', [])) for doc in documents)
        
        
        document_sections = []
        for i, doc in enumerate(documents, 1):
            document_sections.append(self._format_document_section(doc, i))

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Compliance Validation Report</title>
            <style>{self.css}</style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Compliance Validation Report</h1>
                    <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
                
                <div class="summary">
                    <h2>Overall Summary</h2>
                    <p><strong>Total Documents:</strong> {total_docs}</p>
                    <p><strong>Total Rules Applied:</strong> {total_rules}</p>
                    <p><strong>Documents Passed:</strong> {passed_docs}</p>
                    <p><strong>Documents Failed:</strong> {failed_docs}</p>
                    <p><strong>Documents with Errors:</strong> {error_docs}</p>
                </div>
                
                {"".join(document_sections)}
            </div>
        </body>
        </html>
        """
        
        return html
