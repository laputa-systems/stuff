import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
repro = runpy.run_path(str(ROOT / "bin/repro-engine-s3"))


class ReproductionTests(unittest.TestCase):
    def test_remote_context_is_rejected_before_any_mutation(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            output = Path(directory) / "result"
            with patch("sys.argv", ["repro", "--context", "remote", "--output", str(output)]), patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, "ssh://lisa\n", "")) as run:
                with self.assertRaises(SystemExit) as error:
                    repro["main"]()
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(run.call_count, 1)
            self.assertFalse(output.exists())

    def test_startup_failure_removes_owned_resources_and_credentials(self):
        calls = []
        def docker(command, **_options):
            args = command[3:]
            calls.append(args)
            if args[0] == "context":
                return subprocess.CompletedProcess(command, 0, "unix:///local.sock\n", "")
            if args[0] == "run":
                self.assertNotIn("--publish", args)
                self.assertIn("--read-only", args)
                self.assertIn("no-new-privileges", args)
                if "--env-file" in args:
                    env = Path(args[args.index("--env-file") + 1])
                    self.assertEqual(env.stat().st_mode & 0o777, 0o600)
                    raise subprocess.CalledProcessError(1, command, stderr="startup failed")
            return subprocess.CompletedProcess(command, 0, "", "")
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            output = Path(directory) / "result"
            with patch("sys.argv", ["repro", "--context", "local", "--output", str(output)]), patch("subprocess.run", side_effect=docker):
                with self.assertRaises(subprocess.CalledProcessError):
                    repro["main"]()
            self.assertEqual(output.stat().st_mode & 0o777, 0o700)
            self.assertFalse(list(output.glob("credentials-*")))
            self.assertEqual(sum(args[:2] == ["rm", "-f"] for args in calls), 2)
            self.assertEqual(sum(args[:2] == ["network", "rm"] for args in calls), 1)
            self.assertTrue(all(path.stat().st_mode & 0o777 == 0o600 for path in output.glob("*.log")))


if __name__ == "__main__":
    unittest.main()
