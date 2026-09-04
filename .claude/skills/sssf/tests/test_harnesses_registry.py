"""Registry selection: agents.py must dispatch to an adapter without ever
comparing coding_agent against a CLI name itself."""

from __future__ import annotations

from pathlib import Path

import pytest
from adw_modules import agents, harnesses
from adw_modules.agent_cc import ClaudeCodeAdapter
from adw_modules.agent_codex import CodexAdapter
from adw_modules.agent_pi import PiAdapter


def test_registry_maps_all_three_coding_agents():
    assert set(harnesses.ADAPTERS) == {"pi", "claude_code", "codex"}
    assert isinstance(harnesses.ADAPTERS["pi"], PiAdapter)
    assert isinstance(harnesses.ADAPTERS["claude_code"], ClaudeCodeAdapter)
    assert isinstance(harnesses.ADAPTERS["codex"], CodexAdapter)


def test_resolve_returns_the_matching_adapter():
    assert harnesses.resolve("pi") is harnesses.ADAPTERS["pi"]
    assert harnesses.resolve("codex") is harnesses.ADAPTERS["codex"]


def test_resolve_unknown_coding_agent_fails_objectively():
    with pytest.raises(ValueError, match="no adapter"):
        harnesses.resolve("some_other_cli")


def test_agents_module_has_no_per_cli_conditional():
    """agents.py must select behavior only through harnesses.resolve(); a
    literal `coding_agent == "pi"` (or similar) creeping back in would silently
    reintroduce a Pi-only code path other adapters don't get."""
    source = Path(agents.__file__).read_text()
    for needle in ('coding_agent == "pi"', "coding_agent == 'pi'",
                   'coding_agent != "pi"', "coding_agent != 'pi'",
                   'coding_agent == "claude_code"', 'coding_agent == "codex"'):
        assert needle not in source, f"found a CLI-specific conditional: {needle!r}"
