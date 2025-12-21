import streamlit as st
from supabase import create_client

# Initialize Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

target_date = "2025-12-18"
print(f"Checking for records with date_prefix = '{target_date}'")

try:
    # Query for the specific date
    response = supabase.table("evidence_vectors") \
        .select("id, file_path, date_prefix") \
        .eq("date_prefix", target_date) \
        .execute()

    data = response.data

    if data:
        print(f"\n✅ Found {len(data)} chunks with date {target_date}:")
        
        unique_files = set()
        
        for row in data:
            print(f"ID: {row['id']}")
            print(f"File: {row['file_path']}")
            print("-" * 30)
            unique_files.add(row['file_path'])
            
        print("\n" + "="*40)
        print("📊 SUMMARY STATS")
        print("="*40)
        print(f"Total Chunks Found: {len(data)}")
        print(f"Total Unique Files: {len(unique_files)}")
        print("\nUnique Files List:")
        for f in sorted(unique_files):
            print(f" - {f}")
            
    else:
        print(f"\n❌ No records found with date_prefix = '{target_date}'")
        print("The target file exists but has date_prefix = None.")

except Exception as e:
    print(f"\n❌ Error querying database: {e}")