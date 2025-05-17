import psycopg2
from psycopg2.extras import Json
from datetime import datetime
from typing import Dict, Any
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
            
            return {
                "id": result[0],
                "created_at": result[1],
                "raw_text": result[2],
                "structured_data": result[3]
            }
    
    def close(self):
        """
        Close the database connection
        """
        self.conn.close() 