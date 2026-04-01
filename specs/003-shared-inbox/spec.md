# Feature Specification: Shared Inbox — Parallel Task Communication

**Feature Branch**: `003-shared-inbox`
**Created**: 2026-03-31
**Status**: Draft
**Input**: User description: "Parallel task shared inbox where agents can interact with each other mid-task. When tasks run in parallel (different agents working on different tasks simultaneously), they need a way to share decisions, signal completion of dependencies, request help, and hand off context between phases. This enables real multi-agent coordination during implementation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Task Completion Signaling (Priority: P1)

Agents working on parallel tasks need to know when dependency tasks complete. When an agent finishes a task that other tasks depend on, it posts a completion signal to the shared inbox with a summary of what was built and any decisions that deviate from or extend the plan. Agents waiting on that dependency can check the inbox to confirm the prerequisite is ready and learn about any implementation choices that affect their own work.

The implement command automatically posts COMPLETE messages when it marks a task done and automatically checks the inbox before starting each task that has dependencies. This is built into the command behavior, not a separate step the agent must remember.

**Why this priority**: Without dependency signaling, parallel agents either block waiting or build against assumptions that may be wrong. This is the minimum viable coordination — knowing when upstream work is done and what it looks like.

**Independent Test**: Can be tested by having two agents work on dependent tasks in parallel. Agent A completes a foundational task and a COMPLETE message appears in the inbox. Agent B, working on a task that depends on A, reads the inbox and confirms it received the completion signal with the correct context before proceeding.

**Acceptance Scenarios**:

1. **Given** an agent completing a task that other tasks depend on (per tasks.md dependency chain), **When** the task is marked complete by `/speckit.implement`, **Then** a COMPLETE message is automatically posted to the inbox containing the task ID, a summary of what was built, and any deviations from the plan.
2. **Given** an agent about to start a task with dependencies, **When** `/speckit.implement` begins that task, **Then** it automatically checks the inbox for completion signals from dependency tasks and surfaces their summaries.
3. **Given** a completion signal that includes deviations from plan.md (e.g., "used a different data structure than planned"), **When** a dependent agent reads it, **Then** the deviation is clearly flagged so the agent can adapt its approach.
4. **Given** tasks running sequentially (not in parallel), **When** a task completes, **Then** the inbox is still updated for audit purposes, but checking it is not required before the next task starts.

---

### User Story 2 — Cross-Task Information Sharing (Priority: P1)

Agents working on parallel tasks within the same phase need to share real-time decisions that affect each other's work. For example, Agent A building an API endpoint decides on a response format, and Agent B building the frontend consumer needs to know that format. Without the inbox, both agents work from the spec/contracts and hope they align. With the inbox, agents can post decisions as they make them, and other agents can read and adapt.

**Why this priority**: Co-equal with P1 because parallel task execution without coordination leads to integration failures. The spec and contracts provide the intended design, but implementation decisions (naming conventions chosen, error formats used, shared utilities created) need to flow between agents in real time.

**Independent Test**: Can be tested by running two parallel [P] tasks that share a boundary (e.g., API producer and consumer). The producing agent posts a decision to the inbox. The consuming agent reads it and adapts its implementation accordingly.

**Acceptance Scenarios**:

1. **Given** two parallel tasks that share a boundary (e.g., backend API and frontend consumer), **When** one agent makes an implementation decision that affects the shared boundary, **Then** it posts an INFO message to the inbox with enough detail for the other agent to act on it.
2. **Given** an agent working on a parallel task, **When** it starts or resumes work, **Then** it checks the inbox for any messages relevant to its task before proceeding.
3. **Given** multiple messages in the inbox from different agents, **When** an agent reads the inbox, **Then** messages are ordered chronologically and filterable by task ID, sender, or message type.
4. **Given** an agent that has already read previous messages, **When** it checks the inbox again, **Then** it can easily identify new messages since its last check.

---

### User Story 3 — Escalation and Help Requests (Priority: P2)

