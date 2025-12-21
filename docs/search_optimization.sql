-- 1. Drop old function
drop function if exists kw_match_documents(text, int);

-- 2. Create optimized function
create or replace function kw_match_documents (
  query_text text,
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
    -- Force 1.0 score so these results aren't penalized by the aggregator
    1.0::real as similarity,
    v.google_drive_link
  from evidence_vectors v
  join (
    select distinct kw 
    from unnest(string_to_array(query_text, ' ')) as kw 
    where length(kw) > 1
  ) k on v.content ILIKE '%' || k.kw || '%'
  group by v.id, v.content, v.file_path, v.google_drive_link
  -- Rank by:
  -- 1. Number of matching keywords (more matches = better)
  -- 2. Document length (Longer analysis docs > Short chat logs)
  order by count(*) desc, length(v.content) desc
  limit match_count;
end;
$$;
