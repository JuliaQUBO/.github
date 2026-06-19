import json
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SYNC_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sync-labels.yml"
BACKFILL_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "backfill-labels.yml"
WORKFLOW_TEMPLATES = REPO_ROOT / ".github" / "workflow-templates"


class WorkflowContractTests(unittest.TestCase):
    def test_sync_workflow_uses_pinned_shared_ref_and_minimal_permissions(self) -> None:
        content = SYNC_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("name: Derive shared automation ref", content)
        self.assertIn("ref: ${{ steps.workflow_ref.outputs.ref }}", content)
        self.assertNotIn("ref: main", content)
        self.assertIn("issues: write", content)
        self.assertNotIn("pull-requests: write", content)
        self.assertNotIn("description: Repository to sync.", content)

    def test_backfill_workflow_uses_pinned_shared_ref_and_read_only_pr_scope(self) -> None:
        content = BACKFILL_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("name: Derive shared automation ref", content)
        self.assertIn("ref: ${{ steps.workflow_ref.outputs.ref }}", content)
        self.assertNotIn("ref: main", content)
        self.assertIn("issues: write", content)
        self.assertIn("pull-requests: read", content)
        self.assertNotIn("pull-requests: write", content)
        self.assertNotIn("description: Repository to backfill.", content)

    def test_tagbot_templates_declare_required_permissions(self) -> None:
        for name in ("tagbot.yml", "tagbot-ssh.yml"):
            with self.subTest(name=name):
                content = (WORKFLOW_TEMPLATES / name).read_text(encoding="utf-8")
                self.assertIn("contents: write", content)
                self.assertIn("issues: write", content)
                self.assertIn("pull-requests: read", content)
                self.assertIn("token: ${{ secrets.GITHUB_TOKEN }}", content)

    def test_only_ssh_tagbot_template_uses_deploy_key(self) -> None:
        token_only = (WORKFLOW_TEMPLATES / "tagbot.yml").read_text(encoding="utf-8")
        with_ssh = (WORKFLOW_TEMPLATES / "tagbot-ssh.yml").read_text(encoding="utf-8")

        self.assertNotIn("ssh:", token_only)
        self.assertIn("ssh: ${{ secrets.SSH_KEY }}", with_ssh)

    def test_tagbot_template_metadata_is_complete(self) -> None:
        for name in ("tagbot", "tagbot-ssh"):
            with self.subTest(name=name):
                metadata_path = WORKFLOW_TEMPLATES / f"{name}.properties.json"
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                self.assertEqual(metadata["iconName"], "tagbot")
                self.assertIn("Automation", metadata["categories"])
                self.assertIn("Project.toml", metadata["filePatterns"])
                self.assertTrue((WORKFLOW_TEMPLATES / f"{metadata['iconName']}.svg").exists())


if __name__ == "__main__":
    unittest.main()