An agent encounters a problem it cannot resolve alone — a security question, a design ambiguity, a conflict between the spec and what's possible. It posts an ESCALATE message to the inbox addressed to a specific agent role (e.g., "Security Engineer") or to any available specialist. If agent role assignment (Spec 002) is configured, the request can target the assigned specialist. If not, the request is posted broadly and any agent (or the human) can respond.

Escalation resolution follows the append-only model: when an escalation is resolved, a new RESOLVE message is posted referencing the original ESCALATE message. The original message is never modified. Unresolved escalations are those with no corresponding RESOLVE message.

**Why this priority**: Blockers during parallel execution halt individual task progress. Without a way to request help, agents either make questionable decisions alone or stop completely. This depends on the basic inbox (P1) being functional first.

**Independent Test**: Can be tested by having an agent encounter a simulated blocker, post an escalation to the inbox, and verifying another agent (or the user) can see and respond to it with a RESOLVE message.

**Acceptance Scenarios**:

1. **Given** an agent encountering a blocker during task implementation, **When** it posts an ESCALATE message to the inbox, **Then** the message includes the task ID, a description of the blocker, what was attempted, and what input is needed.
2. **Given** an escalation addressed to a specific agent role, **When** the target agent checks the inbox, **Then** the escalation is prominently surfaced as requiring their attention.
3. **Given** an escalation that has been resolved, **When** the resolving agent posts a RESOLVE message referencing the original, **Then** the requesting agent can read the resolution and continue its work.
4. **Given** no agent role assignment is configured (Spec 002 not active), **When** an escalation is posted, **Then** it is addressed broadly and visible to all agents and the user.
5. **Given** an unresolved escalation (no corresponding RESOLVE message), **When** any agent checks the inbox, **Then** the unresolved escalation is surfaced prominently.

---

### User Story 4 — Phase Handoff Context (Priority: P2)

When a phase completes and the next phase begins, the agents from the completed phase post a handoff summary to the inbox. This captures implementation context that the spec artifacts don't cover: shortcuts taken, technical debt introduced, patterns established, environment-specific details, and anything the next phase's agents need to know. This is especially valuable when different agents handle different phases.

The implement command automatically posts a HANDOFF message when all tasks in a phase are marked complete. The next phase's first task automatically reads the handoff before starting.

**Why this priority**: Phase transitions are where context is most commonly lost. Spec artifacts describe intent; the inbox captures reality. Depends on the basic inbox (P1) being functional.

**Independent Test**: Can be tested by completing a phase, verifying a HANDOFF message is posted, starting the next phase, and verifying the new agent reads and uses the handoff context.

**Acceptance Scenarios**:

1. **Given** a phase completing (all tasks in the phase marked done), **When** `/speckit.implement` finishes the phase, **Then** it automatically posts a HANDOFF message covering: decisions made, deviations from plan, patterns established, known issues, and anything the next phase should know.
2. **Given** a HANDOFF message in the inbox, **When** a new agent starts the next phase, **Then** it reads the handoff before beginning any tasks and incorporates the context into its approach.
3. **Given** a handoff that includes deviations from the plan, **When** the next phase agent reads it, **Then** the deviations are clearly distinguished from plan-conforming decisions.

---

### User Story 5 — Review-to-Implementer Communication (Priority: P3)

When the review command (Spec 001) runs in `--parallel` mode and finds issues, it posts findings to the shared inbox rather than relying solely on review.md. The implementing agent working on the next phase can see review findings in real time and adjust its work if the findings affect the current phase. This turns the review from a batch report into a live feedback channel.

**Why this priority**: This integrates the inbox with Spec 001's parallel review mode. Both the review command and the inbox must be functional first. The review already writes to review.md — the inbox adds real-time visibility.

**Independent Test**: Can be tested by running `/speckit.review --parallel` while an implementation agent works on the next phase, and verifying review findings appear in the inbox promptly.

**Acceptance Scenarios**:

