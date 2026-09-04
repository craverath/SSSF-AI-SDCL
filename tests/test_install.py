import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "install.py"
GRILL_SKILL = REPO_ROOT / ".claude/skills/sssf-grill-me/SKILL.md"


def load_installer():
    """The installer as a module. It is a script, not a package, and guards
    main() behind __name__, so importing it only defines its constants."""
    path = REPO_ROOT / ".claude/skills/sssf/scripts/install.py"
    spec = importlib.util.spec_from_file_location("sssf_installer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        (
            "kiro",
            Path(".kiro/skills/sssf"),
            Path(".kiro/skills/sssf-grill-me"),
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
    installed_justfile = (tmp_path / "justfile").read_text()
    assert "sssf *ARGS:" in installed_justfile
    assert "simple-sdlc *ARGS:" not in installed_justfile


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
    for host_dir in (".claude", ".agents", ".kiro"):
        assert not (tmp_path / host_dir).exists()


def test_visualizer_recipe_probes_every_integration():
    """The obs recipe is committed, but which host stamped a given clone is
    not, so it probes for each. The probe chain lives in two places — the
    template a fresh install stamps, and the constant an existing justfile is
    migrated to — and a new INTEGRATION_PATHS entry missing from either yields
    a justfile that cannot find the app."""
    installer = load_installer()
    template = (REPO_ROOT / ".claude/skills/sssf/templates/justfile").read_text()
    for path in installer.INTEGRATION_PATHS.values():
        assert f'skill_dir="{path}"' in installer.PORTABLE_VISUALIZER_COMMAND
        assert f'skill_dir="{path}"' in template


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


def test_migrates_legacy_sssf_recipe_without_replacing_justfile(tmp_path):
    justfile = tmp_path / "justfile"
    justfile.write_text(
        "custom-recipe:\n"
        "    echo keep-me\n"
        "# the full chain, plus review and docs: "
        'just simple-sdlc "add a /health endpoint"\n'
        "simple-sdlc *ARGS:\n"
        '    uv run adws/adw_simple_sdlc.py --config {{config}} "$@"\n'
    )

    subprocess.run(
        [sys.executable, str(INSTALLER), "--integration", "none"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )

    installed = justfile.read_text()
    assert "echo keep-me" in installed
    assert 'just sssf "<prompt or path/to/spec.md>"' in installed
    assert "sssf *ARGS:" in installed
    assert "simple-sdlc" not in installed
