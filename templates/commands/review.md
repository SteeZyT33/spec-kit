---
description: Post-implementation review that validates code against spec artifacts, applies tiered fixes, creates phase PRs, and manages the GitHub review cycle.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
tools:
  - 'github/github-mcp-server/issue_write'
  - 'github/github-mcp-server/pull_request_review_write'
handoffs:
  - label: Continue Implementation
    agent: speckit.implement
    prompt: Continue to the next implementation phase
  - label: Re-Analyze Artifacts
    agent: speckit.analyze
    prompt: Re-analyze spec artifacts after review changes
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before review)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_review` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Parse arguments** from user input:
   - `--security`: Force security pass regardless of spec content
   - `--parallel`: Run review as background agent (see Parallel Mode section)
   - `--phase N`: Review a specific phase (default: current/latest completed phase)
   - Any remaining text: Additional context or focus area for the review

3. **Load review context** — read from FEATURE_DIR:
   - **REQUIRED**: Read `spec.md` for acceptance scenarios, functional requirements, and success criteria
   - **REQUIRED**: Read `plan.md` for architecture decisions, file structure, and project organization
   - **REQUIRED**: Read `tasks.md` for phase boundaries, task dependencies, and current phase status
   - **IF EXISTS**: Read `contracts/` for API specifications, data formats, and interface contracts
   - **IF EXISTS**: Read `data-model.md` for entity definitions and relationships
   - **IF EXISTS**: Read `research.md` for technical decisions and constraints
   - **IF EXISTS**: Read `review.md` for previous phase review history (will be appended to)
   - If any REQUIRED artifact is missing, report which artifacts are missing. Still run passes against available artifacts but clearly note reduced coverage in the output.

4. **Determine current phase** from tasks.md:
   - Scan task checkboxes to identify the most recently completed phase
   - If `--phase N` is specified, use that phase instead
   - Identify which tasks belong to the target phase and what code they produced

5. **Check for agent assignments** (Spec 002 integration — conditional):
   - If tasks.md contains `[@agent-name]` markers on task lines, note which agent implemented each task
   - This provides context for review feedback (e.g., "The frontend task assigned to [@Frontend Developer] has...")
   - If no agent markers are present, proceed without this context

## Review Passes

Execute these three passes sequentially. For each pass, produce findings with file:line references.

### Pass 1 — Spec Compliance (always runs)

Review the implemented code against spec.md:

- **Acceptance scenarios**: For each user story acceptance scenario in spec.md, verify the implementation satisfies it. Report any scenario that is not met, quoting the specific scenario.
- **Functional requirements**: For each FR-### in spec.md, verify the implementation addresses it. Report unimplemented or partially implemented requirements.
- **Contracts alignment**: If contracts/ exists, verify the implementation matches the defined interfaces (endpoints, schemas, formats).
- **Data model alignment**: If data-model.md exists, verify entities, fields, and relationships match the implementation.
- **Scope creep detection**: Identify any implemented features or behaviors that are NOT specified in spec.md. Report them as potential scope creep.

Output: `### Spec Compliance: PASS` or `### Spec Compliance: FAIL` with itemized findings.

### Pass 2 — Code Quality (always runs)

Review the implemented code against plan.md:

- **Architecture alignment**: Verify the code structure matches plan.md's project structure and architecture decisions.
- **File organization**: Verify files are in the locations specified by plan.md.
- **Obvious bugs**: Identify clear bugs, dead code, or missing error handling that the spec required.
- **Plan deviations**: Report any deviations from plan.md's technical decisions (e.g., different framework, different data storage).

Output: `### Code Quality: PASS` or `### Code Quality: FAIL` with itemized findings.

### Pass 3 — Security (conditional)

Runs when ANY of these conditions are met:
- `--security` flag is passed
- spec.md mentions authentication, authorization, login, password, token, OAuth, API key
- spec.md mentions payment, billing, credit card, financial
- spec.md mentions personal data, PII, GDPR, privacy, user data
- spec.md mentions external API, webhook, third-party integration

