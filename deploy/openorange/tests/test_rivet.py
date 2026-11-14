import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
commands = runpy.run_path(str(ROOT / "bin/oo"))
import oolib


class RivetConfigurationTests(unittest.TestCase):
    def test_invalid_privilege_and_network_configuration_is_rejected(self):
        changes = [
            {"operators": []}, {"operators": ["user:owner", "user:owner"]},
            {"operators": ["tags:operator"]}, {"operators": "user:owner"},
            {"operators": ["user:owner\nrespond 200"]}, {"hostname": "public.example.com"},
            {"ip": "172.29.80.11"}, {"ip": "172.29.80.20"}, {"ip": "192.168.1.20"},
            {"ip": "172.29.80.0"}, {"ip": "invalid"}, {"port": 80}, {"port": True},
            {"path": "/admin"}, {"enabled": "yes"},
        ]
        for change in changes:
            with self.subTest(change=change):
                raw = copy.deepcopy(oolib.load().raw)
                raw["rivet"].update(change)
                with self.assertRaises(oolib.ConfigError):
                    oolib.validate(raw)
        raw = copy.deepcopy(oolib.load().raw)
        raw["apps"]["stats"]["public_hostnames"] = ["stats.17166969.xyz"]
        with self.assertRaises(oolib.ConfigError):
            oolib.validate(raw)

    def test_caddy_routes_only_the_private_exact_path_and_subtree(self):
        cfg = oolib.load()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            cfg.stack["etc_dir"] = directory
            image = cfg.app_image_file(cfg.apps["stats"])
            image.parent.mkdir()
            image.write_text("stats:test")
            text = commands["render_caddyfile"](cfg)
        private, public = text.split("# Public listener:", 1)
        self.assertIn("host stats.17166969.xyz", private)
        self.assertIn("path /rivet /rivet/*", private)
        self.assertIn("request_header -Rivet-Gateway-Secret", private)
        self.assertIn("header_up Rivet-Gateway-Secret {$GW_SECRET_RIVET}", private)
        self.assertNotIn("{env.GW_SECRET_", private)
        self.assertLess(private.index("forward_auth"), private.index("handle @rivet"))
        self.assertLess(private.index("handle @rivet"), private.index("reverse_proxy 172.29.80.20:8080"))
        self.assertNotIn("172.29.80.24", public)
        self.assertNotIn("rivet.17166969.xyz", text)
        for app in cfg.enabled_apps():
            for hostname in app.hostnames:
                self.assertIn(hostname, text)
        cfg = replace(cfg, rivet=None)
        self.assertNotIn("handle @rivet", commands["render_caddyfile"](cfg))

    def test_credentials_stay_in_a_protected_file_and_image_is_content_pinned(self):
        cfg = oolib.load()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            cfg.stack["etc_dir"] = directory
            with patch.object(os, "chown") as chown:
                commands["cmd_secrets"](cfg)
            file = cfg.etc / "rivet/config.json"
            settings = json.loads(file.read_text())
            self.assertEqual(settings["operators"], list(cfg.rivet.operators))
            self.assertEqual(settings["engine_token"], oolib.read_env(cfg.engine_env)["RIVET__AUTH__ADMIN_TOKEN"])
            self.assertEqual(file.stat().st_mode & 0o777, 0o440)
            self.assertEqual(file.parent.stat().st_mode & 0o777, 0o700)
            self.assertTrue(any(call.args[1:] == (0, int(oolib.UID)) for call in chown.call_args_list))
            image = "sha256:" + "a" * 64
            (cfg.etc / "rivet.image").write_text(image)
            args = oolib.run_args(cfg, "rivet")
            self.assertEqual(args[-1], image)
            self.assertIn("--read-only", args)
            self.assertIn(f"{oolib.UID}:{oolib.UID}", args)
            self.assertIn(f"{file}:/run/secrets/rivet-explorer.json:ro", args)
            self.assertNotIn("--publish", args)
            self.assertNotIn("-p", args)
            self.assertNotIn("host", args)
            self.assertNotIn("/var/run/docker.sock", " ".join(args))
            self.assertNotIn(settings["engine_token"], " ".join(args))
            self.assertNotIn(settings["gateway_secret"], " ".join(args))
            with patch.object(os, "chown"):
                commands["cmd_secrets"](cfg)
            self.assertEqual(json.loads(file.read_text())["gateway_secret"], settings["gateway_secret"])

    def test_graceful_reload_reads_new_gateway_environment_without_restarting_caddy(self):
        calls = []
        cfg = oolib.load()
        def docker(*args, **kwargs):
            calls.append(args)
            return type("Result", (), {"returncode": 0})()
        with patch.dict(commands["cmd_reload_ingress"].__globals__, {"cmd_render": lambda cfg: None}), patch.object(oolib, "docker", docker):
            commands["cmd_reload_ingress"](cfg)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(call[:4] == ("exec", "--env-file", str(cfg.etc / "ingress.env"), "oo-ingress") for call in calls))
        self.assertIn("validate", calls[0])
        self.assertIn("reload", calls[1])
        self.assertNotIn("restart", calls[1])


if __name__ == "__main__":
    unittest.main()
