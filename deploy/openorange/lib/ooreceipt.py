import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError()
        result[key] = value
    return result


def obj(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError()


def string(value):
    if not isinstance(value, str) or not value:
        raise ValueError()


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError()


def digest(value, prefix=''):
    if not isinstance(value, str) or not re.fullmatch(re.escape(prefix) + r'[0-9a-f]{64}', value):
        raise ValueError()


def label(value):
    string(value)
    if len(value) > 128 or any(c.isspace() for c in value):
        raise ValueError()


def release(item, keys):
    obj(item, keys)
    label(item['releaseId'])
    digest(item['artifactDigest'], 'sha256:')
    if 'components' in item:
        if not isinstance(item['components'], dict):
            raise ValueError()
        for name, value in item['components'].items():
            string(name)
            digest(value, 'sha256:')


def evidence(listed, evidence_dir, required):
    """Requires evidence_dir to hold exactly the listed files with their digests; returns name -> path."""
    if not isinstance(listed, list):
        raise ValueError()
    inputs = {}
    for item in listed:
        obj(item, 'path sha256 bytes')
        path = item['path']
        string(path)
        p = PurePosixPath(path)
        if p.is_absolute() or '..' in p.parts or str(p) != path or path in inputs:
            raise ValueError()
        digest(item['sha256']); integer(item['bytes'])
        inputs[path] = item
    if list(inputs) != sorted(inputs) or not set(required) <= inputs.keys():
        raise ValueError()
    root = Path(evidence_dir)
    if root.is_symlink() or not root.is_dir():
        raise ValueError()
    files = {}
    def walk_error(error):
        raise error
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        for name in dirs + names:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError()
            if path.is_file():
                files[path.relative_to(root).as_posix()] = path
            elif not path.is_dir():
                raise ValueError()
    if set(files) != set(inputs):
        raise ValueError()
    for name, path in files.items():
        data = path.read_bytes()
        if len(data) != inputs[name]['bytes'] or sha(data) != inputs[name]['sha256']:
            raise ValueError()
    return files


def decision(value, verdicts=None):
    obj(value, 'verdict reasonCodes evaluatedAtMs')
    string(value['verdict'])
    if (verdicts is not None and value['verdict'] not in verdicts) or not isinstance(value['reasonCodes'], list):
        raise ValueError()
    for code in value['reasonCodes']:
        string(code)
    integer(value['evaluatedAtMs'])


def verify(receipt_path, evidence_dir, evaluator_path):
    try:
        receipt = json.loads(Path(receipt_path).read_bytes(), object_pairs_hook=json_object)
        obj(receipt, 'schema profile baseline candidate policy workload evaluator observations inputs decision createdAtMs')
        if receipt['schema'] != 'stats-qualification-receipt/1':
            raise ValueError()
        obj(receipt['profile'], 'name definitionSha256')
        if receipt['profile']['name'] not in ('promotion', 'smoke'):
            raise ValueError()
        digest(receipt['profile']['definitionSha256'])
        for role in ('baseline', 'candidate'):
            release(receipt[role], 'releaseId artifactDigest components')
        for key in ('policy', 'workload'):
            obj(receipt[key], 'id sha256')
            string(receipt[key]['id'])
            digest(receipt[key]['sha256'])
        obj(receipt['evaluator'], 'name version sha256')
        if receipt['evaluator']['name'] != 'statsctl verify release':
            raise ValueError()
        string(receipt['evaluator']['version'])
        digest(receipt['evaluator']['sha256'])
        if not isinstance(receipt['observations'], list) or not receipt['observations']:
            raise ValueError()
        for item in receipt['observations']:
            obj(item, 'source producer releaseId windowStartMs windowEndMs')
            string(item['source']); string(item['producer']); label(item['releaseId'])
            integer(item['windowStartMs']); integer(item['windowEndMs'])
            if item['windowStartMs'] > item['windowEndMs']:
                raise ValueError()
        decision(receipt['decision'])
        integer(receipt['createdAtMs'])
        root = Path(evidence_dir)
        files = evidence(receipt['inputs'], root, ('policy.json', 'decision.json'))
        inputs = {item['path']: item for item in receipt['inputs']}
        if inputs['policy.json']['sha256'] != receipt['policy']['sha256'] or canonical(json.loads(files['decision.json'].read_bytes(), object_pairs_hook=json_object)) != canonical(receipt['decision']):
            raise ValueError()
        if sha(Path(evaluator_path).read_bytes()) != receipt['evaluator']['sha256']:
            return None, ['evaluator-mismatch']
        try:
            result = subprocess.run(['node', str(evaluator_path), 'verify', 'release', '--evidence', str(root), '--replay', '--json'], capture_output=True, timeout=60)
            if result.returncode != 0:
                return None, ['replay-mismatch']
        except (OSError, subprocess.TimeoutExpired):
            return None, ['replay-mismatch']
        if receipt['profile']['name'] != 'promotion':
            return None, ['profile-not-promotion']
        if receipt['decision']['verdict'] != 'pass':
            return None, receipt['decision']['reasonCodes'] or ['verdict-' + receipt['decision']['verdict']]
        return receipt, []
    except (OSError, ValueError, TypeError, KeyError):
        return None, ['invalid-evidence']


def verify_admission(receipt_path, evidence_dir):
    """Verifies a stats-app-admission/1 receipt: the exact app artifact, the runtime it requires, and passing focused checks whose logs are in the evidence."""
    try:
        receipt = json.loads(Path(receipt_path).read_bytes(), object_pairs_hook=json_object)
        obj(receipt, 'schema baseline candidate source checks inputs decision createdAtMs')
        if receipt['schema'] != 'stats-app-admission/1':
            raise ValueError()
        release(receipt['baseline'], 'releaseId artifactDigest')
        release(receipt['candidate'], 'releaseId artifactDigest components')
        if 'runtime' not in receipt['candidate']['components']:
            raise ValueError()
        obj(receipt['source'], 'repository commit')
        string(receipt['source']['repository'])
        if not isinstance(receipt['source']['commit'], str) or not re.fullmatch(r'[0-9a-f]{40}', receipt['source']['commit']):
            raise ValueError()
        if not isinstance(receipt['checks'], list) or not receipt['checks']:
            raise ValueError()
        names = set()
        for check in receipt['checks']:
            obj(check, 'name argv exitCode log')
            label(check['name'])
            if check['name'] in names or not isinstance(check['argv'], list) or not check['argv'] or type(check['exitCode']) is not int:
                raise ValueError()
            for arg in check['argv']:
                string(arg)
            string(check['log'])
            names.add(check['name'])
        decision(receipt['decision'], ('admitted', 'refused'))
        integer(receipt['createdAtMs'])
        evidence(receipt['inputs'], evidence_dir, [check['log'] for check in receipt['checks']])
        failed = ['check-failed:' + check['name'] for check in receipt['checks'] if check['exitCode'] != 0]
        if (receipt['decision']['verdict'] == 'admitted') != (not failed):
            raise ValueError()
        if failed:
            return None, failed
        return receipt, []
    except (OSError, ValueError, TypeError, KeyError):
        return None, ['invalid-evidence']
