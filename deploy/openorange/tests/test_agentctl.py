import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
commands = runpy.run_path(str(ROOT / "bin/oo"))
import oolib


class AgentctlConfigurationTests(unittest.TestCase):
    def test_private_only_route_and_container_isolation(self):
        cfg = oolib.load()
        app = cfg.apps["agentctl"]
        self.assertEqual((app.kind, app.namespace, app.ip, app.port, app.health_path),
                         ("orange", "agentctl", "172.29.80.26", 8080, "/healthz"))
        self.assertEqual((app.buckets, app.internet, app.public_hostnames, app.secrets), ((), False, (), ()))
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            cfg.stack["etc_dir"] = directory
            with patch.object(os, "chown"):
                commands["cmd_secrets"](cfg)
            env = oolib.read_env(cfg.app_env(app))
            self.assertTrue(env["GATEWAY_SECRET"])
            oolib.set_app_deployment(cfg.app_image_file(app), "agentctl:test")
            text = commands["render_caddyfile"](cfg)
            args = oolib.run_args(cfg, "app", "agentctl")
        private, public = text.split("# Public listener:", 1)
        block = private.split("# agentctl (orange)", 1)[1].split("\n}\n", 1)[0]
        self.assertIn("agentctl.17166969.xyz", block)
        self.assertLess(block.index("forward_auth unix//run/identity/identity.sock"), block.index("reverse_proxy 172.29.80.26:8080"))
        self.assertNotIn("agentctl.17166969.xyz", public)
        rules = oolib.tunnel_config(cfg)["config"]["ingress"]
        self.assertNotIn("agentctl.17166969.xyz", [rule.get("hostname") for rule in rules])
        self.assertIn("172.29.80.26", args)
        self.assertNotIn(cfg.egress_network, args)
        for flag in ("--publish", "-p", "--publish-all"):
            self.assertNotIn(flag, args)


if __name__ == "__main__":
    unittest.main()
