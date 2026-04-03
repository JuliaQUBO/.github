import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SYNC_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sync-labels.yml"
BACKFILL_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "backfill-labels.yml"


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


if __name__ == "__main__":
    unittest.main()