When this pass runs, check:

- **OWASP top 10**: Scan for common vulnerabilities (injection, broken auth, sensitive data exposure, etc.)
- **Auth/authz**: Verify authentication and authorization match spec requirements
- **Input validation**: Verify all system boundary inputs are validated
- **Secrets handling**: Verify no hardcoded secrets, API keys, or credentials. Verify environment variables are used properly.

When this pass is skipped, output: `### Security: SKIPPED`

Output: `### Security: PASS` or `### Security: FAIL` with itemized findings.

## Tiered Fix Behavior

After all three passes complete, process findings by tier:

### Tier 1: Auto-Fix (trivial, unambiguous, low risk)

For each finding that is trivial and unambiguous:
- Apply the fix
- Create a separate commit with message: `fix(review): [brief description] — auto-fix from /speckit.review`
- Record in review.md: the finding, the fix, and the commit SHA

Examples of auto-fixable issues:
- Missing error handling that the spec explicitly required
- Import cleanup (unused imports, missing imports)
- Naming inconsistencies with the plan (e.g., function named `getUser` but plan says `fetchUser`)
- Missing type annotations that the plan specified

### Tier 2: Suggest-Fix (medium complexity, clear solution)

For each finding with a clear but non-trivial solution:
- Present the finding and a proposed diff to the user
- **Wait for explicit approval** before applying
- If approved: apply, commit, record in review.md
- If rejected: record as flagged in review.md, no code change

Examples of suggest-fix issues:
- Restructuring a function to match plan architecture
- Adding missing validation logic
- Refactoring to match specified patterns

### Tier 3: Flag-Only (judgment call needed)

For each finding that requires human judgment:
- Report in review.md with full context
- Do NOT make any code changes
- These may become PR comments for discussion

Examples of flag-only issues:
- Missing feature or user story
- Architectural drift from plan
- Security concerns requiring design decisions
- Performance issues requiring tradeoff decisions

## Review Report Output

After all passes and fixes, write to `FEATURE_DIR/review.md`. If the file exists, **append** a new section. Never overwrite previous phase reviews.

Use this structure for each phase section:

```markdown
## Phase N Review — YYYY-MM-DD

### Spec Compliance: PASS | FAIL
- [findings with file:line references]

### Code Quality: PASS | FAIL
- [findings with file:line references]

### Security: PASS | FAIL | SKIPPED
- [findings with file:line references]

### Actions Taken
- AUTO-FIXED: [count] issues ([commit SHAs])
- SUGGESTED: [count] issues ([accepted/pending/rejected])
- FLAGGED: [count] issues
- ISSUED: [count] issues ([issue numbers])

### PR: #[number] — [status]
- Comments: [total] | Addressed: [n] | Rejected: [n] | Issued: [n] | Clarify: [n]
```

If no issues are found in a pass, report: `- No issues found.`

## PR Lifecycle

After review.md is written and all fixes are committed:

**Step 1: Check GitHub tool availability**

Attempt to use GitHub MCP tools. If unavailable, output: "GitHub tools not available — review.md produced, PR creation skipped." Skip to the extension hooks section.

**Step 2: Create phase PR** (one per phase, not per feature)

- **Check for existing PR**: If a PR already exists for this phase/branch, update it instead of creating a duplicate.
- **Title**: `Phase N: [phase name from tasks.md] — [feature branch name]`
- **Body**: Include review.md summary for this phase, pass/fail table, list of auto-fixes with commit SHAs.
- **Labels**: Add phase number and review status labels if the repository supports them.

**Step 3: Verify pre-commit hooks and CI locally**

Before pushing any fix commits:
- Run all pre-commit hooks locally and verify they pass
- If hooks fail, fix the issue and re-commit — do NOT skip hooks with `--no-verify`

After pushing:
- Monitor CI pipeline status
- If CI fails:
  1. Pull CI logs and diagnose the failure
  2. Fix the issue **locally**
  3. Verify the fix passes **locally** (run the same checks CI runs)
  4. Push the corrected fix
  5. Repeat until CI passes
