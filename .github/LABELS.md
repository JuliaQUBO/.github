# Shared Labels

This repository defines the shared labeling contract for the JuliaQUBO package
repositories.

## Shared Topical Labels

- `bug`: Something is broken or behaving incorrectly.
- `documentation`: Documentation, examples, badges, citation metadata, or docs
  site changes.
- `enhancement`: A new capability or non-bug improvement.
- `question`: A usage or support question.

## Shared Manual Labels

These labels are intentionally human-maintained and are not auto-applied by the
labeling workflows:

- `release:blocker`: Must be resolved before the next release.
- `release:patch`: Candidate for the next patch release.
- `release:minor`: Candidate for the next minor release.
- `needs-design`: Requires design or architecture discussion before work should
  proceed.
- `defer`: Intentionally deferred from the current release cycle.

## Automation Policy

- Issue forms apply the obvious topical label at creation time.
- PR automation applies `documentation` only when every changed file is
  documentation-like.
- Backfill automation only applies safe topical labels and prints a manual
  review queue for `release:*`, `needs-design`, and `defer`.
- Repo-specific labels remain allowed and are not modified by shared automation.
