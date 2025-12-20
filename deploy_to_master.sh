#!/bin/bash
# Deploy E5-Base Model to Production
# This script commits changes and merges dockerize branch to master

set -e  # Exit on error

echo "=========================================="
echo "ADVOCADO CHATBOT - E5-BASE DEPLOYMENT"
echo "=========================================="

# Check we're in the right directory
if [ ! -f "app.py" ]; then
    echo "ERROR: Must run from project root (app.py not found)"
    exit 1
fi

# Activate conda environment
echo ""
echo "1. Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate advocado-env

# Validate dimensions before deploying
echo ""
echo "2. Running dimension validation..."
python validate_dimensions.py
if [ $? -ne 0 ]; then
    echo ""
    echo "DEPLOYMENT ABORTED: Dimension validation failed"
    echo "Fix the issues above before deploying"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo ""
echo "3. Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "dockerize" ]; then
    echo "ERROR: Must be on 'dockerize' branch to deploy"
    echo "Run: git checkout dockerize"
    exit 1
fi

# Show what files changed
echo ""
echo "4. Files modified for E5-Base:"
git status --short

# Commit changes on dockerize
echo ""
echo "5. Committing E5-Base changes on dockerize branch..."
git add rag_engine.py requirements.txt rpc_v2.sql update_rpc.sql schema_reference.sql setup_database.sql supabase_readme.md .gitignore .github/copilot-instructions.md DEPLOYMENT.md README.md validate_dimensions.py deploy_to_master.sh
git commit -m "feat: Upgrade to E5-Base multilingual model (768 dimensions)

- Change embedding model from all-MiniLM-L6-v2 to intfloat/multilingual-e5-base
- Update vector dimensions from 384 to 768 throughout codebase
- Add query prefix 'query: ' for E5-Base embeddings in search
- Update rpc_v2.sql to accept vector(768) parameters
- Pin sentence-transformers>=2.2.2 for E5 compatibility
- Add validate_dimensions.py pre-deployment test script
- Update documentation with E5-Base requirements and HNSW index setup
- Secure .gitignore with .DS_Store and *.log patterns
- Update copilot-instructions.md with security and deployment notes

Requires:
- Database with 768-dimensional vectors (re-ingestion complete)
- HNSW index on evidence_vectors.embedding (created)
- ~1.1GB RAM for E5-Base model (Streamlit Cloud 2.7GB sufficient)
"

echo "✓ Changes committed on dockerize"

# Checkout master
echo ""
echo "6. Switching to master branch..."
git checkout master

# Merge dockerize into master
echo ""
echo "7. Merging dockerize → master..."
git merge dockerize -m "Merge dockerize: E5-Base multilingual model upgrade

Merges the E5-Base embedding model implementation from dockerize branch.
This enables superior Japanese/English retrieval with 768-dimensional vectors.

Key changes:
- Embedding model: intfloat/multilingual-e5-base (768 dims)
- Database vectors: Re-ingested with E5-Base
- HNSW index: Created for fast search on 21K+ vectors
- Deep search: 4-step multilingual query expansion with RRF
- Full Japanese UI: Complete translation coverage
- Validation: Pre-deployment dimension testing

Production requirements met:
✓ 768-dim vectors in database
✓ HNSW index on evidence_vectors.embedding
✓ RPC function accepts vector(768)
✓ Streamlit Cloud RAM sufficient (~1.1GB model)
"

echo "✓ Merged dockerize → master"

# Push master to remote
echo ""
echo "8. Pushing master to remote origin..."
git push origin master

echo ""
echo "=========================================="
echo "✓ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Master branch now contains E5-Base model code."
echo ""
echo "Next steps:"
echo "1. Verify deployment at https://github.com/advocado-ai/advocado-chatbot"
echo "2. Streamlit Cloud will auto-rebuild from master branch"
echo "3. Monitor Streamlit Cloud logs for successful startup"
echo "4. Test search functionality with Japanese queries"
echo ""
echo "Database checklist (should already be done):"
echo "✓ 21,012 vectors re-ingested with E5-Base"
echo "✓ HNSW index created on evidence_vectors.embedding"
echo "✓ RPC function match_evidence_vectors_v2 updated to vector(768)"
echo ""
