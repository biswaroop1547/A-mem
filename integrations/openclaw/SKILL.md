# Cortex Memory Skill

> Advanced memory system for OpenClaw agents powered by Prem Cortex

## Description

This skill replaces or augments OpenClaw's default markdown-based memory with Cortex's cognitive memory architecture:

- **Dual-tier memory**: Fast STM + persistent LTM (ChromaDB)
- **Temporal awareness**: Query by time ("yesterday", "last week")
- **Memory evolution**: Auto-linking and relationship building
- **Smart Collections**: Domain-aware organization

## Requirements

- Python 3.11+
- ChromaDB server running
- OpenAI API key (or Ollama for self-hosted)

## Setup

### 1. Start ChromaDB

```bash
docker run -d -p 8000:8000 chromadb/chroma:latest
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY=sk-...
export CORTEX_CHROMA_HOST=localhost
export CORTEX_CHROMA_PORT=8000
```

### 3. Install Cortex

```bash
pip install git+https://github.com/prem-research/cortex.git
```

## Usage

### Storing Memories

Use `cortex_remember` instead of writing to MEMORY.md:

```
User: Remember that I prefer Python for backend work
Agent: [calls cortex_remember with content="User prefers Python for backend work", context="preferences.programming"]
```

### Searching Memories

Use `cortex_recall` for intelligent search:

```
User: What did we discuss about the API project last week?
Agent: [calls cortex_recall with query="API project", date_range="last week", temporal_weight=0.5]
```

### Temporal Queries

The `temporal_weight` parameter controls recency vs relevance:

- `0.0` = Pure semantic search (default)
- `0.5` = Balanced
- `1.0` = Pure recency (most recent first)

### Date Ranges

Supported formats:
- Natural: `"yesterday"`, `"last week"`, `"last month"`
- Year-Month: `"2024-01"` (January 2024)
- RFC3339: `"2024-01-15T00:00:00Z"`

## When to Use

### Use Cortex When:
- User asks about past conversations
- User expresses preferences
- Important decisions are made
- Tasks are completed
- User explicitly says "remember this"

### Keep Using Files When:
- Storing code snippets
- Writing documentation
- Managing config files
- Anything that should be human-editable

## Migration

To migrate existing MEMORY.md to Cortex:

```python
from integrations.openclaw.adapter import migrate_markdown_to_cortex, OpenClawCortexAdapter

adapter = OpenClawCortexAdapter(
    api_key=os.getenv("OPENAI_API_KEY"),
    user_id="user_123",
)

stats = migrate_markdown_to_cortex(
    memory_dir="/path/to/workspace",
    adapter=adapter,
)
print(f"Migrated {stats['migrated']} memories")
```

## Tool Reference

### cortex_remember

Store a memory with automatic analysis.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| content | string | Yes | What to remember |
| context | string | No | Domain (e.g., "work.programming") |
| tags | array | No | Searchable tags |

### cortex_recall

Search memories with temporal awareness.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search query |
| temporal_weight | number | No | 0.0-1.0 recency weight |
| date_range | string | No | Time filter |
| limit | integer | No | Max results (default: 10) |

## Links

- [Prem Cortex](https://github.com/prem-research/cortex)
- [OpenClaw](https://github.com/openclaw/openclaw)
- [ChromaDB](https://www.trychroma.com/)
