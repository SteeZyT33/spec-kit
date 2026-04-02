---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
handoffs: 
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: speckit.checklist
    prompt: Create a checklist for the following domain...
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before planning)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_plan` key
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

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied).

3. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

4. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

5. **Check for extension hooks**: After reporting, check if `.specify/extensions.yml` exists in the project root.
   - If it exists, read it and look for entries under the `hooks.after_plan` key
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

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Define interface contracts** (if project has external interfaces) → `/contracts/`:
   - Identify what interfaces the project exposes to users or other systems
   - Document the contract format appropriate for the project type
   - Examples: public APIs for libraries, command schemas for CLI tools, endpoints for web services, grammars for parsers, UI contracts for applications
   - Skip if project is purely internal (build scripts, one-off tools, etc.)

3. **Agent context update**:
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: data-model.md, /contracts/*, quickstart.md, agent-specific file

### Phase 1.5: Agent Expertise Consultation (optional)

**Prerequisites:** Phase 1 complete (plan structure established). This step is optional and additive — it enriches the plan with specialist knowledge but never restructures it.

1. **Read configuration**: Check `.specify/init-options.json` for `agent_source` (or `ai_commands_dir` fallback). This determines whether external agent definitions are available.

2. **Scan spec.md for domain keywords**: Read the feature spec and check for keywords that activate specialist lenses. Use the Tier 1 activation table below:

   | Spec Keywords | Agent Lens | Tasks to Consider Adding |
   |---------------|-----------|--------------------------|
   | authentication, OAuth, login, session, token, password, RBAC, permissions | Security Engineer | Threat model for auth flows, validate auth boundaries at system edges, verify token lifecycle (creation, refresh, revocation), check for credential exposure |
   | migration, schema change, data transfer, ETL, import, export | Data Engineer | Create rollback strategy, validate data integrity post-migration, test with representative data volume, document migration runbook |
   | frontend, UI, component, page, form, layout, responsive | Frontend Developer | Accessibility audit (WCAG), responsive breakpoint testing, component isolation verification, loading state coverage |
   | CI/CD, deployment, pipeline, infrastructure, Docker, Kubernetes | DevOps Automator | Deployment rollback plan, environment parity check, configuration validation, secret rotation verification |
   | test, coverage, quality, validation, verification | Evidence Collector | Coverage threshold tasks, edge case identification from spec scenarios, regression test for existing behavior |
   | database, SQL, query, index, schema, ORM | Database Optimizer | Index strategy for new queries, migration performance test, query plan analysis for complex joins |

   For each matching lens, append a **Specialist Considerations** subsection to the plan:

   ```markdown
   ### Specialist Considerations

   The following tasks were identified by consulting agent expertise lenses activated by spec keywords:

   **[Agent Name] lens** (triggered by: [matched keywords]):
   - [Specific task recommendation based on the spec content]
   - [Another task recommendation]
   ```

   Only add tasks that are genuinely relevant to THIS spec's content. Do not add generic checklists — each recommendation must reference a specific aspect of the feature.

3. **External agent catalog** (if `agent_source` is configured):
   - Scan the external agent directory for markdown files with YAML frontmatter
   - For each external agent, check if its `description` or `tools` fields contain keywords that match spec.md content
   - If matches are found, add specialist considerations from those agents as well
   - External agents supplement (don't replace) the Tier 1 lens table

4. **Guard clause**: If no agent catalog is configured AND no spec keywords match any Tier 1 lens, skip this step entirely with no output. The plan proceeds as before — agent expertise is additive, never required.

**Output**: Specialist Considerations section appended to plan.md (if any lenses activated)

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications
