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
            status = 400

            def do_GET(self):
                requests.append((self.path, dict(self.headers)))
                self.send_response(self.status)
                if self.status == 302:
                    self.send_header("Location", "/elsewhere" if self.path != "/elsewhere" else "/")
                self.end_headers()
                if self.status == 400:
                    self.wfile.write(b'{"error":{"group":"depot","code":"request_deadline_exceeded","message":"private details"}}')
                elif self.status == 200:
                    self.wfile.write(b'{"hosts":[]}')

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
                self.assertEqual(oolib.app_readiness(cfg, cfg.apps["stats"]), (400, "depot.request_deadline_exceeded"))
                Handler.status = 200
                self.assertTrue(commands["ready"](cfg, "app", "stats"))
                for path, headers in requests:
                    self.assertEqual(path, "/api/v1/hosts")
                    self.assertEqual(headers["Host"], "stats.17166969.xyz")
                    self.assertEqual(headers["Stats-Gateway-Secret"], "test-gateway-secret")
                    self.assertTrue(headers["Stats-Tailnet-Identity"].startswith("user:"))
                Handler.status = 302
                requests.clear()
                self.assertEqual(oolib.app_readiness(cfg, cfg.apps["stats"]), (302, ""))
                self.assertEqual([path for path, _ in requests], ["/api/v1/hosts"])
                Handler.status = 503
                self.assertFalse(commands["ready"](cfg, "app", "stats"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
