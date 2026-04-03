import json
import os
import pathlib
import stat
import subprocess
import tempfile
import textwrap
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".github" / "scripts" / "sync-labels.sh"


class SyncLabelsScriptTests(unittest.TestCase):
    def test_sync_reads_all_label_pages_before_deciding_create_vs_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            labels_file = tmp_path / "labels.json"
            gh_log = tmp_path / "gh.log"
            fake_gh = tmp_path / "gh"

            labels_file.write_text(
                json.dumps(
                    [
                        {
                            "name": "release:minor",
                            "color": "5319e7",
                            "description": "Candidate for the next minor release",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            fake_gh.write_text(
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env python3
                    import json
                    import pathlib
                    import sys

                    log_path = pathlib.Path({str(gh_log)!r})
                    log_path.write_text(log_path.read_text() + " ".join(sys.argv[1:]) + "\\n" if log_path.exists() else " ".join(sys.argv[1:]) + "\\n")

                    args = sys.argv[1:]
                    if args[:2] == ["api", "repos/JuliaQUBO/example/labels?per_page=100&page=1"]:
                        print(json.dumps([{{"name": "bug"}}] * 100))
                    elif args[:2] == ["api", "repos/JuliaQUBO/example/labels?per_page=100&page=2"]:
                        print(json.dumps([{{"name": "release:minor"}}]))
                    else:
                        raise SystemExit(f"unexpected gh invocation: {{args}}")
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
                    "LABELS_FILE": str(labels_file),
                    "DRY_RUN": "true",
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

            self.assertIn(
                "DRY-RUN update JuliaQUBO/example:release:minor",
                result.stdout,
            )
            self.assertNotIn(
                "DRY-RUN create JuliaQUBO/example:release:minor",
                result.stdout,
            )

            gh_calls = gh_log.read_text(encoding="utf-8")
            self.assertIn("repos/JuliaQUBO/example/labels?per_page=100&page=1", gh_calls)
            self.assertIn("repos/JuliaQUBO/example/labels?per_page=100&page=2", gh_calls)


if __name__ == "__main__":
    unittest.main()
