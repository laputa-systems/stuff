import os
import runpy
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import oolib


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "stats.image"

    def test_legacy_upgrade_idempotent_redeploy_and_rollback_advance_versions(self):
        self.path.write_text("stats:old\n")
        self.assertEqual(oolib.read_app_deployment(self.path), oolib.AppDeployment("stats:old", 0))
        self.assertEqual(oolib.set_app_deployment(self.path, "stats:old").version, 1)
        self.assertEqual(oolib.set_app_deployment(self.path, "stats:old").version, 1)
        self.assertEqual(oolib.set_app_deployment(self.path, "stats:new").version, 2)
        previous = oolib.read_app_deployment(self.path.with_suffix(".image.prev"))
        self.assertEqual(previous, oolib.AppDeployment("stats:old", 1))
        self.assertEqual(oolib.set_app_deployment(self.path, previous.image).version, 3)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_concurrent_deployments_get_distinct_versions(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda n: oolib.set_app_deployment(self.path, f"stats:{n}"), range(16)))
        self.assertEqual(sorted(x.version for x in results), list(range(1, 17)))
        self.assertEqual(oolib.read_app_deployment(self.path).version, 16)

    def test_conditional_rollout_cannot_replace_or_rollback_a_newer_image(self):
        oolib.set_app_deployment(self.path, "stats:previous")
        oolib.set_app_deployment(self.path, "stats:mine", expected_image="stats:previous")
        with self.assertRaisesRegex(oolib.ConfigError, "changed concurrently"):
            oolib.set_app_deployment(self.path, "stats:other", expected_image="stats:previous")
        oolib.set_app_deployment(self.path, "stats:newer")
        before = self.path.read_bytes()
        previous = self.path.with_suffix(".image.prev").read_bytes()
        with self.assertRaisesRegex(oolib.ConfigError, "changed concurrently"):
            oolib.set_app_deployment(self.path, "stats:previous", expected_image="stats:mine")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.path.with_suffix(".image.prev").read_bytes(), previous)

    def test_registry_provisioning_enables_and_verifies_versioning(self):
        cfg = oolib.load()
        cfg.stack["etc_dir"] = self.directory.name
        commands = runpy.run_path(str(Path(__file__).resolve().parents[1] / "bin" / "oo"))
        with patch.object(os, "chown"):
            commands["cmd_secrets"](cfg)
        app = cfg.apps["stuff"]
        self.assertTrue(app.versioning)
        self.assertFalse(cfg.apps["discover"].versioning)
        calls = []

        class Store:
            def request(self, method, path, **kwargs):
                calls.append((method, path, kwargs))
                if path == "/list-users":
                    return 200, {}, b"<Accounts/>"
                if method == "GET" and path == "/":
                    return 200, {}, b"<ListAllMyBucketsResult/>"
                if method == "GET":
                    return 200, {}, b"<VersioningConfiguration><Status>Enabled</Status></VersioningConfiguration>"
                return 200, {}, b""

        provision = commands["provision_store"]
        with patch.dict(provision.__globals__, {"store_admin": lambda _: Store(), "store_s3": lambda _: Store()}):
            provision(cfg, [app])
        enabled = [(path, kwargs) for method, path, kwargs in calls if method == "PUT"]
        self.assertEqual([path for path, _ in enabled], [f"/{bucket}" for bucket in app.buckets])
        self.assertTrue(all(kwargs["query"] == {"versioning": ""} and b"<Status>Enabled</Status>" in kwargs["body"] for _, kwargs in enabled))
        cfg.raw["apps"]["stuff"]["versioning"] = "true"
        with self.assertRaises(oolib.ConfigError):
            oolib.validate(cfg.raw)

    def test_malformed_and_unknown_records_never_select_an_image(self):
        for value in ["{", '{"schema":2,"image":"stats:a","version":1}',
                      '{"schema":1,"image":"stats:a","version":true}',
                      '{"schema":1,"image":"stats:a","version":-1}',
                      '{"schema":1,"image":"stats:a","version":1,"other":0}', ""]:
            self.path.write_text(value)
            with self.assertRaises(oolib.ConfigError):
                oolib.read_app_deployment(self.path)

    def test_egress_is_explicit_and_does_not_publish_private_ports(self):
        cfg = oolib.load()
        cfg.stack["etc_dir"] = self.directory.name
        app = replace(cfg.apps["discover"], internet=False)
        cfg.apps["discover"] = app
        cfg.app_image_file(app).parent.mkdir()
        oolib.set_app_deployment(cfg.app_image_file(app), "discover:verified")
        private = oolib.run_args(cfg, "app", "discover")
        self.assertNotIn(cfg.egress_network, private)
        cfg.apps["discover"] = replace(app, internet=True)
        egress = oolib.run_args(cfg, "app", "discover")
        self.assertIn(f"name={cfg.network['name']},ip={app.ip}", egress)
        self.assertIn(cfg.egress_network, egress)
        for forbidden in ["--publish", "-p", "--publish-all", "--privileged"]:
            self.assertNotIn(forbidden, egress)
        self.assertFalse(cfg.apps["stats"].internet)
        self.assertFalse(cfg.apps["stuff"].internet)
        cfg.raw["apps"]["discover"]["internet"] = "true"
        with self.assertRaises(oolib.ConfigError):
            oolib.validate(cfg.raw)

    def test_worker_vars_and_secret_names_have_one_derived_binding_list(self):
        cfg = oolib.load()
        cfg.stack["etc_dir"] = self.directory.name
        app = replace(cfg.apps["discover"], vars={"SPACE_NAME": "replacement-rehearsal"})
        cfg.apps["discover"] = app
        commands = runpy.run_path(str(Path(__file__).resolve().parents[1] / "bin" / "oo"))
        with patch.object(os, "chown"):
            commands["cmd_secrets"](cfg)
        values = oolib.read_env(cfg.app_env(app))
        self.assertEqual(values["SPACE_NAME"], "replacement-rehearsal")
        self.assertIn("SPACE_NAME", values["ORANGE_WORKER_SECRETS"].split(","))
        self.assertNotIn("S3_SECRET_ACCESS_KEY", values["ORANGE_WORKER_SECRETS"].split(","))
        stuff = oolib.read_env(cfg.app_env(cfg.apps["stuff"]))
        self.assertIn("S3_SECRET_ACCESS_KEY", stuff["ORANGE_WORKER_SECRETS"].split(","))
        for invalid in [{"S3_SECRET_ACCESS_KEY": "overridden"}, {"OPERATOR_BOOTSTRAP_SHA256": "overlap"}, {"SPACE_NAME": "line\nbreak"}]:
            cfg.raw["apps"]["discover"]["vars"] = invalid
            with self.assertRaises(oolib.ConfigError):
                oolib.validate(cfg.raw)

    def test_tunnel_routes_only_declared_public_hosts_to_loopback(self):
        cfg = oolib.load()
        rules = oolib.tunnel_config(cfg)["config"]["ingress"]
        hosts = {rule["hostname"] for rule in rules if "hostname" in rule}
        expected = {host for app in cfg.enabled_apps() for host in app.public_hostnames}
        self.assertEqual(hosts, expected)
        self.assertNotIn("stats.17166969.xyz", hosts)
        self.assertNotIn("tansu.17166969.xyz", hosts)
        self.assertEqual(rules[-1], {"service": "http_status:404"})
        self.assertTrue(all(rule["service"].startswith("http://127.0.0.1:") for rule in rules[:-1]))
        args = oolib.run_args(cfg, "tunnel")
        self.assertIn(str(cfg.etc / "tunnel.env"), args)
        self.assertNotIn("--token", args)
        self.assertIn(f"127.0.0.1:{cfg.tunnel['metrics_port']}", args)
        cfg.tunnel["enabled"] = False
        with self.assertRaises(oolib.ConfigError):
            oolib.run_args(cfg, "tunnel")

    def test_split_dns_uses_declared_public_names_and_tailnet_listener(self):
        cfg = oolib.load()
        corefile = oolib.dns_config(cfg)
        hosts = {host for app in cfg.enabled_apps() for host in app.public_hostnames}
        self.assertEqual(set(corefile.split(" {", 1)[0].split()), hosts)
        self.assertIn(f"bind {cfg.ingress['bind']}", corefile)
        self.assertIn("template IN AAAA", corefile)
        self.assertIn("rcode NOERROR", corefile)
        self.assertIn("forward . 1.1.1.1 1.0.0.1", corefile)
        args = oolib.run_args(cfg, "dns")
        self.assertIn("host", args)
        self.assertIn("NET_BIND_SERVICE", args)
        self.assertNotIn("--publish", args)
        self.assertNotIn("--privileged", args)
        cfg.raw["dns"]["enabled"] = "true"
        with self.assertRaises(oolib.ConfigError):
            oolib.validate(cfg.raw)
        cfg.dns["enabled"] = False
        with self.assertRaises(oolib.ConfigError):
            oolib.run_args(cfg, "dns")

    def test_app_arguments_use_deployment_version_and_image_together(self):
        cfg = oolib.load()
        cfg.stack["etc_dir"] = self.directory.name
        app = cfg.apps["stats"]
        cfg.app_image_file(app).parent.mkdir()
        oolib.set_app_deployment(cfg.app_image_file(app), "stats:verified")
        args = oolib.run_args(cfg, "app", "stats")
        self.assertIn("RIVET_NODE_VERSION=1", args)
        self.assertEqual(args[-1], "stats:verified")


if __name__ == "__main__":
    unittest.main()
