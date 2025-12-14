import streamlit as st
import time
from rag_engine import RAGEngine
from storage_client import StorageClient
from llm_client import LLMClient
from models import MODELS, DEFAULT_MODEL_ID, get_model_by_id
from translations import TRANSLATIONS

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
    
    # Language Selection
    lang_options = list(TRANSLATIONS.keys())
    selected_lang = st.selectbox("Language / 言語", lang_options, index=0)
    t = TRANSLATIONS[selected_lang]
    
    # Navigation
    page = st.radio("Navigation", [t["nav_chat"], t["nav_docs"]])
    
    st.markdown("---")
    st.markdown(f"**{t['system_online']}**" if st.session_state.get("initialized") else f"**{t['system_offline']}**")
    if st.session_state.get("initialized"):
        st.success(t["system_online"])
    else:
        st.error(t["system_offline"])
    
    if page == t["nav_chat"]:
        st.markdown("---")
        st.markdown(f"### {t['settings']}")
        
        # Model Selection
        st.markdown(f"#### {t['model_config']}")
        model_names = [m.name for m in MODELS]
        default_index = 0
        # Try to find default index
        for i, m in enumerate(MODELS):
            if m.api_id == DEFAULT_MODEL_ID:
                default_index = i
                break
                
        selected_model_name = st.selectbox(t["select_model"], model_names, index=default_index)
        
        # Get selected model object
        selected_model = next((m for m in MODELS if m.name == selected_model_name), MODELS[0])
        
        with st.expander(t["model_info"]):
            st.markdown(f"**{selected_model.name}**")
            st.markdown(f"_{selected_model.description}_")
            st.markdown(f"**Context:** {selected_model.context_window}")
            st.markdown(f"**Max Output:** {selected_model.max_output}")
            st.caption(f"API ID: `{selected_model.api_id}`")

        st.markdown("---")
        st.markdown(f"#### {t['search_params']}")
        match_count = st.slider(
            t["evidence_chunks"], 
            min_value=3, 
            max_value=20, 
            value=10,
            help=t["evidence_chunks_help"]
        )
        threshold = st.slider(
            t["similarity_threshold"], 
            min_value=0.0, 
            max_value=1.0, 
            value=0.3,
            help=t["similarity_threshold_help"]
        )
        
        if st.button(t["clear_history"]):
            st.session_state.messages = []
            st.rerun()

if page == t["nav_docs"]:
    st.title(t["docs_title"])
    
    st.markdown(f"""
    ### {t['docs_overview_title']}
    {t['docs_overview_text']}
    
    ### {t['docs_how_title']}
    {t['docs_how_text']}
    
    ### {t['docs_settings_title']}
    
    #### {t['docs_models_title']}
    {t['docs_models_text']}
    
    #### {t['docs_search_title']}
    {t['docs_search_text']}
        
    ### {t['docs_security_title']}
    {t['docs_security_text']}
    """)

elif page == t["nav_chat"]:
    # Main Chat Interface
    st.title(t["app_title"])
    st.markdown(t["app_intro"])

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # If there are source documents attached to the message, display them
            if "sources" in message:
                with st.expander(t["view_sources"]):
                    for i, source in enumerate(message["sources"]):
                        file_path = source['file_path']
                        similarity = source['similarity']
                        
                        # Generate signed URL
                        url = st.session_state.storage.get_signed_url(file_path)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{i+1}. {file_path}** (Relevance: {similarity:.2f})")
                        with col2:
                            if url:
                                st.markdown(f"[{t['open_file']}]({url})")
                            else:
                                st.markdown(f"*{t['link_unavailable']}*")

    # Chat Input
    if prompt := st.chat_input(t["chat_placeholder"]):
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Assistant Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown(t["searching"])
            
            # Get recent history for context (exclude current message)
            recent_history = st.session_state.messages[:-1][-5:] if len(st.session_state.messages) > 1 else []
            
            # A. Optimize Query
            optimized_query = st.session_state.llm.optimize_query(
                prompt, 
                recent_history, 
                model_id=selected_model.api_id
            )
            
            if optimized_query != prompt:
                st.caption(f"🔍 Searched for: {optimized_query}")
            
            # B. Retrieve Context
            results = st.session_state.rag.search(optimized_query, match_count=match_count, threshold=threshold)
            
            if not results:
                response_text = t["no_results"]
                sources = []
            else:
                # C. Generate Answer
                message_placeholder.markdown(t["analyzing"].format(model=selected_model.name))
                response_text = st.session_state.llm.generate_response(
                    prompt, 
                    results, 
                    history=recent_history,
                    model_id=selected_model.api_id
                )
                sources = results

            # D. Display Final Response
            message_placeholder.markdown(response_text)
            
            # E. Save to History
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_text,
                "sources": sources
            })
        
        # D. Display Sources (Immediate view)
        if sources:
            with st.expander(t["view_sources"], expanded=False):
                for i, source in enumerate(sources):
                    file_path = source['file_path']
                    similarity = source['similarity']
                    doc_id = source.get('id') # Ensure your RAG search returns 'id'
                    
                    url = st.session_state.storage.get_signed_url(file_path)
                    
                    st.markdown(f"**{i+1}. {file_path}** ({similarity:.2f})")
                    
                    col_a, col_b = st.columns([1, 1])
                    with col_a:
                        if url:
                            st.markdown(f"[{t['open_file']}]({url})")
                        else:
                            # Show debug info in tooltip
                            debug_msg = st.session_state.storage.get_debug_info(file_path)
                            st.markdown(f"*{t['link_unavailable']}*", help=debug_msg)
                    with col_b:
                        if doc_id:
                            # Unique key for each button
                            if st.button(f"🔍 Find Similar", key=f"sim_{doc_id}_{i}"):
                                try:
                                    with st.spinner("Finding related documents..."):
                                        # Perform similarity search
                                        similar_docs = st.session_state.rag.find_similar(doc_id)
                                        if similar_docs:
                                            st.markdown("**Related Documents:**")
                                            for sim_doc in similar_docs:
                                                sim_score = sim_doc.get('similarity', 0.0)
                                                st.caption(f"- {sim_doc.get('file_path', 'Unknown')} ({sim_score:.2f})")
                                        else:
                                            st.caption("No similar documents found.")
                                except Exception as e:
                                    st.error(f"Error finding similar documents: {e}")
