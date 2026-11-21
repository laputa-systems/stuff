import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = runpy.run_path(str(ROOT / "bin/oo"))
oolib = COMMANDS["oolib"]
sys.path.insert(0, str(ROOT / "lib"))
import oobuild

CANDIDATE = "sha256:" + "c" * 64


class EngineSelectionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.cfg = oolib.load()
        self.cfg.stack["etc_dir"] = directory.name
        self.upstream = oolib.image_ref("engine")

    def select(self, value, present=True):
        inspected = type("Result", (), {"returncode": 0 if present else 1})()
        out, err = io.StringIO(), io.StringIO()
        with patch.object(oolib, "docker", return_value=inspected), patch.object(COMMANDS["os"], "chown"), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            COMMANDS["cmd_set_engine_image"](self.cfg, [value])
        return out.getvalue().strip()

    def live_image(self):
        return oolib.run_args(self.cfg, "engine")[-1]

    def test_live_unit_runs_the_selected_image_and_upstream_restores_the_pin(self):
        self.assertEqual(self.live_image(), self.upstream)
        self.assertEqual(self.select(CANDIDATE), CANDIDATE)
        self.assertEqual(self.live_image(), CANDIDATE)
        self.assertEqual(self.select("upstream"), self.upstream)
        self.assertEqual(self.live_image(), self.upstream)
        self.assertFalse((self.cfg.etc / oolib.ENGINE_IMAGE_FILE).exists())

    def test_refuses_an_image_the_host_does_not_have_or_a_malformed_reference(self):
        for value, present in ((CANDIDATE, False), ("rivetdev/engine:latest", True), ("sha256:abc", True)):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                self.select(value, present)
        self.assertEqual(self.live_image(), self.upstream)

    def test_a_corrupt_selection_fails_closed_instead_of_running_upstream(self):
        (self.cfg.etc / oolib.ENGINE_IMAGE_FILE).write_text("latest\n")
        with self.assertRaises(oolib.ConfigError):
            self.live_image()


class EngineImageBuildTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.build = Path(directory.name)
        binary = b"patched engine"
        (self.build / "rivet-engine").write_bytes(binary)
        item = oobuild.engine_component()
        self.record = {"schema": "rivet-engine-build-record/1", "component": item["name"], "upstream": {"repository": item["upstream"], "revision": item["revision"]}, "patches": [{"file": p["file"], "sha256": "sha256:" + p["sha256"]} for p in item["patches"]], "lockfile_sha256": "sha256:" + "1" * 64, "builder": oobuild.ENGINE_BUILDER, "rustc": "release: 1.99.0\nhost: x86_64-unknown-linux-gnu", "source_date_epoch": 1, "platform": "linux-x86_64", "rustflags": "--cfg tokio_unstable", "jobs": 4, "memory_bytes": 8589934592, "binary": {"file": "rivet-engine", "sha256": "sha256:" + hashlib.sha256(binary).hexdigest()}}
        self.write_record(self.record)
        self.inside = hashlib.sha256(binary).hexdigest()
        self.commands = []

    def write_record(self, record):
        (self.build / "build-record.json").write_text(json.dumps(record))

    def runner(self, argv, cwd=None, env=None):
        self.commands.append(argv)
        if argv[:2] == ["docker", "build"]:
            context = Path(argv[-1])
            self.assertEqual(sorted(p.name for p in context.iterdir()), ["rivet-engine"])
            return CANDIDATE
        if "sha256sum" in argv:
            return f"{self.inside}  /usr/bin/rivet-engine"
        return "Rivet 3.1.1"

    def test_wraps_the_recorded_binary_in_the_pinned_upstream_image(self):
        self.assertEqual(oobuild.build_engine_image(self.build, self.runner), CANDIDATE)
        build = self.commands[0]
        pin = json.loads((ROOT / "images.lock.json").read_text())["images"]["engine"]
        self.assertIn(f"UPSTREAM={pin['repository']}@{pin['index_digest']}", build)
        self.assertIn("BUILD_RECORD_SHA256=sha256:" + hashlib.sha256((self.build / "build-record.json").read_bytes()).hexdigest(), build)
        self.assertEqual(self.commands[-1][-1], "--version")
        self.assertFalse((self.build / "image-context").exists())

    def test_rejects_a_binary_that_differs_from_its_record_before_building(self):
        (self.build / "rivet-engine").write_bytes(b"other")
        with self.assertRaises(ValueError):
            oobuild.build_engine_image(self.build, self.runner)
        self.assertEqual(self.commands, [])

    def test_rejects_a_record_built_from_a_different_patch_set(self):
        record = copy.deepcopy(self.record)
        record["patches"] = record["patches"][:-1]
        self.write_record(record)
        with self.assertRaises(ValueError):
            oobuild.build_engine_image(self.build, self.runner)
        self.assertEqual(self.commands, [])

    def test_rejects_an_image_whose_binary_differs_from_the_record(self):
        self.inside = "0" * 64
        with self.assertRaises(ValueError):
            oobuild.build_engine_image(self.build, self.runner)


if __name__ == "__main__":
    unittest.main()
