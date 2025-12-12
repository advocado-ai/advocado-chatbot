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
*   **`llm_client.py`**: Generates answers using OpenAI.
