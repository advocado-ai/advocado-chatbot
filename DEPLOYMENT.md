# Deployment Guide for Advocado Chatbot

This guide explains how to deploy the Advocado Chatbot as a standalone application.

## 1. Project Structure

We have separated the chatbot into its own dedicated folder/repository to keep it clean and isolated from the main `advocado` project.

**Location**: `../advocado-chatbot/` (or wherever you moved it)

## 2. Local Development

To run the app on your local machine for testing:

1.  **Navigate to the folder**:
    ```bash
    cd ../advocado-chatbot
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Secrets**:
    Ensure `.streamlit/secrets.toml` exists and contains your keys:
    ```toml
    APP_PASSWORD = "your-password"
    SUPABASE_URL = "..."
    SUPABASE_KEY = "..."
    ANTHROPIC_API_KEY = "..."
    ```

4.  **Run the App**:
    ```bash
    streamlit run app.py
    ```
    Access it at `http://localhost:8501`.

## 3. Deploying to Streamlit Cloud

Streamlit Cloud is the easiest way to host this app securely.

### Step A: Create a GitHub Repository
1.  Create a new **Private** repository on GitHub named `advocado-chatbot`.
2.  Initialize git in your local folder and push:
    ```bash
    cd ../advocado-chatbot
    git init
    git add .
    git commit -m "Initial commit"
    
    # Replace with your actual repo URL
    git remote add origin git@github.com:yourusername/advocado-chatbot.git
    git branch -M main
    git push -u origin main
    ```
    *Note: The `.gitignore` file ensures `secrets.toml` is NOT uploaded to GitHub.*

### Step B: Deploy
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **New app**.
3.  Select your `advocado-chatbot` repository.
4.  Set **Main file path** to `app.py`.
5.  Click **Advanced Settings** -> **Secrets**.
6.  Paste the contents of your local `.streamlit/secrets.toml` into the text box.
7.  Click **Deploy**.

## 4. Security

*   **App Password**: The app is protected by a password defined in `secrets.toml` (`APP_PASSWORD`).
*   **Private Repo**: Keep the GitHub repo private.
*   **Private Bucket**: The Supabase bucket `evidence-files` is private. The app generates temporary signed URLs for access.
