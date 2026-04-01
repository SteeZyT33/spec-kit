#!/usr/bin/env bash
set -euo pipefail

# Cross-harness review launcher.
# Detects tmux and splits pane if available. Otherwise runs in foreground.
# Delegates to crossreview-backend.py for actual CLI invocation.

usage() {
  echo "Usage: crossreview.sh --harness <codex|claude|gemini> --output <path> --prompt-file <path> --patch-file <path> --schema-file <path> [--model <model>] [--effort <effort>]"
  exit 1
}

HARNESS=""
MODEL=""
EFFORT="high"
OUTPUT=""
PROMPT_FILE=""
PATCH_FILE=""
SCHEMA_FILE=""
TIMEOUT="${CROSSREVIEW_TIMEOUT:-300}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --harness) HARNESS="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --effort) EFFORT="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --prompt-file) PROMPT_FILE="$2"; shift 2 ;;
    --patch-file) PATCH_FILE="$2"; shift 2 ;;
    --schema-file) SCHEMA_FILE="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

[[ -z "$HARNESS" || -z "$OUTPUT" || -z "$PROMPT_FILE" || -z "$PATCH_FILE" || -z "$SCHEMA_FILE" ]] && usage

# Verify harness CLI is installed
if ! command -v "$HARNESS" &>/dev/null; then
  echo "ERROR: $HARNESS CLI not found. Install it first."
  exit 1
fi

# Locate the backend script (relative to this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$SCRIPT_DIR/crossreview-backend.py"

if [[ ! -f "$BACKEND" ]]; then
  echo "ERROR: crossreview-backend.py not found at $BACKEND"
  exit 1
fi

# Build backend command
BACKEND_CMD="python3 '${BACKEND}' --harness '${HARNESS}' --output '${OUTPUT}' --prompt-file '${PROMPT_FILE}' --patch-file '${PATCH_FILE}' --schema-file '${SCHEMA_FILE}'"
[[ -n "$MODEL" ]] && BACKEND_CMD="${BACKEND_CMD} --model '${MODEL}'"
[[ -n "$EFFORT" ]] && BACKEND_CMD="${BACKEND_CMD} --effort '${EFFORT}'"

if [[ -n "${TMUX:-}" ]]; then
  echo "Tmux detected — splitting pane for $HARNESS review..."

  # Create a completion marker
  DONE_MARKER="${OUTPUT}.done"
  rm -f "$DONE_MARKER"

  # Split vertically, run reviewer in new pane
  tmux split-window -h -l 50% \
    "bash -c '${BACKEND_CMD} 2>&1; touch \"${DONE_MARKER}\"; echo; echo \"=== CROSS-REVIEW COMPLETE ===\"; sleep 5'"

  # Poll for completion
  ELAPSED=0
  while [[ ! -f "$DONE_MARKER" ]] && [[ $ELAPSED -lt $TIMEOUT ]]; do
    sleep 2
    ELAPSED=$((ELAPSED + 2))
  done
  rm -f "$DONE_MARKER"

  if [[ ! -f "$OUTPUT" ]]; then
    echo "ERROR: Cross-review timed out after ${TIMEOUT}s"
    exit 1
  fi
else
  echo "Running $HARNESS review in foreground..."
  eval "$BACKEND_CMD"
fi

echo "$OUTPUT"
