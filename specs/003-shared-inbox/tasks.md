# Tasks: Shared Inbox — Parallel Task Communication

**Input**: Design documents from `/specs/003-shared-inbox/`
**Prerequisites**: plan.md (required), spec.md (required)

## Phase 1: Inbox Message Template

**Purpose**: Define the message format agents use for inbox communication

- [X] T001 Create `templates/inbox-message-template.md` with YAML frontmatter schema (type, sender, recipient, timestamp, references) and body structure for each message type
- [X] T002 [P] Document file naming convention in template: `{timestamp}-{type}-{sender}.md` for standard messages, `ESC-{NNN}.md` / `RES-ESC-{NNN}.md` for escalations
- [X] T003 [P] Add examples for all 7 message types (COMPLETE, INFO, ESCALATE, RESOLVE, HANDOFF, REVIEW, CROSS) with realistic content

**Checkpoint**: Message template is complete and self-documenting

---

## Phase 2: Implement Command Integration

**Purpose**: Add inbox instructions to the existing implement command template

- [X] T004 Read current `templates/commands/implement.md` and identify insertion points for inbox instructions
- [X] T005 Add inbox check instruction before dependent task execution (step 6 area): "If `FEATURE_DIR/inbox/` exists, scan for COMPLETE messages from dependency tasks and surface summaries before proceeding"
- [X] T006 Add COMPLETE message post instruction after task completion (step 8 area): "After marking a task [X], if inbox/ exists, post a COMPLETE message with task ID, summary, and any plan deviations"
- [X] T007 Add HANDOFF message post instruction after phase completion (step 9 area): "After all tasks in a phase are complete, post a HANDOFF message capturing decisions, deviations, patterns, and known issues"
- [X] T008 Add cross-feature check instruction at task boundaries: "If `FEATURE_DIR/concurrent/` exists with symlinks, check concurrent features' inboxes for CROSS messages. Only read CROSS-type messages. Report broken symlinks as warnings."
- [X] T009 Ensure all inbox instructions are conditional on inbox/ directory existence — existing projects without inbox must work identically

**Checkpoint**: Implement command has inbox integration. Running it without inbox/ directory produces identical behavior to before.

---

## Phase 3: Tests

**Purpose**: Verify template integrity and backward compatibility

- [X] T010 Create `tests/test_inbox.py` with test that inbox message template exists and has required sections (frontmatter schema, naming convention, all 7 message types)
- [X] T011 [P] Add test that `templates/commands/implement.md` contains inbox instructions (grep for key phrases: "inbox/", "COMPLETE message", "HANDOFF message")
- [X] T012 [P] Add test that implement.md inbox instructions are conditional (grep for "If.*inbox" pattern — all inbox behavior must be gated)
- [X] T013 Add test verifying implement.md still has all original required sections (backward compatibility — no existing functionality removed)

**Checkpoint**: All tests pass. Inbox additions are verified and backward-compatible.

---

## Phase 4: Polish

- [X] T014 Review all changes for consistency with spec-kit template conventions (heading hierarchy, markdown formatting, instruction style)
- [X] T015 Verify the inbox message template examples are realistic and cover the cross-spec agreements (tasks.md format `[@agent-name]`, review.md reference format for REVIEW messages)

---

## Dependencies & Execution Order

- **Phase 1**: No dependencies — can start immediately
- **Phase 2**: Depends on Phase 1 (need message template to reference in instructions)
- **Phase 3**: Depends on Phases 1 and 2 (testing what was built)
- **Phase 4**: Depends on all previous phases

### Parallel Opportunities

- T002 and T003 can run in parallel (different sections of the same template)
- T011 and T012 can run in parallel (different test assertions)
- T005, T006, T007, T008 are sequential (each modifies implement.md at different insertion points)
