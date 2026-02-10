"""OpenClaw integration for Prem Cortex.

This package provides an adapter layer and tool wrappers that let OpenClaw-style
agents store and recall memories in Cortex.
"""

from .adapter import (
    OpenClawCortexAdapter,
    init_cortex_adapter,
    cortex_remember,
    cortex_recall,
    migrate_markdown_to_cortex,
)
