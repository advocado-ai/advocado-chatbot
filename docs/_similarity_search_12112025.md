# Vector Similarity Search Guide for Evidence Database

## Overview
This document describes how to perform vector similarity searches on the `evidence_vectors` table using two methods:
1. **MCP Supabase Tool** (SQL-based) - For finding similar existing documents
2. **Python Script** (test_search.py) - For arbitrary text queries

---

## Method 1: MCP Supabase Tool (SQL Direct)

### Use Case
When you want to find documents similar to an **existing document** in the database ("find more like this").

### Requirements
- You need an existing document ID from the `evidence_vectors` table
- Uses PostgreSQL's `<=>` cosine distance operator
- Executes via `mcp_supabase-clou_execute_sql` tool

### SQL Query Pattern

```sql
-- Find documents similar to document ID 48258
WITH query_vector AS (
    SELECT embedding FROM evidence_vectors WHERE id = 48258
)
SELECT ev.id, ev.content, ev.file_path,
       1 - (ev.embedding <=> qv.embedding) as similarity
FROM evidence_vectors ev, query_vector qv
WHERE ev.id != 48258  -- Exclude the query document itself
ORDER BY ev.embedding <=> qv.embedding
LIMIT 20;
```

### Key SQL Operators
- `<=>` : Cosine distance (pgvector extension)
- `1 - (embedding <=> query)` : Converts distance to similarity score (0-1)
- Lower distance = higher similarity

### Example with Context

```sql
-- Find evidence similar to "100m in 5 seconds" recognition evidence
WITH query_vector AS (
    SELECT embedding 
    FROM evidence_vectors 
    WHERE content ILIKE '%100m in 5 seconds%'
    LIMIT 1
)
SELECT ev.id, 
       ev.file_path,
       SUBSTRING(ev.content, 1, 150) as snippet,
       1 - (ev.embedding <=> qv.embedding) as similarity
FROM evidence_vectors ev, query_vector qv
ORDER BY ev.embedding <=> qv.embedding
LIMIT 10;
```

---

## Method 2: Python Script (test_search.py)

### Use Case
When you want to search for **arbitrary text queries** that may not exist in the database.

### Requirements
- Generates new embeddings for text queries on-the-fly
- Uses sentence-transformers model
- Requires `advocado-env` conda environment

### Script Location
```
/media/syslogd/ENCRYPTED-DATA/UserFiles/ADMIN-PC/n/Documents/my_projects/harassment/_supabase_mcp/_similarity_search/test_search.py
```

### Usage

```bash
# Activate conda environment first
conda activate advocado-env

# Run search script
cd /media/syslogd/ENCRYPTED-DATA/UserFiles/ADMIN-PC/n/Documents/my_projects/harassment/_supabase_mcp/_similarity_search
python test_search.py
```

### How It Works

1. **Generate Embedding**: Creates vector for your text query using sentence-transformers
2. **Query Supabase**: Calls `match_evidence_vectors()` RPC function
3. **Returns Results**: Top N most similar documents with similarity scores

### Script Features
- Batch searches multiple queries
- Shows similarity scores (0.0 - 1.0)
- Displays snippets of matching content
- Configurable match count and threshold

---

## Comparison: When to Use Which Method

| Feature | MCP/SQL Method | Python Script |
|---------|----------------|---------------|
| **Query Type** | Existing document ID | Arbitrary text |
| **Speed** | Very fast (server-side) | Slower (embedding generation) |
| **Use Case** | "Find more like this doc" | "Find docs about X" |
| **Environment** | VS Code / MCP tool | Terminal / Python |
| **Dependencies** | None (SQL only) | sentence-transformers model |

---

## Database Schema

### Table: `evidence_vectors`

```sql
CREATE TABLE evidence_vectors (
    id BIGINT PRIMARY KEY,
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384),  -- Sentence-transformer dimension
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index
CREATE INDEX ON evidence_vectors 
USING ivfflat (embedding vector_cosine_ops);
```

### RPC Function: `match_evidence_vectors`

