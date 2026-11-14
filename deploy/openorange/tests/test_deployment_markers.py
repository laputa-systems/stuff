import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import deployments
import oolib


class MarkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.temp.cleanup)
        self.cfg = oolib.load()
        self.cfg.stack["etc_dir"] = self.temp.name + "/etc"
        self.cfg.stack["state_dir"] = self.temp.name + "/state"
        app = self.cfg.apps["stats"]
        self.path = self.cfg.app_image_file(app)
        self.path.parent.mkdir(parents=True)
        oolib.set_app_deployment(self.path, "stats:abc")
        self.host = "h_" + "1" * 32
        self.payloads = []

    def docker(self, *args, **kwargs):
        if args[0] == "image":
            return SimpleNamespace(stdout=json.dumps([{"Id": "sha256:abc"}]))
        return SimpleNamespace(stdout=json.dumps([{"Image": "sha256:abc", "Config": {"Image": "stats:abc", "Env": ["RIVET_NODE_VERSION=1"]}, "State": {"Running": True, "StartedAt": "2026-11-14T12:00:00.123456789Z"}}]))

    def record(self, expected="stats:abc"):
        with patch.object(deployments, "credential", return_value=("secret", [self.host])), patch.object(oolib, "docker", side_effect=self.docker):
            deployments.record(self.cfg, "stats", expected, lambda *args: True)

    def test_success_and_ambiguous_retry_preserve_body(self):
        def fail(cfg, name, token, body):
            self.payloads.append(body)
            raise oolib.ConfigError("failed")
        with patch.object(deployments, "send", side_effect=fail), self.assertRaises(oolib.ConfigError):
            self.record()
        directory = self.cfg.state / "deployments/stats"
        files = list(directory.glob("*.json"))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].stat().st_mode & 0o777, 0o600)
        self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
        marker = json.loads(files[0].read_bytes())
        self.assertEqual(marker, {"markerId": "oo-stats-1", "version": "stats-abc", "hostIds": [self.host], "atMs": 1794657600123})
        with patch.object(deployments, "credential", return_value=("secret", [self.host])), patch.object(deployments, "send", side_effect=lambda cfg, name, token, body: self.payloads.append(body)):
            deployments.sync(self.cfg, "stats")
        self.assertEqual(self.payloads[0], self.payloads[1])
        self.assertFalse(files[0].exists())
        self.assertEqual((directory / "delivered" / files[0].name).read_bytes(), self.payloads[0])

    def test_record_after_restart_keeps_original_activation_and_does_not_resend(self):
        with patch.object(deployments, "send", side_effect=lambda cfg, name, token, body: self.payloads.append(body)):
            self.record()
            original = self.docker
            def restarted(*args, **kwargs):
                result = original(*args, **kwargs)
                result.stdout = result.stdout.replace("12:00:00", "13:00:00")
                return result
            self.docker = restarted
            self.record()
        self.assertEqual(len(self.payloads), 1)

    def test_pending_activation_survives_restart_without_changing_retry_bytes(self):
        with patch.object(deployments, "send", side_effect=oolib.ConfigError("lost response")), self.assertRaises(oolib.ConfigError):
            self.record()
        directory = self.cfg.state / "deployments/stats"
        original_body = next(directory.glob("*.json")).read_bytes()
        original = self.docker
        def restarted(*args, **kwargs):
            result = original(*args, **kwargs)
            result.stdout = result.stdout.replace("12:00:00", "13:00:00")
            return result
        self.docker = restarted
        with patch.object(deployments, "send", side_effect=lambda cfg, name, token, body: self.payloads.append(body)):
            self.record()
        self.assertEqual(self.payloads, [original_body])

    def test_backup_preserves_pending_and_delivered_markers_without_sending(self):
        with patch.object(deployments, "send", side_effect=lambda cfg, name, token, body: self.payloads.append(body)):
            self.record()
        directory = self.cfg.state / "deployments/stats"
        pending = directory / "oo-stats-2.json"
        pending.write_bytes(b'{"markerId":"oo-stats-2"}')
        pending.chmod(0o600)
        backup = Path(self.temp.name) / "backup"
        backup.mkdir(mode=0o700)
        with patch.object(deployments, "send", side_effect=AssertionError("backups must never send markers")):
            deployments.snapshot(self.cfg, backup)
        restored = backup / "deployments/stats"
        self.assertEqual((restored / pending.name).read_bytes(), pending.read_bytes())
        self.assertEqual((restored / "delivered/oo-stats-1.json").read_bytes(), self.payloads[0])
        self.assertEqual((backup / "deployments").stat().st_mode & 0o777, 0o700)
        self.assertEqual((restored / pending.name).stat().st_mode & 0o777, 0o600)
        self.assertFalse((restored / ".lock").exists())

    def test_selection_and_running_mismatches_refused(self):
        with self.assertRaises(oolib.ConfigError):
            self.record("stats:wrong")
        original = self.docker
        def wrong(*args, **kwargs):
            result = original(*args, **kwargs)
            if args[0] != "image":
                doc = json.loads(result.stdout)
                doc[0]["Config"]["Env"] = ["RIVET_NODE_VERSION=2"]
                result.stdout = json.dumps(doc)
            return result
        self.docker = wrong
        with self.assertRaises(oolib.ConfigError):
            self.record()
        self.assertFalse(list((self.cfg.state / "deployments/stats").glob("*.json")))

    def test_rollback_has_distinct_marker(self):
        oolib.set_app_deployment(self.path, "stats:other")
        oolib.set_app_deployment(self.path, "stats:abc")
        original = self.docker
        def rollback(*args, **kwargs):
            result = original(*args, **kwargs)
            if args[0] != "image":
                result.stdout = result.stdout.replace("VERSION=1", "VERSION=3")
            return result
        self.docker = rollback
        with patch.object(deployments, "send", side_effect=lambda cfg, name, token, body: self.payloads.append(body)):
            self.record()
        self.assertEqual(json.loads(self.payloads[0])["markerId"], "oo-stats-3")

    def test_http_accepts_only_success_and_does_not_follow_redirect(self):
        class Response:
            status = 201
            def read(self, size):
                return b""
        class Connection:
            def __init__(self, host, port, timeout):
                self.response = Response()
            def request(self, method, path, body, headers):
                self.requested = (method, path, body, headers)
            def getresponse(self):
                return self.response
            def close(self):
                pass
        with patch.object(deployments.http.client, "HTTPConnection", Connection):
            deployments.send(self.cfg, "stats", "secret", b"{}")
            Response.status = 302
            with self.assertRaises(oolib.ConfigError) as error:
                deployments.send(self.cfg, "stats", "secret", b"{}")
            self.assertNotIn("secret", str(error.exception))

    def test_credential_rejects_insecure_or_missing_without_disclosing_token(self):
        directory = self.cfg.etc / "deploy-markers"
        directory.mkdir()
        path = directory / "stats.json"
        path.write_text(json.dumps({"name": "stats", "deployToken": "secret-token", "hostIds": [self.host]}))
        path.chmod(0o644)
        with self.assertRaises(oolib.ConfigError) as error:
            deployments.credential(self.cfg, "stats")
        self.assertNotIn("secret-token", str(error.exception))
        path.unlink()
        with self.assertRaises(oolib.ConfigError):
            deployments.credential(self.cfg, "stats")


if __name__ == "__main__":
    unittest.main()
