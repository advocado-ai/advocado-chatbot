-- Schema definition for evidence_vectors table
-- Based on usage in ingest_vectors.py and rag_engine.py

create table if not exists evidence_vectors (
  id bigserial primary key,
  content text,
  file_path text,
  folder text,
  document_type text,
  google_drive_link text,
  embedding vector(768),  -- E5-Base multilingual model
  created_at timestamptz default now()
);

-- Indexes for faster filtering
create index if not exists idx_evidence_vectors_folder on evidence_vectors(folder);
create index if not exists idx_evidence_vectors_document_type on evidence_vectors(document_type);