```sql
CREATE OR REPLACE FUNCTION match_evidence_vectors(
    query_embedding VECTOR(384),
    match_threshold FLOAT DEFAULT 0.0,
    match_count INT DEFAULT 20
)
RETURNS TABLE (
    id BIGINT,
    file_path TEXT,
    content TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ev.id,
        ev.file_path,
        ev.content,
        1 - (ev.embedding <=> query_embedding) as similarity
    FROM evidence_vectors ev
    WHERE 1 - (ev.embedding <=> query_embedding) >= match_threshold
    ORDER BY ev.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

---

## Example Workflows

### Workflow 1: Explore Related Evidence (MCP/SQL)

**Scenario**: Found interesting document, want to find related evidence

```sql
-- Step 1: Find document ID
SELECT id, SUBSTRING(content, 1, 100) as preview
FROM evidence_vectors
WHERE content ILIKE '%wish there were 3 more Employees%'
LIMIT 5;

-- Step 2: Use that ID to find similar documents
WITH query_vector AS (
    SELECT embedding FROM evidence_vectors WHERE id = <found_id>
)
SELECT ev.id, ev.file_path,
       SUBSTRING(ev.content, 1, 150) as snippet,
       1 - (ev.embedding <=> qv.embedding) as similarity
FROM evidence_vectors ev, query_vector qv
WHERE ev.id != <found_id>
ORDER BY ev.embedding <=> qv.embedding
LIMIT 15;
```

### Workflow 2: Fact-Check New Text (Python)

**Scenario**: Writing document, need to verify claims against evidence

```python
# Edit test_search.py queries list:
queries = [
    "Fukushi Jun quit on Q2 kickoff day",
    "Inari Mikio demoted in June 2025",
    "100m in 5 seconds recognition"
]

# Run script
python test_search.py
```

### Workflow 3: Cross-Reference Evidence Categories (SQL)

**Scenario**: Find overlap between recognition evidence and retaliation evidence

```sql
-- Find documents mentioning both themes
WITH recognition_docs AS (
    SELECT id, embedding FROM evidence_vectors
    WHERE content ILIKE '%100m in 5 seconds%' OR 
          content ILIKE '%wish there were 3 more%'
    LIMIT 1
)
SELECT ev.id, ev.file_path,
       SUBSTRING(ev.content, 1, 200) as snippet,
       1 - (ev.embedding <=> rd.embedding) as similarity
FROM evidence_vectors ev, recognition_docs rd
WHERE ev.content ILIKE '%retaliation%' 
   OR ev.content ILIKE '%access revoked%'
ORDER BY ev.embedding <=> rd.embedding
LIMIT 10;
```

---

## Performance Notes

### MCP/SQL Method
- **Index**: Uses IVFFlat index for fast approximate nearest neighbor search
- **Optimal for**: <100k vectors
- **Query time**: ~10-50ms for 20 results

### Python Script
- **Bottleneck**: Embedding generation (100-500ms per query)
- **Optimization**: Batch queries together
- **Local cache**: Model downloads once to `~/.cache/`

---

## Troubleshooting

### Issue: "column 'embedding' does not exist"
**Solution**: Ensure pgvector extension is enabled:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue: Python script slow on first run
**Solution**: Model downloads on first use (~100MB). Subsequent runs are fast.

### Issue: Low similarity scores (<0.3)
**Possible causes**:
- Query too vague or generic
- Evidence not in database yet
- Different terminology used in documents

**Solutions**:
- Try more specific queries
- Check if evidence files have been vectorized
- Use keyword search first to find terminology, then use vector search

---

## Integration with Legal Workflow

### For Copilot Instructions
This tool is specified in `.github/copilot-instructions.md` under:
- **Evidence Database (MCP Supabase Tool)** section
- Usage: Prefer Supabase MCP for fact-checking over local grep

### For Email Drafting
When drafting emails to Ogasawara-sensei:
1. Use Python script to find relevant evidence for claims
2. Use MCP/SQL to cross-reference and find corroborating documents
3. Include file paths and exact quotes in email
4. Preserve factual/observational tone

### For Timeline Documentation
1. Search for event-specific evidence: "Q2 kickoff", "Fukushi quit"
2. Find related documents to build context
3. Verify dates and quotes against multiple sources
4. Document contradictions found via similarity search

---

## Quick Reference

### MCP Tool Command
```
Tool: mcp_supabase-clou_execute_sql
Parameter: query (SQL string)
```

### Python Script Commands
```bash
conda activate advocado-env
cd _supabase_mcp/_similarity_search/
python test_search.py
```

### Key SQL Patterns
```sql
-- Cosine distance to similarity
1 - (embedding <=> query_embedding) as similarity

-- Order by similarity (best first)
ORDER BY embedding <=> query_embedding

-- Exclude query document
WHERE id != <query_id>
```

