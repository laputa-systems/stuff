from pathlib import Path
import runpy
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = runpy.run_path(str(ROOT / "bin/oo"))
oolib = COMMANDS["oolib"]


class EngineLimitTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.etc = directory.name

    def config(self, engine=None):
        raw = tomllib.loads((ROOT / "apps.toml").read_text())
        if engine is not None:
            raw["engine"] = engine
        cfg = oolib.validate(raw)
        cfg.stack["etc_dir"] = self.etc
        return cfg

    def engine_args(self, cfg):
        return oolib.run_args(cfg, "engine")

    def without_limits(self, args):
        args = list(args)
        for flag in ("--cpus", "--memory"):
            if flag in args:
                index = args.index(flag)
                del args[index:index + 2]
        return args

    def test_engine_limits_are_added_when_set_and_absent_by_default(self):
        default = self.engine_args(self.config())
        for flag in ("--cpus", "--memory"):
            self.assertNotIn(flag, default)

        limited = self.engine_args(self.config({"cpus": 4.0, "memory": "3g"}))
        self.assertEqual(limited[limited.index("--cpus") + 1], "4.0")
        self.assertEqual(limited[limited.index("--memory") + 1], "3g")
        self.assertEqual(self.without_limits(limited), default)

    def test_engine_limits_reject_invalid_values(self):
        for engine in ({"cpus": 0}, {"cpus": -1.0}, {"cpus": True}, {"cpus": "4"},
                       {"memory": "3 g"}, {"memory": "0g"}, {"memory": 3}, {"other": 1}):
            with self.subTest(engine=engine), self.assertRaises(oolib.ConfigError):
                self.config(engine)


if __name__ == "__main__":
    unittest.main()
