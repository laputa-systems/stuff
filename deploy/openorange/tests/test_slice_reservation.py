import os
from pathlib import Path
import runpy
import tempfile
import unittest

COMMANDS = runpy.run_path(str(Path(__file__).resolve().parents[1] / "bin/oo"))
oolib = COMMANDS["oolib"]


class SliceReservationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.state = self.root / "state"
        self.state.mkdir()
        self.cgroup = self.root / "cgroup"
        self.cgroup.mkdir()
        self.block = self.root / "sys/dev/block"
        self.block.mkdir(parents=True)
        device = os.stat(self.state).st_dev
        disk = self.root / "sys/devices/nvme0n1"
        partition = disk / "nvme0n1p3"
        partition.mkdir(parents=True)
        (disk / "dev").write_text("259:0\n")
        (partition / "dev").write_text(f"{os.major(device)}:{os.minor(device)}\n")
        (partition / "partition").write_text("3\n")
        (self.block / f"{os.major(device)}:{os.minor(device)}").symlink_to(partition)

    def reserved(self):
        return {f.name: f.read_text() for f in (self.cgroup / "oo.slice").iterdir()}

    def test_reserves_cpu_memory_and_whole_disk_latency_for_every_container(self):
        oolib.reserve_slice(self.state, cgroup_root=self.cgroup, sys_dev_block=self.block)
        self.assertEqual(self.reserved(), {
            "cpu.weight": "10000",
            "memory.min": str(6 << 30),
            "memory.swap.max": "0",
            "io.latency": "259:0 target=10000",
        })
        self.assertTrue(oolib.cgroup_slice("engine").startswith("/oo.slice/"))

    def test_a_state_directory_on_an_unpartitioned_disk_uses_that_disk(self):
        device = os.stat(self.state).st_dev
        link = self.block / f"{os.major(device)}:{os.minor(device)}"
        link.unlink()
        whole = self.root / "sys/devices/vda"
        whole.mkdir(parents=True)
        (whole / "dev").write_text("253:0\n")
        link.symlink_to(whole)
        oolib.reserve_slice(self.state, cgroup_root=self.cgroup, sys_dev_block=self.block)
        self.assertEqual(self.reserved()["io.latency"], "253:0 target=10000")

    def prepared(self):
        calls = []
        original = oolib.reserve_slice
        oolib.reserve_slice = lambda state: calls.append(state)
        self.addCleanup(setattr, oolib, "reserve_slice", original)
        cfg = oolib.load()
        for key in ("etc_dir", "state_dir", "run_dir", "log_dir"):
            cfg.stack[key] = str(self.root / key)
        cfg.etc.mkdir()
        return cfg, calls

    def test_prepare_reserves_the_slice_once_the_service_may_start(self):
        cfg, calls = self.prepared()
        (cfg.etc / "tunnel.env").write_text("TUNNEL_TOKEN=unused\n")
        COMMANDS["cmd_prepare"](cfg, "tunnel", None)
        self.assertEqual(calls, [cfg.state])

    def test_prepare_refuses_a_misconfigured_service_before_touching_the_host(self):
        cfg, calls = self.prepared()
        with self.assertRaises(SystemExit):
            COMMANDS["cmd_prepare"](cfg, "tunnel", None)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
