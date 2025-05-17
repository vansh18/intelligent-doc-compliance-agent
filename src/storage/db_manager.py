import psycopg2
from psycopg2.extras import Json
from datetime import datetime
from typing import Dict, Any, List
import os

class DatabaseManager:
    def __init__(self):
        """
        Initialize database connection using environment variables
        """
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "compliance-agent"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "Admin"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        self.create_tables()
    
    def create_tables(self):
        """
        Create necessary tables if they don't exist
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id UUID PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    document_type VARCHAR(100),
                    raw_text TEXT,
                    structured_data JSONB,
                    metadata JSONB
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_relationships (
                    id SERIAL PRIMARY KEY,
                    doc1_id UUID REFERENCES documents(id),
                    doc2_id UUID REFERENCES documents(id),
                    relationship_type VARCHAR(100),
                    confidence FLOAT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(doc1_id, doc2_id, relationship_type)
                )
            """)
            
            self.conn.commit()
    
    def save_document(self, document_id: str, raw_text: str, structured_data: Dict[str, Any]) -> str:
        """
        Save document data to PostgreSQL
        
        Args:
            document_id (str): Unique identifier for the document
            raw_text (str): Original extracted text
            structured_data (Dict[str, Any]): Structured data from Gemini
            
        Returns:
            str: Document ID
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (id, raw_text, structured_data)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (document_id, raw_text, Json(structured_data)))
            self.conn.commit()
            return document_id
    
    def save_relationships(self, relationships: List[Dict[str, Any]]):
        """
        Save document relationships to PostgreSQL
        
        Args:
            relationships (List[Dict[str, Any]]): List of relationship data
        """
        with self.conn.cursor() as cur:
            for rel in relationships:
                cur.execute("""
                    INSERT INTO document_relationships 
                    (doc1_id, doc2_id, relationship_type, confidence)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (doc1_id, doc2_id, relationship_type) 
                    DO UPDATE SET confidence = EXCLUDED.confidence
                """, (
                    rel["doc1_id"],
                    rel["doc2_id"],
                    rel["relationship_type"],
                    rel["confidence"]
                ))
            self.conn.commit()
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieve a document by its ID
        
        Args:
            document_id (str): Document identifier
            
        Returns:
            Dict[str, Any]: Document data
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, created_at, raw_text, structured_data
                FROM documents
                WHERE id = %s
            """, (document_id,))
            result = cur.fetchone()
            
            if not result:
                raise FileNotFoundError(f"No document found with ID: {document_id}")

            cur.execute("""
                SELECT doc1_id, doc2_id, relationship_type, confidence
                FROM document_relationships
                WHERE doc1_id = %s OR doc2_id = %s
            """, (document_id, document_id))
            relationships = cur.fetchall()
            
            return {
                "id": result[0],
                "created_at": result[1],
                "raw_text": result[2],
                "structured_data": result[3],
                "relationships": [
                    {
                        "doc1_id": rel[0],
                        "doc2_id": rel[1],
                        "relationship_type": rel[2],
                        "confidence": rel[3]
                    }
                    for rel in relationships
                ]
            }
    
    def get_related_documents(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents related to a given document
        
        Args:
            document_id (str): Document identifier
            
        Returns:
            List[Dict[str, Any]]: List of related documents
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT 
                    CASE 
                        WHEN doc1_id = %s THEN doc2_id
                        ELSE doc1_id
                    END as related_doc_id
                FROM document_relationships
                WHERE doc1_id = %s OR doc2_id = %s
            """, (document_id, document_id, document_id))
            related_ids = [row[0] for row in cur.fetchall()]
            
            if not related_ids:
                return []
            
            cur.execute("""
                SELECT id, created_at, raw_text, structured_data
                FROM documents
                WHERE id = ANY(%s)
            """, (related_ids,))
            
            return [
                {
                    "id": row[0],
                    "created_at": row[1],
                    "raw_text": row[2],
                    "structured_data": row[3]
                }
                for row in cur.fetchall()
            ]
    
    def close(self):
        """
        Close the database connection
        """
        self.conn.close() 