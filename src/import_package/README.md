# Export Package for External Repo

This folder contains the tools and data needed to generate Google Drive links for the Harassment Project files in an external repository (e.g., Vector DB ingestion).

## Contents

*   `data/inventory.json`: A complete list of all files in the project, including their Google Drive IDs and standard (private) URLs.
*   `data/public_links.json`: A cache of files that have "Anyone with the link" public URLs generated.
*   `generate_links.py`: A script to generate new public links for files in the inventory.

## Usage

### 1. Copy this folder
Copy the entire `_export_package` folder to your other repository.

### 2. Generate Public Links
If you need public links for specific files (e.g., to embed in a Notion page or public report), run the script:

```bash
# Generate links for a specific folder
python3 generate_links.py evidence-timeline

# Generate links for everything (takes time)
python3 generate_links.py
```

The script will:
1.  Check `data/inventory.json` for the file.
2.  Check `data/public_links.json` to see if a link already exists.
3.  If not, use `rclone` to generate a new public link.
4.  Save the result back to `data/public_links.json`.

### 3. Using the Data
Your external application can read `data/inventory.json` to get the file structure and IDs.
If it needs public links, it should look up the file path in `data/public_links.json`.

## Updating Data (Staleness)

The data in `data/` is a snapshot. To update it:

1.  Go to the main `harassment` project.
2.  Run the main sync workflow to ensure Google Drive is up to date.
3.  Run `python3 _sync_google_drive/generate_full_url_list.py` to update the inventory.
4.  Copy the new files to this package:
    *   `full_gdrive_inventory.json` -> `_export_package/data/inventory.json`
    *   `_sync_google_drive/mappings/gdrive_link_cache.json` -> `_export_package/data/public_links.json`

## Requirements
*   Python 3
*   `rclone` configured with the remote `google-drive-apac:harassment_backup/`
