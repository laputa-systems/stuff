"""Record verified OpenOrange activations in the private Stats service."""
import datetime
import fcntl
import http.client
import ipaddress
import json
import os
import re
import stat
import shutil
import tempfile
from pathlib import Path

import oolib


def app_for(cfg, name):
    app = cfg.apps.get(name)
    if not app or app.kind != "orange" or not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", name):
        raise oolib.ConfigError("unknown orange app")
    return app


def private_dir(path):
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700, exist_ok=True)
        sync_dir(directory.parent)
    os.chmod(path, 0o700)


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def credential(cfg, name):
    path = cfg.etc / "deploy-markers" / (name + ".json")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600:
                raise oolib.ConfigError("deployment credential must be root-owned mode 0600")
            data = stream.read(8193)
        if len(data) > 8192:
            raise ValueError()
        value = json.loads(data)
        token = value["deployToken"]
        hosts = value["hostIds"]
        if (value.get("name") != name or not isinstance(token, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,512}", token)
                or not isinstance(hosts, list) or not 1 <= len(hosts) <= 64
                or any(not isinstance(h, str) or not re.fullmatch(r"h_[0-9a-f]{32}", h) for h in hosts)
                or len(set(hosts)) != len(hosts)):
            raise ValueError()
        return token, sorted(hosts)
    except (OSError, ValueError, KeyError, TypeError):
        raise oolib.ConfigError(f"invalid or missing deployment credential for {name}") from None


def destination(cfg):
    stats = cfg.apps.get("stats")
    try:
        ip = ipaddress.ip_address(stats.ip)
        network = ipaddress.ip_network(cfg.network["subnet"])
        if ip.version != 4 or ip not in network or not 1 <= stats.port <= 65535:
            raise ValueError()
        return str(ip), stats.port
    except (AttributeError, ValueError, TypeError, KeyError):
        raise oolib.ConfigError("invalid private Stats address") from None


def send(cfg, name, token, body):
    host, port = destination(cfg)
    connection = http.client.HTTPConnection(host, port, timeout=10)
    try:
        connection.request("POST", f"/ingest/services/{name}/deployments", body,
                           {"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        response = connection.getresponse()
        status = response.status
        response.read(8193)
        if status not in (200, 201):
            raise oolib.ConfigError(f"deployment marker delivery failed (HTTP {status}); queued for sync")
    except (OSError, http.client.HTTPException):
        raise oolib.ConfigError("deployment marker delivery failed; queued for sync") from None
    finally:
        connection.close()


def drain(cfg, name, directory, token):
    delivered = directory / "delivered"
    private_dir(delivered)
    for path in sorted(directory.glob("*.json")):
        body = path.read_bytes()
        if len(body) > 8192:
            raise oolib.ConfigError("invalid queued deployment marker")
        send(cfg, name, token, body)
        os.replace(path, delivered / path.name)
        sync_dir(delivered)
        sync_dir(directory)


def record(cfg, name, expected, ready):
    app = app_for(cfg, name)
    directory = cfg.state / "deployments" / name
    private_dir(directory)
    with (directory / ".lock").open("a") as lock:
        os.chmod(directory / ".lock", 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        token, hosts = credential(cfg, name)
        selection_path = cfg.app_image_file(app)
        with selection_path.with_suffix(".image.lock").open("a") as selection_lock:
            fcntl.flock(selection_lock, fcntl.LOCK_EX)
            selected = oolib.read_app_deployment(selection_path)
            if selected.image != expected or selected.version < 1:
                raise oolib.ConfigError("selected deployment does not match expected image")
            if not ready(cfg, "app", name):
                raise oolib.ConfigError("running deployment is not healthy")
            result = oolib.docker("inspect", "oo-app-" + name, timeout=10)
            image = oolib.docker("image", "inspect", selected.image, timeout=10)
            try:
                container = json.loads(result.stdout)[0]
                image_id = json.loads(image.stdout)[0]["Id"]
                env = container["Config"]["Env"]
                versions = [e for e in env if e.startswith("RIVET_NODE_VERSION=")]
                tag = selected.image.rsplit("/", 1)[-1].rsplit(":", 1)
                if (len(tag) != 2 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}", tag[1])
                        or container["Config"]["Image"] != selected.image or container["Image"] != image_id
                        or versions != [f"RIVET_NODE_VERSION={selected.version}"]
                        or not container["State"]["Running"]):
                    raise ValueError()
                started = datetime.datetime.fromisoformat(container["State"]["StartedAt"].replace("Z", "+00:00"))
                if started.tzinfo is None:
                    raise ValueError()
                at_ms = int(started.timestamp() * 1000)
                if at_ms <= 0:
                    raise ValueError()
            except (ValueError, KeyError, TypeError, IndexError, OverflowError):
                raise oolib.ConfigError("running deployment image, version or health does not match selection") from None
            marker = f"oo-{name}-{selected.version}"
            body = json.dumps({"markerId": marker, "version": (name + "-" if name in ("stats", "stuff") else "") + tag[1], "hostIds": hosts, "atMs": at_ms}, separators=(",", ":")).encode()
            path = directory / (marker + ".json")
            delivered = directory / "delivered" / path.name
            existing = delivered if delivered.exists() else path
            if existing.exists():
                prior = json.loads(existing.read_bytes())
                current = json.loads(body)
                if any(prior[key] != current[key] for key in ("markerId", "version", "hostIds")):
                    raise oolib.ConfigError("queued deployment marker conflicts with running activation")
            else:
                fd, temporary = tempfile.mkstemp(dir=directory, prefix=".marker-")
                try:
                    with os.fdopen(fd, "wb") as out:
                        out.write(body)
                        out.flush()
                        os.fsync(out.fileno())
                    os.replace(temporary, path)
                    sync_dir(directory)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
        drain(cfg, name, directory, token)


def sync(cfg, name):
    app_for(cfg, name)
    directory = cfg.state / "deployments" / name
    private_dir(directory)
    with (directory / ".lock").open("a") as lock:
        os.chmod(directory / ".lock", 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        token, _ = credential(cfg, name)
        drain(cfg, name, directory, token)


def snapshot(cfg, out):
    target = out / "deployments"
    private_dir(target)
    source = cfg.state / "deployments"
    if not source.exists():
        return
    for directory in sorted(source.iterdir()):
        if not directory.is_dir() or not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", directory.name):
            raise oolib.ConfigError("invalid deployment state directory")
        with (directory / ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            shutil.copytree(directory, target / directory.name, ignore=shutil.ignore_patterns(".lock"))
