import os
import streamlit as st
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class RAGEngine:
    """
    Handles Retrieval Augmented Generation tasks:
    1. Generating embeddings for queries.
    2. Searching Supabase vector database.
    """
    
    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.client: Client = create_client(self.url, self.key)
        
        # Load model - using cache to avoid re-downloading on every run
        # @st.cache_resource ensures this is loaded only once per session
        self.model = self._load_model()

    @st.cache_resource
    def _load_model(_self):
        """Load the sentence transformer model."""
        # Using the same model as ingestion to ensure compatibility
        return SentenceTransformer('all-MiniLM-L6-v2')

    def search(self, query: str, match_count: int = 10, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Search the vector database for relevant chunks.
        """
        # 1. Generate embedding
        query_embedding = self.model.encode(query).tolist()
        
        # 2. Query Supabase
        params = {
            'query_embedding': query_embedding,
            'match_threshold': threshold,
            'match_count': match_count,
            'filter_document_type': None,
            'filter_folder': None
        }
        
        try:
            # Call the RPC function we created earlier
            response = self.client.rpc('match_evidence_vectors', params).execute()
            return response.data
        except Exception as e:
            st.error(f"Database search error: {e}")
            return []
