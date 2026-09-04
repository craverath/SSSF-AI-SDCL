"""Real, read-only smoke tests — one per harness. NOT run automatically.

These call the actual `pi`, `claude`, and `codex` CLIs with a trivial
read-only prompt and cost real tokens, so they are skipped unless explicitly
requested:

    SSSF_SMOKE=1 uv run --with pydantic --with pyyaml --with python-dotenv \\
        --with pytest pytest .claude/skills/sssf/tests/test_smoke_manual.py -s
"""

from __future__ import annotations

import os
import shutil
import uuid

import pytest
from adw_modules import agent_cc, agent_codex, agent_pi
from adw_modules.data_types import HarnessRequest

pytestmark = pytest.mark.skipif(
    not os.environ.get("SSSF_SMOKE"),
    reason="manual smoke test only — set SSSF_SMOKE=1 to run (costs real tokens)")

PROMPT = "Reply with exactly one word: pong."


def _request(tmp_path, model: str) -> HarnessRequest:
    return HarnessRequest(
        prompt=PROMPT, system_prompt="Reply with exactly one word.",
        model=model, thinking="low", session_id=str(uuid.uuid4()),
        cwd=str(tmp_path), raw_output_path=str(tmp_path / "raw_output.jsonl"),
        state_dir=str(tmp_path / "state"))


@pytest.mark.skipif(not shutil.which("pi"), reason="pi CLI not on PATH")
def test_pi_smoke(tmp_path):
    result = agent_pi.PiAdapter().run(_request(tmp_path, "google/gemini-3.6-flash"))
    assert result.text.strip()


@pytest.mark.skipif(not shutil.which("claude"), reason="claude CLI not on PATH")
def test_claude_code_smoke(tmp_path):
    result = agent_cc.ClaudeCodeAdapter().run(_request(tmp_path, "haiku"))
    assert result.text.strip()


@pytest.mark.skipif(not shutil.which("codex"), reason="codex CLI not on PATH")
def test_codex_smoke(tmp_path):
    result = agent_codex.CodexAdapter().run(_request(tmp_path, "gpt-5-mini"))
    assert result.text.strip()
