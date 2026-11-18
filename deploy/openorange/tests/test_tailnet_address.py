import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
commands = runpy.run_path(str(ROOT / "bin/oo"))


class TailnetAddressTests(unittest.TestCase):
    def test_local_and_foreign_addresses(self):
        self.assertTrue(commands["address_assigned"]("127.0.0.1"))
        self.assertFalse(commands["address_assigned"]("192.0.2.1"))

    def test_waits_until_tailscale_assigns_the_address(self):
        now = [0.0]
        answers = iter([False, False, True])
        self.assertTrue(commands["wait_for_address"](
            "100.68.104.43", 120, assigned=lambda _: next(answers),
            sleep=lambda s: now.__setitem__(0, now[0] + s), clock=lambda: now[0]))
        self.assertEqual(now[0], 2.0)

    def test_gives_up_at_the_deadline(self):
        now = [0.0]
        self.assertFalse(commands["wait_for_address"](
            "100.68.104.43", 5, assigned=lambda _: False,
            sleep=lambda s: now.__setitem__(0, now[0] + s), clock=lambda: now[0]))
        self.assertEqual(now[0], 5.0)


if __name__ == "__main__":
    unittest.main()
