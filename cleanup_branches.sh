#!/bin/bash
# Cleanup script for advocado-chatbot repository

set -e

cd /media/syslogd/ENCRYPTED-DATA/UserFiles/ADMIN-PC/n/Documents/my_projects/advocado-chatbot

echo "=========================================="
echo "ADVOCADO CHATBOT - BRANCH CLEANUP"
echo "=========================================="

# 1. Remove backup if it exists
echo ""
echo "1. Checking for git-filter-repo backup..."
BACKUP_DIR="/tmp/advocado-chatbot-backup-20251220-174644"
if [ -d "$BACKUP_DIR" ]; then
    echo "   Found backup at: $BACKUP_DIR"
    du -sh "$BACKUP_DIR"
    rm -rf "$BACKUP_DIR"
    echo "   ✓ Backup removed"
else
    echo "   ✓ No backup found (already cleaned)"
fi

# 2. Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo ""
echo "2. Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "master" ]; then
    echo "   Switching to master..."
    git checkout master
fi

# 3. List all local branches
echo ""
echo "3. Current local branches:"
git branch -vv

# 4. Delete local branches except master
echo ""
echo "4. Deleting local branches (keeping only master)..."
for branch in $(git branch | grep -v "master" | sed 's/\*//g' | xargs); do
    echo "   Deleting local branch: $branch"
    git branch -D "$branch"
done

# 5. List remote branches
echo ""
echo "5. Current remote branches:"
git branch -r

# 6. Delete remote branches except master
echo ""
echo "6. Deleting remote branches (keeping only master)..."
for branch in $(git branch -r | grep -v "master" | grep "origin/" | sed 's/origin\///g' | xargs); do
    echo "   Deleting remote branch: origin/$branch"
    git push origin --delete "$branch"
done

# 7. Final status
echo ""
echo "=========================================="
echo "✓ CLEANUP COMPLETE"
echo "=========================================="
echo ""
echo "Local branches:"
git branch -vv
echo ""
echo "Remote branches:"
git branch -r
echo ""