1. **Given** a parallel review running (Spec 001, `--parallel` mode), **When** the review finds a critical or flag-only issue, **Then** it posts a REVIEW message to the inbox so the implementing agent sees it without waiting for review.md.
2. **Given** a REVIEW message posted to the inbox, **When** the implementing agent reads it, **Then** the finding includes the severity, affected files, and whether it requires immediate attention or is informational.
3. **Given** no shared inbox is configured or available, **When** the review command runs in parallel, **Then** it falls back to review.md-only output — the inbox is additive, not required.

---

### User Story 6 — Cross-Feature Coordination via Symlinked Discovery (Priority: P2)

When multiple features are being developed in parallel (e.g., on separate worktrees), agents need to be aware of each other's work. Each feature's spec directory contains a `concurrent/` directory with symlinks to other active features' spec directories. The presence of symlinks is the signal — if `concurrent/` is empty or absent, the agent knows it's working solo. If symlinks exist, the agent can read other features' inboxes to see decisions that affect shared code or interfaces.

This eliminates the need for a separate project-level inbox. Each feature has its own inbox, and the symlinks let concurrent agents read each other's. When an agent makes a change that affects shared code or cross-cutting concerns, it posts a CROSS message to its own inbox, and agents on concurrent features can discover it by following the symlinks.

Symlinks are created as part of the worktree setup protocol and removed when a feature merges.

**Why this priority**: Intra-feature coordination (P1) must work first. But parallel feature development is common and cross-feature conflicts are expensive to fix after the fact. This is the difference between finding out at merge time and finding out while building.

**Independent Test**: Can be tested by running two features in parallel worktrees with concurrent symlinks. An agent on feature A posts a CROSS message about a shared interface change to its own inbox. An agent on feature B follows the symlink, reads feature A's inbox, and sees the cross-feature message before implementing code that depends on that interface.

**Acceptance Scenarios**:

1. **Given** multiple features being developed in parallel with symlinks in `concurrent/`, **When** an agent makes a change that affects shared code, common interfaces, or cross-cutting concerns, **Then** it posts a CROSS message to its own feature inbox.
2. **Given** symlinks in `concurrent/` pointing to other active features, **When** an agent checks the inbox at a task boundary, **Then** it also reads the inboxes of concurrent features (via symlinks) for CROSS messages.
3. **Given** a CROSS message in a concurrent feature's inbox, **When** an agent reads it, **Then** the message includes which feature made the change, what was changed, and what other features might be affected.
4. **Given** no symlinks in `concurrent/` (single-feature workflow), **When** the agent checks, **Then** no cross-feature check occurs — zero overhead for solo development.
5. **Given** a broken symlink in `concurrent/` (e.g., a worktree was cleaned up), **When** the agent follows it, **Then** the broken link is reported as a warning and skipped, not treated as an error.
6. **Given** symlinks in `concurrent/`, **When** an agent reads another feature's inbox, **Then** it only reads CROSS messages — it does not read or act on the other feature's internal INFO, COMPLETE, or ESCALATE messages.

---

### Edge Cases

