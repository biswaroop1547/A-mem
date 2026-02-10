#!/bin/bash
# OpenClaw + Cortex Integration Setup
# Run this script to set up the integration

set -e

echo "🧠 OpenClaw + Cortex Integration Setup"
echo "========================================"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '3\.\d+')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "❌ Python 3.11+ required (found: $PYTHON_VERSION)"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION"

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set"
    echo "   Set it with: export OPENAI_API_KEY=sk-..."
else
    echo "✅ OPENAI_API_KEY configured"
fi

# Install Cortex
echo ""
echo "📦 Installing Cortex..."
pip install git+https://github.com/prem-research/cortex.git --quiet

# Check if ChromaDB is running
echo ""
echo "🔍 Checking ChromaDB..."
CHROMA_HOST=${CORTEX_CHROMA_HOST:-localhost}
CHROMA_PORT=${CORTEX_CHROMA_PORT:-8000}

if curl -s "http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat" > /dev/null 2>&1; then
    echo "✅ ChromaDB running at $CHROMA_HOST:$CHROMA_PORT"
else
    echo "⚠️  ChromaDB not running at $CHROMA_HOST:$CHROMA_PORT"
    echo ""
    echo "   Start ChromaDB with Docker:"
    echo "   docker run -d -p 8000:8000 chromadb/chroma:latest"
    echo ""
    echo "   Or with Poetry (in cortex repo):"
    echo "   poetry run chroma run --host localhost --port 8000"
    echo ""
    
    read -p "   Start ChromaDB with Docker now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Starting ChromaDB..."
        docker run -d --name chromadb -p 8000:8000 chromadb/chroma:latest
        sleep 3
        if curl -s "http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat" > /dev/null 2>&1; then
            echo "   ✅ ChromaDB started"
        else
            echo "   ❌ Failed to start ChromaDB"
            exit 1
        fi
    fi
fi

# Test import
echo ""
echo "🧪 Testing import..."
python3 -c "from cortex.memory_system import AgenticMemorySystem; print('✅ Cortex imported successfully')" 2>/dev/null || {
    echo "❌ Failed to import Cortex"
    exit 1
}

# Summary
echo ""
echo "========================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Ensure OPENAI_API_KEY is set"
echo "2. Ensure ChromaDB is running"
echo "3. Import the adapter in your OpenClaw config:"
echo ""
echo "   from integrations.openclaw.adapter import OpenClawCortexAdapter"
echo "   adapter = OpenClawCortexAdapter("
echo "       api_key=os.getenv('OPENAI_API_KEY'),"
echo "       user_id='your_user_id',"
echo "   )"
echo ""
echo "📚 See README.md for full documentation"
echo "🔗 Cortex repo: https://github.com/prem-research/cortex"
echo "🦞 OpenClaw repo: https://github.com/openclaw/openclaw"
