-- Update the RPC function to support folder filtering
create or replace function match_evidence_vectors (
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  filter_document_type text default null,
  filter_folder text default null
)
returns table (
  id bigint,
  content text,
  file_path text,
  file_name text,
  folder text,
  document_type text,
  chunk_index int,
  total_chunks int,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    evidence_vectors.id,
    evidence_vectors.content,
    evidence_vectors.file_path,
    evidence_vectors.file_name,
    evidence_vectors.folder,
    evidence_vectors.document_type,
    evidence_vectors.chunk_index,
    evidence_vectors.total_chunks,
    evidence_vectors.metadata,
    1 - (evidence_vectors.embedding <=> query_embedding) as similarity
  from evidence_vectors
  where 1 - (evidence_vectors.embedding <=> query_embedding) > match_threshold
  and (filter_document_type is null or evidence_vectors.document_type = filter_document_type)
  and (filter_folder is null or evidence_vectors.folder ilike filter_folder || '%')
  order by evidence_vectors.embedding <=> query_embedding
  limit match_count;
end;
$$;
