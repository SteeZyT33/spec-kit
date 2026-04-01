"""
Tests for the review command template (templates/commands/review.md).

Validates that the review command follows spec-kit's command patterns:
  - YAML frontmatter is well-formed with required fields
  - Script invocation matches the pattern used by implement.md and analyze.md
  - Handoffs point to valid spec-kit commands
  - No unresolved placeholders
  - Review template (templates/review-template.md) exists and has frontmatter
"""

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).parent.parent
_REVIEW_CMD = _REPO_ROOT / "templates" / "commands" / "review.md"
_REVIEW_TEMPLATE = _REPO_ROOT / "templates" / "review-template.md"
_IMPLEMENT_CMD = _REPO_ROOT / "templates" / "commands" / "implement.md"
_ANALYZE_CMD = _REPO_ROOT / "templates" / "commands" / "analyze.md"


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a Markdown file."""
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{path.name} must start with YAML frontmatter"
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestReviewCommandExists:
    """Verify the review command template file exists."""

    def test_review_command_file_exists(self):
        assert _REVIEW_CMD.exists(), "templates/commands/review.md must exist"

    def test_review_template_file_exists(self):
        assert _REVIEW_TEMPLATE.exists(), "templates/review-template.md must exist"


class TestReviewCommandFrontmatter:
    """Verify the YAML frontmatter follows spec-kit command patterns."""

    def test_has_description(self):
        fm = _parse_frontmatter(_REVIEW_CMD)
        assert "description" in fm, "Frontmatter must have 'description' field"
        assert len(fm["description"]) > 10, "Description must be meaningful"

    def test_has_scripts(self):
        fm = _parse_frontmatter(_REVIEW_CMD)
        assert "scripts" in fm, "Frontmatter must have 'scripts' field"
        assert "sh" in fm["scripts"], "Scripts must include 'sh' (Bash)"
        assert "ps" in fm["scripts"], "Scripts must include 'ps' (PowerShell)"

    def test_script_invocation_matches_implement(self):
        """Review and implement use the same prerequisite script with same flags."""
        review_fm = _parse_frontmatter(_REVIEW_CMD)
        implement_fm = _parse_frontmatter(_IMPLEMENT_CMD)
        assert review_fm["scripts"]["sh"] == implement_fm["scripts"]["sh"], (
            "Review command must use same script invocation as implement command"
        )

    def test_script_invocation_matches_analyze(self):
        """Review and analyze use the same prerequisite script with same flags."""
        review_fm = _parse_frontmatter(_REVIEW_CMD)
        analyze_fm = _parse_frontmatter(_ANALYZE_CMD)
        assert review_fm["scripts"]["sh"] == analyze_fm["scripts"]["sh"], (
            "Review command must use same script invocation as analyze command"
        )

    def test_has_handoffs(self):
        fm = _parse_frontmatter(_REVIEW_CMD)
        assert "handoffs" in fm, "Frontmatter must have 'handoffs' field"
        assert len(fm["handoffs"]) >= 1, "Must have at least one handoff"

    def test_handoffs_have_required_fields(self):
        fm = _parse_frontmatter(_REVIEW_CMD)
        for handoff in fm["handoffs"]:
            assert "label" in handoff, "Each handoff must have 'label'"
            assert "agent" in handoff, "Each handoff must have 'agent'"
            assert "prompt" in handoff, "Each handoff must have 'prompt'"

    def test_handoffs_point_to_valid_commands(self):
        fm = _parse_frontmatter(_REVIEW_CMD)
        valid_agents = {
            "speckit.specify", "speckit.plan", "speckit.tasks",
            "speckit.implement", "speckit.analyze", "speckit.clarify",
            "speckit.checklist", "speckit.review", "speckit.constitution",
            "speckit.taskstoissues",
        }
        for handoff in fm["handoffs"]:
            assert handoff["agent"] in valid_agents, (
                f"Handoff agent '{handoff['agent']}' is not a valid spec-kit command"
            )

    def test_has_tools(self):
        fm = _parse_frontmatter(_REVIEW_CMD)
        assert "tools" in fm, "Frontmatter must have 'tools' field"
        assert isinstance(fm["tools"], list), "Tools must be a list"
        assert len(fm["tools"]) >= 1, "Must declare at least one tool"

    def test_tools_match_contract(self):
        fm = _parse_frontmatter(_REVIEW_CMD)
        expected_tools = [
            'github/github-mcp-server/issue_write',
            'github/github-mcp-server/create_pull_request',
            'github/github-mcp-server/pull_request_review_write',
        ]
        assert fm["tools"] == expected_tools, f"Tools must match contract: {expected_tools}"


class TestReviewCommandContent:
    """Verify the command template body follows spec-kit patterns."""

    def test_has_user_input_section(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "## User Input" in content, "Must have User Input section"
        assert "$ARGUMENTS" in content, "Must include $ARGUMENTS placeholder"

    def test_has_pre_execution_checks(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "## Pre-Execution Checks" in content, "Must have Pre-Execution Checks section"
        assert "hooks.before_review" in content, "Must check before_review hooks"

    def test_has_post_execution_hooks(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "hooks.after_review" in content, "Must check after_review hooks"

    def test_has_three_review_passes(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "### Pass 1" in content, "Must have Pass 1 (Spec Compliance)"
        assert "### Pass 2" in content, "Must have Pass 2 (Code Quality)"
        assert "### Pass 3" in content, "Must have Pass 3 (Security)"

    def test_has_tiered_fix_behavior(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "Auto-Fix" in content, "Must define Auto-Fix tier"
        assert "Suggest-Fix" in content, "Must define Suggest-Fix tier"
        assert "Flag-Only" in content, "Must define Flag-Only tier"

    def test_has_comment_response_protocol(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "ADDRESSED" in content, "Must define ADDRESSED status"
        assert "REJECTED" in content, "Must define REJECTED status"
        assert "ISSUED" in content, "Must define ISSUED status"
        assert "CLARIFY" in content, "Must define CLARIFY status"

    def test_has_all_command_flags(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "--security" in content, "Must document --security flag"
        assert "--phase" in content, "Must document --phase flag"
        assert "--parallel" in content, "Must document --parallel flag"
        assert "--comments-only" in content, "Must document --comments-only flag"
        assert "init-options.json" in content, "Must reference agent detection"

    def test_has_ci_verification(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "Never modify CI configuration" in content, (
            "Must include specific CI integrity rule"
        )

    def test_has_comments_only_mode(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "## Comments-Only Mode" in content, "Must have Comments-Only Mode section"
        assert "skip" in content.lower() and "review passes" in content.lower(), (
            "Comments-only must mention skipping review passes"
        )

    def test_has_batch_reject(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "Batch-Reject" in content or "Batch-reject" in content or "batch-reject" in content, (
            "Must have batch-reject feature"
        )
        assert "review-exclusions.md" in content, "Must reference review-exclusions.md"

    def test_has_post_merge_verification(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "Post-Merge Verification" in content, "Must have post-merge verification section"
        assert "REVERTED" in content, "Must detect silent reversions"

    def test_has_reviewer_profile_awareness(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "Reviewer Profile" in content, "Must have reviewer profile awareness"
        assert "copilot-pull-request-reviewer" in content, "Must mention Copilot reviewer"
        assert "coderabbitai" in content, "Must mention CodeRabbit reviewer"

    def test_has_ci_debug_structure(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "CI Debug Structure" in content, "Must have CI debug structure for new integrations"

    def test_has_thread_resolution(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        assert "resolveReviewThread" in content, "Must mention thread resolution GraphQL mutation"

    def test_no_unresolved_placeholders(self):
        content = _REVIEW_CMD.read_text(encoding="utf-8")
        # {SCRIPT} and {ARGS} are legitimate spec-kit placeholders used by CommandRegistrar
        # Check for placeholder patterns that should have been filled in
        import re
        # Look for template-style placeholders like [FEATURE NAME] that should be resolved
        unresolved = re.findall(r'\[(?:FEATURE NAME|DATE|NEEDS CLARIFICATION)[^\]]*\]', content)
        assert len(unresolved) == 0, f"Found unresolved placeholders: {unresolved}"


class TestReviewTemplateFrontmatter:
    """Verify the review output template is well-formed."""

    def test_has_frontmatter(self):
        fm = _parse_frontmatter(_REVIEW_TEMPLATE)
        assert "description" in fm, "Review template must have 'description' field"

    def test_has_phase_section_structure(self):
        content = _REVIEW_TEMPLATE.read_text(encoding="utf-8")
        assert "## Phase N Review" in content, "Must have phase review section template"
        assert "### Spec Compliance" in content, "Must have spec compliance section"
        assert "### Code Quality" in content, "Must have code quality section"
        assert "### Security" in content, "Must have security section"
        assert "### Actions Taken" in content, "Must have actions taken section"

    def test_has_pass_fail_markers(self):
        content = _REVIEW_TEMPLATE.read_text(encoding="utf-8")
        assert "PASS" in content, "Must include PASS marker"
        assert "FAIL" in content, "Must include FAIL marker"
        assert "SKIPPED" in content, "Must include SKIPPED marker"
