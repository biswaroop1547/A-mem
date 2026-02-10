# Cortex ↔ OpenClaw Integration (Proposed)

This repo/patch is a **clean integration package** intended to be copied into the **Cortex** repository at:

```
cortex/integrations/openclaw/
```

It provides:

- A Python adapter (`integrations/openclaw/adapter.py`) bridging OpenClaw-style tool calls to Cortex `AgenticMemorySystem`
- Tool schemas (`integrations/openclaw/tools.json`) for registering `cortex_remember` and `cortex_recall`
- Optional event hooks for auto-memory capture (`on_session_start`, `on_conversation_turn`)
- A migration utility to import OpenClaw markdown memory (`MEMORY.md`, `memory/*.md`) into Cortex

> Note: OpenClaw itself typically registers tools via a **TypeScript plugin**. This integration is specifically for
> adding **OpenClaw support into Cortex** (i.e., Cortex exposing an adapter + tool metadata), as requested.

---

## 1) Quick copy into Cortex repo

From the root of the Cortex repo:

```bash
mkdir -p integrations/openclaw
# copy the contents of this repo into cortex/integrations/openclaw
cp -R /path/to/this-repo/integrations/openclaw/* integrations/openclaw/
```

---

## 2) What Cortex needs to provide / wire up

### A) Ensure Cortex API compatibility

This adapter expects Cortex to expose:

- `from cortex.memory_system import AgenticMemorySystem`
- `AgenticMemorySystem(...)
- `AgenticMemorySystem.add_note(...) -> str` (memory id)
- `AgenticMemorySystem.search(...) -> list[dict]`

If Cortex uses different names/signatures, add a thin compatibility layer in Cortex or adjust the adapter.

### B) Tool runner / registration

`integrations/openclaw/tools.json` is **metadata**. Cortex needs a small loader that:

- reads `tools.json`
- imports the referenced functions, e.g.
  - `integrations.openclaw.adapter:cortex_remember`
  - `integrations.openclaw.adapter:cortex_recall`
- exposes them through Cortex’s existing tool interface (whatever Cortex uses for “tools”)

### C) Event hooks (optional)

`tools.json` includes hooks:

- `on_session_start` → `integrations.openclaw.adapter:init_cortex_adapter`
- `on_conversation_turn` → `integrations.openclaw.adapter:on_conversation_turn`

If Cortex doesn’t have a hook dispatcher yet, treat these as optional and implement later.

---

## 3) Configuration

Environment variables referenced by docs/tool metadata:

- `OPENAI_API_KEY` (required)
- `CORTEX_CHROMA_HOST` (optional)
- `CORTEX_CHROMA_PORT` (optional)

> Important: `chroma_host/chroma_port` are accepted by the adapter constructor, but the current adapter does not forward
> them into `AgenticMemorySystem`. If Cortex needs explicit host/port configuration, update the adapter once the Cortex
> API is confirmed.

---

## 4) Example usage

```python
import os
from integrations.openclaw.adapter import OpenClawCortexAdapter

adapter = OpenClawCortexAdapter(
    api_key=os.environ["OPENAI_API_KEY"],
    user_id="openclaw_user_123",
    session_id="main",
)

adapter.remember(
    content="User prefers Python for backend work",
    context="preferences.programming",
    tags=["python", "backend"],
)

results = adapter.recall(
    query="programming preferences",
    temporal_weight=0.3,
    limit=5,
)
print(results)
```

---

## 5) Proposed next steps for Biswa

1. Drop this into `cortex/integrations/openclaw/`
2. Confirm `AgenticMemorySystem` API compatibility (add_note/search signatures)
3. Add a minimal loader/registry in Cortex that reads `tools.json` and registers functions
4. Decide whether to keep hooks in metadata or implement a Cortex hook dispatcher
5. Add tests (see `tests/` suggestions)

---

## Notes

This package originally arrived as a zip named “OpenClaw + Cortex Integration Package”.
A small fix was applied:

- Added a top-level `on_conversation_turn(...)` function (the metadata referenced it, but only a class method existed)
- Adjusted `init_cortex_adapter` to return a JSON dict instead of a Python object
- Added `__init__.py` so `integrations.openclaw` imports cleanly
