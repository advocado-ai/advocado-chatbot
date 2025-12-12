import streamlit as st
import time
from rag_engine import RAGEngine
from storage_client import StorageClient
from llm_client import LLMClient

# Page Config
st.set_page_config(
    page_title="Advocado Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "rag" not in st.session_state:
    # Initialize engines only once
    try:
        st.session_state.rag = RAGEngine()
        st.session_state.storage = StorageClient()
        st.session_state.llm = LLMClient()
        st.session_state.initialized = True
    except Exception as e:
        st.error(f"Failed to initialize application: {e}")
        st.session_state.initialized = False

# Sidebar
with st.sidebar:
    st.title("⚖️ Advocado AI")
    st.markdown("---")
    st.markdown("**System Status**")
    if st.session_state.get("initialized"):
        st.success("System Online")
    else:
        st.error("System Offline")
    
    st.markdown("---")
    st.markdown("### Settings")
    match_count = st.slider("Evidence Chunks", min_value=3, max_value=20, value=10)
    threshold = st.slider("Similarity Threshold", min_value=0.0, max_value=1.0, value=0.3)
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main Chat Interface
st.title("Legal Evidence Assistant")
st.markdown("Ask questions about the case evidence. I will search the vector database and cite specific documents.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If there are source documents attached to the message, display them
        if "sources" in message:
            with st.expander("📚 View Cited Evidence Sources"):
                for source in message["sources"]:
                    file_path = source['file_path']
                    similarity = source['similarity']
                    
                    # Generate signed URL
                    url = st.session_state.storage.get_signed_url(file_path)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{file_path}** (Relevance: {similarity:.2f})")
                    with col2:
                        if url:
                            st.markdown(f"[Open File ↗️]({url})")
                        else:
                            st.markdown("*Link unavailable*")

# Chat Input
if prompt := st.chat_input("What evidence do we have regarding..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 Searching evidence database...")
        
        # A. Retrieve Context
        results = st.session_state.rag.search(prompt, match_count=match_count, threshold=threshold)
        
        if not results:
            response_text = "I couldn't find any relevant evidence in the database matching your query."
            sources = []
        else:
            # B. Generate Answer
            message_placeholder.markdown("🤔 Analyzing documents...")
            response_text = st.session_state.llm.generate_response(prompt, results)
            sources = results

        # C. Display Final Response
        message_placeholder.markdown(response_text)
        
        # D. Display Sources (Immediate view)
        if sources:
            with st.expander("📚 View Cited Evidence Sources", expanded=False):
                for source in sources:
                    file_path = source['file_path']
                    similarity = source['similarity']
                    url = st.session_state.storage.get_signed_url(file_path)
                    
                    st.markdown(f"- **{file_path}** ({similarity:.2f})")
                    if url:
                        st.markdown(f"  [View Document ↗️]({url})")

    # 3. Save History
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response_text,
        "sources": sources
    })
