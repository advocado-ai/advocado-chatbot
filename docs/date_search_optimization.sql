-- Function to match documents by date_prefix
-- This is used when the LLM extracts a specific date from the query.
-- It provides a hard filter on the date_prefix column.

create or replace function match_documents_by_date (
  filter_date text,
  match_count int
)
returns table (
  id bigint,
  content text,
  file_path text,
  similarity real,
  google_drive_link text
)
language plpgsql
as $$
begin
  return query
  select
    v.id,
    v.content,
    v.file_path,
    -- Assign high similarity score (2.0) to prioritize date matches over vector/keyword matches
    2.0::real as similarity,
    v.google_drive_link
  from evidence_vectors v
  where v.date_prefix = filter_date::date
  -- Order by content length to prefer longer analysis documents over short chat logs
  order by length(v.content) desc
  limit match_count;
end;
$$;
