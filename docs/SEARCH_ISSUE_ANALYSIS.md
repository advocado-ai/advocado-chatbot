# Search Issue Analysis & Fixes

## Date: December 21, 2025

## Issue Report
User query: "12月18日の会議の内容" (December 18 meeting content)
Expected document: `analysis-12182025-meeting-accusations.md`
Problem: Document ranked #10 (0.8374 similarity) instead of top result

## Diagnostic Results

### Issue #1: Poor Search Ranking ⚠️

**Status**: Document EXISTS in database (60 chunks ingested)

**Root Cause**: E5-Base prefix mismatch
- Database vectors: Ingested WITHOUT `passage: ` prefix
- Query vectors: Currently generated WITHOUT `query: ` prefix (temporary hotfix from Dec 20)
- This is suboptimal for E5-Base model which requires matching prefixes for best performance

**Test Results**:
```
Query: "12月18日の会議の内容"
Target document rank: #10 (similarity: 0.8374)
Top-ranked: analysis-ppc-silence-dec2025.md (0.8427)

Query: "meeting accusations Iwabuchi" 
Target document rank: #5 (similarity: 0.8651)
```

**Long-term Fix** (requires `advocado` project work):
1. Re-ingest ALL documents with `passage: ` prefix: `model.encode(f"passage: {chunk}")`
2. Restore `query: ` prefix in chatbot: `model.encode(f"query: {query}")`
3. This will improve E5-Base semantic matching and ranking

**Current Status**: 
- ✅ Document is findable (ranks in top 10)
- ⚠️ Not optimal ranking (should be top 3)
- 🔧 Workaround: User can use more specific queries like "meeting accusations Iwabuchi" (ranks #5)

### Issue #2: Wrong File Paths ✅ FIXED

**Problem**: Citations showed `.md` file paths instead of `.pdf` paths
- Database stores: `data/.../file.md`
- User expects: `data/.../pdf/file.pdf`

**Fix Applied**:
1. Added `convert_to_pdf_path()` helper function in `app.py`
   - Converts: `xxx/file.md` → `xxx/pdf/file.pdf`
   - Preserves: `xxx/file.txt` → `xxx/file.txt` (no change)

2. Updated citation displays in 2 locations:
   - Message history sources display (line ~360)
   - Immediate sources display (line ~500)

**Example**:
```
Before: data/harassment/evidence-timeline/.../FULL_LEGAL_BRIEF_FOR_SENSEI.md
After:  data/harassment/evidence-timeline/.../pdf/FULL_LEGAL_BRIEF_FOR_SENSEI.pdf
```

## Implementation Summary

### Files Modified
1. **app.py**
   - Added: `convert_to_pdf_path()` function (lines 15-32)
   - Updated: Message history sources display (line ~360)
   - Updated: Immediate sources display (line ~500)

### Files Created
1. **diagnose_search_issue.py** - Diagnostic script for future troubleshooting
2. **SEARCH_ISSUE_ANALYSIS.md** - This document

## Testing Recommendations

1. **Test PDF Path Conversion**:
   - Query: "12月18日の会議"
   - Verify citations show `.pdf` paths, not `.md`
   - Check both Japanese and English queries

2. **Test Search Ranking**:
   - Try specific queries: "meeting accusations Iwabuchi" (should rank higher)
   - Try date-based: "2025年12月18日 岩淵"
   - Document current behavior for comparison after re-ingestion

3. **Test Google Drive Links**:
   - Verify Google Drive links still work when present
   - Verify fallback to Supabase Storage signed URLs

## Future Work (Requires `advocado` Project)

### Priority: High
Re-ingest database with proper E5-Base prefixes:
- **Location**: `advocado/src/vectorization/ingest_vectors.py`
- **Change**: Add `passage: ` prefix when encoding: `model.encode(f"passage: {chunk}")`
- **Impact**: Will improve semantic search accuracy and ranking
- **Estimated work**: 2-3 hours (modify ingestion + re-run for 21,012 vectors)

### After Re-ingestion
Restore query prefix in chatbot:
- **Location**: `advocado-chatbot/rag_engine.py` line 54
- **Change**: Restore `query_embedding = self.model.encode(f"query: {query}").tolist()`
- **Impact**: Optimal E5-Base performance with matching prefixes

## Reference Documents
- E5-Base paper: https://arxiv.org/abs/2212.03533
- E5-Base requires:
  - Query embedding: `encode("query: " + text)`
  - Document embedding: `encode("passage: " + text)`
- Current workaround: Both use no prefix (suboptimal but functional)

## Commit Message
```
fix: Convert .md citation paths to .pdf paths for user display

- Add convert_to_pdf_path() helper function
- Update message history sources to show PDF paths
- Update immediate sources to show PDF paths
- Pattern: xxx/file.md → xxx/pdf/file.pdf
- Preserve .txt files unchanged

Fixes issue where users saw .md file references instead of 
corresponding PDF files in citation links.
```

## Status
- ✅ Issue #2 (PDF paths): FIXED
- ⚠️ Issue #1 (Search ranking): DOCUMENTED, requires database re-ingestion
- 📝 Diagnostic tools created for future troubleshooting
