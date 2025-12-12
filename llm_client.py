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

    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]], model_id: str = "claude-sonnet-4-5-20250929") -> str:
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
1. BASE your answer STRICTLY on the provided context. If the answer is not in the context, say "I cannot find evidence for that in the current database."
2. CITE your sources. When you state a fact, reference the Source ID or File Name (e.g., "According to email-sensei.md...").
3. Be professional, objective, and concise.
4. If the context contains Japanese, translate the relevant parts to English in your answer, but keep the original meaning.
"""

        # 3. Call API
        try:
            message = self.client.messages.create(
                model=model_id,
                max_tokens=1024,
                temperature=0.2,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error generating response: {e}"
