import streamlit as st
from anthropic import Anthropic
from typing import List, Dict, Any

class LLMClient:
    """
    Handles interaction with the LLM (Anthropic Claude) to generate answers.
    """
    
    def __init__(self):
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("Anthropic API Key not found in secrets.")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)

    def optimize_query(self, query: str, history: List[Dict[str, Any]], model_id: str = "claude-sonnet-4-5-20250929") -> str:
        """
        Uses the LLM to rewrite the search query based on conversation history.
        """
        if not self.client:
            return query

        # Format history for the prompt
        history_text = ""
        if history:
            for msg in history:
                role = msg["role"]
                content = msg["content"]
                history_text += f"{role.upper()}: {content}\n"
        else:
            history_text = "No previous conversation history."

        prompt = f"""Based on the following conversation history and the user's latest question, generate a specific, standalone search query to find relevant legal evidence.
        
Conversation History:
{history_text}

User's Question: {query}

The search query should:
1. Resolve any pronouns (e.g., "he", "it", "that meeting") to specific names or entities mentioned in the history.
2. Include key technical terms, names, or dates.
3. Be optimized for a vector similarity search.
4. IMPORTANT: If the User's Question is in Japanese, translate the search query into English keywords. The evidence database is in English.

Return ONLY the search query string. Do not add quotes or explanations."""

        try:
            message = self.client.messages.create(
                model=model_id,
                max_tokens=100,
                temperature=0.0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"Query optimization error: {e}")
            return query

    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]], history: List[Dict[str, Any]] = None, model_id: str = "claude-sonnet-4-5-20250929") -> str:
        """
        Generates a response based on the query and retrieved context.
        """
        if not self.client:
            return "Error: LLM client not initialized."

        # 1. Prepare Context
        context_text = ""
        for i, chunk in enumerate(context_chunks):
            source = chunk.get('file_path', 'Unknown File')
            content = chunk.get('content', '').strip()
            context_text += f"--- SOURCE {i+1}: {source} ---\n{content}\n\n"

        # 2. Construct System Prompt
        system_prompt = """You are a legal assistant for the 'Advocado' project. 
Your goal is to answer the lawyer's questions ACCURATELY based ONLY on the provided evidence context.

Rules:
1. LANGUAGE: Answer in the SAME language as the user's question. If the user asks in Japanese, answer in Japanese.
2. REASONING: The evidence is primarily in English. You must analyze the English evidence but explain your findings in the user's language.
3. BASE your answer STRICTLY on the provided context. If the answer is not in the context, say "I cannot find evidence for that in the current database."
4. CITE your sources. When you state a fact, reference the Source ID or File Name (e.g., "According to email-sensei.md...").
5. Be professional, objective, and concise.
"""

        # 3. Prepare Messages with History
        final_messages = []
        
        # Add history if available (excluding the current user message)
        if history:
            for msg in history:
                 final_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the current turn with context
        final_messages.append({
            "role": "user", 
            "content": f"Context:\n{context_text}\n\nQuestion: {query}"
        })

        # 3. Call API
        try:
            message = self.client.messages.create(
                model=model_id,
                max_tokens=1024,
                temperature=0.2,
                system=system_prompt,
                messages=final_messages
            )
            return message.content[0].text
        except Exception as e:
            return f"Error generating response: {e}"
