import os
import streamlit as st
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging

# Configure debug mode - only activates in local development
DEBUG_MODE = os.getenv('STREAMLIT_ENV') != 'cloud'  # True locally, False on Streamlit Cloud

if DEBUG_MODE:
    logging.basicConfig(
        level=logging.DEBUG,
        format='🔍 [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)

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
        # Using E5-Base multilingual model (768 dimensions)
        # Supports excellent multilingual retrieval for Japanese/English
        return SentenceTransformer('intfloat/multilingual-e5-base')

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
        # 1. Generate embedding (temporarily without prefix to match database)
        # TODO: Add "query: " prefix back after re-ingesting DB with "passage: " prefix
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

    def aggregate_by_document(self, chunks: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Aggregate chunks by document and re-rank using Multi-Chunk Boosting.
        Documents with multiple high-scoring chunks are rewarded, but normalized by sqrt(N) 
        to prevent very long documents from dominating.
        
        Args:
            chunks: List of chunk results from vector search
            top_k: Number of top documents to return
            
        Returns:
            List of top documents with their best chunk as representative,
            enriched with doc_score and chunk_count metadata
        """
        import math
        from collections import defaultdict
        
        logger.debug(f"Aggregating {len(chunks)} chunks by document...")
        doc_chunks = defaultdict(list)
        
        # Group chunks by document
        for chunk in chunks:
            file_path = chunk['file_path']
            doc_chunks[file_path].append(chunk)
        
        logger.debug(f"  → Grouped into {len(doc_chunks)} unique documents")
        
        # Calculate document scores using Multi-Chunk Boosting
        doc_scores = []
        for file_path, chunks_list in doc_chunks.items():
            # Sum similarities and normalize by sqrt(count)
            # This rewards multi-chunk docs without over-boosting very long docs
            similarities = [c['similarity'] for c in chunks_list]
            doc_score = sum(similarities) / math.sqrt(len(similarities))
            
            # Keep the highest-scoring chunk as representative
            best_chunk = max(chunks_list, key=lambda x: x['similarity'])
            
            # Enrich with aggregation metadata
            best_chunk['doc_score'] = doc_score
            best_chunk['chunk_count'] = len(chunks_list)
            
            doc_scores.append(best_chunk)
        
        # Sort by document score (descending)
        doc_scores.sort(key=lambda x: x['doc_score'], reverse=True)
        
        return doc_scores[:top_k]

    def search_multilingual(self, queries: Dict[str, str], match_count: int = 10, threshold: float = 0.3, folder_filters: List[str] = None) -> List[Dict[str, Any]]:
        """
        Executes parallel searches for multiple query variants and aggregates results using RRF.
        Then applies document-level aggregation to surface comprehensive multi-chunk documents.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Retrieve MORE chunks initially for better document-level aggregation
        # We'll retrieve 5x the requested amount, then aggregate and return top match_count
        initial_match_count = match_count * 5  # e.g., 50 if user wants 10
        
        logger.info(f"Starting multilingual search: {len(queries)} variants, retrieving {initial_match_count} chunks each")
        
        # Helper function for a single search
        def _single_search(query_text, query_type):
            if not query_text:
                return query_type, []
            # Use expanded retrieval for better recall
            logger.debug(f"Searching variant '{query_type}': {query_text}")
            results = self.search(query_text, initial_match_count, threshold, folder_filters=folder_filters)
            logger.debug(f"  → Found {len(results)} results for '{query_type}'")
            return query_type, results

        # Run searches in parallel
        search_results_map = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_query = {
                executor.submit(_single_search, q_text, q_type): q_type 
                for q_type, q_text in queries.items()
            }
            
            for future in as_completed(future_to_query):
                try:
                    q_type, results = future.result()
                    search_results_map[q_type] = results
                except Exception as e:
                    print(f"Search error for {future_to_query[future]}: {e}")

        # Aggregate results using Reciprocal Rank Fusion (RRF)
        # RRF score = 1 / (k + rank)
        logger.info(f"Applying RRF aggregation across {len(search_results_map)} query variants")
        k = 60
        doc_scores = {}
        doc_data = {}
        
        for q_type, results in search_results_map.items():
            for rank, doc in enumerate(results):
                doc_id = doc['id']
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = 0
                    doc_data[doc_id] = doc
                    doc_data[doc_id]['found_by_methods'] = set()
                
                doc_scores[doc_id] += 1 / (k + rank + 1)
                doc_data[doc_id]['found_by_methods'].add(q_type)
        
        logger.info(f"RRF aggregation: {len(doc_scores)} unique chunks found")

        # Sort by RRF score
        sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)
        
        # Get more results for document-level aggregation
        # We want ~5x match_count for good aggregation (e.g., 50 chunks for 10 results)
        rrf_results = []
        for doc_id in sorted_ids[:initial_match_count]:
            doc = doc_data[doc_id]
            # Convert set to list for JSON serialization/display
            doc['found_by_methods'] = list(doc['found_by_methods'])
            rrf_results.append(doc)
        
        logger.info(f"Top {len(rrf_results)} RRF chunks ready for document aggregation")
        
        # Apply document-level aggregation to surface multi-chunk documents
        final_results = self.aggregate_by_document(rrf_results, match_count)
        
        if DEBUG_MODE:
            logger.info("\n" + "="*60)
            logger.info(f"📊 FINAL TOP {len(final_results)} DOCUMENTS (after aggregation):")
            logger.info("="*60)
            for i, doc in enumerate(final_results, 1):
                file_name = doc['file_path'].split('/')[-1]
                chunk_count = doc.get('chunk_count', 1)
                doc_score = doc.get('doc_score', doc.get('similarity', 0))
                methods = doc.get('found_by_methods', [])
                logger.info(f"{i:2d}. {file_name[:50]:50s} score={doc_score:.4f} chunks={chunk_count} methods={methods}")
            logger.info("="*60 + "\n")
            
        return final_results
