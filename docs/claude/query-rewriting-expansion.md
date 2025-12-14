Yes, **query rewriting/expansion is a common RAG improvement technique** and will give you better retrieval. Here's how to approach it:

**Option 1: Query expansion before vector search**

```python
import anthropic

async def expand_query(user_question):
    """Use Claude to rewrite query for better retrieval"""
    
    prompt = f"""You are helping search through legal evidence documents. 
    
User question: {user_question}

Generate 2-3 alternative phrasings or related search queries that would help find relevant evidence. Focus on:
- Key entities (names, companies, systems)
- Technical terms and their synonyms
- Related concepts
- Time periods if mentioned

Return only the search queries, one per line."""

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    queries = message.content[0].text.strip().split('\n')
    return [user_question] + queries  # Include original too

# Then search with all queries
async def search_evidence(user_question, top_k=5):
    queries = await expand_query(user_question)
    
    all_results = []
    for query in queries:
        # Vector search with each query
        embedding = get_embedding(query)
        results = supabase.rpc('match_documents', {
            'query_embedding': embedding,
            'match_threshold': 0.7,
            'match_count': top_k
        }).execute()
        all_results.extend(results.data)
    
    # Deduplicate and re-rank
    unique_results = deduplicate_by_id(all_results)
    return unique_results[:top_k]
```

**Option 2: Hypothetical Document Embeddings (HyDE)**

```python
async def hyde_search(user_question):
    """Generate hypothetical answer, embed that, search"""
    
    prompt = f"""Given this question about legal evidence: {user_question}

Write a hypothetical 2-3 sentence answer that might appear in the evidence documents. Be specific and use likely terminology."""

    # Get hypothetical answer
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    
    hypo_answer = message.content[0].text
    
    # Embed the hypothetical answer instead of question
    embedding = get_embedding(hypo_answer)
    
    # Search
    results = supabase.rpc('match_documents', {
        'query_embedding': embedding,
        'match_threshold': 0.7,
        'match_count': 5
    }).execute()
    
    return results.data
```

**Option 3: Hybrid approach (best for your case)**

```python
async def search_with_context(user_question, conversation_history=[]):
    """Combine query expansion with context"""
    
    # Build context-aware search query
    prompt = f"""Based on this legal investigation conversation:

Previous context: {conversation_history[-3:] if conversation_history else 'None'}

Current question: {user_question}

Generate a search query that:
1. Extracts key searchable facts (names, dates, systems, violations)
2. Identifies what type of evidence would answer this
3. Uses terminology likely in Slack/email evidence

Return only the optimized search query."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    
    optimized_query = message.content[0].text.strip()
    
    # Search with optimized query
    embedding = get_embedding(optimized_query)
    results = supabase.rpc('match_documents', {...}).execute()
    
    return results.data, optimized_query  # Return query so lawyer sees what was searched
```

**For your tight timeline, I'd go with Option 3** because:
- Shows lawyer what was actually searched (transparency)
- Can incorporate conversation context
- Single API call (fast)
- Works well with legal evidence language

You could also add this as a toggle in Streamlit: "Advanced search" checkbox that enables query rewriting.

Want me to help integrate this into your existing code structure?