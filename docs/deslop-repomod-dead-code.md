# Repomod dead-code review

Vulture 2.16 reported eight findings in `repomod/` at `c71dee1d`, all at
60% confidence. Run it from the Stuff root with the pinned Python environment.

```sh
mkdir -p .work/tmp
TMPDIR="$PWD/.work/tmp" uvx \
  --default-index https://pypi.17166969.xyz/current/simple/ \
  --from vulture==2.16 vulture repomod tests/repomod --min-confidence 60
```

The dependency model's `Index` dataclass and `TagPredicate.describe` had
no callers in source, tests, scripts or other fleet checkouts. The snapshot
writer builds the serialized index from `IndexEntry` records. Rule selection
uses `TagPredicate.matches`. The unused class and method were removed.

The other six production findings still serve callers:

| Finding | Consumer |
| --- | --- |
| `Resolution.UNSUPPORTED` | The graph reader accepts the documented persisted `unsupported` value through `Resolution(value)`. |
| `Mark.OTHER` | The dependency weight view builds its legend from `LANGUAGES`, including the `other` key, through `Mark(language.key)`. |
| `BanMatch.EXACT` | Dependency policy loads `exact` from role configuration through `BanMatch(value)`. |
| `whitespace_split` and `commenters` in `rules/formatters.py` | `shlex` reads these attributes when the rule tokenizes formatter commands. |
| `whitespace_split` in `rules/typescript_standard.py` | `shlex` reads this attribute when the rule tokenizes TypeScript commands. |

The scan also reports pytest fixture parameters, callback parameters and
HTML parser overrides in test files. Pytest injects the fixtures by name and
the fake transports and parser call those methods through their interfaces.
The campaign's effect-boundary Tests qualification remains open.
