"""
Tests for the smart assign feature (005-smart-assign).

Validates assign.md improvements:
  - Human Lead agent, confidence scores, context detection
  - --human-tasks, --force flags
  - Dependency handoff warnings, phase context weighting

Validates plan.md improvements:
  - Agent expertise consultation section
  - Lens activation table
  - Backward compatibility guard clause
"""

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).parent.parent
_ASSIGN_CMD = _REPO_ROOT / "templates" / "commands" / "assign.md"
_PLAN_CMD = _REPO_ROOT / "templates" / "commands" / "plan.md"


def _parse_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{path.name} must start with YAML frontmatter"
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


# === assign.md tests ===


class TestAssignHumanLead:
    def test_human_lead_in_agent_table(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Human Lead" in content

    def test_human_lead_has_judgment_keywords(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        for kw in ["triage", "decide", "evaluate", "approve", "sign off"]:
            assert kw in content.lower(), f"Missing judgment keyword: {kw}"

    def test_multi_word_matching_note(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "phrases" in content.lower(), "Must mention phrase matching for multi-word keywords"


class TestAssignContextDetection:
    def test_has_context_detection_step(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Context detection" in content

    def test_has_skip_recommendation(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Skip Recommendation" in content or "skip" in content.lower()

    def test_has_task_count_threshold(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "15" in content, "Must mention task count threshold of 15"

    def test_has_large_spec_override(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "30" in content, "Must mention large-spec threshold of 30"

    def test_has_worktree_check(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "worktree" in content.lower()


class TestAssignForceFlag:
    def test_force_flag_documented(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "--force" in content

    def test_force_in_quick_reference(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        qr_start = content.find("## Quick Reference")
        assert qr_start != -1
        assert "--force" in content[qr_start:]


class TestAssignHumanTasksFlag:
    def test_human_tasks_flag_documented(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "--human-tasks" in content

    def test_human_tasks_in_quick_reference(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        qr_start = content.find("## Quick Reference")
        assert qr_start != -1
        assert "--human-tasks" in content[qr_start:]


class TestAssignConfidenceScores:
    def test_confidence_mentioned(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "confidence" in content.lower()

    def test_low_confidence_threshold(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "0.3" in content

    def test_confidence_in_output(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Confidence" in content, "Output table must have Confidence column"


class TestAssignDependencyWarnings:
    def test_dependency_analysis_present(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "Dependency" in content
        assert "handoff" in content.lower()


class TestAssignPhaseWeighting:
    def test_phase_context_weighting_present(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "phase context weighting" in content.lower()

    def test_phase_bonus_values(self):
        content = _ASSIGN_CMD.read_text(encoding="utf-8")
        assert "+2" in content, "Must mention +2 bonus"
        assert "+3" in content, "Must mention +3 bonus for Human Lead"


# === plan.md tests ===


class TestPlanAgentExpertise:
    def test_expertise_section_exists(self):
        content = _PLAN_CMD.read_text(encoding="utf-8")
        assert "Agent Expertise Consultation" in content

    def test_lens_activation_table(self):
        content = _PLAN_CMD.read_text(encoding="utf-8")
        assert "Spec Keywords" in content and "Agent Lens" in content

    def test_security_lens_present(self):
        content = _PLAN_CMD.read_text(encoding="utf-8")
        assert "Security Engineer" in content
        assert "authentication" in content.lower()

    def test_data_engineer_lens_present(self):
        content = _PLAN_CMD.read_text(encoding="utf-8")
        assert "Data Engineer" in content or "Database Optimizer" in content
        assert "migration" in content.lower()

    def test_guard_clause(self):
        content = _PLAN_CMD.read_text(encoding="utf-8")
        lower = content.lower()
        assert "guard" in lower or "skip" in lower, "Must have guard clause for no-match scenario"

    def test_external_agent_support(self):
        content = _PLAN_CMD.read_text(encoding="utf-8")
        assert "agent_source" in content, "Must reference external agent catalog"

    def test_backward_compatible(self):
        content = _PLAN_CMD.read_text(encoding="utf-8")
        assert "additive" in content.lower() or "optional" in content.lower(), (
            "Expertise step must be described as optional/additive"
        )
