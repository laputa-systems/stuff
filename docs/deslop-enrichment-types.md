# Enrichment table type boundary

The calibration component is `repomod/`. This slice starts from
`c14465ec50232d029a4fdbaf3588bb25fc6442aa` and changes the private
`repomod.dependencies.enrich._table` return type from `Mapping[str, Any]`
to `Mapping[object, object]`. The helper accepts arbitrary dictionaries,
so neither string keys nor usable value methods are guaranteed.

The helper retains its dictionary check and returns the original dictionary.
The cast expresses that checked boundary because ty's invariant dictionary
narrowing does not establish the generic mapping arguments. No dictionary
copy or new runtime validation is introduced. Registry configuration values
are bound once before their existing string checks so ty can narrow them.

The retained regression invokes the pinned ty checker on an invalid consumer:
`_table({"source": 123})["source"].strip()`. The original annotation accepts
that program. The candidate rejects it with one missing-attribute diagnostic
on `object`. The regression itself fails against the original source and
passes against the candidate. The existing strict checker profile is unchanged.

Run from the repository root with `TMPDIR="$PWD/.work/tmp"`:

```sh
cpu-guard --cores 2 -- uv run pytest -q tests/repomod/test_deps_types.py
cpu-guard --cores 2 -- make repomod-test
cpu-guard --cores 2 -- make repomod-lint
```

Each command uses a separately owned campaign heavy slot. The combined
candidate passes 1,428 tests with three expected skips, plus Ruff and ty.
The focused dependency checks also pass. This removes one `Any` annotation
line in `enrich.py`, leaving five lines containing `Any` or `cast`.
The necessary casts remain explicit. Other type-boundary candidates and
whole-step cost qualification remain open. No measured performance claim is
made. The table helper retains its existing check, cast and aliasing behavior.
