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


class NanoshopConfigurationTests(unittest.TestCase):
    def test_rendered_routes_and_container_isolation(self):
        cfg = oolib.load()
        app = cfg.apps["nanoshop"]
        self.assertEqual((app.kind, app.display, app.namespace, app.ip, app.port, app.health_path),
                         ("orange", "Nanoshop", "nanoshop-storied", "172.29.80.25", 8080, "/healthz"))
        self.assertEqual((app.buckets, app.memory, app.cpus, app.internet),
                         (("nanoshop-media-storied",), "1g", 1.0, False))
        self.assertEqual(app.vars["NANOSHOP_ADMIN_ORIGIN"], "https://shop-admin.17166969.xyz")
        self.assertEqual(json.loads(app.vars["NANOSHOP_OWNER_IDENTITIES"]), ["user:joshua.r.li.98@gmail.com"])
        self.assertEqual(set(app.secrets), {"NANOSHOP_OPERATOR_SHA256", "APPLICATION_EVENTS_TOKEN",
                                            "APPLICATION_EVENTS_ENDPOINT", "APPLICATION_EVENTS_SERVICE"})
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            cfg.stack["etc_dir"] = directory
            with patch.object(os, "chown"):
                commands["cmd_secrets"](cfg)
            env = oolib.read_env(cfg.app_env(app))
            self.assertTrue(env["GATEWAY_SECRET"])
            self.assertTrue(set(app.secrets).issubset(env["ORANGE_WORKER_SECRETS"].split(",")))
            self.assertEqual(env["NANOSHOP_OWNER_IDENTITIES"], app.vars["NANOSHOP_OWNER_IDENTITIES"])
            oolib.set_app_deployment(cfg.app_image_file(app), "nanoshop:test")
            text = commands["render_caddyfile"](cfg)
            args = oolib.run_args(cfg, "app", "nanoshop")

        private, public = text.split("# Public listener:", 1)
        shop_private = private.split("# Nanoshop (orange)", 1)[1].split("\n}\n", 1)[0]
        shop_public = public.split("# Nanoshop (public)", 1)[1].split("\n}\n", 1)[0]
        self.assertIn("shop.17166969.xyz, shop-admin.17166969.xyz", shop_private)
        self.assertLess(shop_private.index("forward_auth unix//run/identity/identity.sock"),
                        shop_private.index("reverse_proxy 172.29.80.25:8080"))
        self.assertIn("uri /auth", shop_private)
        self.assertIn("http://shop.17166969.xyz:18480", shop_public)
        self.assertNotIn("shop-admin.17166969.xyz", public)
        self.assertIn("@deny0 path /admin /admin/*", shop_public)
        self.assertIn("respond @deny0 404", shop_public)
        self.assertIn("@denyre0 path_regexp", shop_public)
        self.assertLess(shop_public.index("respond @deny0 404"), shop_public.index("reverse_proxy 172.29.80.25:8080"))
        self.assertNotIn("@private_method", shop_public)
        self.assertNotIn("405", shop_public)
        rules = oolib.tunnel_config(cfg)["config"]["ingress"]
        self.assertIn({"hostname": "shop.17166969.xyz", "service": "http://127.0.0.1:18480"}, rules)
        self.assertNotIn("shop-admin.17166969.xyz", [rule.get("hostname") for rule in rules])
        self.assertIn("172.29.80.25", args)
        self.assertNotIn(cfg.egress_network, args)
        for flag in ("--publish", "-p", "--publish-all"):
            self.assertNotIn(flag, args)
        self.assertIn("--memory", args)
        self.assertIn("1g", args)
        self.assertIn("1.0", args)

    def test_existing_hosts_and_rivet_remain_routed(self):
        cfg = oolib.load()
        expected = {
            "stats": {"stats.17166969.xyz", "stats-next.17166969.xyz"},
            "stuff": {"stuff.17166969.xyz", "stuff-publish.17166969.xyz", "crates.17166969.xyz",
                      "crates-blobs.17166969.xyz", "npm.17166969.xyz", "pypi.17166969.xyz",
                      "oci.17166969.xyz", "oci-blobs.17166969.xyz", "mirror.17166969.xyz"},
            "tansu": {"tansu.17166969.xyz"},
            "discover": {"hq.17166969.xyz", "research.17166969.xyz", "hq-admin.17166969.xyz"},
            "discover-preview": {"hq-preview.17166969.xyz", "research-preview.17166969.xyz", "hq-preview-admin.17166969.xyz"},
        }
        text = commands["render_caddyfile"](cfg)
        private, public = text.split("# Public listener:", 1)
        for name, hosts in expected.items():
            self.assertEqual(set(cfg.apps[name].hostnames), hosts)
            for host in hosts:
                self.assertIn(host, private)
        self.assertEqual((cfg.rivet.hostname, cfg.rivet.ip, cfg.rivet.port), ("stats.17166969.xyz", "172.29.80.24", 8080))
        self.assertIn("path /rivet /rivet/*", private)
        self.assertIn("reverse_proxy 172.29.80.24:8080", private)
        self.assertNotIn("172.29.80.24", public)


if __name__ == "__main__":
    unittest.main()
