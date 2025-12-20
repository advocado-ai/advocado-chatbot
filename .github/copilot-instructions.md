# Copilot Instructions

## Environment Setup
- Always activate the conda environment `advocado-env` before installing packages or running python scripts.
  Command: `conda activate advocado-env`
- This environment includes `git-filter-repo` for cleaning git history.

## Security
- **NEVER commit** `.streamlit/secrets.toml` - it contains production credentials (Supabase URL, API keys, passwords)
- Always use `.streamlit/secrets.toml.example` as template with placeholder values only
- Private files to keep out of git: secrets.toml, .env, *.log, .DS_Store

## Deployment
- Target platform: Streamlit Cloud free tier (2.7GB RAM)
- Embedding model: `intfloat/multilingual-e5-base` (768 dimensions, ~1.1GB RAM)
- Database requires HNSW index on `evidence_vectors.embedding` column for production performance
- Run `python validate_dimensions.py` before deploying to verify model/database compatibility

