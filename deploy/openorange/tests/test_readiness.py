from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import runpy
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
commands = runpy.run_path(str(ROOT / "bin/oo"))
import oolib


class ReadinessTests(unittest.TestCase):
    def test_readiness_reads_stored_data_with_real_host_and_gateway_identity(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            available = False

            def do_GET(self):
                requests.append((self.path, dict(self.headers)))
                self.send_response(200 if self.available else 503)
                self.end_headers()
                self.wfile.write(b'{"hosts":[]}' if self.available else b'storage unavailable')

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
                cfg = oolib.load()
                cfg.stack["etc_dir"] = directory
                cfg.apps["stats"] = replace(cfg.apps["stats"], ip="127.0.0.1", port=server.server_port)
                env = Path(directory) / "apps/stats.env"
                env.parent.mkdir()
                oolib.write_env(env, {"GATEWAY_SECRET": "test-gateway-secret"})
                self.assertFalse(commands["ready"](cfg, "app", "stats"))
                Handler.available = True
                self.assertTrue(commands["ready"](cfg, "app", "stats"))
                for path, headers in requests:
                    self.assertEqual(path, "/api/v1/hosts")
                    self.assertEqual(headers["Host"], "stats.17166969.xyz")
                    self.assertEqual(headers["Stats-Gateway-Secret"], "test-gateway-secret")
                    self.assertTrue(headers["Stats-Tailnet-Identity"].startswith("user:"))
                Handler.available = False
                self.assertFalse(commands["ready"](cfg, "app", "stats"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
