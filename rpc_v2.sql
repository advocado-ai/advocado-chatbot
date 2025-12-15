create or replace function match_evidence_vectors_v2 (
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  filter_document_type text default null,
  filter_folders text[] default null
)
returns table (
  id bigint,
  content text,
  file_path text,
  folder text,
  document_type text,
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
    evidence_vectors.folder,
    evidence_vectors.document_type,
    1 - (evidence_vectors.embedding <=> query_embedding) as similarity
  from evidence_vectors
  where 1 - (evidence_vectors.embedding <=> query_embedding) > match_threshold
  and (filter_document_type is null or evidence_vectors.document_type = filter_document_type)
  and (filter_folders is null or evidence_vectors.folder = any(filter_folders))
  order by evidence_vectors.embedding <=> query_embedding
  limit match_count;
end;
$$;