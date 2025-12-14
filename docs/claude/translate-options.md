**Google Drive doesn't have built-in PDF translation**, unfortunately. The Google Translate integration only works for Google Docs format, not PDFs.

**Options for your lawyer:**

**Option 1: Chrome extension (easiest for PC)**
- **Google Translate extension** - he can select text in the PDF viewer and right-click → Translate
- **ImTranslator** or similar extensions - offer PDF translation features
- Works in Drive's PDF viewer

**Option 2: Convert to Google Docs (best for full translation)**
You or he can:
1. Right-click PDF in Drive → "Open with" → "Google Docs"
2. It converts to Docs format
3. Tools → Translate document
4. Gets full Japanese version

**Downside:** Formatting might break, OCR quality varies

**Option 3: Build it into your chatbot (BEST for your use case)**

Since you're already building a Streamlit app with Claude, you could:

```python
# When showing a source document
if st.button(f"Translate {filename} to Japanese"):
    # Extract text from PDF
    pdf_text = extract_pdf_text(file_path)
    
    # Use Claude to translate
    translation = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{
            "role": "user", 
            "content": f"Translate this legal document to Japanese:\n\n{pdf_text}"
        }]
    )
    
    st.markdown(translation.content[0].text)
    
    # Option: save translated version to Drive
```

**Option 4: Pre-translate critical documents**

For the most important evidence (the "nuclear option" docs you're compiling), you could:
- Run them through Claude/Google Translate API
- Upload both English and Japanese versions to Drive
- Name them clearly: `evidence_001_EN.pdf` and `evidence_001_JA.pdf`

**Given your timeline and that your lawyer needs to review videos too**, I'd suggest:
1. **Short term:** Ask him to use Chrome's right-click translate for quick spot checks
2. **For key documents:** Pre-translate the most critical ones and upload Japanese versions
3. **If you have time:** Add a translate button to your chatbot for any retrieved document

Your lawyer will probably appreciate having Japanese summaries from the chatbot anyway - Claude can answer in Japanese even when searching English evidence.

Want help adding Japanese translation to the chatbot responses?
