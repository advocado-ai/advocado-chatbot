#!/usr/bin/env python3
"""
Bulk generate PUBLIC "Anyone with the link" Google Drive links.
This script iterates through the full inventory and uses `rclone link` to generate
public links for files. It updates the cache to avoid re-generating existing links.

Usage:
    python generate_links.py [folder_filter]

Arguments:
    folder_filter (optional): Only process files in this folder (e.g., "evidence-timeline")
"""

import json
import subprocess
import os
import sys
import time
from pathlib import Path

# Configuration - Adjusted for Export Package Structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_FILE = os.path.join(DATA_DIR, "public_links.json")
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.json")
RCLONE_REMOTE = "google-drive-apac:harassment_backup/"

def load_json(filepath):
    if not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}")
        return {} if "links" in filepath else []
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def get_public_link(rclone_path):
    """Call rclone link to generate a public shareable link."""
    try:
        # rclone link remote:path/to/file
        full_path = f"{RCLONE_REMOTE}{rclone_path}"
        # Clean up double slashes if any
        full_path = full_path.replace("//", "/")
        
        result = subprocess.run(
            ['rclone', 'link', full_path],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        elif "not found" in result.stderr.lower():
            print(f"  [!] File not found on Drive: {full_path}")
            return None
        else:
            print(f"  [!] Error: {result.stderr.strip()}")
            return None
    except Exception as e:
        print(f"  [!] Exception: {str(e)}")
        return None

def main():
    filter_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    print(f"Working Directory: {BASE_DIR}")
    print("Loading inventory...")
    inventory = load_json(INVENTORY_FILE)
    if not inventory:
        print(f"Error: Inventory empty or not found at {INVENTORY_FILE}")
        return

    print("Loading cache...")
    cache_list = load_json(CACHE_FILE)
    
    # Normalize cache to dict
    if isinstance(cache_list, list):
        cache_map = {item['Path']: item.get('ShareableLink') for item in cache_list if 'ShareableLink' in item}
    else:
        cache_map = cache_list

    print(f"Found {len(inventory)} files in inventory.")
    print(f"Found {len(cache_map)} existing public links in cache.")
    
    processed = 0
    generated = 0
    errors = 0
    skipped = 0

    if not isinstance(inventory, list):
        print("Error: Inventory format incorrect.")
        return

    try:
        for item in inventory:
            file_path = item.get('Path')
            
            if item.get('IsDir'):
                continue

            if filter_path and not file_path.startswith(filter_path):
                continue

            processed += 1
            
            if file_path in cache_map:
                skipped += 1
                continue

            print(f"[{processed}/{len(inventory)}] Generating link for: {file_path}")
            
            public_link = get_public_link(file_path)
            
            if public_link:
                print(f"  -> {public_link}")
                cache_map[file_path] = public_link
                generated += 1
                
                # Save periodically
                if generated % 5 == 0:
                    # Quick save logic
                    pass
            else:
                errors += 1
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping...")

    print("\nSaving updated cache...")
    
    # Reconstruct cache list preserving original structure if possible, 
    # or just creating a clean list of objects with paths and links.
    
    # For the export package, let's keep it simple: List of objects with Path, ID, ShareableLink
    final_cache_list = []
    
    # We want to include EVERYTHING from the inventory that has a link in our map
    for item in inventory:
        path = item.get('Path')
        if path in cache_map:
            # Create a clean entry
            entry = item.copy()
            entry['ShareableLink'] = cache_map[path]
            final_cache_list.append(entry)
            
    save_json(CACHE_FILE, final_cache_list)
    print(f"Saved {len(final_cache_list)} entries to {CACHE_FILE}")
    print(f"Summary: Generated {generated}, Skipped {skipped}, Errors {errors}")

if __name__ == "__main__":
    main()
