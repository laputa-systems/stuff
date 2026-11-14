import copy
import os
from pathlib import Path
import runpy
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "bin/oo"))
import oolib


class PublicReadConfigurationTests(unittest.TestCase):
    def test_public_methods_reject_invalid_or_ambiguous_configuration(self):
        for methods in ("GET", ["get"], ["GET", "GET"], ["GET\nrespond 200"], [{}]):
            with self.subTest(methods=methods):
                raw = copy.deepcopy(oolib.load().raw)
                raw["apps"]["stuff"]["public_methods"] = methods
                with self.assertRaises(oolib.ConfigError):
                    oolib.validate(raw)


@unittest.skipUnless(os.environ.get("OO_PUBLIC_READ_TEST_ORIGIN"), "requires the public ingress listener")
class PublicReadIngressTests(unittest.TestCase):
    def request(self, method, path, *, host="stuff.17166969.xyz"):
        request = urllib.request.Request(
            os.environ["OO_PUBLIC_READ_TEST_ORIGIN"].rstrip("/") + path,
            method=method,
            headers={"Host": host, "Stats-Tailnet-Identity": "user:forged", "Stats-Gateway-Secret": "forged", "X-OO-Ingress": "tailnet"},
        )
        try:
            return urllib.request.urlopen(request, timeout=15)
        except urllib.error.HTTPError as error:
            return error

    def test_anonymous_reads_work_and_private_routes_and_mutations_are_blocked(self):
        for method in ("GET", "HEAD"):
            with self.request(method, "/") as response:
                self.assertEqual(response.status, 200)
                if method == "HEAD":
                    self.assertEqual(response.read(), b"")
            for path in ("/_s3/stuff-mycrates/current", "/_publication/cargo/current", "/_publication/cargo/begin"):
                with self.request(method, path) as response:
                    self.assertEqual(response.status, 404)
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"):
            with self.subTest(method=method), self.request(method, "/__public_method_probe") as response:
                self.assertEqual(response.status, 405)
                self.assertEqual(response.headers["Allow"], "GET, HEAD")
        with self.request("GET", "/_publication/cargo/current", host="stuff-publish.17166969.xyz") as response:
            self.assertEqual(response.status, 404)


if __name__ == "__main__":
    unittest.main()
