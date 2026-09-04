import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "install.py"


@pytest.mark.parametrize(
    ("integration", "skill_path"),
    [
        ("claude", Path(".claude/skills/sssf")),
        ("codex", Path(".agents/skills/sssf")),
    ],
)
def test_installs_selected_integration(tmp_path, integration, skill_path):
    result = subprocess.run(
        [sys.executable, str(INSTALLER), "--integration", integration],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )

    assert f"integration: {integration}" in result.stdout
    assert (tmp_path / skill_path / "SKILL.md").is_file()
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
