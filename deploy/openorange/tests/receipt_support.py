import hashlib
import json
import time
from pathlib import Path


def make_receipt(root, baseline, candidate, baseline_digest, candidate_digest, verdict='pass', profile='promotion', replay_exit=0):
    root = Path(root)
    evidence = root / 'evidence'
    evidence.mkdir(exist_ok=True)
    evaluator = root / 'evaluator.mjs'
    evaluator.write_text('process.exit(' + str(replay_exit) + ');\n')
    decision = {'verdict': verdict, 'reasonCodes': [], 'evaluatedAtMs': int(time.time() * 1000)}
    for name, value in {'decision.json': decision, 'policy.json': {'id': 'policy'}, 'workload.json': {'id': 'workload'}, 'ledger.json': {'entries': []}}.items():
        (evidence / name).write_text(json.dumps(value))
    sha = lambda data: hashlib.sha256(data).hexdigest()
    inputs = [{'path': p.name, 'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size} for p in sorted(evidence.iterdir())]
    receipt = {'profile': {'name': profile, 'definitionSha256': '0' * 64},
               'baseline': {'releaseId': baseline, 'artifactDigest': baseline_digest, 'components': {}},
               'candidate': {'releaseId': candidate, 'artifactDigest': candidate_digest, 'components': {}},
               'policy': {'id': 'policy', 'sha256': sha((evidence / 'policy.json').read_bytes())},
               'workload': {'id': 'workload', 'sha256': sha((evidence / 'workload.json').read_bytes())},
               'evaluator': {'name': 'statsctl verify release', 'version': '1', 'sha256': sha(evaluator.read_bytes())},
               'observations': [{'source': 'ledger', 'producer': 'test', 'releaseId': candidate, 'windowStartMs': 1, 'windowEndMs': 2}],
               'inputs': inputs, 'decision': decision, 'createdAtMs': decision['evaluatedAtMs']}
    path = root / 'receipt.json'
    path.write_text(json.dumps(receipt))
    return path, evidence, evaluator
