import os
import pathlib
import stat
import subprocess
import tempfile
import textwrap
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".github" / "scripts" / "backfill-labels.sh"


class BackfillLabelsScriptTests(unittest.TestCase):
    def test_feature_support_issue_is_classified_as_enhancement(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            fake_gh = tmp_path / "gh"
            summary_file = tmp_path / "summary.md"

            fake_gh.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    import sys

                    args = sys.argv[1:]
                    if args[:4] == ["issue", "list", "--repo", "JuliaQUBO/example"]:
                        print(json.dumps([
                            {
                                "number": 1,
                                "title": "Feature request: add support for spin models",
                                "body": "",
                                "labels": [],
                                "url": "https://example.com/issues/1",
                            },
                            {
                                "number": 2,
                                "title": "Architecture discussion for release process",
                                "body": "",
                                "labels": [],
                                "url": "https://example.com/issues/2",
                            },
                        ]))
                    elif args[:4] == ["pr", "list", "--repo", "JuliaQUBO/example"]:
                        print(json.dumps([
                            {
                                "number": 3,
                                "title": "Document the release checklist",
                                "body": "",
                                "labels": [],
                                "url": "https://example.com/pulls/3",
                            }
                        ]))
                    elif args[:4] == ["pr", "view", "3", "--repo"]:
                        print(json.dumps({"files": [{"path": "docs/src/index.md"}]}))
                    else:
                        raise SystemExit(f"unexpected gh invocation: {args}")
                    """
                ),
                encoding="utf-8",
            )
            fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IEXEC)

            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{tmp_path}{os.pathsep}{env['PATH']}",
                    "GITHUB_REPOSITORY": "JuliaQUBO/example",
                    "DRY_RUN": "true",
                    "MAX_ITEMS": "50",
                    "GITHUB_STEP_SUMMARY": str(summary_file),
                }
            )

            result = subprocess.run(
                ["bash", str(SCRIPT)],
                cwd=REPO_ROOT,
                env=env,
                check=True,
                text=True,
                capture_output=True,
            )

            self.assertIn("DRY-RUN add label 'enhancement' to #1", result.stdout)
            self.assertNotIn("DRY-RUN add label 'question' to #1", result.stdout)
            self.assertIn("DRY-RUN add label 'documentation' to #3", result.stdout)

            summary = summary_file.read_text(encoding="utf-8")
            self.assertIn("- issue [#2](https://example.com/issues/2): consider needs-design", summary)
            self.assertIn("- PR [#3](https://example.com/pulls/3): review for release:*", summary)

    def test_doc_path_helper_accepts_shared_template_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            fake_gh = tmp_path / "gh"

            fake_gh.write_text(
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import json
                    import sys

                    args = sys.argv[1:]
                    if args[:4] == ["issue", "list", "--repo", "JuliaQUBO/example"]:
                        print("[]")
                    elif args[:4] == ["pr", "list", "--repo", "JuliaQUBO/example"]:
                        print(json.dumps([
                            {
                                "number": 7,
                                "title": "Refresh issue forms",
                                "body": "",
                                "labels": [],
                                "url": "https://example.com/pulls/7",
                            }
                        ]))
                    elif args[:4] == ["pr", "view", "7", "--repo"]:
                        print(json.dumps({"files": [{"path": ".github/ISSUE_TEMPLATE/bug-report.yml"}]}))
                    else:
                        raise SystemExit(f"unexpected gh invocation: {args}")
                    """
                ),
                encoding="utf-8",
            )
            fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IEXEC)

            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{tmp_path}{os.pathsep}{env['PATH']}",
                    "GITHUB_REPOSITORY": "JuliaQUBO/example",
                    "DRY_RUN": "true",
                    "MAX_ITEMS": "50",
                }
            )

            result = subprocess.run(
                ["bash", str(SCRIPT)],
                cwd=REPO_ROOT,
                env=env,
                check=True,
                text=True,
                capture_output=True,
            )

            self.assertIn("DRY-RUN add label 'documentation' to #7", result.stdout)


if __name__ == "__main__":
    unittest.main()
