#!/bin/bash

# Simple Push Script for HW2

cd ~/Documents/GitHub/hws_repo

echo "═══════════════════════════════════════════"
echo "  Pushing HW2 to GitHub"
echo "═══════════════════════════════════════════"
echo ""
echo "Repository: mmf-code/hws"
echo "Branch: claude/sensor-integration-visualization-..."
echo ""
echo "Commits to push: 4"
echo "  - Update RViz config after testing"
echo "  - Complete HW2: Sensor integration, visualization, and documentation"
echo "  - Add quick start guides for HW2 simulation"
echo "  - Clean up nested workspace structure"
echo ""

# Check git status
echo "Checking git status..."
git status

echo ""
echo "─────────────────────────────────────────────"
echo "Ready to push!"
echo "─────────────────────────────────────────────"
echo ""
echo "Option 1: Use GitHub Desktop (recommended)"
echo "  1. Open GitHub Desktop"
echo "  2. Select 'hws_repo' repository"
echo "  3. Click 'Push origin' button"
echo ""
echo "Option 2: Use terminal with credentials"
echo "  Run: git push"
echo "  Enter GitHub username and Personal Access Token"
echo ""
echo "Press Enter to attempt automatic push..."
read

echo "Attempting push..."
git push

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! All commits pushed to GitHub!"
    echo ""
    echo "View your code at:"
    echo "https://github.com/mmf-code/hws"
else
    echo ""
    echo "❌ Push failed. Please use GitHub Desktop or:"
    echo "   git config credential.helper store"
    echo "   git push"
    echo "   (then enter username + token)"
fi
