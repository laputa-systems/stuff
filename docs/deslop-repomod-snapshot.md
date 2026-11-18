# Repomod snapshot index mutation evidence

The dependency snapshot uses a recorded commit while a repository's inputs
and state stay the same. A full snapshot can rebuild malformed cached
metadata. A filtered snapshot must validate the existing index before writing.
[Stuff #74](https://github.com/laputa-systems/stuff/pull/74) restored full
snapshot recovery for a recorded state with the wrong JSON type.

At `b72fe3af`, serial mutmut 3.8.1 with pytest 9.2.0 and CPython 3.15.2 on
macOS arm64 classified 123 identities against the real local Git fixture.
The run took about 15 minutes. The source blob was
`43cd8a98ac999eebeb2c48bd8645b9fdd1c07c3f`.

| Region | Selected | Caught | Survived |
| --- | ---: | ---: | ---: |
| `_entries` | 23 | 23 | 0 |
| `_index_payload` | 56 | 50 | 6 |
| `_recorded_entries` | 44 | 37 | 7 |

All six targeted survivors were caught with the same source and the tests
from [#77](https://github.com/laputa-systems/stuff/pull/77) and
[#78](https://github.com/laputa-systems/stuff/pull/78):

| Region and suffix | Witness |
| --- | --- |
| `_recorded_entries` 11, 18 | Full snapshot repairs a non-object index and retains a healthy cached commit after a corrupt entry. |
| `_recorded_entries` 34, 43 | A corrupt state or commit preserves the healthy cached commit and is rebuilt with valid data. |
| `_index_payload` 16, 19 | The first filtered snapshot has the current schema. An invalid repository map is rejected before any write. |

The UTF-8 spelling changes (`_recorded_entries` 8 and `_index_payload` 14)
are codec aliases. The cast-only change (`_index_payload` 41) returns the
same value. The two filename case substitutions (`_recorded_entries` 6
and `_index_payload` 9) were caught when the pytest fixture directory was
placed on a case-sensitive HFS+ scratch volume on the same macOS host.
Before the run a lower-case probe was present and its upper-case
counterpart was absent. The volume was detached after the run.
Default encoding substitutions (`_recorded_entries` 3 and
`_index_payload` 12) also survived a run with a verified US-ASCII default
encoding. This scenario only writes canonical index records. Repository IDs
are restricted to ASCII and the other stored fields are Git object IDs,
hashes, numeric versions and closed state labels. The tracked index is
also ASCII. Within that scope the default encoding has no observable
effect. The explicit UTF-8 reads remain.

## Reproduction

Archive the source, tests, fleet data, pyproject and lock into a fresh
scratch directory. Set `TMPDIR` to its `.work/tmp`. Install the locked
development environment and mirrored mutmut 3.8.1. In the scratch
`pyproject.toml`, configure:

```toml
[tool.mutmut]
source_paths = ["repomod"]
only_mutate = ["repomod/dependencies/snapshot.py"]
also_copy = ["fleet"]
pytest_add_cli_args = ["-p", "no:parallel"]
pytest_add_cli_args_test_selection = ["tests/repomod/test_deps_snapshot.py"]
```

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m mutmut run --max-children 1 \
  'repomod.dependencies.snapshot.x__entries__mutmut_*' \
  'repomod.dependencies.snapshot.x__index_payload__mutmut_*' \
  'repomod.dependencies.snapshot.x__recorded_entries__mutmut_*'
```

Inspect the three prefixes in `mutmut results --all true`. For the follow-up,
use a fresh scratch tree with the #78 tests and replace the globs with the
six exact identities in the witness table. For the case-sensitive rerun,
point `TMPDIR` at a verified case-sensitive filesystem and select only
`_recorded_entries` 6 and `_index_payload` 9. For the default encoding
control, use `LC_ALL=C PYTHONUTF8=0 PYTHONCOERCECLOCALE=0
PYTHONIOENCODING=utf-8`, confirm `locale.getencoding()` is `US-ASCII`,
and select `_recorded_entries` 3 and `_index_payload` 12. The campaign
still needs to qualify the whole-change union and its hosted cost.
