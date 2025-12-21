-- Create HNSW index for fast vector similarity search
-- This is critical for performance with 20K+ vectors

CREATE INDEX IF NOT EXISTS evidence_vectors_embedding_idx 
ON evidence_vectors 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Note: This will take a few minutes to build on 21K vectors
-- but subsequent searches will be 100-1000x faster
