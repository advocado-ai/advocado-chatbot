#!/bin/bash
# Sync timeline_events.md from harassment project and track changes

set -e

# Paths
SOURCE_FILE="/media/syslogd/ENCRYPTED-DATA/UserFiles/ADMIN-PC/n/Documents/my_projects/harassment/evidence-timeline/_timeline_webpage/timeline_events.md"
DEST_DIR="imports/timeline_examples"
DEST_FILE="$DEST_DIR/timeline_events.md"
DIFF_DIR="$DEST_DIR/diffs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Ensure destination directories exist
mkdir -p "$DEST_DIR"
mkdir -p "$DIFF_DIR"

# Check if source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "❌ Source file not found: $SOURCE_FILE"
    exit 1
fi

# Check if destination file exists (for diff)
if [ -f "$DEST_FILE" ]; then
    echo "📊 Checking for changes..."
    
    # Create diff if files are different
    if ! diff -q "$SOURCE_FILE" "$DEST_FILE" > /dev/null 2>&1; then
        echo "🔄 Changes detected! Creating diff..."
        
        # Create unified diff
        diff -u "$DEST_FILE" "$SOURCE_FILE" > "$DIFF_DIR/timeline_diff_${TIMESTAMP}.diff" || true
        
        echo "✅ Diff saved to: $DIFF_DIR/timeline_diff_${TIMESTAMP}.diff"
        
        # Sync the file
        rsync -av --progress "$SOURCE_FILE" "$DEST_FILE"
        echo "✅ Timeline synced successfully!"
    else
        echo "✅ No changes detected. Timeline is up to date."
    fi
else
    echo "📥 First sync - no diff to generate."
    rsync -av --progress "$SOURCE_FILE" "$DEST_FILE"
    echo "✅ Timeline synced successfully!"
fi

echo ""
echo "📍 Timeline location: $DEST_FILE"
echo "📂 Diffs location: $DIFF_DIR"
