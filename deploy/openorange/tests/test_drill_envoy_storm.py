import struct
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
drill = runpy.run_path(str(ROOT / "bin/drill-envoy-storm"))


class LogCountTests(unittest.TestCase):
    def test_counts_refusals_and_each_disconnect_write_attempt(self):
        text = "\n".join([
            "warn refusing envoy connect that storage could not register; the envoy reconnects",
            "debug retrying envoy disconnect write",
            "debug retrying envoy disconnect write",
            "warn envoy disconnect write failed; readers treat the record as disconnected",
            "info unrelated line",
        ])
        self.assertEqual(drill["count_log"](text), {
            "refused_connects": 1,
            "disconnect_writes": 3,
            "disconnect_retries": 2,
            "disconnect_failures": 1,
        })

    def test_an_empty_log_counts_nothing(self):
        self.assertEqual(drill["count_log"](""), {
            "refused_connects": 0,
            "disconnect_writes": 0,
            "disconnect_retries": 0,
            "disconnect_failures": 0,
        })

    def test_per_refusal_is_none_without_refusals(self):
        self.assertIsNone(drill["per_refusal"](0, 0))
        self.assertEqual(drill["per_refusal"](2, 4), 0.5)


class FrameTests(unittest.TestCase):
    def test_metadata_is_the_empty_init_union_body(self):
        self.assertEqual(drill["encode_metadata"](), b"\x00\x00\x00")

    def test_pong_is_a_little_endian_i64_tagged_union(self):
        self.assertEqual(drill["encode_pong"](-2), b"\x04" + struct.pack("<q", -2))

    def test_close_reason_is_parsed_from_the_close_frame(self):
        self.assertEqual(
            drill["parse_close"](b"\x03\xf5envoy.connect_unavailable"),
            (1013, "envoy.connect_unavailable"),
        )

    def test_a_short_close_frame_has_no_code(self):
        self.assertEqual(drill["parse_close"](b""), (1005, ""))


class VerdictTests(unittest.TestCase):
    def result(self, kind, refusals, writes, drain=1.0, quiesce=1.0):
        return {
            "kind": kind,
            "refused_connects": refusals,
            "disconnect_writes": writes,
            "drain_seconds": drain,
            "quiesce_seconds": quiesce,
        }

    def test_candidate_zero_and_upstream_at_least_one_per_refusal_pass(self):
        ok, candidate, upstream = drill["verdict"](self.result("candidate", 10, 0), self.result("upstream", 10, 10))
        self.assertTrue(ok)
        self.assertTrue(candidate)
        self.assertTrue(upstream)

    def test_candidate_disconnect_write_fails_the_verdict(self):
        ok, candidate, _ = drill["verdict"](self.result("candidate", 10, 1), self.result("upstream", 10, 10))
        self.assertFalse(ok)
        self.assertFalse(candidate)

    def test_upstream_below_one_per_refusal_fails_the_verdict(self):
        ok, _, upstream = drill["verdict"](self.result("candidate", 10, 0), self.result("upstream", 10, 9))
        self.assertFalse(ok)
        self.assertFalse(upstream)

    def test_no_refusals_or_no_drain_fails_both_sides(self):
        self.assertFalse(drill["verdict"](self.result("candidate", 0, 0), self.result("upstream", 10, 10))[0])
        self.assertFalse(drill["verdict"](self.result("candidate", 10, 0, None), self.result("upstream", 10, 10, None))[0])
        self.assertFalse(drill["verdict"](self.result("candidate", 10, 0, 1.0, None), self.result("upstream", 10, 10, 1.0, None))[0])


class ConfigTests(unittest.TestCase):
    def test_engine_config_points_object_storage_at_the_private_store(self):
        config = drill["engine_config"]("bucket-a", "172.31.150.10")
        self.assertEqual(config["object_storage"]["primary"]["s3"]["bucket"], "bucket-a")
        self.assertEqual(
            config["object_storage"]["primary"]["s3"]["endpoint"],
            "http://172.31.150.10:7070",
        )
        self.assertFalse(config["storage"]["balancing"]["enabled"])


if __name__ == "__main__":
    unittest.main()
