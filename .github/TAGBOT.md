# TagBot Workflow Policy

Use the organization workflow templates in `.github/workflow-templates/` when
adding TagBot to JuliaQUBO package repositories.

## Default Template

Use `tagbot.yml` for most Julia packages. It uses the repository
`GITHUB_TOKEN` and declares the permissions TagBot needs:

- `contents: write` to push tags and create releases.
- `issues: write` to open manual-intervention issues when release automation
  fails.
- `pull-requests: read` to read pull request metadata for changelogs.

## SSH Template

Use `tagbot-ssh.yml` only when the tag push itself must trigger downstream
workflows, such as documentation deployments. GitHub does not trigger workflows
from pushes made with `GITHUB_TOKEN`, so those repositories need TagBot's `ssh`
input.

Before using the SSH template:

- Add a repository secret named `SSH_KEY` containing the private deploy key.
- Add the matching public key as a repository deploy key with write access.
- Verify the deploy key is enabled and write-capable before the next release.

## Release Verification

After each registration, check:

- The TagBot workflow run completed successfully.
- The Git tag exists.
- The GitHub release exists and points at the registered commit.

If TagBot fails after a registration, manually create the missing annotated tag
and GitHub release, then fix the workflow or deploy key before the next release.
