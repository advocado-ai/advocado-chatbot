import os
import streamlit as st
from supabase import create_client, Client
from typing import List, Dict, Any, Optional

class StorageClient:
    """
    Handles interactions with Supabase Storage for retrieving file URLs.
    """
    
    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.bucket_name = "evidence-files" # Must match the bucket created in Supabase
        self.client: Client = create_client(self.url, self.key)

    def get_signed_url(self, file_path: str, expiry_duration: int = 3600) -> Optional[str]:
        """
        Generates a signed URL for a file in Supabase Storage.
        
        Args:
            file_path: The path of the file as stored in the DB (e.g., data/harassment/...)
            expiry_duration: How long the link is valid in seconds (default 1 hour)
            
        Returns:
            Signed URL string or None if error
        """
        try:
            # The file_path in DB might be 'data/harassment/folder/file.md'
            # We need to ensure it matches how we uploaded it to Storage.
            # Assuming we upload preserving the structure under 'data/'.
            
            # Clean path if necessary (remove leading slash)
            storage_path = file_path.lstrip('/')
            
            response = self.client.storage.from_(self.bucket_name).create_signed_url(
                storage_path, 
                expiry_duration
            )
            
            # Supabase-py v2 returns a dict or object depending on version, 
            # usually {'signedURL': '...'} or an object with .signedURL
            if isinstance(response, dict):
                return response.get('signedURL')
            elif hasattr(response, 'signedURL'):
                return response.signedURL
            # Fallback for some versions might return the URL directly as string (unlikely)
            return str(response)
            
        except Exception as e:
            print(f"Error generating signed URL for {file_path}: {e}")
            return None

    def list_files(self, path: str = ""):
        """List files in the bucket (for debugging)."""
        return self.client.storage.from_(self.bucket_name).list(path)
