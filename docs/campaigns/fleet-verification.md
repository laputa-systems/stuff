# Fleet verification rollout

## Status

The rollout covers all 72 managed repositories in `fleet/catalog.toml` at `407249c6c`, including private repositories. The catalog excludes `zzz`. This record distinguishes completed changes from full repository conformance.

| Repository | Accepted evidence | Remaining proof |
| --- | --- | --- |
| `joshuarli/loc` | `f54cf9e2` scopes `make clean`. The disposable cleanup probe, 551 Change tests, benchmark parser tests, `ty` on the driver, and `make bench TIER=change WORKLOAD=count_generated_corpus` passed. [Hosted CI passed](https://github.com/joshuarli/loc/actions/runs/45063328421). | Paired workload comparisons and attribution under LOCC-2. |
| `joshuarli/nanoshop` | `d219153` preserves the hosted gate's suite selection through `make test-ci`. `make test` passed 1,258 tests, `pnpm run typecheck` passed, and `make bench WORKLOAD=browse/storied` completed five runs. The benchmark preflight, dry run, and unavailable-workload checks passed. | GitHub blocked hosted jobs before any test step with a billing or spending-limit error. NANO-48 tracks the OpenOrange benchmark path. [Hosted run](https://github.com/joshuarli/nanoshop/actions/runs/45063420766). |
| `joshuarli/img` | `1e7aca7` passed the disposable cleanup probe and `make-clean-target` lint. | Audit current test, benchmark, and type evidence. |
| `joshuarli/lz` | `338c9dd` passed the disposable cleanup probe and `make-clean-target` lint. | Audit current test, benchmark, and type evidence. |
| `laputa-systems/fz` | `77c5c53` passed the disposable cleanup probe and `make-clean-target` lint. | Audit current test, benchmark, and type evidence. |
| `laputa-systems/e` | `695942e` passed the disposable cleanup probe and `make-clean-target` lint. | Audit current test, benchmark, and type evidence. |

At rollout start, the focused repomod check flagged 46 repositories for missing `make clean` and 17 for PR test workflow conformance. It reported no retained strict-profile violations. The strict-profile result covers only repositories registered for those rules, so it is insufficient as a type audit.

## Qualify a repository

1. Inspect its current checkout, repository guidance, and [existing deslop evidence](deslop-scorecard.md). Reuse evidence when the relevant sources, configuration, fixtures, and runners still match. Record the exact revision.
2. Use the repository's native tools. Keep `make test` bounded to Change and keep Full manual. Prove that the gates exercise real required work and surface an empty selection, required skip, or timeout as incomplete. Keep coverage when a stronger test has yet to catch the same defect.
3. Verify representative benchmark selection, preflight, and completed work on one named Change workload. Record unavailable host or service requirements. Keep timing comparisons separate from workload completion and qualify them under the existing performance rules.
4. Run the configured type checker on audited boundaries. Record an actual bad program the checker rejects or an unchecked assertion the change removes. Retain the existing typing profile.
5. Verify cleanup in a disposable checkout. Create an owned output, a nested fixture with the same basename, a `.work` sentinel, and an external target set through the build environment. Run `make clean` twice. The owned output disappears and all sentinels survive. Repeat with the output path replaced by a symlink to the external target and verify the recipe refuses it.
6. Follow the default branch's rules before pushing. Record local and hosted checks independently. Continue local work when GitHub or a named runner blocks hosted evidence.

Start with small Rust tools and then apply the same evidence to other toolchains and services. Use the repo's existing tiered setup wherever it meets the [fleet quality standard](../fleet.md#quality-standard). Repomod's initial check is reproducible with `uv run repomod lint --include-private --rule make-clean-target --rule gha-test-workflow --rule strict-typing-profile`.
