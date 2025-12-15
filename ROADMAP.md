# Development Roadmap: Persistent Chat & Session Management

## Phase 1: Session Persistence (Stop Logging Out)
**Goal:** Ensure browser refreshes do not require re-login or clear the current view.
- [ ] **Cookie Management**: Install `extra-streamlit-components` to manage browser cookies.
- [ ] **Auth Update**: Modify `app.py` to set a secure cookie upon successful login. On startup, check for this cookie to bypass the login screen automatically.

## Phase 2: Database-Backed Chat History
**Goal:** Enable a "ChatGPT-style" sidebar where past research threads are saved and accessible.
- [ ] **Supabase Schema**: Create two new tables:
    *   `conversations`: Stores session ID, title (e.g., "First query..."), and timestamps.
    *   `messages`: Stores the actual text, role (user/assistant), and—crucially—the **JSON source data** (so citations still work when reloading old chats).
- [ ] **Save Logic**: Update `app.py` to write every message to Supabase immediately after generation.
- [ ] **Sidebar UI**: Add a "History" section in the sidebar listing the last 20 conversations. Clicking one loads that history into the main view.

## Phase 3: High-Utility Features (Beating the Email)
**Goal:** Make the tool more useful than a static email.
- [ ] **"Copy for Email" Button**: Add a button below each answer that formats the text and Google Drive links into a clean, clipboard-ready format for Ogasawara-sensei to paste into his correspondence.
- [ ] **"Pin" Evidence**: (Future) Allow "starring" specific documents to a "Case Dossier" list in the sidebar, independent of the chat.

## Considerations
- **Privacy**: Currently assuming **Shared History** for collaboration simplicity.
- **Title Generation**: Use LLM to auto-generate titles for conversations.
