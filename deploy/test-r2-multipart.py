#!/usr/bin/env python3
import datetime
import importlib.util
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = pathlib.Path(__file__).with_name("r2-multipart.py")
sys.path.insert(0, str(SCRIPT.parent))
import fake_s3
spec = importlib.util.spec_from_file_location("r2_multipart", SCRIPT)
r2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r2)

AWS_ACCESS = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
MAY_24_2013 = datetime.datetime(2013, 5, 24, tzinfo=datetime.timezone.utc)


class SigV4Tests(unittest.TestCase):
    def setUp(self):
        self.saved = dict(os.environ)
        os.environ["R2_S3_ENDPOINT"] = "https://examplebucket.s3.amazonaws.com"
        os.environ["R2_S3_ACCESS_KEY_ID"] = AWS_ACCESS
        os.environ["R2_S3_SECRET_ACCESS_KEY"] = AWS_SECRET
        os.environ["R2_S3_REGION"] = "us-east-1"
        os.environ.pop("R2_S3_SESSION_TOKEN", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved)

    def test_matches_aws_get_object_vector(self):
        headers = r2.signature_headers(
            "GET",
            "https://examplebucket.s3.amazonaws.com/test.txt",
            r2.EMPTY_SHA256,
            now=MAY_24_2013,
            extra_headers={"range": "bytes=0-9"},
        )
        self.assertTrue(
            headers["Authorization"].endswith(
                "SignedHeaders=host;range;x-amz-content-sha256;x-amz-date, "
                "Signature=f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41"
            ),
            headers["Authorization"],
        )

    def test_initiation_canonicalizes_empty_query_as_uploads_equals(self):
        canonical, signed = r2.canonical_request(
            "POST",
            "https://examplebucket.s3.amazonaws.com/bucket/key?uploads",
            r2.EMPTY_SHA256,
            amzdate="20130524T000000Z",
        )
        self.assertIn("\nuploads=\n", canonical)
        self.assertEqual(signed, "host;x-amz-content-sha256;x-amz-date")

    def test_part_upload_sorts_content_type_before_amz_headers(self):
        canonical, signed = r2.canonical_request(
            "PUT",
            "https://examplebucket.s3.amazonaws.com/bucket/key?partNumber=1&uploadId=abc",
            "a" * 64,
            content_type="application/octet-stream",
            amzdate="20130524T000000Z",
        )
        self.assertIn("\npartNumber=1&uploadId=abc\n", canonical)
        self.assertEqual(
            signed,
            "content-type;host;x-amz-content-sha256;x-amz-date",
        )
        self.assertIn(
            "content-type:application/octet-stream\nhost:examplebucket.s3.amazonaws.com\n",
            canonical,
        )

    def test_completion_canonicalizes_query_in_sorted_order(self):
        canonical, _ = r2.canonical_request(
            "POST",
            "https://examplebucket.s3.amazonaws.com/bucket/key?uploadId=abc",
            "a" * 64,
            content_type="text/plain",
            amzdate="20130524T000000Z",
        )
        self.assertIn("\nuploadId=abc\n", canonical)

    def test_session_token_is_signed_and_sent(self):
        os.environ["R2_S3_SESSION_TOKEN"] = "temporary-token"
        headers = r2.signature_headers(
            "POST",
            "https://examplebucket.s3.amazonaws.com/bucket/key?uploads",
            r2.EMPTY_SHA256,
            now=MAY_24_2013,
        )
        self.assertIn("x-amz-security-token", headers["Authorization"])
        self.assertIn(
            "SignedHeaders=host;x-amz-content-sha256;x-amz-date;x-amz-security-token",
            headers["Authorization"],
        )
        self.assertEqual(headers["x-amz-security-token"], "temporary-token")

    def test_detects_error_body_inside_http_200(self):
        body = b'<?xml version="1.0"?><Error><Code>InternalError</Code><Message>try again</Message></Error>'
        self.assertEqual(r2.completion_error(body), "InternalError")
        self.assertEqual(r2.completion_error(b""), "")


class MultipartFlowTests(unittest.TestCase):
    def setUp(self):
        self.saved = dict(os.environ)
        self.isolated = tempfile.TemporaryDirectory()
        os.environ["STUFF_CONFIG_HOME"] = self.isolated.name
        with patch("socket.getfqdn", side_effect=AssertionError("fake S3 must bind without DNS")):
            self.server = fake_s3.serve()
        self.server.verify_signature = True
        self.server.request_log_style = "full"
        os.environ["R2_S3_ENDPOINT"] = f"http://127.0.0.1:{self.server.server_port}"
        os.environ["R2_S3_ACCESS_KEY_ID"] = AWS_ACCESS
        os.environ["R2_S3_SECRET_ACCESS_KEY"] = AWS_SECRET
        os.environ["R2_S3_REGION"] = "auto"
        os.environ.pop("R2_S3_SESSION_TOKEN", None)
        self.saved_part = r2.PART_SIZE
        r2.PART_SIZE = 4
        self.saved_argv = sys.argv

    def tearDown(self):
        r2.PART_SIZE = self.saved_part
        sys.argv = self.saved_argv
        self.server.shutdown()
        self.server.server_close()
        os.environ.clear()
        os.environ.update(self.saved)
        self.isolated.cleanup()

    def run_upload(self, payload):
        with tempfile.TemporaryDirectory() as work:
            path = os.path.join(work, "artifact")
            with open(path, "wb") as f:
                f.write(payload)
            sys.argv = ["r2-multipart.py", path, "bucket", "path/artifact", "text/plain"]
            r2.main()

    def test_uploads_parts_and_completes(self):
        self.run_upload(b"abcdefghij")
        methods = [(method, query) for method, _, query, _ in self.server.requests]
        self.assertEqual(methods[0][0], "POST")
        self.assertIn("uploads", methods[0][1])
        parts = [query["partNumber"][0] for method, _, query, _ in self.server.requests if method == "PUT"]
        self.assertEqual(parts, ["1", "2", "3"])
        completion = self.server.requests[-1]
        self.assertEqual(completion[0], "POST")
        self.assertIn(b"<PartNumber>3</PartNumber>", completion[3])

    def test_completion_error_inside_http_200_aborts(self):
        self.server.fail_complete = True
        with self.assertRaises(SystemExit):
            self.run_upload(b"abcdefghij")
        self.assertEqual(self.server.requests[-1][0], "DELETE")

    def test_upload_accepts_lowercase_gateway_response_headers(self):
        original = fake_s3.FakeS3Handler._reply

        def lowercase(handler, status, body=b"", headers=None):
            return original(handler, status, body, {name.lower(): value for name, value in (headers or {}).items()})

        with patch.object(fake_s3.FakeS3Handler, "_reply", lowercase):
            self.run_upload(b"abcdefghij")
        self.assertEqual(self.server.objects[("bucket", "path/artifact")][0], b"abcdefghij")

    def test_conditional_completion_verifies_existing_bytes_and_aborts_parts(self):
        self.run_upload(b"abcdefghij")
        actual = r2.request

        def immutable_complete(method, url, *args, **kwargs):
            if method == "POST" and "uploadId=" in url:
                return 412, b"", {}
            return actual(method, url, *args, **kwargs)

        with patch.object(r2, "request", side_effect=immutable_complete):
            self.run_upload(b"abcdefghij")
            self.assertEqual(self.server.requests[-1][0], "DELETE")
            with self.assertRaises(SystemExit):
                self.run_upload(b"changedxxx")
        self.assertEqual(self.server.requests[-1][0], "DELETE")
        self.assertEqual(self.server.uploads, {})


if __name__ == "__main__":
    unittest.main()

