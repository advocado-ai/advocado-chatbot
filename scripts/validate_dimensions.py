#!/usr/bin/env python3
"""
Dimension Validation Test Script

Verifies that the embedding model dimensions match the database vector dimensions
to prevent runtime errors in production. Run this before deploying to ensure consistency.

Usage:
    python validate_dimensions.py
"""

import sys
import os
from sentence_transformers import SentenceTransformer
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try streamlit secrets first, fall back to env vars
try:
    import streamlit as st
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    print("✓ Loaded credentials from Streamlit secrets")
except:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    print("✓ Loaded credentials from environment variables")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("✗ ERROR: Missing SUPABASE_URL or SUPABASE_KEY")
    sys.exit(1)


def test_model_dimensions():
    """Test that the model produces expected dimensions."""
    print("\n1. Testing Model Dimensions...")
    
    try:
        model = SentenceTransformer('intfloat/multilingual-e5-base')
        test_embedding = model.encode("query: test").tolist()
        model_dims = len(test_embedding)
        
        print(f"   Model: intfloat/multilingual-e5-base")
        print(f"   Dimensions: {model_dims}")
        
        if model_dims == 768:
            print("   ✓ Model produces 768-dimensional vectors (E5-Base)")
            return 768, True
        else:
            print(f"   ✗ ERROR: Expected 768 dimensions, got {model_dims}")
            return model_dims, False
            
    except Exception as e:
        print(f"   ✗ ERROR loading model: {e}")
        return None, False


def test_database_dimensions():
    """Test database schema and actual vector dimensions."""
    print("\n2. Testing Database Dimensions...")
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if table exists and has vectors
        response = client.table('evidence_vectors').select('id, embedding').limit(1).execute()
        
        if not response.data:
            print("   ⚠ WARNING: evidence_vectors table is empty")
            return None, False
        
        # Check actual vector dimension
        first_vector = response.data[0]['embedding']
        db_dims = len(first_vector)
        
        print(f"   Table: evidence_vectors")
        print(f"   Sample vector dimensions: {db_dims}")
        print(f"   Total vectors: {len(response.data)} (sampled)")
        
        if db_dims == 768:
            print("   ✓ Database contains 768-dimensional vectors (E5-Base)")
            return db_dims, True
        else:
            print(f"   ✗ ERROR: Expected 768 dimensions, got {db_dims}")
            return db_dims, False
            
    except Exception as e:
        print(f"   ✗ ERROR querying database: {e}")
        return None, False


def test_rpc_function():
    """Test that RPC function accepts correct dimensions."""
    print("\n3. Testing RPC Function...")
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        model = SentenceTransformer('intfloat/multilingual-e5-base')
        
        # Generate a test embedding
        test_embedding = model.encode("query: test").tolist()
        
        # Try calling the RPC function
        response = client.rpc('match_evidence_vectors_v2', {
            'query_embedding': test_embedding,
            'match_threshold': 0.5,
            'match_count': 1,
            'filter_document_type': None,
            'filter_folders': None
        }).execute()
        
        print(f"   Function: match_evidence_vectors_v2")
        print(f"   Input dimensions: {len(test_embedding)}")
        print(f"   Results returned: {len(response.data)}")
        print("   ✓ RPC function accepts 768-dimensional vectors")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "vector" in error_msg.lower() and "dimension" in error_msg.lower():
            print(f"   ✗ DIMENSION MISMATCH ERROR: {error_msg}")
            print("   → RPC function may still expect 384 dimensions")
            print("   → Run rpc_v2.sql in Supabase SQL Editor to update")
        else:
            print(f"   ✗ ERROR calling RPC: {error_msg}")
        return False


def test_vector_index():
    """Check if HNSW index exists for performance."""
    print("\n4. Testing Vector Index...")
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query for indexes on evidence_vectors table
        response = client.rpc('exec_sql', {
            'query': """
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'evidence_vectors' 
                AND indexname LIKE '%embedding%'
            """
        }).execute()
        
        if response.data and len(response.data) > 0:
            for idx in response.data:
                print(f"   Index: {idx['indexname']}")
                if 'hnsw' in idx['indexdef'].lower():
                    print("   ✓ HNSW vector index exists (fast search)")
                    return True
            
            print("   ⚠ WARNING: Vector index exists but may not be HNSW")
            return True
        else:
            print("   ⚠ WARNING: No vector index found")
            print("   → Searches will be slow on large datasets")
            print("   → Run create_vector_index.sql to create HNSW index")
            return False
            
    except Exception as e:
        # Many Supabase setups don't have exec_sql RPC, so skip this check
        print(f"   ⚠ Could not check index (this is optional): {e}")
        return True


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("ADVOCADO CHATBOT - DIMENSION VALIDATION")
    print("=" * 60)
    
    # Run tests
    model_dims, model_ok = test_model_dimensions()
    db_dims, db_ok = test_database_dimensions()
    rpc_ok = test_rpc_function()
    index_ok = test_vector_index()
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_ok = model_ok and db_ok and rpc_ok
    
    if all_ok:
        print("✓ ALL CHECKS PASSED")
        print(f"  - Model: {model_dims}D ✓")
        print(f"  - Database: {db_dims}D ✓")
        print("  - RPC Function: ✓")
        if index_ok:
            print("  - HNSW Index: ✓")
        else:
            print("  - HNSW Index: ⚠ (recommended for performance)")
        print("\n✓ Safe to deploy to production!")
        sys.exit(0)
    else:
        print("✗ VALIDATION FAILED")
        if not model_ok:
            print(f"  - Model: {model_dims}D ✗")
        if not db_ok:
            print(f"  - Database: {db_dims}D ✗")
        if not rpc_ok:
            print("  - RPC Function: ✗")
        
        print("\n⚠ DO NOT DEPLOY - Fix dimension mismatches first!")
        print("\nTroubleshooting:")
        print("1. Ensure rag_engine.py uses 'intfloat/multilingual-e5-base'")
        print("2. Run rpc_v2.sql in Supabase to update function to vector(768)")
        print("3. Re-ingest all vectors with E5-Base model if needed")
        sys.exit(1)


if __name__ == "__main__":
    main()
