# Repomod strict type checks

At `0d15d8ef`, `make repomod-lint` passes with ty 0.0.101 and Ruff 0.17.4.
The ty profile keeps all rules at error and ignores suppression comments
spelled `# type: ignore`. Its baseline and current scope are the repomod
component, its tests and its benchmark. The vendored fixer payload remains
outside the first-party measurement.

Measure each Ruff family with `ruff check --isolated --exclude repomod/fixers
--select FAMILY --output-format concise repomod tests/repomod bench`.

| Family | Diagnostics | Decision |
| --- | ---: | --- |
| `ANN` | 334 | Keep off. The blanket annotation rule flags working boundaries beyond the repaired contracts. |
| `ANN401` | 40 | Keep off globally. Tighten proven `Any` boundaries individually and retain checker witnesses. |
| `PGH003` | 0 | Keep ty's existing suppression policy. |
| `TC` | 257 | Retain the import policy. The inventory supplies no demonstrated defect that justifies rearranging imports. |
| `B` | 8 | Keep enabled. All eight isolated findings are deliberate attribute substitutions in `bench/deps_perf.py`, already covered by its narrow `B010` exception. |
| `RET` | 0 | Keep enabled with the existing `RET505` style exception. |

Compared with `c14465ec`, lines containing `Any`, `cast(`, `# type: ignore`
or `# ty: ignore` in first-party `repomod/` fell from 324 to 319. Count those
lines in each Git tree with `git grep -n -e Any -e 'cast(' -e 'type: ignore'
-e 'ty: ignore' REF -- repomod`, excluding `repomod/fixers/` and matching
whole-word `Any` and `cast`. This is a line count, with one line counted once.

`tests/repomod/test_deps_types.py` invokes ty on two invalid consumers. The
registry-table and build-lock lookups now require narrowing before `.strip()`.
The previous annotations accepted both uses. Existing runtime validation and
the dashboard's output contracts retain their ordinary repomod tests.
