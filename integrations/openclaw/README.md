# OpenClaw + Cortex Integration

> Integrate Prem Cortex memory system into OpenClaw AI agents

## Overview

This integration brings Cortex's advanced memory capabilities to OpenClaw agents:

- **Dual-tier memory** (STM/LTM) replacing flat markdown files
- **Temporal awareness** for time-based queries
- **Memory evolution** with automatic linking
- **Smart Collections** for domain organization

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenClaw Agent                          │
├─────────────────────────────────────────────────────────────┤
│  Existing Tools:          │  New Cortex Tools:              │
│  - memory_search          │  - cortex_add                   │
│  - memory_get             │  - cortex_search                │
│  - read/write files       │  - cortex_evolve                │
├─────────────────────────────────────────────────────────────┤
│                    Cortex Adapter Layer                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ AgenticMemorySystem                                  │    │
│  │ - user_id = openclaw_user_id                        │    │
│  │ - session_id = openclaw_session_key                 │    │
│  │ - Auto-store on conversation events                  │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                     ChromaDB (Vector Store)                  │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Option 1: Add to Cortex repo (recommended for Biswa)

```bash
# In cortex repo
mkdir -p integrations/openclaw
cp -r ./* /path/to/cortex/integrations/openclaw/
```

### Option 2: Install as OpenClaw skill

```bash
# In openclaw workspace
git clone https://github.com/prem-research/cortex.git skills/cortex
```

## Files

| File | Purpose |
|------|---------|
| `adapter.py` | OpenClaw ↔ Cortex bridge |
| `tools.py` | Tool definitions for OpenClaw gateway |
| `config.py` | Configuration management |
| `SKILL.md` | OpenClaw skill instructions |

## Quick Start

```python
from integrations.openclaw import OpenClawCortexAdapter

# Initialize with OpenClaw context
adapter = OpenClawCortexAdapter(
    api_key=os.getenv("OPENAI_API_KEY"),
    user_id="openclaw_user_123",
    session_id="main",
)

# Store a memory (called automatically on significant events)
adapter.remember(
    content="User prefers Python for backend work",
    context="preferences.programming",
    tags=["python", "backend"]
)

# Search with temporal awareness
results = adapter.recall(
    query="programming preferences",
    temporal_weight=0.3,  # 70% semantic, 30% recency
    limit=5
)

# Search with date filter
results = adapter.recall(
    query="what did we discuss?",
    date_range="yesterday",
    limit=10
)
```

## OpenClaw Tool Definitions

Add to OpenClaw's tool registry:

```json
{
  "tools": [
    {
      "name": "cortex_remember",
      "description": "Store a memory with automatic analysis and linking",
      "parameters": {
        "content": { "type": "string", "required": true },
        "context": { "type": "string" },
        "tags": { "type": "array", "items": { "type": "string" } }
      }
    },
    {
      "name": "cortex_recall", 
      "description": "Search memories with temporal awareness",
      "parameters": {
        "query": { "type": "string", "required": true },
        "temporal_weight": { "type": "number", "default": 0.0 },
        "date_range": { "type": "string" },
        "limit": { "type": "integer", "default": 10 }
      }
    }
  ]
}
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
CORTEX_CHROMA_HOST=localhost
CORTEX_CHROMA_PORT=8000
CORTEX_STM_CAPACITY=100
CORTEX_ENABLE_SMART_COLLECTIONS=true
CORTEX_ENABLE_BACKGROUND_PROCESSING=true
```

### OpenClaw Gateway Config

```yaml
# In openclaw config
memory:
  provider: cortex
  cortex:
    chroma_host: localhost
    chroma_port: 8000
    stm_capacity: 100
    smart_collections: true
    background_processing: true
```

## Event Hooks

OpenClaw can auto-store memories on events:

```python
# In adapter.py
class OpenClawCortexAdapter:
    
    def on_conversation_turn(self, user_message: str, agent_response: str):
        """Called after each conversation turn"""
        # Store significant exchanges
        if self._is_significant(user_message, agent_response):
            self.remember(
                content=f"User: {user_message}\nAgent: {agent_response}",
                context="conversation",
                time=datetime.now().isoformat()
            )
    
    def on_user_preference(self, preference: str, value: str):
        """Called when user expresses a preference"""
        self.remember(
            content=f"User preference: {preference} = {value}",
            context="preferences",
            tags=["preference", preference.lower()]
        )
    
    def on_task_completed(self, task: str, result: str):
        """Called when a task is completed"""
        self.remember(
            content=f"Completed task: {task}\nResult: {result}",
            context="tasks",
            tags=["task", "completed"]
        )
```

## Migration from Markdown Memory

For existing OpenClaw users with markdown memories:

```python
from integrations.openclaw import migrate_markdown_to_cortex

# Migrate MEMORY.md and memory/*.md to Cortex
migrate_markdown_to_cortex(
    memory_dir="/path/to/openclaw/workspace",
    adapter=adapter,
    preserve_dates=True  # Extract dates from filenames
)
```

## API Reference

### OpenClawCortexAdapter

#### `__init__(api_key, user_id, session_id, **kwargs)`

Initialize the adapter.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `api_key` | str | required | OpenAI API key |
| `user_id` | str | required | OpenClaw user identifier |
| `session_id` | str | "main" | Session identifier |
| `stm_capacity` | int | 100 | Short-term memory capacity |
| `enable_smart_collections` | bool | True | Enable domain organization |
| `enable_background_processing` | bool | True | Async LTM processing |

#### `remember(content, context=None, tags=None, time=None)`

Store a memory.

| Param | Type | Description |
|-------|------|-------------|
| `content` | str | Memory content |
| `context` | str | Domain context (e.g., "work.programming") |
| `tags` | list[str] | Searchable tags |
| `time` | str | ISO timestamp (default: now) |

Returns: `str` - Memory ID

#### `recall(query, temporal_weight=0.0, date_range=None, limit=10)`

Search memories.

| Param | Type | Description |
|-------|------|-------------|
| `query` | str | Search query |
| `temporal_weight` | float | 0.0-1.0, blend of recency vs semantic |
| `date_range` | str | "yesterday", "last week", "2024-01", etc. |
| `limit` | int | Max results |

Returns: `list[dict]` - Ranked memory results with scores

## Contributing

1. Fork the Cortex repo
2. Add this integration to `integrations/openclaw/`
3. Submit PR with tests

## Links

- [OpenClaw](https://github.com/openclaw/openclaw)
- [Prem Cortex](https://github.com/prem-research/cortex)
- [OpenClaw Docs](https://docs.openclaw.ai)
- [Prem AI](https://premai.io)

## License

MIT - Same as Cortex
