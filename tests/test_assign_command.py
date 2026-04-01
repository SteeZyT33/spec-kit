"""
Tests for the assign command template (templates/commands/assign.md).

Validates that the assign command follows spec-kit's command patterns
and includes all features from issue #2053.
"""

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).parent.parent
_ASSIGN_CMD = _REPO_ROOT / "templates" / "commands" / "assign.md"


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a Markdown file."""
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{path.name} must start with YAML frontmatter"
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestAssignCommandExists:
    def test_assign_command_file_exists(self):
        assert _ASSIGN_CMD.exists(), "templates/commands/assign.md must exist"


class TestAssignCommandFrontmatter:
    def test_has_description(self):
        fm = _parse_frontmatter(_ASSIGN_CMD)
        assert "description" in fm
        assert len(fm["description"]) > 10

    def test_has_scripts(self):
        fm = _parse_frontmatter(_ASSIGN_CMD)
        assert "scripts" in fm
        assert "sh" in fm["scripts"]
        assert "ps" in fm["scripts"]


class TestAssignCommandContent:
    def test_has_user_input_section(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "## User Input" in content
        assert "$ARGUMENTS" in content

    def test_has_extension_hooks(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "hooks.before_assign" in content
        assert "hooks.after_assign" in content

    def test_has_two_tier_discovery(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Tier 1: Internal Agents" in content
        assert "Tier 2: External Agents" in content

    def test_has_agent_annotation_convention(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "## Agent Annotation Convention" in content
        assert "[@" in content


class TestAssignHumanAgent:
    """Tests for #2053: [@Human Lead] agent type."""

    def test_has_human_lead_agent(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Human Lead" in content, "Must include [@Human Lead] in agent table"

    def test_human_lead_has_judgment_keywords(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        judgment_keywords = ["triage", "decide", "evaluate", "salvage", "approve", "sign off"]
        found = sum(1 for kw in judgment_keywords if kw in content.lower())
        assert found >= 4, f"Human Lead must have judgment keywords, found {found}/6"


class TestAssignConfidenceScores:
    """Tests for #2053: confidence scores per assignment."""

    def test_has_confidence_scoring(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "confidence" in content.lower(), "Must mention confidence scoring"

    def test_has_low_confidence_threshold(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "0.3" in content, "Must define low-confidence threshold (0.3)"

    def test_confidence_in_output_table(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Confidence" in content, "Output table must include Confidence column"


class TestAssignHumanTasksFlag:
    """Tests for #2053: --human-tasks flag."""

    def test_has_human_tasks_flag(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "--human-tasks" in content, "Must document --human-tasks flag"

    def test_human_tasks_in_quick_reference(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        # Check quick reference section includes the flag
        qr_start = content.find("## Quick Reference")
        assert qr_start != -1, "Must have Quick Reference section"
        qr_section = content[qr_start:]
        assert "--human-tasks" in qr_section, "--human-tasks must appear in Quick Reference"


class TestAssignDependencyAwareness:
    """Tests for #2053: dependency awareness."""

    def test_has_dependency_analysis(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Dependency" in content, "Must have dependency analysis step"
        assert "handoff" in content.lower(), "Must mention handoff warnings"


class TestAssignPhaseWeighting:
    """Tests for #2053: phase context weighting."""

    def test_has_phase_context_weighting(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "phase context weighting" in content.lower(), "Must mention phase context weighting"

    def test_phase_weighting_examples(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Setup" in content, "Must mention Setup phase weighting"
        assert "Audit" in content or "Triage" in content, "Must mention Audit/Triage phase weighting"
        assert "Polish" in content, "Must mention Polish phase weighting"
