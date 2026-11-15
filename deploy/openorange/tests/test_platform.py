import copy
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
commands = runpy.run_path(str(ROOT / "bin/oo"))
import oolib


def enabled():
    raw = copy.deepcopy(oolib.load().raw)
    raw["platform_bridge"]["enabled"] = True
    return oolib.validate(raw)


def selectors():
    return [{"role": "installation", "name": "installation-1234abcd", "key": "1" * 64},
            {"role": "observation", "name": "observation-store-1234abcd", "key": "2" * 64}]


class PlatformBridgeTests(unittest.TestCase):
    def test_disabled_is_optional_and_bad_active_configuration_is_rejected(self):
        self.assertIsNone(oolib.load().platform_bridge)
        for change in ({"source_app": "stuff"}, {"ip": "172.29.80.20"}, {"ip": "172.29.80.24"}, {"ip": "0.0.0.0"}, {"ip": "172.29.80.0"}, {"port": True}, {"port": 80}, {"sample_ppm": 0}, {"sample_ppm": 1000001}, {"native_version": "unsafe\nversion"}, {"hostname": "platform.example.com"}):
            with self.subTest(change=change):
                raw = copy.deepcopy(enabled().raw)
                raw["platform_bridge"].update(change)
                with self.assertRaises(oolib.ConfigError):
                    oolib.validate(raw)
        raw = copy.deepcopy(oolib.load().raw)
        raw["platform_bridge"] = {"enabled": False}
        self.assertIsNone(oolib.validate(raw).platform_bridge)

    def test_credentials_are_stable_protected_and_scoped_to_stats(self):
        cfg = enabled()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            cfg.stack["etc_dir"] = directory
            with patch.object(os, "chown"), redirect_stdout(io.StringIO()) as output:
                commands["cmd_secrets"](cfg)
            bridge = oolib.read_env(cfg.etc / "platform.env")
            stats = oolib.read_env(cfg.app_env(cfg.apps["stats"]))
            self.assertRegex(bridge["STATS_INGEST_TOKEN"], r"^nft_[A-Za-z0-9_-]{43}$")
            self.assertEqual(stats["PLATFORM_BRIDGE_TOKEN_SHA256"], hashlib.sha256(bridge["STATS_INGEST_TOKEN"].encode()).hexdigest())
            self.assertIn("PLATFORM_BRIDGE_TOKEN_SHA256", stats["ORANGE_WORKER_SECRETS"].split(","))
            self.assertNotIn("OTEL_EXPORTER_OTLP_HEADERS", stats["ORANGE_WORKER_SECRETS"].split(","))
            self.assertEqual(stats["OTEL_EXPORTER_OTLP_HEADERS"], "Authorization=Bearer " + bridge["PLATFORM_OTLP_TOKEN"])
            self.assertEqual(stats["OTEL_TRACES_SAMPLER_ARG"], "0.1")
            self.assertEqual(stats["OTEL_BSP_MAX_QUEUE_SIZE"], "256")
            self.assertEqual(bridge["STATS_ORIGIN"], "http://172.29.80.20:8080")
            engine = oolib.read_env(cfg.engine_env)["RIVET__AUTH__ADMIN_TOKEN"]
            self.assertNotIn(engine, json.dumps(bridge))
            self.assertNotIn(stats["GATEWAY_SECRET"], json.dumps(bridge))
            self.assertNotIn(bridge["STATS_INGEST_TOKEN"], output.getvalue())
            self.assertNotIn(bridge["PLATFORM_OTLP_TOKEN"], output.getvalue())
            self.assertEqual((cfg.etc / "platform.env").stat().st_mode & 0o777, 0o600)
            for name, app in cfg.apps.items():
                if name == "stats":
                    continue
                env = oolib.read_env(cfg.app_env(app))
                self.assertFalse(any(key.startswith("OTEL_") or key == "PLATFORM_BRIDGE_TOKEN_SHA256" for key in env))
            with patch.object(os, "chown"):
                commands["cmd_secrets"](cfg)
            self.assertEqual(oolib.read_env(cfg.etc / "platform.env"), bridge)
            cfg.platform_bridge = None
            with patch.object(os, "chown"):
                commands["cmd_secrets"](cfg)
            disabled = oolib.read_env(cfg.app_env(cfg.apps["stats"]))
            self.assertFalse(any(key.startswith("OTEL_") or key == "PLATFORM_BRIDGE_TOKEN_SHA256" for key in disabled))

    def test_policy_is_validated_atomically_and_container_has_no_admin_access(self):
        cfg = enabled()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            cfg.stack["etc_dir"] = directory
            with patch.object(os, "chown"):
                commands["cmd_secrets"](cfg)
                commands["cmd_configure_platform"](cfg, selectors())
                commands["replace_platform_file"](cfg.etc / "platform.image", "sha256:" + "a" * 64 + "\n")
            path = cfg.etc / "platform/policy.json"
            original = path.read_text()
            policy = json.loads(original)
            self.assertEqual(policy["nativeVersion"], "3.1.1")
            self.assertEqual(policy["rivetkitVersion"], "3.1.2-rc.1")
            self.assertEqual(policy["samplePpm"], 100000)
            self.assertEqual(policy["actors"], selectors())
            self.assertEqual(path.stat().st_mode & 0o777, 0o440)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            for value in ([], [selectors()[0]] * 2, [{**selectors()[0], "name": "other-1234abcd"}, selectors()[1]], [{**selectors()[0], "key": "bad"}, selectors()[1]]):
                with self.assertRaises(oolib.ConfigError):
                    commands["cmd_configure_platform"](cfg, value)
                self.assertEqual(path.read_text(), original)
            self.assertEqual(list(path.parent.glob(".platform-*")), [])
            args = oolib.run_args(cfg, "platform")
            for flag in ("--publish", "-p", "--publish-all"):
                self.assertNotIn(flag, args)
            self.assertNotIn("host", args)
            self.assertNotIn("/var/run/docker.sock", " ".join(args))
            self.assertEqual(args[-1], "sha256:" + "a" * 64)
            self.assertIn("--read-only", args)
            self.assertIn(f"{oolib.UID}:{oolib.UID}", args)
            self.assertIn("128m", args)
            self.assertIn("PLATFORM_BRIDGE_RELEASE=platform-aaaaaaaaaaaa", args)
            env = oolib.read_env(cfg.etc / "platform.env")
            self.assertNotIn(env["STATS_INGEST_TOKEN"], " ".join(args))
            self.assertNotIn(env["PLATFORM_OTLP_TOKEN"], " ".join(args))
            self.assertNotIn("engine.env", " ".join(args))

    def test_only_stats_resource_attributes_follow_selected_image_and_routes_do_not_change(self):
        cfg = enabled()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            cfg.stack["etc_dir"] = directory
            with patch.object(os, "chown"):
                commands["cmd_secrets"](cfg)
            for name in ("stats", "stuff"):
                oolib.set_app_deployment(cfg.app_image_file(cfg.apps[name]), f"{name}:123456789abc")
            before = commands["render_caddyfile"](cfg)
            stats = oolib.run_args(cfg, "app", "stats")
            self.assertIn("OTEL_RESOURCE_ATTRIBUTES=service.version=stats-123456789abc,openorange.version=1.0.2", stats)
            self.assertFalse(any(arg.startswith("OTEL_") for arg in oolib.run_args(cfg, "app", "stuff")))
            oolib.set_app_deployment(cfg.app_image_file(cfg.apps["stats"]), "stats:abcdef123456")
            self.assertIn("OTEL_RESOURCE_ATTRIBUTES=service.version=stats-abcdef123456,openorange.version=1.0.2", oolib.run_args(cfg, "app", "stats"))
            cfg.platform_bridge = None
            self.assertEqual(commands["render_caddyfile"](cfg), before)
            self.assertNotIn("172.29.80.27", before)
        unit = (ROOT / "openrc/oo-platform").read_text()
        self.assertNotIn("need oo-engine", unit)
        self.assertNotIn("rc-service", unit)
        self.assertIn("oo_wait platform", unit)
        self.assertIn("sha256:5df79989", (ROOT / "platform/Dockerfile").read_text())

    def test_discovery_verifies_live_actor_keys_before_replacing_policy(self):
        from types import SimpleNamespace
        cfg = enabled()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            cfg.stack["etc_dir"] = directory
            result = SimpleNamespace(returncode=0, stdout=json.dumps(selectors()))
            calls = []
            def engine(_cfg, method, path):
                calls.append((method, path))
                name = "installation-1234abcd" if "installation-" in path else "observation-store-1234abcd"
                actor = next(actor for actor in selectors() if actor["name"] == name)
                return 200, {"actors": [{"name": name, "key": actor["key"], "destroy_ts": None}]}
            with patch.object(oolib, "docker", return_value=result) as docker, patch.object(os, "chown"), patch.dict(commands["cmd_discover_platform"].__globals__, {"engine_call": engine}):
                commands["cmd_discover_platform"](cfg)
            self.assertEqual(len(calls), 2)
            self.assertTrue(all("namespace=stats-prod" in path for _, path in calls))
            script = docker.call_args.kwargs["input"]
            self.assertIn('version !== "1.0.2"', script)
            self.assertNotIn("RIVET__AUTH__ADMIN_TOKEN", script)
            stored = (cfg.etc / "platform/policy.json").read_text()
            with patch.object(oolib, "docker", return_value=result), patch.dict(commands["cmd_discover_platform"].__globals__, {"engine_call": lambda *args: (200, {"actors": []})}):
                with self.assertRaises(oolib.ConfigError):
                    commands["cmd_discover_platform"](cfg)
            self.assertEqual((cfg.etc / "platform/policy.json").read_text(), stored)

    def test_readiness_requires_http_health(self):
        cfg = enabled()
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            cfg.stack["etc_dir"] = directory
            self.assertFalse(commands["ready"](cfg, "platform", None))
            with patch.object(os, "chown"):
                commands["cmd_secrets"](cfg)
                commands["cmd_configure_platform"](cfg, selectors())
                commands["replace_platform_file"](cfg.etc / "platform.image", "sha256:" + "a" * 64)
            with patch.dict(commands["ready"].__globals__, {"http_ok": lambda *args, **kwargs: False}):
                self.assertFalse(commands["ready"](cfg, "platform", None))
            with patch.dict(commands["ready"].__globals__, {"http_ok": lambda *args, **kwargs: True}):
                self.assertTrue(commands["ready"](cfg, "platform", None))


if __name__ == "__main__":
    unittest.main()
