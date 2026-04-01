"""
Unit tests for shared inbox integration.

Tests cover:
- Inbox message template exists and has required sections
- Implement command template contains inbox instructions
- Inbox instructions are conditional (gated on inbox/ existence)
- Implement command backward compatibility (no existing functionality removed)
"""

import re
from pathlib import Path

import pytest


# ===== Fixtures =====


@pytest.fixture
def repo_root():
    """Return the repository root path."""
    return Path(__file__).parent.parent


@pytest.fixture
def inbox_template(repo_root):
    """Load the inbox message template."""
    path = repo_root / "templates" / "inbox-message-template.md"
    assert path.exists(), f"Inbox message template not found at {path}"
    return path.read_text()


@pytest.fixture
def implement_template(repo_root):
    """Load the implement command template."""
    path = repo_root / "templates" / "commands" / "implement.md"
    assert path.exists(), f"Implement command template not found at {path}"
    return path.read_text()


# ===== Inbox Message Template Tests =====


class TestInboxMessageTemplate:
    """Tests for templates/inbox-message-template.md"""

    def test_template_exists(self, repo_root):
        path = repo_root / "templates" / "inbox-message-template.md"
        assert path.exists()

    def test_has_frontmatter(self, inbox_template):
        assert inbox_template.startswith("---"), "Template must start with YAML frontmatter"
        assert inbox_template.count("---") >= 2, "Template must have frontmatter delimiters"

    def test_has_file_naming_convention(self, inbox_template):
        assert "File Naming Convention" in inbox_template
        # Template uses {YYYY-MM-DDTHH-MM-SS}-{TYPE}-{sender-slug}.md format
        assert "timestamp" in inbox_template.lower()
        assert "sender" in inbox_template.lower()
        assert ".md" in inbox_template

    def test_has_escalation_naming(self, inbox_template):
        assert "ESC-{NNN}" in inbox_template or "ESC-" in inbox_template
        assert "RES-ESC-{NNN}" in inbox_template or "RES-ESC-" in inbox_template

    def test_has_all_message_types(self, inbox_template):
        required_types = ["COMPLETE", "INFO", "ESCALATE", "RESOLVE", "HANDOFF", "REVIEW", "CROSS"]
        for msg_type in required_types:
            assert msg_type in inbox_template, f"Missing message type: {msg_type}"

    def test_has_message_frontmatter_schema(self, inbox_template):
        required_fields = ["type:", "sender:", "recipient:", "timestamp:", "task_id:", "phase:"]
        for field in required_fields:
            assert field in inbox_template, f"Missing frontmatter field: {field}"

    def test_has_checking_instructions(self, inbox_template):
        assert "Checking the Inbox" in inbox_template


# ===== Implement Command Integration Tests =====


class TestImplementInboxIntegration:
    """Tests for inbox instructions in templates/commands/implement.md"""

    def test_has_inbox_pre_task_check(self, implement_template):
        assert "Shared Inbox: Pre-Task Coordination" in implement_template

    def test_has_inbox_post_task_signals(self, implement_template):
        assert "Shared Inbox: Post-Task Signals" in implement_template

    def test_has_complete_message_instruction(self, implement_template):
        assert "COMPLETE message" in implement_template or "COMPLETE" in implement_template

    def test_has_handoff_message_instruction(self, implement_template):
        assert "HANDOFF message" in implement_template or "HANDOFF" in implement_template

    def test_has_cross_feature_check(self, implement_template):
        assert "concurrent/" in implement_template
        assert "CROSS" in implement_template

    def test_inbox_instructions_are_conditional(self, implement_template):
        """All inbox behavior must be gated on inbox/ directory existence."""
        # Both inbox sections should have conditional checks
        assert re.search(
            r"if.*inbox/.*exists|if.*FEATURE_DIR/inbox/.*exists",
            implement_template,
            re.IGNORECASE,
        ), "Inbox instructions must be conditional on inbox/ existence"

    def test_inbox_skip_when_absent(self, implement_template):
        """Explicit skip instruction when inbox doesn't exist."""
        assert "skip this step entirely" in implement_template.lower()


# ===== Backward Compatibility Tests =====


class TestImplementBackwardCompatibility:
    """Ensure inbox additions don't break existing implement functionality."""

    def test_has_script_execution(self, implement_template):
        assert "check-prerequisites.sh" in implement_template

    def test_has_checklist_check(self, implement_template):
        assert "Check checklists status" in implement_template

    def test_has_context_loading(self, implement_template):
        assert "Load and analyze the implementation context" in implement_template

    def test_has_task_parsing(self, implement_template):
        assert "Parse tasks.md structure" in implement_template

    def test_has_execution_rules(self, implement_template):
        assert "Implementation execution rules" in implement_template

    def test_has_progress_tracking(self, implement_template):
        assert "Progress tracking and error handling" in implement_template

    def test_has_completion_validation(self, implement_template):
        assert "Completion validation" in implement_template

    def test_has_extension_hooks(self, implement_template):
        assert "Check for extension hooks" in implement_template

    def test_has_frontmatter(self, implement_template):
        assert implement_template.startswith("---")
        assert "description:" in implement_template
        assert "scripts:" in implement_template
