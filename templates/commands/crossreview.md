---
description: Invoke a cross-harness review using a different AI agent to adversarially review completed work
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
handoffs:
  - label: Run Standard Review
    agent: speckit.review
    prompt: Run the standard review passes on the current phase
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Parse arguments** from user input:
   - `--phase N`: Review a specific phase (default: latest completed phase from tasks.md)
   - Any remaining text: Additional review focus or instructions for the reviewer

3. **Read configuration** from `.specify/init-options.json`:
   - `review_harness` (required): The CLI harness to invoke (`codex`, `claude`, `gemini`)
   - `review_model` (optional): Model override for the review session
   - `review_effort` (optional, default: `"high"`): Reasoning effort level
   - If `review_harness` is not set, output:
     ```
     Cross-review harness not configured. Add to .specify/init-options.json:
       "review_harness": "codex",
       "review_model": "o4-mini-high",
       "review_effort": "high"
     ```
     Then stop.

4. **Verify the harness CLI is installed**: Run `command -v $REVIEW_HARNESS`. If not found:
   ```
   Harness CLI '$REVIEW_HARNESS' not found. Install it:
     codex: https://github.com/openai/codex
     claude: https://github.com/anthropics/claude-code
     gemini: https://github.com/google-gemini/gemini-cli
   ```
   Then stop.

5. **Determine the review scope**:
   - Read tasks.md to identify the target phase and its tasks
   - Read spec.md for acceptance criteria relevant to the phase
   - Read plan.md for architecture decisions
   - Run `git diff --merge-base --name-only main HEAD` to get the list of changed files
   - If no files changed, report "No changes to review against main" and stop

6. **Compute the diff** (externally — the reviewer reads a patch file, does not run git):
   ```bash
   git diff --merge-base main HEAD --no-ext-diff --unified=3 --no-color > FEATURE_DIR/.crossreview.patch
   git diff --merge-base --name-only main HEAD > FEATURE_DIR/.crossreview-files.txt
   ```

7. **Build the review prompt** — write to `FEATURE_DIR/.crossreview-prompt.md`:

   # Cross-Harness Adversarial Review

   You are reviewing work done by a DIFFERENT AI agent. Your job is to be
   adversarial — assume the implementing agent has blind spots and find them.

   ## Review Checklist
   - Spec compliance: does the implementation satisfy the acceptance criteria below?
   - Correctness: logic errors, edge cases, off-by-one, null/undefined handling
   - Security: injection, auth bypass, secrets exposure, OWASP top 10
   - Data integrity: race conditions, partial writes, missing validation at boundaries
   - Backwards compatibility: breaking changes to existing interfaces
   - Missing tests: untested paths that the spec requires

   ## Changed Files
   [insert contents of FEATURE_DIR/.crossreview-files.txt]

   ## Acceptance Criteria for Phase [N]
   [insert relevant acceptance criteria from spec.md for the target phase]

   ## Architecture Context
   [insert key decisions from plan.md — tech stack, file structure, patterns]

   ## Additional Focus
   [insert any additional text from user arguments, or "None" if empty]

   ## Instructions
   Read the patch at the end of this prompt and inspect the changed files in the
   working directory if needed. Focus on substance — ignore style unless it hides a bug.

   Return your findings as JSON with this exact structure:
   ```json
   {
     "summary": "one-paragraph summary of findings",
     "blocking": [{"file": "path", "line": 42, "issue": "description", "fix": "suggestion"}],
     "non_blocking": [{"file": "path", "line": 10, "issue": "description", "fix": "suggestion"}]
   }
   ```

   Only blocking issues should be things that MUST be fixed before merge.
   Non-blocking issues are improvements worth noting but not merge-gating.

   Fill in the bracketed sections with actual content from spec.md, plan.md, and the files list. Do not leave placeholders.

8. **Write the output schema** to `FEATURE_DIR/.crossreview.schema.json` by copying from `.specify/templates/crossreview.schema.json`.

9. **Generate timestamp**: `TIMESTAMP=$(date +%Y-%m-%dT%H-%M-%S)`

10. **Invoke the launcher script**:
    ```bash
    bash scripts/bash/crossreview.sh \
      --harness "$REVIEW_HARNESS" \
      --model "$REVIEW_MODEL" \
      --effort "$REVIEW_EFFORT" \
      --output ".shared/crossreview-${REVIEW_HARNESS}-${TIMESTAMP}.json" \
      --prompt-file "FEATURE_DIR/.crossreview-prompt.md" \
      --patch-file "FEATURE_DIR/.crossreview.patch" \
      --schema-file "FEATURE_DIR/.crossreview.schema.json"
    ```

    If in tmux, this splits the pane and the reviewer runs visually in the side pane.
    If not in tmux, this blocks until the reviewer finishes.

    Note: crossreview.sh delegates to crossreview-backend.py for the actual harness CLI invocation and JSON processing.

11. **Read the output JSON** from `.shared/crossreview-*.json`. Parse the JSON structure.

12. **Present findings** to the user:

    ```markdown
    ## Cross-Harness Review — {harness} ({model})

    **Phase**: Phase N — [phase name]
    **Reviewer**: {harness} ({model}, effort: {effort})

    ### Summary
    [summary from JSON]

    ### Blocking Issues ({count})
    | # | File | Line | Issue | Suggested Fix |
    |---|------|------|-------|---------------|
    [rows from blocking array]

    ### Non-Blocking Issues ({count})
    | # | File | Line | Issue | Suggested Fix |
    |---|------|------|-------|---------------|
    [rows from non_blocking array]
    ```

    If no blocking issues: "No blocking issues found. Cross-review passed."

13. **Append to review.md** in FEATURE_DIR under a `### Cross-Harness Review` section using the same format as step 12.

14. **If blocking issues exist**, recommend: "There are N blocking issues from the cross-harness review. Address them before merge."

15. **Check for extension hooks** (`hooks.after_crossreview`):
    - Check if `.specify/extensions.yml` exists in the project root
    - If it exists, read it and look for entries under the `hooks.after_crossreview` key
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
