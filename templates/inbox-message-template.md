---
description: "Template for shared inbox message files used in parallel task coordination"
---

# Inbox Message Format

Messages are individual files in `specs/###-feature/inbox/`. Each file represents one communication between agents during implementation.

## File Naming Convention

- **Standard messages**: `{YYYY-MM-DDTHH-MM-SS}-{TYPE}-{sender-slug}.md`
  - Example: `2026-03-31T14-30-00-COMPLETE-backend-architect.md`
  - Example: `2026-03-31T15-00-00-INFO-frontend-developer.md`
- **Escalations**: `ESC-{NNN}.md` (zero-padded three digits)
  - Example: `ESC-001.md`
- **Resolutions**: `RES-ESC-{NNN}.md` (references the escalation number)
  - Example: `RES-ESC-001.md`

The naming convention enables:
- Chronological ordering via timestamp prefix
- Filtering by type via the type segment
- Trivial unresolved-escalation scanning: list `ESC-*.md`, subtract those with matching `RES-ESC-*.md`

## Message Frontmatter

Every message file starts with YAML frontmatter:

```yaml
---
type: COMPLETE | INFO | ESCALATE | RESOLVE | HANDOFF | REVIEW | CROSS
sender: "[agent name from Spec 002 assignment, or task ID if no assignment]"
recipient: "[agent name/role, task ID, or 'all']"
timestamp: "YYYY-MM-DDTHH:MM:SS"
task_id: "T###"
phase: "[Phase N name]"
references: "[optional: ESC-NNN for RESOLVE, review.md section for REVIEW]"
---
```

## Message Body

The body follows the frontmatter. Keep messages **concise** — summaries, not transcripts. File references are encouraged; short code snippets and fenced code blocks are allowed when necessary (e.g., API response formats), but avoid large code dumps or full transcripts.

## Message Types

### COMPLETE — Task Completion Signal

Posted automatically by `/speckit.implement` when a task is marked done.

```markdown
---
type: COMPLETE
sender: "Backend Architect"
recipient: "all"
timestamp: "2026-03-31T14:30:00"
task_id: "T004"
phase: "Phase 2: Foundational"
---

## Task T004 Complete: Setup database schema and migrations

**Summary**: Created SQLite schema with users, sessions, and audit_log tables. Migrations framework using Alembic.

**Deviations from plan**: None — followed data-model.md exactly.

**Decisions made**:
- Used WAL mode for concurrent read access
- Added created_at/updated_at timestamps to all tables (not in data model but standard practice)

**Artifacts created**: `src/models/schema.py`, `alembic/versions/001_initial.py`
```

### INFO — Cross-Task Decision Sharing

Posted by agents when making implementation decisions that affect parallel tasks.

```markdown
---
type: INFO
sender: "Backend Architect"
recipient: "Frontend Developer"
timestamp: "2026-03-31T15:00:00"
task_id: "T012"
phase: "Phase 3: User Story 1"
---

## API Response Format Decision

The `/api/users` endpoint returns:

```json
{"data": [{"id": 1, "name": "...", "email": "..."}], "meta": {"total": 100, "page": 1}}
```

Pagination uses `?page=N&per_page=M` query params. Default per_page=20.

This affects frontend tasks T018 and T020 which consume this endpoint.
```

### ESCALATE — Help Request

Posted when an agent hits a blocker needing specialist input. Targeting is **advisory** — any agent sees all messages. The recipient label helps agents self-identify.

```markdown
---
type: ESCALATE
sender: "Frontend Developer"
recipient: "Security Engineer"
timestamp: "2026-03-31T16:00:00"
task_id: "T020"
phase: "Phase 4: User Story 2"
---

## ESCALATION: OAuth token storage approach

**Blocker**: Need to store OAuth refresh tokens client-side. Spec requires "secure token handling" (FR-005) but doesn't specify the approach.

**Attempted**: Considered localStorage (insecure), httpOnly cookies (requires backend proxy), encrypted IndexedDB.

**Input needed**: Which approach aligns with the security requirements? This blocks T020 and T021.
```

### RESOLVE — Escalation Resolution

Posted when an escalation is answered. References the original ESC file. The original ESCALATE message is **never modified** (append-only).

