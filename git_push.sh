#!/bin/bash

# to make it executable, run chmod +x git_push.sh

# Navigate to the directory of the script
cd "$(dirname "$0")"

# Ensure we're in a git repo
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
  echo "❌ Not a Git repository. Aborting."
  exit 1
fi

# Confirm current branch is 'main'
branch=$(git symbolic-ref --short HEAD)
if [ "$branch" != "main" ]; then
  echo "⚠️  You're on branch '$branch', not 'main'. Aborting push."
  exit 1
fi

# Stage all changes
git add .

# Skip commit if no staged changes
git diff --cached --quiet && echo "✅ No changes to commit." && exit 0

# Commit with a default message (customize as needed)
git commit -m "തന്നതാൻ മാഺം - श्रीराम"

# Push to the main branch
echo "🚀 Pushing changes to origin/main..."
git push origin main
