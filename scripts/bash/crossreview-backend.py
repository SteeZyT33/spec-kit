#!/usr/bin/env python3
"""Cross-harness review backend.

Invokes a configured AI harness CLI to review a patch file.
Returns structured JSON with summary, blocking, and non_blocking findings.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cross-harness review backend")
    p.add_argument("--harness", required=True, choices=["codex", "claude", "gemini"])
    p.add_argument("--model", default=None)
    p.add_argument("--effort", default="high")
    p.add_argument("--patch-file", required=True, type=Path)
    p.add_argument("--prompt-file", required=True, type=Path)
    p.add_argument("--schema-file", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def invoke_codex(args: argparse.Namespace, prompt: str) -> str:
    cmd = [
        "codex", "exec",
        "--sandbox", "read-only",
        "--ask-for-approval", "never",
    ]
    if args.model:
        cmd += ["-c", f"model={args.model}"]
    if args.effort:
        cmd += ["-c", f"model_reasoning_effort={args.effort}"]
    cmd += ["--output-schema", str(args.schema_file)]
    cmd.append(prompt)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        sys.stderr.write(f"codex stderr: {result.stderr}\n")
    return result.stdout


def invoke_claude(args: argparse.Namespace, prompt: str) -> str:
    cmd = [
        "claude", "-p",
        "--allowedTools", "Read,Grep,Glob,Bash",
    ]
    if args.model:
        cmd += ["--model", args.model]
    if args.effort:
        cmd += ["--effort", args.effort]
    cmd.append(prompt)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        sys.stderr.write(f"claude stderr: {result.stderr}\n")
    return result.stdout


def invoke_gemini(args: argparse.Namespace, prompt: str) -> str:
    cmd = ["gemini", "--sandbox", "-p"]
    if args.model:
        cmd += ["-m", args.model]
    cmd += ["--output-format", "json"]
    cmd.append(prompt)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        sys.stderr.write(f"gemini stderr: {result.stderr}\n")
    out = result.stdout
    try:
        payload = json.loads(out)
        return payload.get("response", out)
    except json.JSONDecodeError:
        return out


def extract_json(raw: str) -> dict:
    """Extract JSON from raw output, handling markdown fences and preamble."""
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fence
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Fallback: wrap raw output in a valid structure
    return {
        "summary": "Review completed but output was not structured JSON. Raw output preserved below.",
        "blocking": [],
        "non_blocking": [{"file": "\u2014", "issue": raw[:2000]}],
    }


def main() -> None:
    args = parse_args()

    prompt = args.prompt_file.read_text(encoding="utf-8")
    patch = args.patch_file.read_text(encoding="utf-8")

    full_prompt = f"{prompt}\n\n## Patch to Review\n\n```diff\n{patch}\n```"

    harness_fn = {
        "codex": invoke_codex,
        "claude": invoke_claude,
        "gemini": invoke_gemini,
    }[args.harness]

    sys.stderr.write(f"Invoking {args.harness}")
    if args.model:
        sys.stderr.write(f" ({args.model})")
    sys.stderr.write("...\n")

    try:
        raw_result = harness_fn(args, full_prompt)
    except subprocess.TimeoutExpired:
        raw_result = json.dumps({
            "summary": "Review timed out after 300s",
            "blocking": [],
            "non_blocking": [],
        })
    except FileNotFoundError:
        raw_result = json.dumps({
            "summary": f"Harness CLI '{args.harness}' not found. Is it installed?",
            "blocking": [],
            "non_blocking": [],
        })

    parsed = extract_json(raw_result)
    output_json = json.dumps(parsed, indent=2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_json, encoding="utf-8")
    print(output_json)


if __name__ == "__main__":
    main()
