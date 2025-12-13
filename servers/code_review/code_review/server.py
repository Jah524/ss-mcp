from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP
from openai import OpenAI

# --- logging (IMPORTANT: never print to stdout on stdio servers) ---
logger = logging.getLogger("review-mcp")
handler = logging.StreamHandler()  # stderr
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

mcp = FastMCP("review-mcp")

# --- config ---
# e.g. REVIEW_ALLOWED_ROOTS="/home/me/src:/home/me/work"
ALLOWED_ROOTS = [
    Path(p).expanduser().resolve()
    for p in os.getenv("REVIEW_ALLOWED_ROOTS", "").split(os.pathsep)
    if p.strip()
]
MAX_DIFF_CHARS = int(os.getenv("REVIEW_MAX_DIFF_CHARS", "120000"))
MAX_CTX_BYTES = int(os.getenv("REVIEW_MAX_CTX_BYTES", "160000"))  # total file bytes
MAX_FILES = int(os.getenv("REVIEW_MAX_FILES", "30"))
DEFAULT_MODEL = os.getenv("OPENAI_REVIEW_MODEL", "gpt-4o-2024-08-06")


def _sh(cwd: Path, *args: str) -> str:
    p = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"command failed: {' '.join(args)}")
    return p.stdout


def _resolve_repo_root(repo_root: str) -> Path:
    root = Path(repo_root).expanduser().resolve()

    if not root.exists() or not root.is_dir():
        raise ValueError(f"repo_root not found: {root}")

    # allowlist gate (recommended when sharing server across projects)
    if ALLOWED_ROOTS:
        ok = any(str(root).startswith(str(ar) + os.sep) or root == ar for ar in ALLOWED_ROOTS)
        if not ok:
            raise PermissionError(
                f"repo_root is not under REVIEW_ALLOWED_ROOTS: {root}"
            )

    # must be a git repo
    _ = _sh(root, "git", "rev-parse", "--show-toplevel")
    return root


def _changed_files_from_unified_diff(diff: str) -> list[str]:
    # +++ b/path
    files: list[str] = []
    for m in re.finditer(r"^\+\+\+\s+b/(.+)$", diff, re.MULTILINE):
        path = m.group(1).strip()
        if path != "/dev/null":
            files.append(path)
    # dedupe, keep stable order
    out: list[str] = []
    seen = set()
    for f in files:
        if f not in seen:
            out.append(f)
            seen.add(f)
    return out[:MAX_FILES]


def _read_worktree_files(repo: Path, relpaths: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    used = 0
    for rp in relpaths:
        p = (repo / rp).resolve()
        # safety: stay within repo
        if not str(p).startswith(str(repo) + os.sep):
            continue
        if not p.is_file():
            continue
        b = p.read_bytes()
        if used + len(b) > MAX_CTX_BYTES:
            break
        out[rp] = b.decode("utf-8", errors="replace")
        used += len(b)
    return out


REVIEW_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "nit"],
                    },
                    "file": {"type": ["string", "null"]},
                    "line": {"type": ["integer", "null"]},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "patch": {
                        "type": ["string", "null"],
                        "description": "If possible, propose a unified diff patch.",
                    },
                },
                "required": ["severity", "file", "line", "title", "detail", "patch"],
            },
        },
    },
    "required": ["summary", "issues"],
}


def _call_openai_review(model: str, focus: str, diff: str, context: dict[str, str]) -> dict:
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict senior code reviewer. "
                    "Return ONLY valid JSON matching this schema: "
                    f"{json.dumps(REVIEW_JSON_SCHEMA)}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Focus: {focus}\n\n"
                    f"=== DIFF (unified) ===\n{diff}\n\n"
                    f"=== CONTEXT FILES (json map: path -> content) ===\n"
                    f"{json.dumps(context, ensure_ascii=False)}"
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


@mcp.tool()
def review_git_diff(
    repo_root: str,
    diff_source: Literal["staged", "working", "branch"] = "staged",
    base_ref: Optional[str] = None,
    head_ref: Optional[str] = None,
    focus: str = "bugs, edge cases, security, performance, readability",
    model: str = DEFAULT_MODEL,
    include_context_files: bool = True,
) -> dict:
    """
    Review git diff for a repo (staged / working / between refs).
    - repo_root: absolute/relative path to the target repo root (explicit on purpose)
    - diff_source:
        - staged: git diff --staged
        - working: git diff
        - branch:  git diff <base_ref>...<head_ref>
    """
    repo = _resolve_repo_root(repo_root)

    if diff_source == "staged":
        diff = _sh(repo, "git", "diff", "--staged")
    elif diff_source == "working":
        diff = _sh(repo, "git", "diff")
    else:
        if not base_ref or not head_ref:
            raise ValueError("branch diff requires base_ref and head_ref")
        diff = _sh(repo, "git", "diff", f"{base_ref}...{head_ref}")

    diff = diff.strip()
    if not diff:
        return {"summary": "No changes.", "issues": []}

    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n... (diff truncated)"

    ctx: dict[str, str] = {}
    if include_context_files:
        files = _changed_files_from_unified_diff(diff)
        ctx = _read_worktree_files(repo, files)

    return _call_openai_review(model=model, focus=focus, diff=diff, context=ctx)


@mcp.tool()
def repo_info(repo_root: str) -> dict:
    """Quick sanity tool: returns repo toplevel, branch, and remotes."""
    repo = _resolve_repo_root(repo_root)
    top = _sh(repo, "git", "rev-parse", "--show-toplevel").strip()
    br = _sh(repo, "git", "rev-parse", "--abbrev-ref", "HEAD").strip()
    remotes = _sh(repo, "git", "remote", "-v").strip()
    return {"toplevel": top, "branch": br, "remotes": remotes}


def main() -> None:
    # Official pattern: run stdio transport. :contentReference[oaicite:3]{index=3}
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
