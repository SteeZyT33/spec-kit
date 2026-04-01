---
description: Assign the best-fit agent to each task in tasks.md based on available agent capabilities, task descriptions, and phase context.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before assignment)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_assign` key
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

2. **Check for `--reassign-all` flag**: If the user passed `--reassign-all` (or similar intent in `$ARGUMENTS`), set REASSIGN_ALL = true. Otherwise REASSIGN_ALL = false.

3. **Read configuration**: Read `.specify/init-options.json` from the project root.
   - Extract the `ai` field (identifies the active AI harness — e.g., "claude", "codex", "cursor")
   - Extract the optional `agent_source` field (filesystem path to an external agent definition directory)
   - If `init-options.json` does not exist or cannot be parsed, use defaults: ai = "generic", agent_source = null

4. **Discover available agents** using a two-tier approach:

   ### Tier 1: Internal Agents (zero-config, always available)

   Based on the `ai` field, use the following built-in agent type mappings. These represent common specialist roles available in most AI harnesses:

   | Agent Name | Specialization Keywords |
   |------------|------------------------|
   | Backend Architect | backend, API, database, server, endpoint, REST, GraphQL, migration, schema, model, service, middleware |
   | Frontend Developer | frontend, UI, component, React, Vue, Angular, CSS, HTML, page, layout, form, button, modal, responsive |
   | Security Engineer | security, auth, authentication, authorization, OAuth, OWASP, encryption, secrets, RBAC, permissions, CORS, CSRF, XSS, SQL injection, input validation |
   | DevOps Automator | CI/CD, Docker, infrastructure, deployment, pipeline, Kubernetes, terraform, monitoring, logging, environment, config, nginx |
   | AI Engineer | ML, AI, LLM, model, embeddings, vector, training, inference, prompt, fine-tune, RAG, NLP |
   | Mobile App Builder | mobile, iOS, Android, Swift, Kotlin, React Native, Flutter, app, touch, gesture, notification |
   | Database Optimizer | database, SQL, query, index, migration, schema, ORM, performance, normalization, join, transaction |
   | Evidence Collector | test, testing, jest, vitest, pytest, spec, assertion, mock, stub, fixture, coverage, E2E, integration test, unit test, QA, quality, verify, validate |
   | Technical Writer | documentation, README, docs, guide, tutorial, API docs, changelog, comment |
   | UX Architect | design, UX, wireframe, prototype, user flow, accessibility, a11y, WCAG |
   | Data Engineer | data pipeline, ETL, stream, Kafka, Spark, data lake, warehouse, analytics, batch |
   | SRE | reliability, SLO, SLI, observability, incident, alert, chaos, toil, on-call |

   These are the **internal agents**. They are always available regardless of configuration.

   ### Tier 2: External Agents (configured, richer definitions)

   If `agent_source` is set in init-options.json:

   a. Validate the path exists and is a directory. If not:
      - Output a warning: "Agent source path '{path}' not found or not a directory. Falling back to internal agents only."
      - Continue with internal agents only.

   b. Scan the directory **recursively** for markdown files (`.md`):
      - For each file, attempt to parse YAML frontmatter
      - Extract these fields from frontmatter:
        - `name` (required — skip file if missing)
        - `description` (required — skip file if missing)
        - `tools` (optional — used as capabilities/keywords)
      - Use the **parent directory name** as a division/category signal (e.g., a file in `engineering/` gets category "engineering", a file in `testing/` gets category "testing")
      - If a file cannot be parsed (no frontmatter, invalid YAML, missing required fields): skip it with a warning and continue

   c. Build the external agent catalog: a list of agents with name, description, tools/capabilities, and division.

   **Priority**: Evaluate external agents first. Use internal agents only if no external agent achieves a non-zero keyword match score.

5. **Read and parse tasks.md**:
   - Load tasks.md from FEATURE_DIR
   - Identify task lines: lines matching the pattern `- [ ] T\d+` (checkbox + task ID)
   - For each task line, extract:
     - Task ID (e.g., T001, T012)
     - Existing markers: `[P]`, `[US1]`, `[US2]`, etc.
     - Whether an `[@` annotation already exists
     - The task description text (everything after the markers)
     - The phase/section the task belongs to (from the heading structure)

6. **Determine which tasks need assignment**:
   - If REASSIGN_ALL is true: strip all existing `[@...]` annotations from all unchecked task lines — every unchecked task gets reassigned
   - If REASSIGN_ALL is false: skip any unchecked task that already has an `[@...]` annotation (preserve manual edits and previous assignments)
   - Among unchecked tasks, those without `[@...]` annotations are candidates for assignment
   - Completed tasks (`- [x]` / `- [X]`) are never modified by this command

7. **Match agents to tasks** using heuristic keyword matching:

   For each candidate task:

   a. **Extract matching signals**:
      - Keywords from the task description (split into meaningful terms)
      - Phase context from the section heading:
        - "Setup" or "Foundational" → favor infrastructure/DevOps agents
        - "User Story" phases → favor domain-appropriate agents based on task content
        - "Polish" or "Cross-Cutting" → favor QA/documentation agents
      - File paths mentioned in the task (e.g., `src/frontend/` → frontend, `tests/` → testing, `src/api/` → backend)

   b. **Score candidates** (simple keyword overlap):
      - For each available agent, count how many of the agent's specialization keywords appear in the task description + file path + phase context
      - External agents: also check the agent's `description` and `tools` fields for keyword matches
      - External agents: give a small bonus if the agent's division matches the task's domain (e.g., `engineering/` division + backend task)

   c. **Select the best match**:
      - Compute scores for external agents first
      - If any external agent has a score > 0, pick the highest-scoring external agent
      - Otherwise, compute scores for internal agents and pick the highest-scoring one
      - If no agent (external or internal) has any keyword overlap, assign `[@Unassigned]`

8. **Write annotations back to tasks.md**:
   - For each assigned task, insert the `[@Agent Name]` annotation into the task line
   - Placement: after existing markers (`[P]`, `[US1]`, etc.) and before the task description text
   - Example transformation:
     - Before: `- [ ] T012 [P] [US1] Create React component in src/components/Auth.tsx`
     - After: `- [ ] T012 [P] [US1] [@Frontend Developer] Create React component in src/components/Auth.tsx`
   - Preserve all existing formatting, checkboxes, markers, and descriptions exactly
   - Write the updated tasks.md back to disk

9. **Report results**:

   Output a summary table:

   ```text
   ## Agent Assignment Report

   **Feature**: [feature name]
   **Agent Source**: Internal only | Internal + External ({path})
   **Mode**: Fresh assignment | Reassign all

   | Agent | Tasks Assigned | Source |
   |-------|---------------|--------|
   | Frontend Developer | 5 | internal |
   | Backend Architect | 8 | external |
   | Security Engineer | 2 | internal |
   | [@Unassigned] | 1 | - |

   **Total**: X tasks | Assigned: Y | Skipped (existing): Z | Unassigned: W

   Tasks.md updated at: {absolute path}
   ```

   If any tasks were unassigned, list them with a suggestion:
   ```text
   ### Unassigned Tasks (manual assignment recommended)
   - T015: "Implement custom analytics dashboard" — no matching specialist found
   ```

   If any agent definition files were skipped during discovery, list warnings:
   ```text
   ### Discovery Warnings
   - Skipped: /path/to/file.md — missing 'name' in frontmatter
   ```

10. **Check for extension hooks**: After reporting, check if `.specify/extensions.yml` exists in the project root.
    - If it exists, read it and look for entries under the `hooks.after_assign` key
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

## Review Integration (Spec 001)

When `/speckit.review` runs after implementation, it can read the `[@Agent Name]` annotations in tasks.md to understand which agent was assigned to each task. This enables:

- **"Don't review your own work"**: If `[@Backend Architect]` was assigned to implement a task, the review command can suggest a different agent (e.g., Security Engineer, Evidence Collector) for reviewing that task's output.
- **Review pass matching**: The security review pass can reference whether a security specialist was assigned to security-related tasks.

The `@` annotations are informational hints — the review command works identically with or without them. Agent assignment is purely additive.

## Agent Annotation Convention

The `[@Agent Name]` format is the standard convention for agent role annotations in tasks.md:

- **Prefix**: `[@` distinguishes agent annotations from other markers (`[P]`, `[US1]`)
- **Closing**: `]` closes the annotation
- **Content**: The agent's display name exactly as discovered (e.g., `Frontend Developer`, `Backend Architect`)
- **Platform-neutral**: The annotation is a role name, not tied to any specific AI harness. Any harness can interpret it.
- **Manual override**: Users can edit `[@...]` annotations directly in tasks.md. Re-running `/speckit.assign` without `--reassign-all` preserves manual edits.
- **Special value**: `[@Unassigned]` indicates no matching agent was found. The user should manually assign these tasks.

## Quick Reference

```bash
# Assign agents to tasks (zero-config, uses harness built-in agents)
/speckit.assign

# Assign agents using an external agent library
# First: add "agent_source": "/path/to/agents" to .specify/init-options.json
/speckit.assign

# Reassign all tasks from scratch (clears existing annotations)
/speckit.assign --reassign-all

# Assign with specific context
/speckit.assign focus on security-heavy assignments for this feature
```
