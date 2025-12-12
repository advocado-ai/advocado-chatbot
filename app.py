import streamlit as st
import time
from rag_engine import RAGEngine
from storage_client import StorageClient
from llm_client import LLMClient
from models import MODELS, DEFAULT_MODEL_ID, get_model_by_id

# Page Config
st.set_page_config(
    page_title="Advocado Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

# --- Authentication ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Please enter the application password to access the Legal Assistant:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Please enter the application password to access the Legal Assistant:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()

# --- Application Logic ---

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
    
    # Navigation
    page = st.radio("Navigation", ["Chat Assistant", "Documentation"])
    
    st.markdown("---")
    st.markdown("**System Status**")
    if st.session_state.get("initialized"):
        st.success("System Online")
    else:
        st.error("System Offline")
    
    if page == "Chat Assistant":
        st.markdown("---")
        st.markdown("### Settings")
        
        # Model Selection
        st.markdown("#### Model Configuration")
        model_names = [m.name for m in MODELS]
        default_index = 0
        # Try to find default index
        for i, m in enumerate(MODELS):
            if m.api_id == DEFAULT_MODEL_ID:
                default_index = i
                break
                
        selected_model_name = st.selectbox("Select Model", model_names, index=default_index)
        
        # Get selected model object
        selected_model = next((m for m in MODELS if m.name == selected_model_name), MODELS[0])
        
        with st.expander("ℹ️ Model Info"):
            st.markdown(f"**{selected_model.name}**")
            st.markdown(f"_{selected_model.description}_")
            st.markdown(f"**Context:** {selected_model.context_window}")
            st.markdown(f"**Max Output:** {selected_model.max_output}")
            st.caption(f"API ID: `{selected_model.api_id}`")

        st.markdown("---")
        st.markdown("#### Search Parameters")
        match_count = st.slider(
            "Evidence Chunks", 
            min_value=3, 
            max_value=20, 
            value=10,
            help="Number of evidence snippets to retrieve from the database. Higher values provide more context but may increase noise."
        )
        threshold = st.slider(
            "Similarity Threshold", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.3,
            help="Minimum relevance score (0-1). Lower values include more loosely related documents; higher values are stricter."
        )
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

if page == "Documentation":
    st.title("📚 Application Documentation")
    
    st.markdown("""
    ### Overview
    This application uses Retrieval Augmented Generation (RAG) to help you search and analyze the evidence database.
    
    ### How it Works
    1. **Search**: Your question is converted into a mathematical vector.
    2. **Retrieval**: We search the Supabase database for the most similar evidence chunks.
    3. **Generation**: The selected AI model (Claude) reads the evidence and answers your question.
    
    ### Settings Explained
    
    #### 🧠 Model Selection
    *   **Claude Sonnet 4.5**: The default, balanced model. Good for most legal reasoning.
    *   **Claude Haiku 4.5**: Faster, cheaper, but slightly less nuanced. Good for simple lookups.
    *   **Claude Opus 4.5**: The most powerful model. Use for complex reasoning or drafting, but it is slower.
    
    #### 🔍 Search Parameters
    *   **Evidence Chunks**: Controls *how much* text the AI reads. 
        *   *Increase* if the answer requires synthesizing many small details.
        *   *Decrease* if you want focused answers or if the AI is getting confused by irrelevant info.
    *   **Similarity Threshold**: Controls *quality control*.
        *   **0.0**: "Show me everything, even if it's barely relevant."
        *   **0.5**: "Only show me things that are clearly about this topic."
        *   **0.8**: "Only show me exact matches."
        *   *Recommended*: 0.3 - 0.5 for general queries.
        
    ### Security
    *   This application is password protected.
    *   Evidence files are stored in a private Supabase bucket.
    *   Links to files are temporary (signed URLs) and expire after 1 hour.
    """)

elif page == "Chat Assistant":
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
                message_placeholder.markdown(f"🤔 Analyzing documents with {selected_model.name}...")
                response_text = st.session_state.llm.generate_response(
                    prompt, 
                    results, 
                    model_id=selected_model.api_id
                )
                sources = results

            # C. Display Final Response
            message_placeholder.markdown(response_text)
            
            # D. Save to History
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_text,
                "sources": sources
            })
        
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