- What happens when two agents write to the inbox simultaneously? Messages are individual entries (not a single file edited by multiple writers). The inbox format must support concurrent appends without corruption.
- What happens when the inbox grows very large over a long feature lifecycle? Agents should be able to filter by task ID, message type, and recency rather than reading the entire history.
- What happens when an escalation goes unanswered? Unresolved escalations (those with no RESOLVE message) are surfaced prominently when any agent checks the inbox. The system does not auto-resolve them.
- What happens when the inbox is used without parallel execution (single agent)? The inbox still works for audit and context capture, but checking it is not required since there's no concurrent agent to communicate with.
- What happens when agent role assignment (Spec 002) is not configured? The inbox works with generic sender/recipient identifiers (e.g., task IDs) instead of named agent roles. Agent assignment enriches the inbox but is not required.
- What happens when a message references a task that has been removed or renumbered? The message remains in the inbox with its original reference. Orphaned references are noted but do not cause errors.
- What happens when the inbox is checked but there are no new messages? The system reports "no new messages" without error — this is the normal state when all agents are in sync.
- What happens when a concurrent symlink is broken (worktree removed)? The broken link is reported as a warning and skipped. The agent continues with remaining valid symlinks.
- What happens when a concurrent feature has been merged/completed? The symlink should be removed as part of the merge cleanup. If not removed, the agent follows it, finds no new CROSS messages, and moves on.
- What happens when an agent reads another feature's inbox via symlink? It only reads CROSS messages. Internal coordination messages (COMPLETE, INFO, ESCALATE, HANDOFF) from other features are ignored.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a shared communication channel (the "inbox") within the spec directory that agents can write to and read from during implementation.
- **FR-002**: System MUST support concurrent writes from multiple agents without message corruption or data loss. Each message is stored as an individual file in the inbox directory, named `{timestamp}-{type}-{sender}.md`. Escalation files use `ESC-{NNN}.md` and resolution files use `RES-ESC-{NNN}.md` for trivial unresolved-escalation scanning.
- **FR-003**: System MUST support the following message types: COMPLETE (task done), INFO (decision or context sharing), ESCALATE (help request), RESOLVE (escalation resolution), HANDOFF (phase transition summary), REVIEW (review finding from Spec 001), and CROSS (cross-feature coordination).
- **FR-004**: Each message MUST include: timestamp, sender identifier (agent name from Spec 002 when available, otherwise task ID), recipient (specific agent/role, task ID, or "all"), message type, and content. RESOLVE messages MUST reference the original ESCALATE message. Messages MUST be concise summaries — not transcripts or full code dumps. File references are allowed; inline code blocks are not.
- **FR-004a**: Escalation targeting is advisory, not enforced. The recipient field is a label for filtering — any agent that checks the inbox sees all messages. When Spec 002 is active, recipient labels map to agent catalog names. No routing logic is required.
- **FR-005**: System MUST allow agents to filter messages by task ID, sender, recipient, message type, and recency (messages since last check).
- **FR-006**: System MUST surface unresolved escalations (those with no corresponding RESOLVE message) prominently when any agent checks the inbox.
- **FR-007**: The `/speckit.implement` command MUST automatically post COMPLETE messages when marking a task done and HANDOFF messages when all tasks in a phase are complete. This is achieved by adding inbox instructions to the existing `templates/commands/implement.md` template — behavioral additions to the command's Markdown instructions, not structural changes to the Python CLI.
- **FR-008**: The `/speckit.implement` command MUST automatically check the inbox before starting any task that has dependencies (per tasks.md dependency chain) and surface relevant completion signals and context. This modification composes with Spec 002's agent assignments (which affect WHO runs a task) without conflict — 003 affects WHEN coordination happens.
- **FR-009**: System MUST integrate with the review command (Spec 001) so parallel review findings can be posted to the inbox as REVIEW-type messages.
- **FR-010**: System MUST work without agent role assignment (Spec 002) by using task IDs and generic identifiers. When agent assignment is configured, messages SHOULD use assigned agent names for richer context.
- **FR-011**: System MUST be additive to the spec-kit pipeline — all existing commands work identically with or without the inbox configured.
- **FR-012**: System MUST follow spec-kit's existing patterns for artifacts: file-based, in the spec directory, human-readable, and compatible with existing command parsing.
- **FR-013**: System MUST support cross-feature discovery via a `concurrent/` directory in the spec directory containing symlinks to other active features' spec directories. The presence of symlinks is the signal that cross-feature coordination is active. Note: US6 (cross-feature coordination) is independently deferrable — the core inbox (US1-US4) delivers full value without it.
- **FR-014**: When `concurrent/` symlinks exist, agents MUST check concurrent features' inboxes for CROSS messages at task boundaries. Only CROSS messages are read from concurrent features — internal messages are ignored.
- **FR-015**: System MUST gracefully handle broken symlinks in `concurrent/` by warning and skipping, not erroring.
- **FR-016**: All messages MUST be append-only. Escalation resolution is recorded as a new RESOLVE message, not a modification to the original ESCALATE message.
- **FR-017**: System MUST follow spec-kit's existing command patterns: YAML frontmatter, script hooks (if applicable), and artifact reading conventions.