```markdown
---
type: RESOLVE
sender: "Security Engineer"
recipient: "Frontend Developer"
timestamp: "2026-03-31T16:30:00"
task_id: "T020"
phase: "Phase 4: User Story 2"
references: "ESC-001"
---

## Resolution for ESC-001: OAuth token storage

**Answer**: Use httpOnly cookies with SameSite=Strict. Backend proxy at `/api/auth/token` handles the refresh flow. Frontend never touches raw tokens.

**Rationale**: This is the only approach that satisfies OWASP token storage guidelines and the spec's FR-005.

**Impact**: T020 can proceed. T021 (backend auth endpoints) needs to implement the `/api/auth/token` proxy endpoint.
```

### HANDOFF — Phase Transition Summary

Posted automatically by `/speckit.implement` when all tasks in a phase are complete.

```markdown
---
type: HANDOFF
sender: "Backend Architect"
recipient: "all"
timestamp: "2026-03-31T18:00:00"
task_id: "Phase 2"
phase: "Phase 2: Foundational → Phase 3: User Story 1"
---

## Phase 2 Handoff: Foundational Complete

**Decisions made**:
- Chose SQLite with WAL mode (plan specified "relational database")
- Used Alembic for migrations instead of raw SQL
- Added rate limiting middleware not in spec (defensive, 100 req/min default)

**Deviations from plan**:
- Skipped Redis caching layer — not needed at current scale. Plan noted it as optional.

**Patterns established**:
- All service functions return `Result` objects with `.data` and `.error` fields
- Logging uses structured JSON format to `logs/app.jsonl`

**Known issues**:
- Migration rollback not tested — works forward only for now

**Environment details**:
- Python 3.12, FastAPI 0.115, SQLite 3.45
- Dev server at localhost:8000, test DB at tests/test.db
```

### REVIEW — Review Finding Notification

Posted by `/speckit.review` (Spec 001) when running in `--parallel` mode. References review.md for full details — the inbox message is a **notification**, not the authoritative record.

```markdown
---
type: REVIEW
sender: "Code Reviewer"
recipient: "all"
timestamp: "2026-03-31T19:00:00"
task_id: "Phase 3"
phase: "Phase 3: User Story 1"
references: "review.md Phase 3 Spec Compliance"
---

## Review Finding: CRITICAL — Missing input validation

**Severity**: flag-only (requires judgment)
**Category**: spec-compliance
**Affected**: `src/api/users.py:45`
**Requires immediate attention**: Yes

FR-003 requires input validation on all API endpoints. The `/api/users` POST endpoint accepts raw input without schema validation. See review.md Phase 3 Spec Compliance section for full analysis.
```

### CROSS — Cross-Feature Coordination

Posted to a feature's own inbox when a change affects shared code or interfaces. Agents on concurrent features (discovered via `concurrent/` symlinks) read only CROSS messages from other features.

```markdown
---
type: CROSS
sender: "Backend Architect"
recipient: "all"
timestamp: "2026-03-31T20:00:00"
task_id: "T008"
phase: "Phase 2: Foundational"
---

## Cross-Feature Notice: Shared auth middleware modified

**Feature**: 001-review-command
**Change**: Added `require_auth` decorator to `src/middleware/auth.py`
**Affects**: Any feature using the `/api/` route prefix — the decorator is applied globally.
**Other features that may be affected**: 002-agent-role-assignment (if it adds API endpoints), 003-shared-inbox (if it reads/writes via API).

If your feature adds API endpoints, they will require authentication by default. Use `@skip_auth` to opt out.
```

## Checking the Inbox

Agents check the inbox at natural checkpoints:

1. **Before starting a dependent task**: Scan for COMPLETE messages from dependency tasks
2. **After completing a task**: Post a COMPLETE message (automated by implement command)
3. **After completing a phase**: Post a HANDOFF message (automated by implement command)
4. **When encountering a blocker**: Post an ESCALATE message
5. **At task boundaries when concurrent/ exists**: Scan concurrent features for CROSS messages

To check for new messages since last check, use the timestamp-based filename ordering. Compare the most recent file you've seen against the directory listing.

To find unresolved escalations: list `ESC-*.md` files, check for matching `RES-ESC-*.md` files. Missing matches = unresolved.
