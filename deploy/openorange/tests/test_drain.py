import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DrainTests(unittest.TestCase):
    def exercise(self, mode=(), failure=None, unchanged=False, discovery_fails=False):
        directory = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        state = root / 'running'
        services = ['oo-tunnel', 'oo-ingress', 'oo-rivet', 'oo-platform', 'oo-app.stats', 'oo-app.stuff', 'oo-identity', 'oo-engine', 'oo-store']
        state.write_text('' if mode == ('--start',) else '\n'.join(services) + '\n')
        oo = root / 'oo'
        oo.write_text('''#!/bin/sh
case "$1" in
apps-list) [ "${DISCOVERY_FAIL:-}" != 1 ] || exit 1; printf 'stats\\nstuff\\n' ;;
*-enabled) exit 0 ;;
esac
''')
        rc = root / 'rc-service'
        rc.write_text('''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
root=Path(os.environ['DRAIN_TEST_ROOT'])
path=root/'running'
services=set(path.read_text().splitlines())
name,operation=sys.argv[1:3]
if operation=='status': sys.exit(0 if name in services else 3)
with (root/'calls').open('a') as log: log.write(f'{operation} {name}\\n')
if operation=='stop':
    if name==os.environ.get('STOP_FAIL'): sys.exit(1)
    if name!=os.environ.get('STAYS_UP'): services.discard(name)
else: services.add(name)
path.write_text('\\n'.join(sorted(services))+'\\n')
''')
        oo.chmod(0o755)
        rc.chmod(0o755)
        script = root / 'drain'
        script.write_text((ROOT / 'bin/drain').read_text().replace('OO=/opt/openorange/bin/oo', f'OO={oo}'))
        env = {**os.environ, 'PATH': f'{root}:{os.environ["PATH"]}', 'DRAIN_TEST_ROOT': str(root)}
        if failure:
            env['STAYS_UP' if unchanged else 'STOP_FAIL'] = failure
        if discovery_fails:
            env['DISCOVERY_FAIL'] = '1'
        result = subprocess.run(['sh', str(script), *mode], env=env, text=True, capture_output=True)
        calls = (root / 'calls').read_text().splitlines() if (root / 'calls').exists() else []
        return result, calls, set(state.read_text().split())

    def test_stop_failure_cannot_claim_a_fence(self):
        result, calls, running = self.exercise(failure='oo-engine')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('oo-engine', running)
        self.assertIn('stop oo-store', calls)

    def test_successful_stop_that_leaves_service_running_fails(self):
        result, _, running = self.exercise(failure='oo-app.stats', unchanged=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('oo-app.stats', running)

    def test_app_discovery_failure_stops_before_any_mutation(self):
        result, calls, _ = self.exercise(discovery_fails=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])

    def test_bridge_stops_before_apps_and_engine_and_restarts_after_stats(self):
        result, calls, running = self.exercise()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(running)
        self.assertLess(calls.index('stop oo-platform'), calls.index('stop oo-app.stats'))
        self.assertLess(calls.index('stop oo-app.stats'), calls.index('stop oo-engine'))
        result, calls, _ = self.exercise(('--start',))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(calls.index('start oo-app.stats'), calls.index('start oo-platform'))
        self.assertLess(calls.index('start oo-platform'), calls.index('start oo-ingress'))

    def test_apps_only_also_stops_the_bridge(self):
        result, calls, running = self.exercise(('--apps',))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('stop oo-platform', calls)
        self.assertNotIn('stop oo-engine', calls)
        self.assertIn('oo-engine', running)


if __name__ == '__main__':
    unittest.main()