- **NON-NEGOTIABLE**: Never modify CI configuration, workflow files, or hook configuration to achieve a pass. Fix the actual code problem.

**Step 4: Comment Response Protocol**

When processing PR comments (from other contributors, reviewers, or automated systems), respond to **every** comment with exactly one status:

| Status | Format | When to Use |
|--------|--------|-------------|
| ADDRESSED | `ADDRESSED in [commit SHA] — [brief description of fix]` | Fix applied and pushed |
| REJECTED | `REJECTED — [reason with evidence from spec/plan]` | Comment conflicts with spec/plan or is incorrect |
| ISSUED | `ISSUED #[issue number] — [why deferred, with actual reason]` | Valid but out of scope for current phase |
| CLARIFY | `CLARIFY — [specific question]` | Comment is ambiguous, needs more context |

**Rules**:
- Every comment gets exactly one response. No exceptions. No silent fixes.
- Always prefer fixing immediately over deferring. If the fix is clear, just do it (ADDRESSED).
- Never say "noted for later" without creating an issue. If deferring, always use ISSUED with a real GitHub issue.
- After a CLARIFY response is answered, follow up with ADDRESSED, REJECTED, or ISSUED.

**Step 5: Deferred Fix Protocol**

For every ISSUED response, create a GitHub issue containing:
- Title: descriptive of the deferred issue
- Body:
  - Link to the original PR comment
  - Which spec and phase it relates to
  - Why it was deferred (an actual reason — not "noted for later")
  - Suggested approach if known
- When GitHub tools are unavailable: record the same information in review.md under the Actions Taken section with `ISSUED:` prefix.

## Inbox Integration (Spec 003 — conditional)

If a shared inbox exists at `FEATURE_DIR/inbox/`:

- During `--parallel` mode, post critical and flag-only findings as REVIEW messages to the inbox
- Message format: individual file named `{timestamp}-REVIEW-review-command.md`
- Message content: `REVIEW | Phase N | [severity] | [category] | See review.md Phase N [section] for details`
- The inbox message is a **notification** referencing review.md (the authoritative record), not a duplicate of the full finding

If no inbox exists, skip silently. The inbox is additive, not required.

## Parallel Mode (`--parallel`)

When `--parallel` is passed:

1. **Detect active agent**: Read `.specify/init-options.json` and check the `ai` field.

2. **Dispatch based on agent**:
   - **`claude`** (Claude Code): Launch the review as a subagent using the Agent tool, or in a new tmux session. Return control to the user immediately.
   - **`codex`** (Codex): Launch the review as a background sandbox task.
   - **All other agents** or unrecognized values: Output message: "Parallel mode is not supported for [agent name]. Running review in blocking mode." Then proceed with normal blocking review.

3. **Async completion**: When the parallel review completes:
   - Write review.md
   - Create PR (if GitHub tools available)
   - Post inbox notification (if inbox available)
   - If critical issues found, write a prominent summary to review.md

When `--parallel` is NOT passed, the review runs in blocking mode (default).

## Completion

After all steps complete:

1. Output a summary:
   - Pass/fail status for each review pass
   - Count of auto-fixes, suggest-fixes, and flagged issues
   - PR number and URL (if created)
   - Path to review.md

2. **Check for extension hooks**: After completion, check if `.specify/extensions.yml` exists in the project root.
   - If it exists, read it and look for entries under the `hooks.after_review` key
   - If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
   - Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
   - For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
     - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
     - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
   - For each executable hook, output the following based on its `optional` flag:
     - **Optional hook** (`optional: true`):
       ```
       ## Extension Hooks

       **Optional Hook**: {extension}
       Command: `/{command}`
       Description: {description}

       Prompt: {prompt}
       To execute: `/{command}`
       ```
     - **Mandatory hook** (`optional: false`):
       ```
       ## Extension Hooks

       **Automatic Hook**: {extension}
       Executing: `/{command}`
       EXECUTE_COMMAND: {command}
       ```
   - If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
