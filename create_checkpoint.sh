#!/bin/bash
# Create a checkpoint of the KM System

echo "🔒 Creating KM System Checkpoint..."

# Get current date and commit hash
DATE=$(date +"%Y-%m-%d")
COMMIT=$(git rev-parse --short HEAD)

# Create checkpoint tag
TAG_NAME="checkpoint-${DATE}-working-system"

echo "📋 Current Status:"
git status

echo ""
echo "📝 Recent Commits:"
git log --oneline -5

echo ""
echo "🏷️  Creating tag: ${TAG_NAME}"
git tag -a ${TAG_NAME} -m "Checkpoint: Fully working KM System with AI classification, GraphRAG, and metadata persistence

Key features:
- AI classification working (no more 'unclassified')
- GraphRAG entity/relationship extraction
- Full document storage (no truncation)
- Metadata persistence for all GraphRAG data
- Auto-tagging from keywords
- Results page showing all data properly

All services deployed and functional."

echo ""
echo "📊 Service Versions:"
echo "Commit: ${COMMIT}"
echo "Date: ${DATE}"

echo ""
echo "✅ Checkpoint created!"
echo ""
echo "To push this checkpoint to GitHub, run:"
echo "  git push origin ${TAG_NAME}"
echo ""
echo "To return to this checkpoint later, run:"
echo "  git checkout ${TAG_NAME}"