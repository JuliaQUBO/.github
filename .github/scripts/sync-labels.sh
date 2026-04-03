#!/usr/bin/env bash

set -euo pipefail

python3 - <<'PY'
import json
import os
import subprocess
import urllib.parse


def gh(*args: str) -> str:
    result = subprocess.run(
        ["gh", *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


target_repository = os.environ.get("INPUT_REPOSITORY") or os.environ.get("GITHUB_REPOSITORY")
if not target_repository:
    raise SystemExit("INPUT_REPOSITORY or GITHUB_REPOSITORY is required")

labels_file = os.environ.get("LABELS_FILE", ".github/labels/shared-labels.json")
dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

with open(labels_file, "r", encoding="utf-8") as fh:
    label_definitions = json.load(fh)

existing_labels = json.loads(gh("api", f"repos/{target_repository}/labels?per_page=100"))
existing_by_name = {label["name"]: label for label in existing_labels}

created = 0
updated = 0

for label in label_definitions:
    name = label["name"]
    color = label["color"].lstrip("#")
    description = label["description"]

    if name in existing_by_name:
        if dry_run:
            print(f"DRY-RUN update {target_repository}:{name}")
        else:
            gh(
                "api",
                "--method",
                "PATCH",
                f"repos/{target_repository}/labels/{urllib.parse.quote(name, safe='')}",
                "--raw-field",
                f"new_name={name}",
                "--raw-field",
                f"color={color}",
                "--raw-field",
                f"description={description}",
            )
        updated += 1
    else:
        if dry_run:
            print(f"DRY-RUN create {target_repository}:{name}")
        else:
            gh(
                "api",
                "--method",
                "POST",
                f"repos/{target_repository}/labels",
                "--raw-field",
                f"name={name}",
                "--raw-field",
                f"color={color}",
                "--raw-field",
                f"description={description}",
            )
        created += 1

summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_path:
    with open(summary_path, "a", encoding="utf-8") as summary:
        summary.write("## Label Sync\n\n")
        summary.write(f"- Repository: `{target_repository}`\n")
        summary.write(f"- Mode: `{'dry-run' if dry_run else 'apply'}`\n")
        summary.write(f"- Definitions file: `{labels_file}`\n")
        summary.write(f"- Labels processed: {len(label_definitions)}\n")
        summary.write(f"- Created: {created}\n")
        summary.write(f"- Updated: {updated}\n")
PY
