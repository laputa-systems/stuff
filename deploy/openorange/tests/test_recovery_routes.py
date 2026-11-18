import contextlib
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest

COMMANDS = runpy.run_path(str(Path(__file__).resolve().parents[1] / "bin/oo"))


class RecoveryRoutesTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.cfg = COMMANDS["oolib"].load()
        self.cfg.stack["etc_dir"] = directory.name

    def write_routes(self, routes):
        (self.cfg.etc / "recovery-routes.json").write_text(json.dumps(routes))

    def test_writer_route_supersedes_the_image_and_blocks_local_activation(self):
        render = COMMANDS["render_caddyfile"]
        self.assertNotIn("127.0.0.1:18489", render(self.cfg))
        before = self.cfg.app_image_file(self.cfg.apps["stats"])
        before.parent.mkdir()
        before.write_text("stats:previous\n")
        self.write_routes({"stats": {"mode": "writer", "upstream": "127.0.0.1:18489"}})
        caddy = render(self.cfg)
        self.assertIn("forward_auth unix//run/identity/identity.sock", caddy)
        self.assertIn("reverse_proxy 127.0.0.1:18489 {\n\t\t\theader_up Stats-Gateway-Secret {$GW_SECRET_RECOVERY_STATS}", caddy)
        self.assertNotIn("reverse_proxy 172.29.80.20:8080", caddy)
        for name, args in (
            ("cmd_prepare", ("app", "stats")),
            ("cmd_set_image", ("stats", "stats:replacement")),
        ):
            error = io.StringIO()
            with contextlib.redirect_stderr(error), self.assertRaises(SystemExit):
                COMMANDS[name](self.cfg, *args)
            self.assertIn("local writer fenced", error.getvalue())
        self.assertEqual(before.read_text(), "stats:previous\n")
        COMMANDS["require_local_writer"](self.cfg, "stuff")

    def test_reader_applies_only_to_public_read_hosts_and_leaves_primary_route(self):
        discover = self.cfg.apps["discover"]
        image = self.cfg.app_image_file(discover)
        image.parent.mkdir()
        image.write_text("discover:primary\n")
        self.write_routes({"discover": {
            "mode": "reader",
            "upstream": "127.0.0.1:18485",
            "hosts": ["hq.17166969.xyz"],
            "deny_paths": ["/mcp", "/api/v1/operator"],
            "snapshot_at": "2026-11-18T01:24:07Z",
        }})
        caddy = COMMANDS["render_caddyfile"](self.cfg)
        self.assertEqual(caddy.count("host hq.17166969.xyz\n\t\t\tmethod GET HEAD"), 2)
        self.assertEqual(caddy.count("not path_regexp (?i)^/+(?:\\.{1,2}/+)*(?:admin|mcp|api/v1/operator)(?:[/;]|$)"), 2)
        self.assertEqual(caddy.count("reverse_proxy @recoveryRead 127.0.0.1:18485"), 2)
        self.assertEqual(caddy.count("header_down X-Discover-Recovery-Snapshot 2026-11-18T01:24:07Z"), 2)
        self.assertEqual(caddy.count("reverse_proxy 172.29.80.22:8080"), 2)
        self.assertNotIn("Stats-Gateway-Secret", caddy.split("reverse_proxy @recoveryRead", 1)[1].split("}", 1)[0])
        COMMANDS["require_local_writer"](self.cfg, "discover")

    def test_malformed_inputs_fail_before_rendering(self):
        for app, spec in (
            ("unknown", {}),
            ("stats", {"mode": "writer", "upstream": "127.0.0.1:18489\nrespond 200"}),
            ("stats", {"mode": "writer", "upstream": "8.8.8.8:443"}),
            ("discover", {"mode": "writer", "upstream": "127.0.0.1:18485"}),
            ("discover", {"mode": "reader", "upstream": "127.0.0.1:18485",
                          "hosts": ["hq-admin.17166969.xyz"], "deny_paths": []}),
        ):
            with self.subTest(app=app, spec=spec):
                self.write_routes({app: spec})
                with self.assertRaises(COMMANDS["ConfigError"]):
                    COMMANDS["render_caddyfile"](self.cfg)
