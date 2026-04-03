#!/usr/bin/env bash

set -euo pipefail

python3 - <<'PY'
import json
import os
import re
import subprocess
from pathlib import PurePosixPath


SAFE_LABELS = {"bug", "documentation", "enhancement", "question"}
DOC_PATTERNS = (
    "docs/**",
    "**/*.md",
    "**/*.rst",
    "README*",
    "CHANGELOG*",
    "NEWS*",
    "CITATION.cff",
    "LICENSE*",
    "papers/**",
    ".github/ISSUE_TEMPLATE/**",
    ".github/pull_request_template.md",
)


def gh(*args: str) -> str:
    result = subprocess.run(
        ["gh", *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def has_safe_label(labels: list[dict]) -> bool:
    return any(label.get("name") in SAFE_LABELS for label in labels)


def is_doc_path(path: str) -> bool:
    candidate = PurePosixPath(path)
    return any(candidate.match(pattern) for pattern in DOC_PATTERNS)


def classify_issue_text(text: str) -> str:
    lowered = text.lower()
    if re.search(r"(docs?|documentation|readme|badge|logo|citation|example|tutorial|typo)", lowered):
        return "documentation"
    if re.search(r"(\?|how\s+can|can\s+i|would\s+like\s+to\s+know|question|support|help)", lowered):
        return "question"
    if re.search(r"(bug|broken|error|fails?|failing|doesn.t\s+work|incorrect|regression|crash|exception|traceback)", lowered):
        return "bug"
    if re.search(r"(feature|enhancement|implement|support\s+for|proposal|idea|would\s+like|should\s+be|request)", lowered):
        return "enhancement"
    return ""


def manual_reason(kind: str, text: str, labeled: bool) -> str:
    lowered = text.lower()
    reason = ""

    if re.search(r"(rfc|design|architecture|discussion)", lowered):
        reason = "consider needs-design"

    if kind == "pr":
        return f"{reason}; review for release:*" if reason else "review for release:*"

    if not reason and not labeled:
        return "needs human topical triage"

    return reason


def apply_label(target_repository: str, number: int, label: str, dry_run: bool) -> None:
    if dry_run:
        print(f"DRY-RUN add label '{label}' to #{number}")
        return

    gh(
        "api",
        "--method",
        "POST",
        f"repos/{target_repository}/issues/{number}/labels",
        "-f",
        f"labels[]={label}",
    )


def classify_pr_docs_only(target_repository: str, number: int) -> str:
    pr_view = json.loads(gh("pr", "view", str(number), "--repo", target_repository, "--json", "files"))
    files = pr_view.get("files", [])
    if not files:
        return ""

    paths = [(entry.get("path") or entry.get("filename") or "") for entry in files]
    return "documentation" if all(path and is_doc_path(path) for path in paths) else ""


target_repository = os.environ.get("INPUT_REPOSITORY") or os.environ.get("GITHUB_REPOSITORY")
if not target_repository:
    raise SystemExit("INPUT_REPOSITORY or GITHUB_REPOSITORY is required")

dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"
max_items = int(os.environ.get("MAX_ITEMS", "100"))

issues = json.loads(
    gh(
        "issue",
        "list",
        "--repo",
        target_repository,
        "--state",
        "open",
        "--limit",
        str(max_items),
        "--json",
        "number,title,body,labels,url",
    )
)
prs = json.loads(
    gh(
        "pr",
        "list",
        "--repo",
        target_repository,
        "--state",
        "open",
        "--limit",
        str(max_items),
        "--json",
        "number,title,body,labels,url",
    )
)

applied_lines: list[str] = []
review_lines: list[str] = []

for issue in issues:
    text = f"{issue['title']}\n{issue.get('body') or ''}"
    labeled = False
    if not has_safe_label(issue["labels"]):
        candidate = classify_issue_text(text)
        if candidate:
            apply_label(target_repository, issue["number"], candidate, dry_run)
            applied_lines.append(f"- issue [#{issue['number']}]({issue['url']}): `{candidate}`")
            labeled = True

    reason = manual_reason("issue", text, labeled)
    if reason:
        review_lines.append(f"- issue [#{issue['number']}]({issue['url']}): {reason}")

for pr in prs:
    text = f"{pr['title']}\n{pr.get('body') or ''}"
    labeled = False
    if not has_safe_label(pr["labels"]):
        candidate = classify_pr_docs_only(target_repository, pr["number"])
        if candidate:
            apply_label(target_repository, pr["number"], candidate, dry_run)
            applied_lines.append(f"- PR [#{pr['number']}]({pr['url']}): `{candidate}`")
            labeled = True

    reason = manual_reason("pr", text, labeled)
    if reason:
        review_lines.append(f"- PR [#{pr['number']}]({pr['url']}): {reason}")

summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_path:
    with open(summary_path, "a", encoding="utf-8") as summary:
        summary.write("## Label Backfill\n\n")
        summary.write(f"- Repository: `{target_repository}`\n")
        summary.write(f"- Mode: `{'dry-run' if dry_run else 'apply'}`\n")
        summary.write(f"- Issues scanned: {len(issues)}\n")
        summary.write(f"- PRs scanned: {len(prs)}\n\n")
        summary.write("### Applied topical labels\n")
        if applied_lines:
            summary.write("\n".join(applied_lines) + "\n")
        else:
            summary.write("No safe labels were applied.\n")
        summary.write("\n### Manual review queue\n")
        if review_lines:
            summary.write("\n".join(review_lines) + "\n")
        else:
            summary.write("No manual follow-up suggestions.\n")
PY
