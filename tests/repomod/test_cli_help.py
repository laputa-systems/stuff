from __future__ import annotations

import argparse
import shlex
from collections.abc import Iterator

import pytest

from repomod.cli import OWNED_TOOL_FOOTER, _parser, main


def commands(parser: argparse.ArgumentParser) -> Iterator[argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for child in action.choices.values():
                assert isinstance(child, argparse.ArgumentParser)
                yield child
                yield from commands(child)


def test_reference_contains_every_command_option_and_example() -> None:
    parser = _parser()
    reference = parser.format_help()
    assert reference.startswith("usage: repomod")
    assert reference.index("Common options:") < reference.index("repomod status:")
    assert reference.count("show this help message and exit") == 1
    assert reference.count("Maintained by Joshua Li:") == 1
    assert reference.rstrip().endswith(OWNED_TOOL_FOOTER)
    for command in commands(parser):
        assert f"{command.prog}:" in reference
        assert f"usage: {command.prog}" in reference
        assert command.epilog is not None
        assert command.epilog.startswith("Examples:\n")
        for action in command._actions:
            if isinstance(action, (argparse._HelpAction, argparse._SubParsersAction)):
                continue
            assert action.help is not None
            assert action.help != ""
            for option in action.option_strings:
                assert option in reference
        for example in command.epilog.splitlines()[1:]:
            assert example.strip() in reference
            argv = shlex.split(example)
            assert argv[0] == "repomod"
            parser.parse_args(argv[1:])


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_every_help_page_succeeds_before_required_arguments(
    flag: str, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden() -> None:
        pytest.fail("help tried to load the live catalog")

    monkeypatch.setattr("repomod.cmd.common.default_catalog", forbidden)
    parser = _parser()
    for command in [parser, *commands(parser)]:
        argv = [*shlex.split(command.prog)[1:], flag]
        with pytest.raises(SystemExit) as raised:
            main(argv)
        assert raised.value.code == 0
        output = capsys.readouterr()
        assert output.err == ""
        assert output.out.startswith(f"usage: {command.prog}")
        if command is not parser:
            assert "Full reference: repomod -h" in output.out


def test_bare_invocation_prints_the_complete_reference(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert output.out == _parser().format_help()
