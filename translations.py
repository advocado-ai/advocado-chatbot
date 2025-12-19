TRANSLATIONS = {
    "English": {
        "nav_chat": "Chat Assistant",
        "nav_docs": "Documentation",
        "system_online": "System Online",
        "system_offline": "System Offline",
        "settings": "Settings",
        "model_config": "Model Configuration",
        "select_model": "Select Model",
        "model_info": "ℹ️ Model Info",
        "search_params": "Search Parameters",
        "evidence_chunks": "Evidence Chunks",
        "evidence_chunks_help": "Number of evidence snippets to retrieve from the database. Higher values provide more context but may increase noise.",
        "similarity_threshold": "Similarity Threshold",
        "similarity_threshold_help": "Minimum relevance score (0-1). Lower values include more loosely related documents; higher values are stricter.",
        "clear_history": "Clear Chat History",
        "app_title": "Legal Evidence Assistant",
        "app_intro": "Ask questions about the case evidence. I will search the vector database and cite specific documents.",
        "view_sources": "📚 View Cited Evidence Sources",
        "chat_placeholder": "What evidence do we have regarding...",
        "searching": "🔍 Searching evidence database...",
        "analyzing": "🤔 Analyzing documents with {model}...",
        "no_results": "I couldn't find any relevant evidence in the database matching your query.",
        "open_file": "Open File ↗️",
        "link_unavailable": "Link unavailable",
        "docs_title": "📚 Application Documentation",
        "docs_overview_title": "Overview",
        "docs_overview_text": "This application uses Retrieval Augmented Generation (RAG) to help you search and analyze the evidence database.",
        "docs_how_title": "How it Works",
        "docs_how_text": """1. **Search**: Your question is converted into a mathematical vector.
2. **Retrieval**: We search the Supabase database for the most similar evidence chunks.
3. **Generation**: The selected AI model (Claude) reads the evidence and answers your question.""",
        "docs_settings_title": "Settings Explained",
        "docs_models_title": "🧠 Model Selection",
        "docs_models_text": """*   **Claude Sonnet 4.5**: The default, balanced model. Good for most legal reasoning.
*   **Claude Haiku 4.5**: Faster, cheaper, but slightly less nuanced. Good for simple lookups.
*   **Claude Opus 4.5**: The most powerful model. Use for complex reasoning or drafting, but it is slower.""",
        "docs_search_title": "🔍 Search Parameters",
        "docs_search_text": """*   **Evidence Chunks**: Controls *how much* text the AI reads. 
    *   *Increase* if the answer requires synthesizing many small details.
    *   *Decrease* if you want focused answers or if the AI is getting confused by irrelevant info.
*   **Similarity Threshold**: Controls *quality control*.
    *   **0.0**: "Show me everything, even if it's barely relevant."
    *   **0.5**: "Only show me things that are clearly about this topic."
    *   **0.8**: "Only show me exact matches."
    *   *Recommended*: 0.3 - 0.5 for general queries.""",
        "docs_security_title": "Security",
        "docs_security_text": """*   This application is password protected.
*   Evidence files are stored in a private Supabase bucket.
*   Links to files are temporary (signed URLs) and expire after 1 hour.""",
        "password_incorrect": "😕 Password incorrect",
        "failed_to_initialize": "Failed to initialize application",
        "history": "History",
        "new_chat": "New Chat",
        "delete_this_chat": "Delete this chat",
        "enable_delete_mode": "Enable delete mode",
        "no_recent_chats": "No recent chats.",
        "navigation": "Navigation",
        "reload_folders": "Reload Folders",
        "filter_by_folder": "Filter by Folder",
        "select_folders": "Select Folders",
        "no_folders_found": "No folders found.",
        "select_folders_to_search": "Select folders to search in:",
        "advanced_search": "Advanced Search",
        "search_mode": "Search Mode",
        "standard_fast": "Standard (Fast)",
        "deep_multilingual": "Deep Multilingual (Slower, High Recall)",
        "search_mode_help": "Standard: Single optimized query. Deep: Searches with original, keywords, and translated queries.",
        "deep_search_details": "Deep Search Details",
        "searching_with": "Searching with:"
    },
    "Japanese": {
        "nav_chat": "チャットアシスタント",
        "nav_docs": "ドキュメント",
        "system_online": "システム稼働中",
        "system_offline": "システムオフライン",
        "settings": "設定",
        "model_config": "モデル設定",
        "select_model": "モデル選択",
        "model_info": "ℹ️ モデル情報",
        "search_params": "検索パラメータ",
        "evidence_chunks": "証拠チャンク数",
        "evidence_chunks_help": "データベースから取得する証拠スニペットの数。値を大きくするとコンテキストが増えますが、ノイズも増える可能性があります。",
        "similarity_threshold": "類似度しきい値",
        "similarity_threshold_help": "最小関連度スコア（0-1）。値を小さくすると関連性の低い文書も含まれ、大きくすると厳密になります。",
        "clear_history": "チャット履歴を消去",
        "app_title": "法的証拠アシスタント",
        "app_intro": "事件の証拠について質問してください。ベクトルデータベースを検索し、特定の文書を引用します。",
        "view_sources": "📚 引用された証拠ソースを表示",
        "chat_placeholder": "〜に関する証拠は何がありますか...",
        "searching": "🔍 証拠データベースを検索中...",
        "analyzing": "🤔 {model} で文書を分析中...",
        "no_results": "クエリに一致する関連証拠がデータベースに見つかりませんでした。",
        "open_file": "ファイルを開く ↗️",
        "link_unavailable": "リンク利用不可",
        "docs_title": "📚 アプリケーションドキュメント",
        "docs_overview_title": "概要",
        "docs_overview_text": "このアプリケーションは、検索拡張生成（RAG）を使用して、証拠データベースの検索と分析を支援します。",
        "docs_how_title": "仕組み",
        "docs_how_text": """1. **検索**: 質問は数学的なベクトルに変換されます。
2. **取得**: Supabaseデータベースから最も類似した証拠チャンクを検索します。
3. **生成**: 選択されたAIモデル（Claude）が証拠を読み、質問に答えます。""",
        "docs_settings_title": "設定の説明",
        "docs_models_title": "🧠 モデル選択",
        "docs_models_text": """*   **Claude Sonnet 4.5**: デフォルトのバランスの取れたモデル。ほとんどの法的推論に適しています。
*   **Claude Haiku 4.5**: 高速で安価ですが、ニュアンスが少し劣ります。単純な検索に適しています。
*   **Claude Opus 4.5**: 最も強力なモデル。複雑な推論や起草に使用しますが、速度は遅くなります。""",
        "docs_search_title": "🔍 検索パラメータ",
        "docs_search_text": """*   **証拠チャンク数**: AIが読むテキストの*量*を制御します。
    *   *増やす*: 回答に多くの小さな詳細を統合する必要がある場合。
    *   *減らす*: 焦点の絞った回答が必要な場合、またはAIが無関係な情報に混乱している場合。
*   **類似度しきい値**: *品質管理*を制御します。
    *   **0.0**: 「関連性が低くてもすべて表示」
    *   **0.5**: 「明らかにこのトピックに関するものだけ表示」
    *   **0.8**: 「完全一致のみ表示」
    *   *推奨*: 一般的なクエリでは 0.3 - 0.5""",
        "docs_security_title": "セキュリティ",
        "docs_security_text": """*   このアプリケーションはパスワードで保護されています。
*   証拠ファイルはプライベートなSupabaseバケットに保存されています。
*   ファイルへのリンクは一時的（署名付きURL）で、1時間後に期限切れになります。""",
        "password_incorrect": "😕 パスワードが正しくありません",
        "failed_to_initialize": "アプリケーションの初期化に失敗しました",
        "history": "履歴",
        "new_chat": "新しいチャット",
        "delete_this_chat": "このチャットを削除",
        "enable_delete_mode": "削除モードを有効化",
        "no_recent_chats": "最近のチャットはありません。",
        "navigation": "ナビゲーション",
        "reload_folders": "フォルダを再読み込み",
        "filter_by_folder": "フォルダでフィルタ",
        "select_folders": "フォルダを選択",
        "no_folders_found": "フォルダが見つかりません。",
        "select_folders_to_search": "検索するフォルダを選択:",
        "advanced_search": "詳細検索",
        "search_mode": "検索モード",
        "standard_fast": "標準（高速）",
        "deep_multilingual": "深層多言語（低速、高再現率）",
        "search_mode_help": "標準：単一の最適化されたクエリ。深層：元のクエリ、キーワード、翻訳されたクエリで検索します。",
        "deep_search_details": "深層検索の詳細",
        "searching_with": "次の条件で検索中:"
    }
}
