# Catalog admission checks

The fixtures check diagnostics for invalid names, overlapping personal and
organization checkout paths in both declaration orders, and macOS case
collisions in nested checkouts. They use synthetic catalog files and temporary
directories.

At `344afebc`, mutmut 3.8.1 selected 60 identities across
`validate_identifier`, `fork_tag_error`, and `_validate_checkout_collisions`.
The original catalog tests caught 39. The added cases catch 52, with eight
survivors and zero timeouts. macOS arm64 ran the catalog suite with Python
3.15.2.

The eight surviving collision identities are `__mutmut_9`, `10`,
and `13` through `18` in `_validate_checkout_collisions`. They change
the equal case-folded path check or its diagnostic. In the current call
paths, the loader rejects case-equivalent repository IDs before checking
paths, add rejects a duplicate ID before adding it, and a single-repository
path lookup has no prior entry. The personal and organization layouts
have different path depths. No exclusion is installed.

In a fresh source snapshot, set `source_paths = ["repomod"]`,
`only_mutate = ["repomod/catalog.py"]`, `also_copy = ["fleet"]`,
`pytest_add_cli_args = ["-p", "no:parallel"]`, and
`pytest_add_cli_args_test_selection = ["tests/repomod/test_catalog.py"]`
in `[tool.mutmut]`. Run these selectors with mutmut 3.8.1.

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m mutmut run --max-children 1 \
  'repomod.catalog.x_validate_identifier__mutmut_*' \
  'repomod.catalog.x_fork_tag_error__mutmut_*' \
  'repomod.catalog.x__validate_checkout_collisions__mutmut_*'
```

Changing the prefix-overlap condition from `or` to `and` causes both
declaration-order cases to fail. Returning early after the first missing
checkout makes the nested macOS case fail. The aggregate gate remains open.
