#!/bin/bash

# Update Export Package Data
# This script refreshes the data in the export package from the main project.

PROJECT_ROOT="/media/syslogd/ENCRYPTED-DATA/UserFiles/ADMIN-PC/n/Documents/my_projects/harassment"
EXPORT_DIR="$PROJECT_ROOT/_export_package"

echo "Updating Export Package Data..."

# 1. Generate latest inventory
echo "Generating latest inventory..."
cd "$PROJECT_ROOT"
python3 _sync_google_drive/generate_full_url_list.py

# 2. Copy files
echo "Copying files..."
cp "$PROJECT_ROOT/full_gdrive_inventory.json" "$EXPORT_DIR/data/inventory.json"
cp "$PROJECT_ROOT/_sync_google_drive/mappings/gdrive_link_cache.json" "$EXPORT_DIR/data/public_links.json"

echo "Done! Export package data is up to date."
echo "Location: $EXPORT_DIR"
