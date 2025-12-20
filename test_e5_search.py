"""
Test E5-Base embedding search against Supabase.
This verifies the model is working and can find the Dec 18, 2025 meeting documents.
"""

from sentence_transformers import SentenceTransformer
from supabase import create_client
import os
from dotenv import load_dotenv

# Load env
if os.path.exists('.streamlit/secrets.toml'):
    import toml
    secrets = toml.load('.streamlit/secrets.toml')
    supabase_url = secrets["SUPABASE_URL"]
    supabase_key = secrets["SUPABASE_KEY"]
else:
    load_dotenv('.env.cloud')
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

# Initialize
model = SentenceTransformer('intfloat/multilingual-e5-base')
supabase = create_client(supabase_url, supabase_key)

# Test query (same as the chatbot received)
query = "what happened on December 18, 2025?"

# Generate embedding with E5 prefix
embedding = model.encode(f"query: {query}").tolist()

print(f"Query: {query}")
print(f"Embedding dims: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")

# Call the database function
response = supabase.rpc('match_evidence_vectors_v2', {
    'query_embedding': embedding,
    'match_threshold': 0.3,
    'match_count': 10,
    'filter_document_type': None,
    'filter_folders': None
}).execute()

print(f"\nFound {len(response.data)} results:")
for i, doc in enumerate(response.data[:5]):
    print(f"\n{i+1}. {doc['file_path']}")
    print(f"   Similarity: {doc['similarity']:.3f}")
    print(f"   Preview: {doc['content'][:100]}...")
