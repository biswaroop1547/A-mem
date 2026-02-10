# Integration Notes (Cortex-side)

This document is for the Cortex maintainer integrating `integrations/openclaw`.

## Key design points

- The OpenClaw side “memory” concept is file-based (`MEMORY.md`, `memory/*.md`).
- This adapter provides two canonical tools:
  - `cortex_remember(content, context?, tags?)`
  - `cortex_recall(query, temporal_weight?, date_range?, limit?)`
- User/session isolation is done via `user_id` and `session_id` passed into every call.

## Tool metadata

`integrations/openclaw/tools.json` defines:

- tool name/description
- JSON-schema parameters
- Python function import targets (`module:function`)
- optional hook definitions

Cortex needs a loader/registry to consume this metadata.

### Suggestion: minimal loader

Pseudo-code:

```python
import json
import importlib

spec = json.load(open("integrations/openclaw/tools.json"))

for tool in spec["tools"]:
    mod_path, fn_name = tool["function"].split(":")
    fn = getattr(importlib.import_module(mod_path), fn_name)
    register_tool(tool["name"], tool["description"], tool["parameters"], fn)
```

## Hooks

The metadata includes:

- `on_session_start` → calls `init_cortex_adapter(**kwargs)`
- `on_conversation_turn` → calls `on_conversation_turn(user_message, agent_response, auto_detect=True)`

If Cortex doesn’t support hooks, ignore this field.

## API compatibility check

The adapter assumes these methods exist:

- `AgenticMemorySystem.add_note(...)` returning a memory id
- `AgenticMemorySystem.search(...)` returning a list[dict]

If Cortex differs:

- Either adjust adapter to match actual API
- Or add a small compatibility wrapper inside Cortex

## Security / privacy

- Ensure `user_id`/`session_id` are used as mandatory filters for search.
- Avoid cross-user memory leakage.
- Consider disabling auto-store hooks by default until audited.
