"""Test builders for oc-meter contract tests.

These builders are test code only. The export shape is provisional untill a real OpenCode export is inspected and the field mapping is frozen
"""

from __future__ import annotations
from typing import Any

MODEL = "deepseek/deepseek-v4-flash"

TOKEN_KEYS = {
    "input",
    "output",
    "reasoning",
    "cache_read", 
    "cache_write"
}

def message(
    *,
    inputTokens: int = 0,
    output: int = 0, 
    reasoning: int = 0, 
    cache_read: int = 0,
    cache_write: int = 0,
    agent: str = "build",
    model: str = MODEL, 
    start: int = 0,
    end: int = 1000,
    role: str = "assistant",
    include_tokens: bool = True, 
    include_reasoning: bool = True
) -> dict[str, Any]:
    """Build a raw Opencode-like message for fixtures"""
    info: dict[str, Any] = {
        "role": role,
        "agent": agent, 
        "modelID": model,
        "time": {
            "createdAt": {"created": start, "completed": end}
        }
    }

    if include_tokens:
        tokens: dict[str, Any] = {
            "input": inputTokens,
            "output": output, 
            "cache": {"read": cache_read, "write": cache_write},
        }

        if include_reasoning:
            tokens["reasoning"] = reasoning
        info["tokens"] = tokens

    return {"info": info, "parts": []}

def export(
        session_id: str, 
        *messages: dict[str, Any],
        parent_id: str | None = None
):
    """Build a raw session export."""
    return {
        "session": {"id": session_id, "parentID": parent_id}
    }

def activity(
        time_ms: int, 
        session_id: str = "root",
        kind: str = "activity"
) -> dict[str, Any]:
    """Build an activity event for clock reconstruction."""
    return {
        "t_ms": time_ms,
        "session_id": session_id,
        "kind": kind
    }

def make_bundle(
    exports: tuple[dict[str, Any], ...],
    *,
    events: tuple[dict[str, Any], ...] = (),
    debounce_ms: int = 5000,
    effort_source: str = "observed",
    tree_ids: tuple[str, ...] | None = None, 
    model: str = MODEL, 
    work_id: str = "sha256:test",
    labels: dict[str, str] | None = None
) -> dict[str, Any]:
    """Build a measurement bundle.
    
    When tree_ids is omitted, tree memberships is derived from exports in arrival order.
    Tests that care about determinism should declare tree_ids explicitly.
    """

    ids = (
        tuple(tree_ids)
        if tree_ids is not None
        else tuple(item["session"]["id"] for item in exports)
    )

    parents = {
        item["session"]["id"]: item["session"].get("parentID") for item in exports
    }

    depth = 0

    for session_id in ids:
        current = session_id
        steps = 0
        while parents.get(current):
            current = parents[current]
            steps += 1
        depth = max(depth, steps)
    
    return {
        "run": {
            "id": "r-test",
            "work-id": work_id, 
            "labels": labels or {}
        },
        "conditions": {
            "opencode_version": "2.0.0",
            "model": model,
            "reasoning_effort": "low",
            "reasoning_effort_source": effort_source,
            "cleanliness_certificate_hash": None
        }, 
        "tree": {
            "root": ids[0] if ids else "",
            "session_ids": list(ids),
            "max_depth": depth
        }, 
        "debounce_ms": debounce_ms, 
        "events": list(events),
        "exports": list(exports)
    }

def make_mapping(
    *,
    included: bool = False,
    fields: dict[str, str] | None = None, 
    version: str = "test"
) -> dict[str, Any]:
    """Build a provisional mapping."""
    return {
        "version": version,
        "fields": fields or {
            "input": "tokens.input",
            "output": "tokens.output",
            "reasoning": "tokens.reasoning",
            "cache_read": "tokens.cache.read",
            "cache_write": "tokens.cache.write",
        },
        "reasoning_included_in_output": included,
    }
