# Advocado Legal Chatbot

A Streamlit-based RAG (Retrieval Augmented Generation) application for legal counsel to query the evidence database.

## Setup Instructions

### 1. Supabase Setup
1.  **Create Bucket**: Go to Supabase Dashboard -> Storage. Create a new bucket named `evidence-files`.
    *   **Important**: Make it **Private** (Public Access disabled).
2.  **Upload Files**: Run the sync script to upload your local `data/` folder to this bucket.
    ```bash
    # From project root
    export SUPABASE_URL="your_url"
    export SUPABASE_KEY="your_service_role_key" # Use SERVICE_ROLE key for writing to storage if anon doesn't have permission
    
    python src/c2c_chatbot/sync_storage.py --dir data
    ```

### 2. Streamlit Setup (Local)
1.  Install dependencies:
    ```bash
    pip install -r src/c2c_chatbot/requirements.txt
    ```
2.  Create `.streamlit/secrets.toml` in the project root (or `src/c2c_chatbot/.streamlit/secrets.toml` if running from there, but usually root is better for paths).
    ```toml
    # App Security
    APP_PASSWORD = "your-secure-password-here"

    # Supabase Configuration
    SUPABASE_URL = "your_supabase_url"
    SUPABASE_KEY = "your_supabase_anon_key"
    
    # OpenAI Configuration
    OPENAI_API_KEY = "your_openai_key"
    ```
3.  Run the app:
    ```bash
    streamlit run src/c2c_chatbot/app.py
    ```

### 3. Deployment (Streamlit Cloud)
1.  Push code to GitHub.
2.  Sign up for [Streamlit Cloud](https://streamlit.io/cloud).
3.  Connect your GitHub repo.
4.  In the Streamlit Cloud dashboard for your app, go to **Settings -> Secrets** and paste the content of your `secrets.toml`.
5.  Deploy!

## Architecture
*   **`app.py`**: The UI.
*   **`rag_engine.py`**: Vector search logic.
*   **`storage_client.py`**: Generates secure links to files.
*   **`llm_client.py`**: Generates answers using Anthropic Claude.
*   **`models.py`**: Configuration for available LLM models.

## Supported Models
The application supports the following Anthropic models (configurable via UI):
*   **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`): Best balance of intelligence and speed.
*   **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`): Fastest model.
*   **Claude Opus 4.5** (`claude-opus-4-5-20251101`): Maximum intelligence.

## Security & Sharing

### Password Protection
The application is protected by a simple password mechanism.
*   The password is set in `.streamlit/secrets.toml` under `APP_PASSWORD`.
*   Users must enter this password to access the chat interface.

### Sharing the App
To share the app with others:
1.  **Deploy to Streamlit Cloud**: Connect your private GitHub repository to Streamlit Cloud.
2.  **Invite Users**:
    *   **Option A (Secure)**: Use Streamlit Cloud's "Invite" feature to give access only to specific email addresses.
    *   **Option B (Password)**: Share the public URL and the `APP_PASSWORD` with your intended users.
3.  **Data Privacy**:
    *   The GitHub repository should be **Private**.
    *   The Supabase Storage bucket should be **Private**.
    *   The app generates temporary, signed URLs for viewing evidence files, which expire after 1 hour.


