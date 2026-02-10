# Test plan (contract-level)

> This is a suggested test plan; implement in Cortex’s test framework (pytest/unittest).

## 1) Adapter initializes

- Given a valid API key and user/session
- When `OpenClawCortexAdapter(...)` is created
- Then it should construct `AgenticMemorySystem` and not throw

## 2) remember() stores

- When `remember(content="x")`
- Then it should call `AgenticMemorySystem.add_note` with:
  - `user_id`, `session_id` present
  - `time` in ISO format

## 3) recall() searches

- When `recall(query="x")`
- Then it should call `AgenticMemorySystem.search` with:
  - `user_id`, `session_id` present
  - `limit` respected

## 4) Hook wrappers

- `init_cortex_adapter(...)` returns `{success: true}` and sets global adapter
- `on_conversation_turn(...)` returns `{success: true, stored: bool, memory_id: ...}`

## 5) Migration

- Provide a temp dir with:
  - `MEMORY.md`
  - `memory/2026-02-10.md`
- Run `migrate_markdown_to_cortex(..., preserve_dates=True)`
- Assert `add_note` called expected number of times with expected contexts/tags
