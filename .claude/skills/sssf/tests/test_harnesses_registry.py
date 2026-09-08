"""Registry selection: agents.py must dispatch to an adapter without ever
comparing coding_agent against a CLI name itself."""

from __future__ import annotations

from pathlib import Path

import pytest
from adw_modules import agents, harnesses
from adw_modules.agent_antigravity import AntigravityAdapter
from adw_modules.agent_claudecode import ClaudeCodeAdapter
from adw_modules.agent_codex import CodexAdapter
from adw_modules.agent_kirocli import KiroCliAdapter
from adw_modules.agent_pi import PiAdapter
from adw_modules.data_types import CodingAgent


def test_registry_maps_every_coding_agent():
    assert set(harnesses.ADAPTERS) == {"pi", "claude_code", "codex",
                                       "kiro_cli", "antigravity"}
    assert isinstance(harnesses.ADAPTERS["pi"], PiAdapter)
    assert isinstance(harnesses.ADAPTERS["claude_code"], ClaudeCodeAdapter)
    assert isinstance(harnesses.ADAPTERS["codex"], CodexAdapter)
    assert isinstance(harnesses.ADAPTERS["kiro_cli"], KiroCliAdapter)
    assert isinstance(harnesses.ADAPTERS["antigravity"], AntigravityAdapter)


def test_config_type_and_registry_name_the_same_set():
    """`coding_agent` is a Literal in data_types.py and a dict key in
    harnesses.py. A name in one and not the other is either a config value with
    no adapter or an adapter no config can select."""
    assert set(CodingAgent.__args__) == set(harnesses.ADAPTERS)


def test_resolve_returns_the_matching_adapter():
    assert harnesses.resolve("pi") is harnesses.ADAPTERS["pi"]
    assert harnesses.resolve("codex") is harnesses.ADAPTERS["codex"]


def test_resolve_unknown_coding_agent_fails_objectively():
    with pytest.raises(ValueError, match="no adapter"):
        harnesses.resolve("some_other_cli")


def test_starter_roster_uses_kiro_for_judgement_and_antigravity_for_the_rest():
    """The shipped roster must be internally consistent, not merely parseable.

    Each pair is checked through the adapter's own validate(), which is where
    the harness-forced keys live: kiro_cli and antigravity both reject a
    non-null `tools`, and antigravity additionally rejects a `thinking` that
    contradicts the effort tier baked into its model slug. A roster edit that
    changes a model without its matching tier, or that reintroduces a
    `defaults.tools` list, fails here rather than at the first spawn.
    """
    config_path = Path(__file__).resolve().parents[1] / "templates/sssf.config.yaml"
    config = agents.load_config(str(config_path))

    expected = {
        "planner": ("kiro_cli", "claude-opus-5"),
        "builder": ("kiro_cli", "claude-sonnet-5"),
        "scout": ("antigravity", "gemini-3.8-flash-medium"),
        "reviewer": ("kiro_cli", "gpt-5.6-sol"),
        "documenter": ("antigravity", "gemini-3.8-flash-medium"),
    }
    for name, (coding_agent, model) in expected.items():
        agent = agents.resolve(config, name)
        assert (agent.coding_agent, agent.model) == (coding_agent, model)
        assert harnesses.resolve(coding_agent).validate(agent) == []


def test_agents_module_has_no_per_cli_conditional():
    """agents.py must select behavior only through harnesses.resolve(); a
    literal `coding_agent == "pi"` (or similar) creeping back in would silently
    reintroduce a Pi-only code path other adapters don't get."""
    source = Path(agents.__file__).read_text()
    for needle in ('coding_agent == "pi"', "coding_agent == 'pi'",
                   'coding_agent != "pi"', "coding_agent != 'pi'",
                   'coding_agent == "claude_code"', 'coding_agent == "codex"',
                   'coding_agent == "kiro_cli"', 'coding_agent == "antigravity"'):
        assert needle not in source, f"found a CLI-specific conditional: {needle!r}"
