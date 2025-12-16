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

    def get_available_folders(self) -> List[str]:
        """
        Fetches unique folder paths from the database for filtering.
        """
        try:
            # Fetch distinct folders
            # Note: Supabase JS client doesn't support .distinct() directly on select easily without a view or RPC
            # But we can fetch 'folder' column and deduplicate in python for now if dataset is small (<10k rows)
            # Or use a simple RPC if we had one.
            # Let's try fetching all folders (lightweight string) and set() them.
            
            response = self.client.table('evidence_vectors').select('folder').execute()
            if response.data:
                folders = sorted(list(set(item['folder'] for item in response.data if item['folder'])))
                return folders
            return []
        except Exception as e:
            st.error(f"Error fetching folders: {e}")
            return []

    def search(self, query: str, match_count: int = 10, threshold: float = 0.3, folder_filter: str = None, folder_filters: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search the vector database for relevant chunks.
        """
        # 1. Generate embedding
        query_embedding = self.model.encode(query).tolist()
        
        # 2. Query Supabase
        if folder_filters:
            # Use V2 RPC that supports array filtering
            params = {
                'query_embedding': query_embedding,
                'match_threshold': threshold,
                'match_count': match_count,
                'filter_document_type': None,
                'filter_folders': folder_filters
            }
            rpc_name = 'match_evidence_vectors_v2'
        else:
            # Fallback to V1 for single folder or no filter (backward compatibility)
            params = {
                'query_embedding': query_embedding,
                'match_threshold': threshold,
                'match_count': match_count,
                'filter_document_type': None,
                'filter_folder': folder_filter
            }
            rpc_name = 'match_evidence_vectors'
        
        try:
            # Call the RPC function
            response = self.client.rpc(rpc_name, params).execute()
            results = response.data
            
            if not results:
                return []

            # 3. Fetch Google Drive links for these results
            # If using V2, the link is already in the response (if we updated the RPC)
            # But to be safe and backward compatible, we check if it's missing
            
            # Check if google_drive_link is missing in the first result
            if results and 'google_drive_link' not in results[0]:
                ids = [r['id'] for r in results]
                try:
                    link_response = self.client.table('evidence_vectors') \
                        .select('id, google_drive_link') \
                        .in_('id', ids) \
                        .execute()
                    
                    # Create a map of id -> link
                    link_map = {item['id']: item.get('google_drive_link') for item in link_response.data}
                    
                    # Merge into results
                    for r in results:
                        r['google_drive_link'] = link_map.get(r['id'])
                        
                except Exception as e:
                    print(f"Error fetching Google Drive links: {e}")
                    # Continue without links if this fails
                
            return results
        except Exception as e:
            st.error(f"Database search error: {e}")
            return []

    def find_similar(self, document_id: int, match_count: int = 5) -> List[Dict[str, Any]]:
        """
        Find documents similar to an existing document ID.
        """
        try:
            # 1. Get the embedding of the source document
            # We select the embedding column for the specific row
            response = self.client.table('evidence_vectors') \
                .select('embedding') \
                .eq('id', document_id) \
                .execute()
            
            if not response.data:
                st.error(f"Document ID {document_id} not found.")
                return []
                
            embedding = response.data[0]['embedding']
            
            # 2. Search using that embedding
            # We reuse the existing RPC function
            params = {
                'query_embedding': embedding,
                'match_threshold': 0.5, # Higher threshold for "more like this"
                'match_count': match_count,
                'filter_document_type': None,
                'filter_folder': None
            }
            
            rpc_response = self.client.rpc('match_evidence_vectors', params).execute()
            
            # Filter out the document itself (RPC might return it as 1.0 match)
            results = [r for r in rpc_response.data if r['id'] != document_id]
            
            if not results:
                return []

            # Fetch Google Drive links
            ids = [r['id'] for r in results]
            try:
                link_response = self.client.table('evidence_vectors') \
                    .select('id, google_drive_link') \
                    .in_('id', ids) \
                    .execute()
                link_map = {item['id']: item.get('google_drive_link') for item in link_response.data}
                for r in results:
                    r['google_drive_link'] = link_map.get(r['id'])
            except Exception as e:
                print(f"Error fetching Google Drive links: {e}")

            return results
            
        except Exception as e:
            st.error(f"Find similar error: {e}")
            return []
