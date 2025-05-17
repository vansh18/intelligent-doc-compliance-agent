from typing import List, Dict, Any, Set, Optional
import re
from datetime import datetime
from difflib import SequenceMatcher
import json

class DocumentGrouper:
    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize the document grouper.
        
        Args:
            similarity_threshold (float): Threshold for considering identifiers similar (0-1)
        """
        self.similarity_threshold = similarity_threshold
        
    def extract_identifiers(self, structured_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract potential identifiers from structured document data.
        
        Args:
            structured_data (Dict[str, Any]): Structured document data
            
        Returns:
            Dict[str, str]: Dictionary of identifier types and values
        """
        identifiers = {}
        
        try:
            if "document_id" in structured_data and structured_data["document_id"]:
                identifiers["document_id"] = str(structured_data["document_id"])
                
            if "parties" in structured_data:
                parties = structured_data["parties"]
                if "sender" in parties and "name" in parties["sender"] and parties["sender"]["name"]:
                    identifiers["sender_name"] = str(parties["sender"]["name"])
                if "recipient" in parties and "name" in parties["recipient"] and parties["recipient"]["name"]:
                    identifiers["recipient_name"] = str(parties["recipient"]["name"])
                    
            if "dates" in structured_data:
                dates = structured_data["dates"]
                for date_type, date_value in dates.items():
                    if date_value:
                        identifiers[f"date_{date_type}"] = str(date_value)
        except Exception as e:
            print(f"Warning: Error extracting identifiers: {str(e)}")
            
        return identifiers
    
    def normalize_identifier(self, identifier: Optional[str]) -> str:
        """
        Normalize identifier for comparison.
        
        Args:
            identifier (Optional[str]): Identifier to normalize
            
        Returns:
            str: Normalized identifier
        """
        if identifier is None:
            return ""
            
        try:
            normalized = str(identifier).lower()
            normalized = re.sub(r'[^a-z0-9]', '', normalized)
            
            return normalized
        except Exception as e:
            print(f"Warning: Error normalizing identifier '{identifier}': {str(e)}")
            return ""
    
    def are_identifiers_similar(self, id1: Optional[str], id2: Optional[str]) -> bool:
        """
        Check if two identifiers are similar using fuzzy matching.
        
        Args:
            id1 (Optional[str]): First identifier
            id2 (Optional[str]): Second identifier
            
        Returns:
            bool: True if identifiers are similar
        """
        if id1 is None or id2 is None:
            return False
            
        norm1 = self.normalize_identifier(id1)
        norm2 = self.normalize_identifier(id2)
        
        if not norm1 or not norm2:
            return False

        try:
            similarity = SequenceMatcher(None, norm1, norm2).ratio()
            return similarity >= self.similarity_threshold
        except Exception as e:
            print(f"Warning: Error calculating similarity between '{id1}' and '{id2}': {str(e)}")
            return False
    
    def find_related_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group related documents based on their identifiers.
        
        Args:
            documents (List[Dict[str, Any]]): List of document data
            
        Returns:
            List[Dict[str, Any]]: List of documents with relationship information
        """
        try:
            doc_identifiers = []
            for doc in documents:
                try:
                    identifiers = self.extract_identifiers(doc["structured_data"])
                    doc_identifiers.append({
                        "doc_id": doc["id"],
                        "identifiers": identifiers
                    })
                except Exception as e:
                    print(f"Warning: Error processing document {doc.get('id', 'unknown')}: {str(e)}")
                    continue
            
            relationships = []
            for i, doc1 in enumerate(doc_identifiers):
                for j, doc2 in enumerate(doc_identifiers[i+1:], i+1):
                    try:
                        for id_type, id_value1 in doc1["identifiers"].items():
                            if id_type in doc2["identifiers"]:
                                id_value2 = doc2["identifiers"][id_type]
                                if self.are_identifiers_similar(id_value1, id_value2):
                                    relationships.append({
                                        "doc1_id": doc1["doc_id"],
                                        "doc2_id": doc2["doc_id"],
                                        "relationship_type": id_type,
                                        "confidence": SequenceMatcher(
                                            None,
                                            self.normalize_identifier(id_value1),
                                            self.normalize_identifier(id_value2)
                                        ).ratio()
                                    })
                    except Exception as e:
                        print(f"Warning: Error comparing documents {doc1['doc_id']} and {doc2['doc_id']}: {str(e)}")
                        continue
            
            for doc in documents:
                doc["relationships"] = [
                    rel for rel in relationships
                    if rel["doc1_id"] == doc["id"] or rel["doc2_id"] == doc["id"]
                ]
                
            return documents
        except Exception as e:
            print(f"Error in find_related_documents: {str(e)}")
            for doc in documents:
                doc["relationships"] = []
            return documents 