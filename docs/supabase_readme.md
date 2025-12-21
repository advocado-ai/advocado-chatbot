# Supabase Database Schema

## Table: `evidence_vectors`

Stores the embeddings and metadata for the evidence documents.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `bigint` | Primary Key |
| `created_at` | `timestamptz` | Creation timestamp |
| `content` | `text` | The text content of the chunk |
| `embedding` | `vector(768)` | The embedding vector (intfloat/multilingual-e5-base) |
| `file_path` | `text` | Path to the file in Supabase Storage (e.g., `data/harassment/...`) |
| `file_name` | `text` | Name of the file |
| `folder` | `text` | Folder containing the file |
| `chunk_index` | `int` | Index of the chunk in the file |
| `total_chunks` | `int` | Total chunks for the file |
| `document_type` | `text` | Type of document (e.g., 'evidence') |
| `metadata` | `jsonb` | Additional metadata |
| `google_drive_link` | `text` | **New**: Direct link to the file in Google Drive |

## RPC: `match_evidence_vectors`

Performs a similarity search using cosine distance.

**Parameters:**
- `query_embedding`: `vector(768)`
- `match_threshold`: `float`
- `match_count`: `int`
- `filter_document_type`: `text` (optional)
- `filter_folder`: `text` (optional)

**Returns:**
- `id`, `content`, `file_path`, `file_name`, `folder`, `document_type`, `chunk_index`, `total_chunks`, `metadata`, `similarity`

**Note:** The RPC does *not* currently return `google_drive_link`. The application performs a secondary fetch to retrieve this column for the search results.
