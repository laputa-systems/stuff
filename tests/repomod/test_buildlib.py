from __future__ import annotations

import hashlib

from repomod import buildlib_pins
from repomod.rules import buildlib


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def test_vendored_shims_match_the_policy_digests() -> None:
    policy = buildlib._load_policy()
    for name, content in buildlib_pins.VENDORED_SHIMS.items():
        assert _sha256(content) in policy.bootstrap_sha256[name]


def test_vendored_wheel_identity_matches_the_policy() -> None:
    policy = buildlib._load_policy()
    assert buildlib_pins.WHEEL_URL.endswith(policy.wheel_filename)
    wheel_line = f'wheel {buildlib_pins.WHEEL_URL} {policy.wheel_sha256}'
    assert wheel_line in buildlib_pins.VENDORED_SHIMS['python.lock']


def test_vendored_shims_are_the_buildlib_0_3_0_bytes() -> None:
    assert buildlib_pins.shim_sha256('buildlib-run') == (
        'd595bbe198d93547c4c0bf98118167bba0ad046f0e07f8b505053cfedd2009df'
    )
    assert buildlib_pins.shim_sha256('python.lock') == (
        '98d595416fe3e361a2aa480144de87cd8024aed060541c0f9fba52eedfc2461f'
    )
