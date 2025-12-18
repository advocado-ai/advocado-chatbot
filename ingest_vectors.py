import os
import time
from pathlib import Path
from typing import List, Dict
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load env vars
if os.path.exists('.env.cloud'):
    load_dotenv('.env.cloud')
else:
    load_dotenv()

# Try to load from secrets.toml if env vars are missing
if not os.getenv("SUPABASE_URL"):
    try:
        import toml
        secrets_path = Path(".streamlit/secrets.toml")
        if secrets_path.exists():
            secrets = toml.load(secrets_path)
            os.environ["SUPABASE_URL"] = secrets.get("SUPABASE_URL", "")
            os.environ["SUPABASE_KEY"] = secrets.get("SUPABASE_KEY", "")
            print("Loaded credentials from .streamlit/secrets.toml")
    except ImportError:
        print("Warning: 'toml' package not installed. Install it to load from secrets.toml")
    except Exception as e:
        print(f"Error loading secrets.toml: {e}")

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
MODEL_NAME = 'all-MiniLM-L6-v2'
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Mappings (Same as sync_storage.py)
MAPPINGS = [
    # Example mapping: ("/local/path/to/data", "storage/prefix")
    # ("/path/to/your/data", "data/evidence")
]

def split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Simple sliding window splitter."""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)
        
        if end == text_len:
            break
            
        start += chunk_size - overlap
        
    return chunks

def ingest():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set.")
        return

    print("Initializing Supabase client...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print(f"Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    total_chunks = 0
    
    for local_dir, storage_prefix in MAPPINGS:
        base_path = Path(local_dir)
        if not base_path.exists():
            print(f"Skipping {local_dir} (not found)")
            continue
            
        print(f"Processing {local_dir}...")
        
        for file_path in base_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.md', '.txt']:
                try:
                    # Read content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if not content.strip():
                        continue
                        
                    # Create relative path for metadata
                    rel_path = file_path.relative_to(base_path)
                    storage_path = f"{storage_prefix}/{rel_path}".replace("//", "/")
                    
                    # Chunk
                    chunks = split_text(content, CHUNK_SIZE, CHUNK_OVERLAP)
                    
                    # Embed and Insert
                    records = []
                    for chunk in chunks:
                        embedding = model.encode(chunk).tolist()
                        records.append({
                            "content": chunk,
                            "metadata": {"file_path": storage_path},
                            "embedding": embedding,
                            # Add required fields for evidence_vectors table
                            "file_path": storage_path,
                            "file_name": file_path.name,
                            "chunk_index": 0, # Placeholder
                            "total_chunks": len(chunks)
                        })
                        
                    if records:
                        # Batch insert
                        try:
                            data = supabase.table("evidence_vectors").insert(records).execute()
                            total_chunks += len(records)
                            print(f"  Inserted {len(records)} chunks from {file_path.name}")
                        except Exception as e:
                            print(f"  Error inserting chunks for {file_path.name}: {e}")
                        
                except Exception as e:
                    print(f"  Error processing {file_path.name}: {e}")

    print(f"Ingestion complete. Total chunks: {total_chunks}")

if __name__ == "__main__":
    ingest()
