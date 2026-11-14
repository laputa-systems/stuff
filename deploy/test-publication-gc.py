#!/usr/bin/env python3
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

import publication_service


def sibling(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixtures = sibling("gc_fixtures", "test-r2-gc.py")
blobs = sibling("gc_blobs", "r2-gc-blobs.py")
put = sibling("service_put", "r2-put.py")
multipart = sibling("service_multipart", "r2-multipart.py")


class Coordinator(fixtures.FakeR2):
    def _request(self):
        self.path = self.path.removeprefix("/_s3")
        return super()._request()

    def do_DELETE(self):
        self.server.raw_deletes.append(self.path)
        self._reply(403)

    def do_PUT(self):
        _, key, _ = self._request()
        value = self.rfile.read(int(self.headers["content-length"]))
        if self.headers.get("x-amz-security-token") != "gc-token":
            self._reply(403)
            return
        if key in self.server.objects:
            self._reply(412)
            return
        self.server.objects[key] = {"body": value, "time": fixtures.OLD}
        self._reply(200, headers={"ETag": '"' + fixtures.md5(value) + '"'})

    def do_POST(self):
        if self.headers.get("authorization") != "Bearer coordinator-secret":
            self._reply(401)
            return
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        operation = self.path.rsplit("/", 1)[-1]
        self.server.operations.append((operation, body))
        if operation in ("gc-claim", "begin"):
            self._reply(200, b'{"token":"gc-token","expires":9999999999999,"revision":0}')
            return
        if body.get("token") != "gc-token":
            self._reply(409)
            return
        if operation == "renew":
            self.server.renewed.set()
            self._reply(503 if self.server.fail_renew else 200, b'{"ok":true}')
            return
        if operation == "gc-delete":
            generation = body["generation"]
            remaining = self.server.partial_gc.get(generation, 0)
            if remaining:
                self.server.partial_gc[generation] = remaining - 1
                self._reply(200, b'{"deleted":1,"complete":false}')
                return
            for key in list(self.server.objects):
                if key == f"manifests/{generation}.json" or key.startswith(f"generations/{generation}/"):
                    del self.server.objects[key]
            self._reply(200, b'{"deleted":1,"complete":true}')
            return
        if operation == "gc-object":
            self.server.objects.pop(body["key"], None)
        self._reply(200, b'{"ok":true}')


class PublicationGCTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.GcTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.server = self.fixture.server
        self.server.RequestHandlerClass = Coordinator
        self.server.operations = []
        self.server.raw_deletes = []
        self.server.fail_renew = False
        self.server.partial_gc = {}
        self.server.renewed = threading.Event()
        self.file = Path(os.environ["STUFF_CONFIG_HOME"], "credentials.json")
        self.file.write_text(json.dumps(dict(schema=1, endpoint=os.environ["R2_S3_ENDPOINT"], coordinator_token="coordinator-secret", access_key_id="read-access", secret_access_key="read-secret", region="auto")))
        self.file.chmod(0o600)

    def test_generation_and_shared_gc_use_remote_lease_without_raw_deletes(self):
        self.server.partial_gc["g1"] = 2
        with contextlib.redirect_stdout(io.StringIO()):
            fixtures.gc.main(["bucket", "--keep-previous", "0", "--keep-newer", "0", "--grace-minutes", "0"])
        operations = [operation for operation, _ in self.server.operations]
        self.assertEqual(operations[0], "gc-claim")
        self.assertEqual(operations[-1], "abort")
        self.assertIn("gc-delete", operations)
        self.assertIn("gc-object", operations)
        self.assertEqual(sum(operation == "gc-delete" and body["generation"] == "g1"
                             for operation, body in self.server.operations), 3)
        self.assertEqual(self.server.raw_deletes, [])
        self.assertEqual(self.server.objects["current"]["body"], b"g3")
        self.assertIn("manifests/g3.json", self.server.objects)
        self.assertNotIn("manifests/g1.json", self.server.objects)
        self.assertEqual(os.environ["R2_S3_ENDPOINT"], publication_service.configured().endpoint + "/_s3")

    def test_renewal_failure_stops_deletion_and_releases_joined_thread(self):
        service = publication_service.configured()
        lease = service.gc_lease("bucket")
        actual = lease._stop

        class FastWait:
            def wait(self, seconds):
                return actual.wait(min(seconds, 0.01))

            def set(self):
                actual.set()

        lease._stop = FastWait()
        self.server.fail_renew = True
        with self.assertRaisesRegex(publication_service.PublicationError, "renewal failed"):
            with lease:
                self.assertTrue(lease._failed.wait(2))
                lease.delete("gc-object", key="blobs/old1")
        self.assertFalse(lease._thread.is_alive())
        self.assertEqual([operation for operation, _ in self.server.operations], ["gc-claim", "renew", "abort"])
        self.assertIn("blobs/old1", self.server.objects)

    def test_exceptions_abort_lease_and_blob_script_routes_to_gc_object(self):
        service = publication_service.configured()
        lease = service.gc_lease("bucket")
        with self.assertRaisesRegex(ValueError, "injected"):
            with lease:
                raise ValueError("injected")
        self.assertFalse(lease._thread.is_alive())
        self.assertEqual(self.server.operations[-1][0], "abort")
        plan = {"drop": ["sha256/" + "a" * 64], "current": "g3", "retained": {"g3"}, "in_flight": [], "unreadable": [], "kept": 1, "recent": 0, "signature": None}
        def execute(args, plan, list_meta, get_body, delete_batch):
            delete_batch(plan["drop"])
        with patch.object(blobs, "registry_for_bucket", return_value="oci"), patch.object(publication_service, "registry_for_bucket", return_value="oci"), patch.object(blobs, "plan_drop", return_value=plan), patch.object(blobs, "delete_batches", side_effect=execute), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(blobs.main(["bucket", "bucket"]), 0)
        self.assertEqual(self.server.operations[-2], ("gc-object", {"token": "gc-token", "key": "sha256/" + "a" * 64}))
        self.assertEqual(self.server.raw_deletes, [])

    def test_invalid_credentials_never_fall_back_to_legacy_gc(self):
        self.file.chmod(0o644)
        with self.assertRaisesRegex(publication_service.PublicationError, "owner-only"):
            publication_service.configured()
        self.file.chmod(0o600)
        self.file.write_text('{"schema":1,"coordinator_token":"must-not-appear"}')
        with self.assertRaisesRegex(publication_service.PublicationError, "schema") as failure:
            publication_service.configured()
        self.assertNotIn("must-not-appear", str(failure.exception))
        os.environ["STUFF_COORDINATOR_URL"] = "https://service.example"
        with self.assertRaisesRegex(publication_service.PublicationError, "all publishing"):
            publication_service.configured()
        self.assertEqual(self.server.operations, [])

    def test_writer_puts_hold_upload_lease_and_verify_existing_bytes(self):
        site = self.file.parent / "site"
        (site / "blobs").mkdir(parents=True)
        key = "blobs/new-upload"
        (site / key).write_bytes(b"immutable source bytes")
        keys = self.file.parent / "keys"
        keys.write_text(key + "\n")
        args = [str(site), "bucket", str(keys)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(put.main(args), 0)
            self.assertEqual(put.main(args), 0)
        self.assertEqual(self.server.objects[key]["body"], b"immutable source bytes")
        self.assertEqual([operation for operation, _ in self.server.operations], ["begin", "abort", "begin", "abort"])
        (site / key).write_bytes(b"different source bytes")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(put.main(args), 1)
        self.assertEqual(self.server.objects[key]["body"], b"immutable source bytes")
        self.assertEqual(self.server.operations[-1][0], "abort")

    def test_multipart_entry_uses_the_same_upload_lease_and_cleanup(self):
        def upload(lease):
            self.assertIsNotNone(lease)
            self.assertEqual(os.environ["R2_S3_SESSION_TOKEN"], "gc-token")
            self.assertEqual(os.environ["R2_S3_ENDPOINT"], publication_service.configured().endpoint + "/_s3")
            raise OSError("injected multipart failure")
        with patch("sys.argv", ["r2-multipart.py", "file", "bucket", "key", "application/octet-stream"]), patch.object(multipart, "upload", side_effect=upload), self.assertRaisesRegex(OSError, "injected"):
            multipart.main()
        self.assertEqual([operation for operation, _ in self.server.operations], ["begin", "abort"])


if __name__ == "__main__":
    unittest.main()
