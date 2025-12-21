import streamlit as st
import time
import datetime
import extra_streamlit_components as stx
from modules.rag_engine import RAGEngine
from modules.storage_client import StorageClient
from modules.llm_client import LLMClient
from modules.models import MODELS, DEFAULT_MODEL_ID, get_model_by_id
from modules.translations import TRANSLATIONS
from streamlit_tree_select import tree_select
from modules.tree_utils import build_folder_tree, load_folders_from_json
from modules.chat_history import ChatHistoryManager
import os
from pathlib import Path

# Helper Functions
def convert_to_pdf_path(file_path: str) -> str:
    """
    Convert markdown file paths to their PDF equivalents.
    - .md files: xxx/file.md → xxx/pdf/file.pdf
    - .txt files: keep as-is (no PDF version)
    
    Args:
        file_path: Original file path from database (e.g., "data/.../file.md")
    
    Returns:
        Converted path if .md, otherwise original path
    """
    if file_path.endswith('.md'):
        path_obj = Path(file_path)
        # Insert 'pdf/' directory before filename and change extension
        pdf_path = path_obj.parent / 'pdf' / path_obj.with_suffix('.pdf').name
        return str(pdf_path)
    # Keep .txt and other formats as-is
    return file_path

# Page Config
st.set_page_config(
    page_title="Advocado Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

# --- Authentication ---
# Note: experimental_allow_widgets parameter was removed in recent Streamlit versions
# If this causes issues with widgets in cache, we might need to remove caching or use a different pattern
# @st.cache_resource
# def get_manager():
#     return stx.CookieManager()

# cookie_manager = get_manager()
cookie_manager = stx.CookieManager()

def check_password():
    """Returns `True` if the user had the correct password."""
    
    # 1. Check for existing auth cookie
    # We use a simple check: if the cookie value matches the password, they are logged in.
    # In a real production app, you'd use a session token, but this is sufficient for this use case.
    auth_cookie = cookie_manager.get(cookie="advocado_auth")
    if auth_cookie == st.secrets["APP_PASSWORD"]:
        st.session_state["password_correct"] = True
        return True

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Check if the key exists in session state before accessing it
        if "password" in st.session_state and st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            # Set cookie to expire in 30 days
            expires = datetime.datetime.now() + datetime.timedelta(days=30)
            cookie_manager.set("advocado_auth", st.secrets["APP_PASSWORD"], expires_at=expires)
            # Don't delete the key immediately to avoid KeyError in the callback
            # del st.session_state["password"] 
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
        # Get translations for error message
        t_temp = TRANSLATIONS.get(st.session_state.get('language', 'English'), TRANSLATIONS['English'])
        st.error(t_temp["password_incorrect"])
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

if "history_manager" not in st.session_state:
    st.session_state.history_manager = ChatHistoryManager()

if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

if "rag" not in st.session_state:
    # Initialize engines only once
    try:
        st.session_state.rag = RAGEngine()
        st.session_state.storage = StorageClient()
        st.session_state.llm = LLMClient()
        st.session_state.initialized = True
    except Exception as e:
        t_temp = TRANSLATIONS.get(st.session_state.get('language', 'English'), TRANSLATIONS['English'])
        st.error(f"{t_temp['failed_to_initialize']}: {e}")
        st.session_state.initialized = False

# Sidebar
with st.sidebar:
    st.title("⚖️ Advocado AI")
    
    # Language Selection
    lang_options = list(TRANSLATIONS.keys())
    selected_lang = st.selectbox("Language / 言語", lang_options, index=0)
    t = TRANSLATIONS[selected_lang]
    
    st.markdown("---")
    
    # Chat History
    with st.expander(f"🕒 {t['history']}", expanded=False):
        col_new, col_manage = st.columns([3, 1])
        with col_new:
            if st.button(f"➕ {t['new_chat']}", use_container_width=True):
                st.session_state.messages = []
                st.session_state.current_conversation_id = None
                st.rerun()
        
        # Toggle for delete mode
        with col_manage:
            delete_mode = st.toggle("🗑️", key="delete_mode_toggle", help=t["enable_delete_mode"])

        recent_convos = st.session_state.history_manager.get_recent_conversations()
        
        if not recent_convos:
            st.caption(t["no_recent_chats"])
        
        for convo in recent_convos:
            # Truncate title if too long
            title = convo['title']
            if len(title) > 25:
                title = title[:25] + "..."
            
            if delete_mode:
                col_name, col_del = st.columns([4, 1])
                with col_name:
                    st.text(f"📄 {title}")
                with col_del:
                    if st.button("🗑️", key=f"del_{convo['id']}", help=t["delete_this_chat"]):
                        st.session_state.history_manager.delete_conversation(convo['id'])
                        # If deleted current conversation, reset state
                        if st.session_state.current_conversation_id == convo['id']:
                            st.session_state.messages = []
                            st.session_state.current_conversation_id = None
                        st.rerun()
            else:
                # Normal mode: Click to load
                # Highlight current conversation
                type_prefix = "📂" if st.session_state.current_conversation_id == convo['id'] else "📄"
                
                if st.button(f"{type_prefix} {title}", key=convo['id'], use_container_width=True):
                    # Load conversation
                    st.session_state.current_conversation_id = convo['id']
                    msgs = st.session_state.history_manager.get_messages(convo['id'])
                    # Convert DB format to UI format
                    st.session_state.messages = []
                    for m in msgs:
                        msg_obj = {"role": m["role"], "content": m["content"]}
                        if m.get("sources"):
                            msg_obj["sources"] = m["sources"]
                        st.session_state.messages.append(msg_obj)
                    st.rerun()

    # Navigation
    # Use a consistent key for the radio button to avoid state reset issues, 
    # but we need to handle the label change manually if we want it to persist across languages.
    # Actually, simpler: just check against both English and Japanese strings.
    page = st.radio(t["navigation"], [t["nav_chat"], t["nav_docs"]])
    
    st.markdown("---")
    st.markdown(f"**{t['system_online']}**" if st.session_state.get("initialized") else f"**{t['system_offline']}**")
    if st.session_state.get("initialized"):
        st.success(t["system_online"])
    else:
        st.error(t["system_offline"])
    
    # Check if page matches EITHER English OR Japanese "Chat" string
    # This ensures the sidebar renders even if the radio button state is slightly out of sync during a rerun
    is_chat_page = (page == TRANSLATIONS["English"]["nav_chat"]) or (page == TRANSLATIONS["Japanese"]["nav_chat"])
    
    if is_chat_page:
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
        
        # Folder Filter (Tree View)
        # Force reload or check type to avoid stale state issues
        # Reload if not in session, or if empty list (retry), or if malformed
        if "available_folders" not in st.session_state or not st.session_state.available_folders:
            # Try to load from JSON first (faster/better structure), fallback to DB
            json_path = "docs/search_by_folder/ingested_folders.json"
            if os.path.exists(json_path):
                print(f"Loading folders from {json_path}")
                folders = load_folders_from_json(json_path)
                print(f"Loaded {len(folders)} folders.")
                st.session_state.available_folders = folders
            else:
                # Fallback to DB fetch if JSON missing
                print("JSON not found, fetching from DB")
                folders = st.session_state.rag.get_available_folders()
                st.session_state.available_folders = folders
                print("Folders loaded from DB.")
        
        if st.button(f"🔄 {t['reload_folders']}"):
            if "available_folders" in st.session_state:
                del st.session_state.available_folders
            st.rerun()
        
        st.markdown(t["filter_by_folder"])
        
        # Sidebar Width Adjustment
        st.markdown("""
        <style>
        /* Widen the sidebar */
        [data-testid="stSidebar"] {
            min-width: 400px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f"### {t['select_folders']}")
        if not st.session_state.get("available_folders"):
            st.warning(t["no_folders_found"])
        else:
            selected_folders = st.multiselect(
                t["select_folders_to_search"],
                options=st.session_state.available_folders,
                default=[],
                key="folder_multiselect"
            )
            
        # selected_folders is already defined by the multiselect return value
        if 'selected_folders' not in locals():
            selected_folders = []
        
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
        
        # Advanced Search Options
        st.markdown(f"#### {t['advanced_search']}")
        search_mode = st.radio(
            t["search_mode"],
            options=[t["standard_fast"], t["deep_multilingual"]],
            index=0,
            help=t["search_mode_help"]
        )
        use_deep_search = search_mode == t["deep_multilingual"]
        
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
                        doc_score = source.get('doc_score')
                        chunk_count = source.get('chunk_count')
                        
                        # Convert to PDF path for display
                        display_path = convert_to_pdf_path(file_path)
                        display_name = os.path.basename(display_path)
                        
                        # Content Preview
                        if 'translated_preview' in source:
                            preview = source['translated_preview']
                        else:
                            content = source.get('content', '')
                            if not content and 'all_chunks' in source and source['all_chunks']:
                                 content = source['all_chunks'][0].get('content', '')
                            preview = content[:200].replace('\n', ' ') + "..." if content else ""
                        
                        # Check for Google Drive link first
                        url = source.get('google_drive_link')
                        if not url:
                            # Fallback to signed URL (use converted path)
                            url = st.session_state.storage.get_signed_url(display_path)
                        
                        # Display
                        score_val = doc_score if doc_score else similarity
                        chunk_info = f", {chunk_count} chunks" if chunk_count and chunk_count > 1 else ""
                        
                        st.markdown(f"**{i+1}. {display_name}** (Score: {score_val:.2f}{chunk_info})")
                        if preview:
                            st.caption(f"_{preview}_")
                            
                        if url:
                            st.markdown(f"[{t['open_file']}]({url})")
                        else:
                            st.markdown(f"*{t['link_unavailable']}*")

    # Chat Input
    if prompt := st.chat_input(t["chat_placeholder"]):
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Create conversation if needed
        if not st.session_state.current_conversation_id:
            # Generate title (simple for now)
            title = prompt[:30] + "..." if len(prompt) > 30 else prompt
            st.session_state.current_conversation_id = st.session_state.history_manager.create_conversation(title)
            
        # Save User Message
        st.session_state.history_manager.add_message(
            st.session_state.current_conversation_id, 
            "user", 
            prompt
        )
        
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Assistant Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown(t["searching"])
            
            # Get recent history for context (exclude current message)
            recent_history = st.session_state.messages[:-1][-5:] if len(st.session_state.messages) > 1 else []
            
            # A. Optimize Query
            start_time = time.time()
            print(f"[{time.strftime('%X')}] Starting query optimization...")
            
            if use_deep_search:
                # Deep Search Mode
                query_variants = st.session_state.llm.expand_query_multilingual(
                    prompt, 
                    recent_history, 
                    model_id=selected_model.api_id
                )
                print(f"[{time.strftime('%X')}] Deep Search Variants: {query_variants}")
                
                with st.expander(f"🔍 {t['deep_search_details']}", expanded=False):
                    st.write(f"{t['searching_with']}:")
                    st.json(query_variants)
                
                # B. Retrieve Context (Multilingual)
                search_start = time.time()
                results = st.session_state.rag.search_multilingual(
                    query_variants,
                    match_count=match_count,
                    threshold=threshold,
                    folder_filters=selected_folders if selected_folders else None
                )
                
                # For the LLM generation, we use the ORIGINAL query intent but pass the rich context
                # We can pass the 'translated' query as the 'optimized_query' for the LLM to understand context better if it was JP
                optimized_query = query_variants.get('translated', prompt)

            else:
                # Standard Mode
                optimization_result = st.session_state.llm.optimize_query(
                    prompt, 
                    recent_history, 
                    model_id=selected_model.api_id
                )
                optimized_query = optimization_result.get("query", prompt)
                date_filter = optimization_result.get("date_filter")
                
                print(f"[{time.strftime('%X')}] Optimization done ({time.time() - start_time:.2f}s): {optimized_query} (Date: {date_filter})")
                
                if optimized_query != prompt:
                    st.caption(f"🔍 Searched for: {optimized_query}")
                
                # B. Retrieve Context (Standard + Date)
                search_start = time.time()
                print(f"[{time.strftime('%X')}] Starting vector search with {len(selected_folders)} folders selected...")
                
                # 1. Vector Search
                results = st.session_state.rag.search(
                    optimized_query, 
                    match_count=match_count, 
                    threshold=threshold,
                    folder_filters=selected_folders if selected_folders else None
                )
                
                # 2. Date Search (if applicable)
                if date_filter:
                    print(f"[{time.strftime('%X')}] Performing date search for: {date_filter}")
                    date_results = st.session_state.rag.search_date(date_filter, match_count=match_count)
                    
                    # Merge results (prioritize date results)
                    # Create a map of existing IDs to avoid duplicates
                    existing_ids = {r['id'] for r in results}
                    
                    for dr in date_results:
                        if dr['id'] not in existing_ids:
                            results.insert(0, dr) # Add to top
                            existing_ids.add(dr['id'])
                        else:
                            # If it exists, update score to the boosted date score
                            for r in results:
                                if r['id'] == dr['id']:
                                    r['similarity'] = max(r['similarity'], dr['similarity'])
                                    break
                    
                    # Re-sort by similarity
                    results.sort(key=lambda x: x['similarity'], reverse=True)
                    results = results[:match_count] # Trim to match_count

            print(f"[{time.strftime('%X')}] Search complete ({time.time() - search_start:.2f}s). Found {len(results)} unique results.")
            
            if not results:
                response_text = t["no_results"]
                sources = []
            else:
                # C. Generate Answer
                gen_start = time.time()
                print(f"[{time.strftime('%X')}] Generating answer...")
                message_placeholder.markdown(t["analyzing"].format(model=selected_model.name))
                
                # UPDATED CALL: Unpack tuple
                response_text, previews = st.session_state.llm.generate_response(
                    prompt, 
                    results, 
                    history=recent_history,
                    model_id=selected_model.api_id
                )
                
                # Inject previews into results
                for i, res in enumerate(results):
                    idx = str(i + 1)
                    if idx in previews:
                        res['translated_preview'] = previews[idx]
                
                print(f"[{time.strftime('%X')}] Generation complete ({time.time() - gen_start:.2f}s)")
                sources = results

            # D. Display Final Response
            message_placeholder.markdown(response_text)
            
            # E. Save to History
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_text,
                "sources": sources
            })
            
            # Save Assistant Message to DB
            if st.session_state.current_conversation_id:
                st.session_state.history_manager.add_message(
                    st.session_state.current_conversation_id,
                    "assistant",
                    response_text,
                    sources=sources
                )
        
        # D. Display Sources (Immediate view)
        if sources:
            with st.expander(t["view_sources"], expanded=False):
                for i, source in enumerate(sources):
                    file_path = source['file_path']
                    similarity = source['similarity']
                    doc_id = source.get('id') # Ensure your RAG search returns 'id'
                    
                    # Get document-level metadata if available
                    chunk_count = source.get('chunk_count')
                    doc_score = source.get('doc_score')
                    
                    # Convert to PDF path for display
                    display_path = convert_to_pdf_path(file_path)
                    # CLEANUP: Show only filename
                    display_name = os.path.basename(display_path)
                    
                    # CONTENT PREVIEW
                    # Check for translated preview first
                    if 'translated_preview' in source:
                        preview = source['translated_preview']
                    else:
                        content = source.get('content', '')
                        # If aggregated, might be in 'all_chunks'
                        if not content and 'all_chunks' in source and source['all_chunks']:
                             content = source['all_chunks'][0].get('content', '')
                        
                        preview = content[:200].replace('\n', ' ') + "..." if content else ""

                    # Check for Google Drive link first
                    url = source.get('google_drive_link')
                    if not url:
                        # Fallback to signed URL (use converted path)
                        url = st.session_state.storage.get_signed_url(display_path)
                    
                    # Display with chunk count if available
                    score_display = f"{doc_score:.2f}" if doc_score else f"{similarity:.2f}"
                    chunk_info = f", {chunk_count} chunks" if chunk_count and chunk_count > 1 else ""
                    
                    st.markdown(f"**{i+1}. {display_name}** (Score: {score_display}{chunk_info})")
                    if preview:
                        st.caption(f"_{preview}_")
                    
                    if url:
                        st.markdown(f"[{t['open_file']}]({url})")
                    else:
                        # Show debug info in tooltip
                        debug_msg = st.session_state.storage.get_debug_info(display_path)
                        st.markdown(f"*{t['link_unavailable']}*", help=debug_msg)
