"""
OpenClaw ↔ Cortex Adapter

Bridge between OpenClaw agent tools and Cortex memory system.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from cortex.memory_system import AgenticMemorySystem


class OpenClawCortexAdapter:
    """
    Adapter that wraps Cortex AgenticMemorySystem for OpenClaw agents.
    
    Provides:
    - Simplified remember/recall API
    - Automatic user/session context
    - Event hooks for auto-storage
    - Migration utilities
    """
    
    def __init__(
        self,
        api_key: str,
        user_id: str,
        session_id: str = "main",
        stm_capacity: int = 100,
        enable_smart_collections: bool = True,
        enable_background_processing: bool = True,
        chroma_host: str = "localhost",
        chroma_port: int = 8000,
        model_name: str = "text-embedding-3-small",
        llm_backend: str = "openai",
    ):
        """
        Initialize the OpenClaw-Cortex adapter.
        
        Args:
            api_key: OpenAI API key for embeddings and LLM
            user_id: OpenClaw user identifier (for memory isolation)
            session_id: Session identifier (default: "main")
            stm_capacity: Short-term memory capacity
            enable_smart_collections: Enable domain-aware collections
            enable_background_processing: Enable async LTM processing
            chroma_host: ChromaDB host
            chroma_port: ChromaDB port
            model_name: Embedding model name
            llm_backend: LLM backend ("openai" or "ollama")
        """
        self.user_id = user_id
        self.session_id = session_id
        
        # Initialize Cortex memory system
        # NOTE: Chroma host/port are accepted by this adapter for consistency
        # with OpenClaw-style configuration, but the underlying Cortex API
        # may or may not use them depending on its implementation.
        self.memory = AgenticMemorySystem(
            api_key=api_key,
            stm_capacity=stm_capacity,
            enable_smart_collections=enable_smart_collections,
            enable_background_processing=enable_background_processing,
            model_name=model_name,
            llm_backend=llm_backend,
        )
        
        # Significance detection keywords
        self._significant_keywords = [
            "prefer", "like", "hate", "always", "never",
            "remember", "important", "decision", "agreed",
            "todo", "task", "deadline", "meeting", "project"
        ]
    
    def remember(
        self,
        content: str,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
        time: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a memory with automatic analysis.
        
        Args:
            content: Memory content to store
            context: Domain context (e.g., "work.programming.python")
            tags: Searchable tags
            time: ISO timestamp (default: now)
            metadata: Additional metadata
            
        Returns:
            Memory ID
        """
        return self.memory.add_note(
            content=content,
            user_id=self.user_id,
            session_id=self.session_id,
            context=context,
            tags=tags,
            time=time or datetime.now().astimezone().isoformat(),
            **(metadata or {}),
        )
    
    def recall(
        self,
        query: str,
        temporal_weight: float = 0.0,
        date_range: Optional[str] = None,
        memory_source: str = "all",
        limit: int = 10,
        context: Optional[str] = None,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search memories with temporal awareness.
        
        Args:
            query: Search query
            temporal_weight: 0.0-1.0, blend of recency (1.0) vs semantic (0.0)
            date_range: Filter by date ("yesterday", "last week", "2024-01", etc.)
            memory_source: "stm", "ltm", or "all"
            limit: Maximum results to return
            context: Context for relevance boosting
            where_filter: Metadata filter
            
        Returns:
            List of memory results with scores
        """
        results = self.memory.search(
            query=query,
            user_id=self.user_id,
            session_id=self.session_id,
            temporal_weight=temporal_weight,
            date_range=date_range,
            memory_source=memory_source,
            limit=limit,
            context=context,
            where_filter=where_filter,
        )
        
        # Format results for OpenClaw consumption
        return [
            {
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "recency_score": r.get("recency_score"),
                "temporal_weighted": r.get("temporal_weighted", False),
                "context": r.get("context"),
                "tags": r.get("tags", []),
                "time": r.get("time"),
                "id": r.get("id"),
            }
            for r in results
        ]
    
    # ─────────────────────────────────────────────────────────────
    # Event Hooks - Called by OpenClaw on various events
    # ─────────────────────────────────────────────────────────────
    
    def on_conversation_turn(
        self,
        user_message: str,
        agent_response: str,
        auto_detect: bool = True,
    ) -> Optional[str]:
        """
        Called after each conversation turn.
        Stores significant exchanges automatically.
        
        Args:
            user_message: The user's message
            agent_response: The agent's response
            auto_detect: Whether to auto-detect significance
            
        Returns:
            Memory ID if stored, None if skipped
        """
        if auto_detect and not self._is_significant(user_message, agent_response):
            return None
        
        content = f"User: {user_message}\nAssistant: {agent_response}"
        return self.remember(
            content=content,
            context="conversation",
            tags=["conversation", "exchange"],
        )
    
    def on_user_preference(self, preference: str, value: Any) -> str:
        """
        Called when user expresses a preference.
        
        Args:
            preference: Preference name (e.g., "code_editor")
            value: Preference value (e.g., "VS Code")
            
        Returns:
            Memory ID
        """
        return self.remember(
            content=f"User preference: {preference} = {value}",
            context="preferences",
            tags=["preference", preference.lower().replace(" ", "_")],
        )
    
    def on_task_completed(self, task: str, result: str) -> str:
        """
        Called when a task is completed.
        
        Args:
            task: Task description
            result: Task result/outcome
            
        Returns:
            Memory ID
        """
        return self.remember(
            content=f"Completed task: {task}\nResult: {result}",
            context="tasks",
            tags=["task", "completed"],
        )
    
    def on_decision_made(self, decision: str, reasoning: str = "") -> str:
        """
        Called when a decision is made.
        
        Args:
            decision: The decision made
            reasoning: Optional reasoning behind it
            
        Returns:
            Memory ID
        """
        content = f"Decision: {decision}"
        if reasoning:
            content += f"\nReasoning: {reasoning}"
        
        return self.remember(
            content=content,
            context="decisions",
            tags=["decision"],
        )
    
    def on_explicit_remember(self, content: str, context: str = "explicit") -> str:
        """
        Called when user explicitly asks to remember something.
        
        Args:
            content: What to remember
            context: Optional context category
            
        Returns:
            Memory ID
        """
        return self.remember(
            content=content,
            context=context,
            tags=["explicit", "user_requested"],
        )
    
    # ─────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────
    
    def _is_significant(self, user_message: str, agent_response: str) -> bool:
        """
        Detect if a conversation turn is significant enough to store.
        """
        combined = f"{user_message} {agent_response}".lower()
        
        # Check for significant keywords
        for keyword in self._significant_keywords:
            if keyword in combined:
                return True
        
        # Check for questions that indicate preferences/decisions
        if any(q in user_message.lower() for q in ["do you remember", "what did we", "last time"]):
            return True
        
        # Check message length (longer exchanges often more significant)
        if len(user_message) > 200 or len(agent_response) > 500:
            return True
        
        return False
    
    def get_recent_context(self, limit: int = 5) -> str:
        """
        Get recent memories as context string for prompts.
        
        Args:
            limit: Number of recent memories
            
        Returns:
            Formatted context string
        """
        results = self.recall(
            query="",
            memory_source="stm",
            limit=limit,
            temporal_weight=1.0,  # Pure recency
        )
        
        if not results:
            return ""
        
        context_lines = ["Recent context:"]
        for r in results:
            context_lines.append(f"- {r['content'][:200]}...")
        
        return "\n".join(context_lines)


# ─────────────────────────────────────────────────────────────────
# Migration Utilities
# ─────────────────────────────────────────────────────────────────

def migrate_markdown_to_cortex(
    memory_dir: str,
    adapter: OpenClawCortexAdapter,
    preserve_dates: bool = True,
) -> Dict[str, int]:
    """
    Migrate existing OpenClaw markdown memories to Cortex.
    
    Args:
        memory_dir: Path to OpenClaw workspace (containing MEMORY.md, memory/)
        adapter: Initialized OpenClawCortexAdapter
        preserve_dates: Extract dates from filenames for daily logs
        
    Returns:
        Migration stats {"migrated": N, "skipped": N, "errors": N}
    """
    import re
    from pathlib import Path
    
    stats = {"migrated": 0, "skipped": 0, "errors": 0}
    workspace = Path(memory_dir)
    
    # Migrate MEMORY.md (long-term curated memories)
    memory_md = workspace / "MEMORY.md"
    if memory_md.exists():
        try:
            content = memory_md.read_text()
            sections = _parse_markdown_sections(content)
            
            for section_title, section_content in sections.items():
                if section_content.strip():
                    adapter.remember(
                        content=section_content,
                        context=f"memory.{section_title.lower().replace(' ', '_')}",
                        tags=["migrated", "memory_md"],
                    )
                    stats["migrated"] += 1
        except Exception as e:
            print(f"Error migrating MEMORY.md: {e}")
            stats["errors"] += 1
    
    # Migrate memory/*.md (daily logs)
    memory_folder = workspace / "memory"
    if memory_folder.exists():
        for md_file in sorted(memory_folder.glob("*.md")):
            try:
                content = md_file.read_text()
                
                # Extract date from filename (e.g., 2024-01-15.md)
                date_match = re.match(r"(\d{4}-\d{2}-\d{2})", md_file.stem)
                time = None
                if preserve_dates and date_match:
                    time = f"{date_match.group(1)}T12:00:00+00:00"
                
                # Parse sections within the daily log
                sections = _parse_markdown_sections(content)
                
                for section_title, section_content in sections.items():
                    if section_content.strip():
                        adapter.remember(
                            content=section_content,
                            context=f"daily.{section_title.lower().replace(' ', '_')}",
                            tags=["migrated", "daily_log", md_file.stem],
                            time=time,
                        )
                        stats["migrated"] += 1
                        
            except Exception as e:
                print(f"Error migrating {md_file}: {e}")
                stats["errors"] += 1
    
    return stats


def _parse_markdown_sections(content: str) -> Dict[str, str]:
    """
    Parse markdown into sections by headers.
    """
    import re
    
    sections = {}
    current_section = "general"
    current_content = []
    
    for line in content.split("\n"):
        header_match = re.match(r"^#+\s+(.+)$", line)
        if header_match:
            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = header_match.group(1)
            current_content = []
        else:
            current_content.append(line)
    
    # Save last section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()
    
    return sections


# ─────────────────────────────────────────────────────────────────
# OpenClaw Tool Functions (for gateway registration)
# ─────────────────────────────────────────────────────────────────

# Global adapter instance (initialized by OpenClaw gateway)
_adapter: Optional[OpenClawCortexAdapter] = None


def init_cortex_adapter(**kwargs) -> Dict[str, Any]:
    """OpenClaw hook: initialize the global Cortex adapter.

    Returns a small status object so tool/hook runners that expect JSON don't
    attempt to serialize a complex Python object.
    """
    global _adapter
    _adapter = OpenClawCortexAdapter(**kwargs)
    return {"success": True}


def on_conversation_turn(
    user_message: str,
    agent_response: str,
    auto_detect: bool = True,
) -> Dict[str, Any]:
    """OpenClaw hook: store significant conversation exchanges.

    This is a thin wrapper around the adapter instance method.
    """
    if not _adapter:
        return {"success": False, "error": "Cortex adapter not initialized"}

    try:
        memory_id = _adapter.on_conversation_turn(
            user_message=user_message,
            agent_response=agent_response,
            auto_detect=auto_detect,
        )
        return {"success": True, "memory_id": memory_id, "stored": bool(memory_id)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def cortex_remember(
    content: str,
    context: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    OpenClaw tool: Store a memory.
    
    Args:
        content: What to remember
        context: Domain context (e.g., "work.programming")
        tags: Searchable tags
        
    Returns:
        {"success": True, "memory_id": "..."}
    """
    if not _adapter:
        return {"success": False, "error": "Cortex adapter not initialized"}
    
    try:
        memory_id = _adapter.remember(content=content, context=context, tags=tags)
        return {"success": True, "memory_id": memory_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def cortex_recall(
    query: str,
    temporal_weight: float = 0.0,
    date_range: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    OpenClaw tool: Search memories.
    
    Args:
        query: Search query
        temporal_weight: 0.0 (semantic) to 1.0 (recency)
        date_range: "yesterday", "last week", "2024-01", etc.
        limit: Max results
        
    Returns:
        {"success": True, "results": [...]}
    """
    if not _adapter:
        return {"success": False, "error": "Cortex adapter not initialized"}
    
    try:
        results = _adapter.recall(
            query=query,
            temporal_weight=temporal_weight,
            date_range=date_range,
            limit=limit,
        )
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        return {"success": False, "error": str(e)}
