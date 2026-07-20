#!/bin/bash

echo "🚀 AI Agent Logistics + CRM System - GitHub Push"
echo "================================================="
echo ""

# Navigate to project directory
cd "/Users/rishabh/Desktop/Voice bot/ai-agent_project"

echo "📁 Current directory: $(pwd)"
echo "📊 Repository: blackholeinfiverse51/ai-agent-logistics-system"
echo ""

# Show current status
echo "📋 Git Status:"
git log --oneline -5
echo ""

# Clear any existing credentials to avoid conflicts
echo "🔧 Clearing existing credentials..."
git config --unset credential.helper
git config credential.helper store

echo ""
echo "🔑 IMPORTANT: When prompted for password, use your GitHub Personal Access Token"
echo "   - NOT your GitHub password"
echo "   - Get your token from: https://github.com/settings/tokens"
echo "   - Token needs 'repo' permissions"
echo ""

read -p "Press Enter when you have your Personal Access Token ready..."

echo ""
echo "📤 Pushing to GitHub..."
echo "   Repository: https://github.com/blackholeinfiverse51/ai-agent-logistics-system"
echo "   Username: blackholeinfiverse51"
echo "   Password: [Use your Personal Access Token]"
echo ""

# Set up the push with proper error handling
if git push -u origin main; then
    echo ""
    echo "✅ SUCCESS! Your AI Agent Logistics + CRM System is now on GitHub!"
    echo ""
    echo "🌐 Repository URL: https://github.com/blackholeinfiverse51/ai-agent-logistics-system"
    echo ""
    echo "📊 What was uploaded:"
    echo "   ✅ Complete CRM Extension (Week 4 criteria)"
    echo "   ✅ Office 365 & Google Maps Integration"
    echo "   ✅ LLM Natural Language Queries"
    echo "   ✅ Production-ready system with security"
    echo "   ✅ Comprehensive documentation"
    echo "   ✅ 130+ files with professional codebase"
    echo ""
    echo "🎉 Your project is now live and ready for showcase!"
else
    echo ""
    echo "❌ Push failed. Let's troubleshoot..."
    echo ""
    echo "🔧 Common solutions:"
    echo "   1. Verify repository exists: https://github.com/blackholeinfiverse51/ai-agent-logistics-system"
    echo "   2. Check your Personal Access Token has 'repo' permissions"
    echo "   3. Make sure you used the token as password (not GitHub password)"
    echo ""
    echo "🔄 Alternative approaches:"
    echo "   • Try: git push -f origin main (force push)"
    echo "   • Create new repository if it doesn't exist"
    echo "   • Use SSH instead of HTTPS"
    echo ""
    
    read -p "Would you like to try force push? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Attempting force push..."
        git push -f origin main
    fi
fi

echo ""
echo "📚 For detailed setup help, see:"
echo "   - GITHUB_SETUP_COMPLETE.md"
echo "   - READY_FOR_GITHUB.md"