#!/usr/bin/env python3
"""
Diagnostic script to investigate search issues:
1. Check if analysis-12182025-meeting-accusations.md exists in database
2. Test embedding similarity with different queries
3. Verify PDF path mapping logic
"""

import os
import sys
from pathlib import Path
from supabase import create_client
from sentence_transformers import SentenceTransformer
import streamlit as st

# Load secrets (need to run with streamlit context or load manually)
def load_secrets():
    """Load secrets from .streamlit/secrets.toml"""
    import toml
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print(f"❌ Secrets file not found: {secrets_path}")
        sys.exit(1)
    return toml.load(secrets_path)

def check_document_in_db(client, target_file: str):
    """Check if a specific document exists in the database"""
    print(f"\n{'='*60}")
    print(f"🔍 Checking for: {target_file}")
    print(f"{'='*60}\n")
    
    # Search for exact match
    response = client.table('evidence_vectors').select('*').ilike('file_path', f'%{target_file}%').execute()
    
    if response.data:
        print(f"✅ Found {len(response.data)} chunks for this document\n")
        for i, chunk in enumerate(response.data[:3], 1):
            print(f"Chunk {i}:")
            print(f"  ID: {chunk['id']}")
            print(f"  File Path: {chunk['file_path']}")
            print(f"  Content Preview: {chunk['content'][:100]}...")
            print(f"  Embedding Dim: {len(chunk['embedding']) if chunk.get('embedding') else 'None'}")
            print()
        return True
    else:
        print(f"❌ No chunks found for this document in database")
        print(f"   This means the document hasn't been ingested yet or the path is different\n")
        return False

def test_search_similarity(client, model, queries: list, target_file: str):
    """Test similarity scores for various queries"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing Search Similarity")
    print(f"{'='*60}\n")
    
    for query in queries:
        print(f"Query: '{query}'")
        
        # Generate embedding (without prefix to match current DB state)
        query_embedding = model.encode(query).tolist()
        
        # Search with RPC
        result = client.rpc('match_evidence_vectors', {
            'query_embedding': query_embedding,
            'match_threshold': 0.3,
            'match_count': 10,
            'filter_document_type': None,
            'filter_folder': None
        }).execute()
        
        if result.data:
            print(f"  Found {len(result.data)} results")
            
            # Check if target file is in results
            target_found = False
            for i, doc in enumerate(result.data, 1):
                is_target = target_file in doc['file_path']
                marker = "🎯" if is_target else "  "
                print(f"  {marker} {i}. {doc['file_path']} ({doc['similarity']:.4f})")
                if is_target:
                    target_found = True
            
            if not target_found:
                print(f"  ⚠️  Target file NOT in top 10 results")
        else:
            print(f"  ❌ No results found")
        print()

def check_pdf_path_logic():
    """Test PDF path conversion logic"""
    print(f"\n{'='*60}")
    print(f"📄 Testing PDF Path Conversion Logic")
    print(f"{'='*60}\n")
    
    test_cases = [
        "data/harassment/evidence-timeline/11102025-c2c-requests-meeting/legal_brief_package/FULL_LEGAL_BRIEF_FOR_SENSEI.md",
        "data/harassment/ppc_submission/stock-options/offer-meeting-12242024-documents/transcript.txt",
        "data/harassment/evidence-timeline/12182025-meeting-with-c2c-morihamada/assessments/analysis-12182025-meeting-accusations.md",
    ]
    
    for path in test_cases:
        pdf_path = path.replace('.md', '.pdf').replace('.txt', '.txt')
        if path.endswith('.md'):
            # Insert /pdf/ before filename
            parts = Path(path).parts
            pdf_path = str(Path(*parts[:-1]) / 'pdf' / Path(parts[-1]).with_suffix('.pdf'))
        
        print(f"Original: {path}")
        print(f"PDF Path: {pdf_path}")
        print()

def main():
    print("🚀 Advocado Chatbot - Search Diagnostics")
    print("="*60)
    
    # Load configuration
    secrets = load_secrets()
    url = secrets["SUPABASE_URL"]
    key = secrets["SUPABASE_KEY"]
    
    # Initialize clients
    print("\n📡 Connecting to Supabase...")
    client = create_client(url, key)
    
    print("🤖 Loading E5-Base model...")
    model = SentenceTransformer('intfloat/multilingual-e5-base')
    print(f"   Model loaded: {model.get_sentence_embedding_dimension()} dimensions")
    
    # Target document
    target_file = "analysis-12182025-meeting-accusations.md"
    
    # 1. Check if document exists in database
    doc_exists = check_document_in_db(client, target_file)
    
    if not doc_exists:
        print("\n⚠️  ROOT CAUSE #1: Document not in database")
        print("   This document needs to be ingested in the 'advocado' project")
        print("   Path should be: docs/evidence_examples/analysis-12182025-meeting-accusations.md")
    
    # 2. Test search queries
    queries = [
        "12月18日の会議の内容",  # Original Japanese query
        "December 18 meeting content",  # English translation
        "岩淵 由香理 会議",  # Specific person
        "meeting accusations Iwabuchi",  # English specific
        "2025年12月18日 岩淵",  # Date + person
    ]
    
    test_search_similarity(client, model, queries, target_file)
    
    # 3. Test PDF path logic
    check_pdf_path_logic()
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 DIAGNOSTIC SUMMARY")
    print(f"{'='*60}\n")
    
    print("Issue #1: Poor Search Matching")
    if not doc_exists:
        print("  ❌ Document not in database - needs ingestion")
        print("  ⚙️  Fix: Run ingestion in 'advocado' project with E5-Base 'passage: ' prefix")
    else:
        print("  ⚠️  Document exists but ranking poorly")
        print("  ⚙️  Fix: Re-ingest with 'passage: ' prefix, restore 'query: ' prefix in chatbot")
    
    print("\nIssue #2: Wrong File Paths (showing .md instead of .pdf)")
    print("  ❌ App currently shows raw database paths")
    print("  ⚙️  Fix: Add PDF path conversion in app.py before displaying citations")
    print("     - Convert: xxx/file.md → xxx/pdf/file.pdf")
    print("     - Keep:    xxx/file.txt → xxx/file.txt (no change)")

if __name__ == "__main__":
    main()
