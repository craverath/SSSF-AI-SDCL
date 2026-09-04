import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "install.py"
GRILL_SKILL = REPO_ROOT / ".claude/skills/sssf-grill-me/SKILL.md"


@pytest.mark.parametrize(
    ("integration", "skill_path", "grill_skill_path"),
    [
        (
            "claude",
            Path(".claude/skills/sssf"),
            Path(".claude/skills/sssf-grill-me"),
        ),
        (
            "codex",
            Path(".agents/skills/sssf"),
            Path(".agents/skills/sssf-grill-me"),
        ),
    ],
)
def test_installs_selected_integration(
    tmp_path, integration, skill_path, grill_skill_path
):
    result = subprocess.run(
        [sys.executable, str(INSTALLER), "--integration", integration],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )

    assert f"integration: {integration}" in result.stdout
    assert (tmp_path / skill_path / "SKILL.md").is_file()
    installed_grill_skill = tmp_path / grill_skill_path / "SKILL.md"
    assert installed_grill_skill.read_text() == GRILL_SKILL.read_text()
    assert not (tmp_path / skill_path / "apps/visualizer/node_modules").exists()
    assert not (tmp_path / skill_path / "apps/visualizer/dist").exists()
    assert (tmp_path / "adws/adw_modules/harnesses.py").is_file()
    assert (tmp_path / "adws/adw_sssf_config/sssf.config.yaml").is_file()


def test_none_installs_factory_without_host_integration(tmp_path):
    result = subprocess.run(
        [sys.executable, str(INSTALLER), "--integration", "none"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "integration: none" in result.stdout
    assert (tmp_path / "adws/adw_modules/harnesses.py").is_file()
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".agents").exists()


def test_migrates_legacy_visualizer_path_without_replacing_justfile(tmp_path):
    justfile = tmp_path / "justfile"
    justfile.write_text(
        "custom-recipe:\n"
        "    echo keep-me\n"
        "obs:\n"
        "    cd .claude/skills/sssf/apps/visualizer && bun install\n"
    )

    subprocess.run(
        [sys.executable, str(INSTALLER), "--integration", "codex"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )

    installed = justfile.read_text()
    assert "echo keep-me" in installed
    assert 'skill_dir=".agents/skills/sssf"' in installed
    assert "cd .claude/skills/sssf/apps/visualizer" not in installed
