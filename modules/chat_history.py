import streamlit as st
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import uuid

class ChatHistoryManager:
    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.client: Client = create_client(self.url, self.key)

    def create_conversation(self, title: str = "New Conversation") -> str:
        """Creates a new conversation and returns its ID."""
        try:
            response = self.client.table("conversations").insert({"title": title}).execute()
            if response.data:
                return response.data[0]["id"]
        except Exception as e:
            print(f"Error creating conversation: {e}")
        return None

    def add_message(self, conversation_id: str, role: str, content: str, sources: List[Dict[str, Any]] = None):
        """Adds a message to a conversation."""
        if not conversation_id:
            return
            
        try:
            data = {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "sources": sources
            }
            self.client.table("messages").insert(data).execute()
            
            # Update conversation timestamp
            self.client.table("conversations").update({"updated_at": "now()"}).eq("id", conversation_id).execute()
            
        except Exception as e:
            print(f"Error adding message: {e}")

    def get_recent_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetches recent conversations."""
        try:
            response = self.client.table("conversations") \
                .select("*") \
                .order("updated_at", desc=True) \
                .limit(limit) \
                .execute()
            return response.data
        except Exception as e:
            print(f"Error fetching conversations: {e}")
            return []

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Fetches all messages for a conversation."""
        try:
            response = self.client.table("messages") \
                .select("*") \
                .eq("conversation_id", conversation_id) \
                .order("created_at", desc=False) \
                .execute()
            return response.data
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []

    def update_title(self, conversation_id: str, title: str):
        """Updates the title of a conversation."""
        try:
            self.client.table("conversations").update({"title": title}).eq("id", conversation_id).execute()
        except Exception as e:
            print(f"Error updating title: {e}")

    def delete_conversation(self, conversation_id: str):
        """Deletes a conversation and its messages."""
        try:
            self.client.table("conversations").delete().eq("id", conversation_id).execute()
        except Exception as e:
            print(f"Error deleting conversation: {e}")

