from __future__ import annotations

import hashlib

from repomod import buildlib_pins
from repomod.rules import buildlib


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def test_vendored_shims_match_the_policy_digests() -> None:
    policy = buildlib._load_policy()
    for name, content in buildlib_pins.vendored_shims().items():
        assert _sha256(content) in policy.bootstrap_sha256[name]


def test_vendored_wheel_identity_matches_the_policy() -> None:
    policy = buildlib._load_policy()
    url = buildlib_pins.wheel_url()
    assert url.endswith(policy.wheel_filename)
    assert f'wheel {url} {policy.wheel_sha256}' in buildlib_pins.vendored_shims()['python.lock']


def test_approved_shim_refuses_bytes_the_policy_does_not_approve() -> None:
    assert buildlib_pins.approved_shim('python.lock', frozenset()) is None
    content = buildlib_pins.vendored_shims()['python.lock']
    assert buildlib_pins.approved_shim('python.lock', frozenset({_sha256(content)})) == content
