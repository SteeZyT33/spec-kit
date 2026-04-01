# Implementation Plan: Shared Inbox — Parallel Task Communication

**Branch**: `003-shared-inbox` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)

## Summary

Add a shared inbox system to spec-kit that enables inter-agent coordination during parallel implementation. The inbox is a directory of individual message files in the spec directory, with behavioral instructions added to the existing implement command template. No new Python code — this follows spec-kit's template-driven pattern.

## Technical Context

**Language/Version**: Markdown templates (spec-kit's command and artifact templates)
**Primary Dependencies**: Existing implement command template, spec directory conventions
**Storage**: Individual markdown message files in `specs/###-feature/inbox/`
**Testing**: pytest (spec-kit's existing invariant and parity test patterns)
**Target Platform**: Cross-platform, all supported AI agents
**Project Type**: Template additions + command template modification
**Constraints**: Must not break existing implement command behavior. Must be purely additive.
**Scale/Scope**: One message template + implement.md modifications + test additions

## Project Structure

### Documentation (this feature)

```text
specs/003-shared-inbox/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── checklists/
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Task breakdown (next step)
```

### Source Code (repository root)

```text
templates/
├── commands/
│   └── implement.md         # MODIFIED: Add inbox check/post instructions
└── inbox-message-template.md # NEW: Template for inbox message files

tests/
└── test_inbox.py            # NEW: Inbox template and format tests
```

**Structure Decision**: Minimal footprint. One new template file, one modified template, one test file. No new directories in source. The `inbox/` directory is created per-feature at runtime by the implementing agent, not by project scaffolding.

## Complexity Tracking

No complexity violations. The implementation adds behavioral instructions to an existing template and one new template file.

## Implementation Approach

### What Gets Built

1. **`templates/inbox-message-template.md`** — Defines the format for inbox message files. Contains:
   - YAML frontmatter: message type, sender, recipient, timestamp, references
   - Body: message content following type-specific structure
   - Examples for each message type (COMPLETE, INFO, ESCALATE, RESOLVE, HANDOFF, REVIEW, CROSS)
   - File naming convention: `{timestamp}-{type}-{sender}.md`, `ESC-{NNN}.md`, `RES-ESC-{NNN}.md`

2. **Modifications to `templates/commands/implement.md`** — Add inbox instructions at three points:
   - **Before dependent tasks**: Check `inbox/` for COMPLETE signals from dependency tasks
   - **After task completion**: Post COMPLETE message to `inbox/`
   - **After phase completion**: Post HANDOFF message to `inbox/`
   - **At task boundaries (when concurrent/ exists)**: Check concurrent features' inboxes for CROSS messages
   - All inbox instructions are conditional: "If `inbox/` directory exists in FEATURE_DIR..."

3. **`tests/test_inbox.py`** — Tests following spec-kit's existing patterns:
   - Message template has required sections
   - Implement.md contains inbox instructions
   - Message file naming conventions are documented
   - Inbox instructions don't break existing implement behavior

### What Does NOT Get Built

- No new Python modules or classes
- No new shell scripts
- No new CLI commands (inbox is implicit, not a separate command)
- No changes to existing Python source (agents.py, __init__.py)
- Cross-feature US6 (concurrent/ symlinks) — instructions are included but this is documented as independently deferrable

### Key Design Decisions

1. **Inbox directory creation**: The implementing agent creates `specs/###-feature/inbox/` on first message post. It is not pre-created by scaffolding.

2. **Conditional instructions**: All inbox instructions in implement.md are wrapped in "If inbox/ exists" checks. This ensures existing projects without inbox continue working identically.

3. **Message template as reference**: The inbox message template is a reference document — agents use it to format their messages. It's not processed by CommandRegistrar (it's not a command).

4. **No explicit inbox command**: The inbox is accessed through implement.md instructions (automatic) and by agents reading the directory directly (manual). No `/speckit.inbox` command.
