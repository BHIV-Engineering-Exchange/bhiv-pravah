#!/bin/bash

# GitHub Repository Upload Script for AI Agent Logistics System
# Run this script to upload your project to GitHub

echo "🚀 AI Agent Logistics System - GitHub Upload"
echo "============================================="

# Navigate to project directory
cd "/Users/rishabh/Desktop/Voice bot/ai-agent_project"

# Check if we're in the right directory
if [ ! -f "api_app.py" ]; then
    echo "❌ Error: Not in project directory"
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo "📊 Files to upload: $(git ls-files | wc -l) files"

# Show current git status
echo "📋 Git Status:"
git status --short

# Set up authentication (you'll need to enter your GitHub token when prompted)
echo ""
echo "🔑 Setting up GitHub authentication..."
echo "When prompted for password, use your GitHub Personal Access Token"
echo ""

# Configure git to use token for this session
git config credential.helper 'cache --timeout=3600'

# Set up authentication with username in URL
echo "🔧 Configuring remote URL with authentication..."
git remote set-url origin https://blackholeinfiverse51@github.com/blackholeinfiverse51/ai-agent-logistics-system.git

# Try to push with authentication
echo "📤 Pushing to GitHub repository..."
echo "💡 When prompted for password, use your GitHub Personal Access Token (not your GitHub password)"
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Project uploaded to GitHub"
    echo "🌐 Repository URL: https://github.com/blackholeinfiverse51/ai-agent-logistics-system"
    echo ""
    echo "📋 What was uploaded:"
    echo "   - Complete AI Agent System (84+ files)"
    echo "   - Professional documentation"
    echo "   - Ready-to-run codebase"
    echo "   - Docker and cloud deployment configs"
    echo ""
else
    echo ""
    echo "❌ Upload failed. Please check:"
    echo "   1. GitHub repository exists: https://github.com/blackholeinfiverse51/ai-agent-logistics-system"
    echo "   2. You have write access to the repository"
    echo "   3. Your GitHub Personal Access Token is valid"
    echo ""
    echo "🔧 Manual upload option:"
    echo "   Visit: https://github.com/blackholeinfiverse51/ai-agent-logistics-system"
    echo "   Click: 'uploading an existing file'"
    echo "   Upload: README.md first, then other files"
fi

echo ""
echo "📖 For detailed setup instructions, see GITHUB_SETUP.md"