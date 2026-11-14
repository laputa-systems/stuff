"""Exclusive publication-service leases for the registry GC planners."""

import json
import os
import stat
import subprocess
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class GCError(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Service:
    def __init__(self, document):
        expected = {"schema", "endpoint", "coordinator_token", "access_key_id", "secret_access_key", "region"}
        if (not isinstance(document, dict) or set(document) != expected
                or type(document["schema"]) is not int or document["schema"] != 1):
            raise GCError("unsupported publishing credential schema")
        if any(not isinstance(document[key], str) or not document[key] or not document[key].isascii()
               or any(ord(char) < 32 or ord(char) == 127 for char in document[key])
               for key in expected - {"schema"}):
            raise GCError("invalid publishing credential fields")
        try:
            url = urllib.parse.urlsplit(document["endpoint"])
            _ = url.port
        except ValueError:
            raise GCError("invalid publishing endpoint") from None
        loopback = url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1", "::1")
        if (not url.hostname or url.username is not None or url.password is not None
                or url.path not in ("", "/") or url.query or url.fragment
                or (url.scheme != "https" and not loopback)):
            raise GCError("publishing endpoint requires HTTPS without credentials, path or query")
        self._document = document
        self.endpoint = document["endpoint"].rstrip("/")
        self._opener = urllib.request.build_opener(_NoRedirect())

    def read_credentials(self):
        document = self._document
        for name in ("R2_S3_ENDPOINT", "R2_S3_ACCESS_KEY_ID", "R2_S3_SECRET_ACCESS_KEY",
                     "R2_S3_REGION", "R2_S3_SESSION_TOKEN"):
            os.environ.pop(name, None)
        os.environ.update(R2_S3_ENDPOINT=self.endpoint + "/_s3",
                          R2_S3_ACCESS_KEY_ID=document["access_key_id"],
                          R2_S3_SECRET_ACCESS_KEY=document["secret_access_key"], R2_S3_REGION=document["region"])

    def request(self, registry, operation, body):
        request = urllib.request.Request(
            f"{self.endpoint}/_publication/{registry}/{operation}", method="POST",
            headers={"authorization": "Bearer " + self._document["coordinator_token"],
                     "content-type": "application/json"},
            data=json.dumps(body, separators=(",", ":")).encode(),
        )
        try:
            with self._opener.open(request, timeout=15) as response:
                encoded = response.read(16385)
                if len(encoded) > 16384:
                    raise GCError("publication service response exceeds 16 KiB")
            value = json.loads(encoded)
        except urllib.error.HTTPError as error:
            error.close()
            raise GCError(f"publication service {operation} failed: HTTP {error.code}") from None
        except (OSError, ValueError):
            raise GCError(f"publication service {operation} unavailable") from None
        if not isinstance(value, dict):
            raise GCError("invalid publication service response")
        return value

    def lease(self, bucket):
        return Lease(self, registry_for_bucket(bucket))


def configured():
    names = ("STUFF_COORDINATOR_URL", "STUFF_COORDINATOR_TOKEN", "STUFF_S3_ACCESS_KEY_ID", "STUFF_S3_SECRET_ACCESS_KEY")
    if any(name in os.environ for name in names):
        if not all(os.environ.get(name) for name in names):
            raise GCError("all publishing service environment credentials are required")
        gateway = os.environ.get("STUFF_S3_GATEWAY_URL")
        if gateway is not None and gateway.rstrip("/") != os.environ[names[0]].rstrip("/") + "/_s3":
            raise GCError("STUFF_S3_GATEWAY_URL must be the publishing endpoint's /_s3 route")
        return Service({"schema": 1, "endpoint": os.environ[names[0]], "coordinator_token": os.environ[names[1]],
                        "access_key_id": os.environ[names[2]], "secret_access_key": os.environ[names[3]],
                        "region": os.environ.get("STUFF_S3_REGION", "auto")})
    root = os.environ.get("STUFF_CONFIG_HOME") or os.path.join(
        os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "stuff")
    path = Path(os.environ.get("STUFF_CREDENTIAL_FILE") or os.path.join(root, "credentials.json"))
    try:
        with path.open("rb") as handle:
            metadata = os.fstat(handle.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077 or metadata.st_size > 65536:
                raise GCError("publishing credentials require an owner-only regular file of at most 64 KiB")
            value = handle.read(65537)
    except FileNotFoundError:
        if "STUFF_CREDENTIAL_FILE" in os.environ:
            raise GCError("cannot read publishing credentials") from None
        if os.environ.get("STUFF_COORDINATOR_ENABLED") == "true":
            raise GCError("publishing service credentials are required") from None
        return None
    except OSError:
        raise GCError("cannot read publishing credentials") from None
    try:
        if len(value) > 65536:
            raise ValueError()
        document = json.loads(value)
    except ValueError:
        raise GCError("invalid publishing credential JSON") from None
    return Service(document)


def registry_for_bucket(bucket):
    from r2_common import bucket_lock_path
    bucket_lock = bucket_lock_path(bucket)
    for registry in ("cargo", "npm", "pypi", "oci", "mirror"):
        try:
            result = subprocess.run([os.environ.get("STUFF", "stuff"), "lock-path", "--registry", registry],
                                    capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            raise GCError("cannot resolve registry publication lock") from None
        if result.returncode != 0:
            raise GCError("cannot resolve registry publication lock")
        if result.stdout.strip() == bucket_lock:
            return registry
    raise GCError("bucket has no configured registry publication lock")


class Lease:
    def __init__(self, service, registry):
        self.service = service
        self.registry = registry
        self._stop = threading.Event()
        self._failed = threading.Event()
        self._thread = None
        self._token = None

    def __enter__(self):
        value = self.service.request(self.registry, "gc-claim", {})
        token = value.get("token")
        if (not isinstance(token, str) or not token or len(token) > 128
                or any(not (char.isascii() and (char.isalnum() or char in "_-")) for char in token)):
            raise GCError("invalid GC lease token")
        self._token = token
        self._thread = threading.Thread(target=self._renew, name="publication-gc-renew")
        try:
            self._thread.start()
        except RuntimeError:
            self.service.request(self.registry, "abort", {"token": self._token})
            raise
        return self

    def _renew(self):
        while not self._stop.wait(60):
            try:
                self.service.request(self.registry, "renew", {"token": self._token})
            except GCError:
                self._failed.set()
                return

    def check(self):
        if self._failed.is_set():
            raise GCError("GC lease renewal failed; deletion stopped")

    def delete(self, operation, **body):
        self.check()
        result = self.service.request(self.registry, operation, dict(token=self._token, **body))
        self.check()
        return result

    def __exit__(self, error_type, error, traceback):
        self._stop.set()
        self._thread.join()
        try:
            self.service.request(self.registry, "abort", {"token": self._token})
        except GCError:
            if error_type is None:
                raise
        if error_type is None:
            self.check()
