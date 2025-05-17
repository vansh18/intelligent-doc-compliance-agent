import json
import os
from datetime import datetime
from typing import Dict, Any

class DocumentStore:
    def __init__(self, storage_dir: str = "storage"):
        """
        Initialize the document store.
        
        Args:
            storage_dir (str): Directory where documents will be stored
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_document(self, document_id: str, structured_data: Dict[str, Any]) -> str:
        """
        Save the structured document data to storage.
        
        Args:
            document_id (str): Unique identifier for the document
            structured_data (Dict[str, Any]): Structured document data
            
        Returns:
            str: Path to the saved document
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{document_id}_{timestamp}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
            
        return filepath
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieve a stored document by its ID.
        
        Args:
            document_id (str): Document identifier
            
        Returns:
            Dict[str, Any]: Stored document data
        """

        files = [f for f in os.listdir(self.storage_dir) if f.startswith(document_id)]
        if not files:
            raise FileNotFoundError(f"No document found with ID: {document_id}")
            
        latest_file = sorted(files)[-1]
        filepath = os.path.join(self.storage_dir, latest_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f) 