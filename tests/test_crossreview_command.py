"""
Tests for the cross-harness review command and supporting files.

Validates:
  - Command template follows spec-kit patterns
  - Launcher script exists and has tmux detection
  - Backend script exists and handles all harnesses
  - Output schema is valid JSON
  - Template references all required components
"""

import json
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).parent.parent
_CROSSREVIEW_CMD = _REPO_ROOT / "templates" / "commands" / "crossreview.md"
_CROSSREVIEW_SH = _REPO_ROOT / "scripts" / "bash" / "crossreview.sh"
_CROSSREVIEW_PY = _REPO_ROOT / "scripts" / "bash" / "crossreview-backend.py"
_CROSSREVIEW_SCHEMA = _REPO_ROOT / "templates" / "crossreview.schema.json"


def _parse_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{path.name} must start with YAML frontmatter"
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestCrossreviewFilesExist:
    def test_command_template_exists(self):
        assert _CROSSREVIEW_CMD.exists()

    def test_launcher_script_exists(self):
        assert _CROSSREVIEW_SH.exists()

    def test_backend_script_exists(self):
        assert _CROSSREVIEW_PY.exists()

    def test_output_schema_exists(self):
        assert _CROSSREVIEW_SCHEMA.exists()


class TestCrossreviewFrontmatter:
    def test_has_description(self):
        fm = _parse_frontmatter(_CROSSREVIEW_CMD)
        assert "description" in fm
        assert len(fm["description"]) > 10

    def test_has_scripts(self):
        fm = _parse_frontmatter(_CROSSREVIEW_CMD)
        assert "scripts" in fm
        assert "sh" in fm["scripts"]
        assert "ps" in fm["scripts"]

    def test_has_handoffs(self):
        fm = _parse_frontmatter(_CROSSREVIEW_CMD)
        assert "handoffs" in fm
        assert len(fm["handoffs"]) >= 1


class TestCrossreviewContent:
    def test_has_user_input_section(self):
        content = _CROSSREVIEW_CMD.read_text(encoding="utf-8")
        assert "## User Input" in content
        assert "$ARGUMENTS" in content

    def test_references_review_harness_config(self):
        content = _CROSSREVIEW_CMD.read_text(encoding="utf-8")
        assert "review_harness" in content
        assert "init-options.json" in content

    def test_references_launcher_script(self):
        content = _CROSSREVIEW_CMD.read_text(encoding="utf-8")
        assert "crossreview.sh" in content

    def test_references_backend_script(self):
        content = _CROSSREVIEW_CMD.read_text(encoding="utf-8")
        assert "crossreview-backend.py" in content

    def test_references_shared_output(self):
        content = _CROSSREVIEW_CMD.read_text(encoding="utf-8")
        assert ".shared/" in content

    def test_has_adversarial_instruction(self):
        content = _CROSSREVIEW_CMD.read_text(encoding="utf-8")
        lower = content.lower()
        assert "adversarial" in lower
        assert "different ai agent" in lower or "different agent" in lower

    def test_has_json_output_schema_reference(self):
        content = _CROSSREVIEW_CMD.read_text(encoding="utf-8")
        assert "crossreview.schema.json" in content

    def test_computes_diff_externally(self):
        content = _CROSSREVIEW_CMD.read_text(encoding="utf-8")
        assert "git diff" in content
        assert ".crossreview.patch" in content

    def test_appends_to_review_md(self):
        content = _CROSSREVIEW_CMD.read_text(encoding="utf-8")
        assert "review.md" in content
        assert "Cross-Harness Review" in content


class TestCrossreviewSchema:
    def test_schema_is_valid_json(self):
        data = json.loads(_CROSSREVIEW_SCHEMA.read_text(encoding="utf-8"))
        assert data["type"] == "object"

    def test_schema_has_required_fields(self):
        data = json.loads(_CROSSREVIEW_SCHEMA.read_text(encoding="utf-8"))
        assert "summary" in data["properties"]
        assert "blocking" in data["properties"]
        assert "non_blocking" in data["properties"]
        assert data["required"] == ["summary", "blocking", "non_blocking"]

    def test_blocking_items_require_file_and_issue(self):
        data = json.loads(_CROSSREVIEW_SCHEMA.read_text(encoding="utf-8"))
        item_schema = data["properties"]["blocking"]["items"]
        assert "file" in item_schema["required"]
        assert "issue" in item_schema["required"]


class TestCrossreviewBackend:
    def test_backend_has_harness_choices(self):
        content = _CROSSREVIEW_PY.read_text(encoding="utf-8")
        assert "codex" in content
        assert "claude" in content
        assert "gemini" in content

    def test_backend_has_json_extraction(self):
        content = _CROSSREVIEW_PY.read_text(encoding="utf-8")
        assert "extract_json" in content

    def test_backend_has_timeout_handling(self):
        content = _CROSSREVIEW_PY.read_text(encoding="utf-8")
        assert "TimeoutExpired" in content

    def test_backend_has_missing_cli_handling(self):
        content = _CROSSREVIEW_PY.read_text(encoding="utf-8")
        assert "FileNotFoundError" in content


class TestCrossreviewLauncher:
    def test_launcher_has_tmux_detection(self):
        content = _CROSSREVIEW_SH.read_text(encoding="utf-8")
        assert "TMUX" in content
        assert "split-window" in content

    def test_launcher_has_timeout(self):
        content = _CROSSREVIEW_SH.read_text(encoding="utf-8")
        assert "TIMEOUT" in content
        assert "CROSSREVIEW_TIMEOUT" in content

    def test_launcher_has_foreground_fallback(self):
        content = _CROSSREVIEW_SH.read_text(encoding="utf-8")
        assert "foreground" in content.lower()