### Key Entities

- **Feature Inbox**: The shared communication channel for a single feature. Lives in the feature's spec directory (e.g., `specs/###-feature/inbox/`). Contains all messages across all phases. One per feature.
- **Message**: A single communication unit. Has a timestamp, sender, recipient, type (COMPLETE, INFO, ESCALATE, RESOLVE, HANDOFF, REVIEW, CROSS), and content. Messages are append-only — once written, they are not modified or deleted.
- **Concurrent Links**: Symlinks in the feature's `specs/###-feature/concurrent/` directory pointing to other active features' spec directories. Their presence signals cross-feature coordination is active. Created during worktree setup, removed on feature merge.
- **Escalation**: An ESCALATE message paired with its optional RESOLVE message. An escalation is "unresolved" when no RESOLVE message referencing it exists.
- **Handoff Summary**: A HANDOFF message posted at phase boundaries. Captures implementation context that supplements spec artifacts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agents working on parallel tasks can discover each other's completion signals and implementation decisions without reading each other's code or relying solely on spec artifacts.
- **SC-002**: Zero messages are lost or corrupted when multiple agents write to the inbox concurrently.
- **SC-003**: An agent can check the inbox for new messages relevant to its current task in under 5 seconds, even when the inbox contains hundreds of messages.
- **SC-004**: Unresolved escalations are visible to the target agent (or all agents) within one inbox check cycle — no escalation goes silently unnoticed.
- **SC-005**: Phase handoff summaries reduce context loss between phases — agents starting a new phase report fewer plan deviations caused by missing context from the previous phase.
- **SC-006**: The inbox operates as a pure addition — removing it has zero impact on existing spec-kit commands and workflows.
- **SC-007**: Agents on concurrent features discover CROSS messages from other features' inboxes via symlinks without any additional configuration beyond the symlinks themselves.

## Assumptions

- The inbox is file-based and lives in the spec directory, consistent with spec-kit's artifact model. It is not a running service or daemon.
- Agents are expected to check the inbox at natural checkpoints: before starting a task, after completing a task, and when encountering a blocker. The implement command automates the most critical checkpoints (dependency checks, phase handoffs). The system does not push notifications to agents (pull-based model).
- The feature inbox is scoped to a single feature (one per spec directory). Cross-feature visibility is achieved through symlinks in `concurrent/` — not a separate shared inbox.
- Message ordering is based on timestamps. Clock synchronization between agents is assumed (they're on the same machine).
- The inbox does not replace spec artifacts (spec.md, plan.md, contracts/). It supplements them with runtime coordination context that artifacts can't capture.
- The inbox format uses individual message files (one per message) named `{timestamp}-{type}-{sender}.md` to avoid concurrent write conflicts. Escalations use `ESC-{NNN}.md` / `RES-ESC-{NNN}.md` for easy resolution scanning.
- Inbox integration into `/speckit.implement` is achieved by adding behavioral instructions to the existing command template (`templates/commands/implement.md`). No changes to the Python CLI or shell scripts. This follows the same pattern as all spec-kit commands — Markdown instructions processed by the AI agent.
- Integration with Spec 001 (review findings in inbox) and Spec 002 (agent names in messages) is additive. The inbox works without either.
- The inbox is most valuable during parallel execution but provides audit value even for sequential execution.
- Cross-feature symlinks are created as part of the worktree setup protocol and removed when a feature merges. This is a manual or scripted step, not automated by spec-kit itself.
- The symlink-based approach assumes a filesystem that supports symlinks. Most development environments (Linux, macOS, WSL2) support this natively.
