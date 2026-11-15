import os
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
commands = runpy.run_path(str(ROOT / "bin/oo"))
import oolib


class StatsPerformanceIngressTests(unittest.TestCase):
    def test_rehearsal_splits_the_existing_alias_without_public_exposure(self):
        normal = oolib.load()
        staged = oolib.load(overlay=ROOT / "fixtures/stats-performance.toml")
        before = {host for app in normal.enabled_apps() for host in app.hostnames}
        after = {host for app in staged.enabled_apps() for host in app.hostnames}
        self.assertEqual(before, after)
        self.assertEqual(staged.apps["stats"].namespace, normal.apps["stats"].namespace)
        self.assertEqual(staged.apps["stats"].ip, normal.apps["stats"].ip)
        self.assertEqual(staged.rivet, normal.rivet)
        self.assertEqual(staged.apps["stats-perf"].public_hostnames, ())
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            staged.stack["etc_dir"] = directory
            image = staged.app_image_file(staged.apps["stats"])
            image.parent.mkdir()
            image.write_text("stats:test")
            text = commands["render_caddyfile"](staged)
        private, public = text.split("# Public listener:", 1)
        fixture = private.split("# Stats scale fixture (native)", 1)[1]
        self.assertIn("stats-next.17166969.xyz {", fixture)
        self.assertIn(f"bind {normal.ingress['bind']}", fixture)
        self.assertIn("request_header -Stats-Gateway-Secret", fixture)
        self.assertIn("forward_auth unix//run/identity/identity.sock", fixture)
        self.assertIn("copy_headers Stats-Tailnet-Identity", fixture)
        self.assertIn("reverse_proxy 172.31.90.2:8787", fixture)
        self.assertIn("header_up Stats-Gateway-Secret {$GW_SECRET_STATS_PERF}", fixture)
        self.assertLess(fixture.index("forward_auth"), fixture.index("reverse_proxy"))
        self.assertNotIn("stats-next", public)
        self.assertNotIn("172.31.90.2", public)
        canonical = private.split("# Stats (orange)", 1)[1].split("# Stuff", 1)[0]
        self.assertIn("stats.17166969.xyz {", canonical)
        self.assertNotIn("stats-next", canonical)
        self.assertIn("reverse_proxy 172.29.80.20:8080", canonical)
        self.assertNotIn("172.31.90.2", canonical)


if __name__ == "__main__":
    unittest.main()
