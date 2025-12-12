import os
import argparse
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
# Prefer .env.cloud for this script as it's intended for the cloud chatbot
if os.path.exists('.env.cloud'):
    load_dotenv('.env.cloud')
    print("Loaded configuration from .env.cloud")
else:
    load_dotenv()
    print("Loaded configuration from .env")

def sync_to_storage(
    mappings: list,
    bucket_name: str = "evidence-files",
    supabase_url: str = None,
    supabase_key: str = None
):
    """
    Syncs local directories to a Supabase Storage bucket with specific path mappings.
    
    Args:
        mappings: List of tuples (local_path, storage_prefix)
        bucket_name: Name of the Supabase bucket
    """
    url = supabase_url or os.getenv("SUPABASE_URL")
    # Prefer Service Role Key for admin tasks (uploads), fall back to provided key or env var
    key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_LEGACY_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) must be set.")
        return

    print(f"Connecting to Supabase at: {url}")
    if os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_LEGACY_SERVICE_ROLE_KEY"):
        print("Using Service Role Key (Admin Access)")
    else:
        print("Using Standard/Anon Key (Check RLS policies if upload fails)")

    client: Client = create_client(url, key)
    
    # Check bucket
    try:
        buckets = client.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        if bucket_name not in bucket_names:
            print(f"Warning: Bucket '{bucket_name}' not found in bucket list.")
            print("Attempting to proceed anyway (bucket might be private and unlisted)...")
        else:
            print(f"✓ Bucket '{bucket_name}' found.")
    except Exception as e:
        print(f"Warning: Could not list buckets ({e}). Proceeding anyway...")

    total_count = 0
    total_errors = 0
    error_log = []

    for local_dir, storage_prefix in mappings:
        base_path = Path(local_dir)
        if not base_path.exists():
            print(f"Warning: Local directory '{local_dir}' does not exist. Skipping.")
            continue

        print(f"\nSyncing '{local_dir}' -> '{bucket_name}/{storage_prefix}'...")
        
        for file_path in base_path.rglob("*"):
            if file_path.is_file():
                if '.git' in str(file_path) or file_path.name.startswith('.'):
                    continue
                
                # Calculate relative path from the source folder
                # e.g. /media/.../evidence-timeline/folder/file.md -> folder/file.md
                rel_path = file_path.relative_to(base_path)
                
                # Construct storage path
                # e.g. data/harassment/evidence-timeline/folder/file.md
                storage_path = f"{storage_prefix}/{rel_path}".replace("//", "/")
                
                try:
                    with open(file_path, 'rb') as f:
                        client.storage.from_(bucket_name).upload(
                            path=storage_path,
                            file=f,
                            file_options={"content-type": "text/markdown", "upsert": "true"}
                        )
                    print(f"✅ Uploaded: {storage_path}")
                    total_count += 1
                except Exception as e:
                    print(f"❌ Failed: {storage_path} - {e}")
                    error_log.append(f"{storage_path}: {str(e)}")
                    total_errors += 1

    print(f"\nSync Complete.")
    print(f"Total Uploaded: {total_count}")
    print(f"Total Errors: {total_errors}")
    
    if error_log:
        with open("sync_errors.log", "w") as f:
            f.write("\n".join(error_log))
        print("Errors written to sync_errors.log")

if __name__ == "__main__":
    # Hardcoded mappings based on user request
    # (local_path, storage_prefix)
    # The storage_prefix should match the path structure in the vector DB (relative to project root)
    
    MAPPINGS = [
        (
            "/media/syslogd/ENCRYPTED-DATA/UserFiles/ADMIN-PC/n/Documents/my_projects/harassment/evidence-timeline",
            "data/harassment/evidence-timeline"
        ),
        (
            "/media/syslogd/ENCRYPTED-DATA/UserFiles/ADMIN-PC/n/Documents/my_projects/harassment/ppc_submission",
            "data/harassment/ppc_submission"
        )
    ]
    
    sync_to_storage(MAPPINGS)
