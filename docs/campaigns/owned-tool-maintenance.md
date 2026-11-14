# Campaign: ownership and repair of agent-facing tools

Status: in progress. Landed: the `owned-tool-support` rule, `repomod tools which|coverage`, and
`fleet/policy/owned-tools.toml` in stuff; the standing rule in usr
(`dotfiles/base/.agents/instructions/owned-tools.md`, triggered from both contracts); help footers
in stuff, repomod, usr's agent-facing utilities, kache, python-build (source only, no release), e,
fz, srv, and img. usr installs `img` from `joshuarli/img` in place of the former `rimage`, and no
longer installs the archived `laputa-systems/fs`. `uv run repomod tools coverage` lists every
remaining `gap`; tm is parked on laputa-systems/tm#28. Open: the remaining producers and the
controlled agent and release exercises.

## Mission and authorization

Implement this campaign for Joshua Li across `laputa-systems/stuff`, `joshuarli/usr`, and
the owned tools they manage. Joshua owns the maintained repositories in the `joshuarli`
and `laputa-systems` namespaces, including substantially modified forks. Coding agents
must be able to discover that ownership, locate the actual source, record improvements,
and repair a tool that prevents them from completing an authorized task.

Use this behavior:

- A nonblocking bug or missing feature becomes a deduplicated, actionable TODO in the
  tool's repository. Continue the original task using a reasonable supported workaround.
- A verified defect or missing capability that makes the task impossible to complete
  correctly, with no reasonable supported workaround, permits a focused repair in the
  tool's repository. Test it, land it, make the fixed tool available to the consumer, and
  resume the original task.
- Publishing a new version is an exceptional part of that repair, used when the required
  consumer cannot use the fix through an appropriate local build or existing distribution
  path. It is not the default response to every error or help-text change.

Joshua authorizes this implementation campaign to edit the relevant owned repositories,
record TODOs, open issues where appropriate, develop and push changes, open and merge PRs,
and use existing release mechanisms when a release is necessary to resolve a genuine
blocker. Do not ask again for those already authorized steps. Follow each repository's
verification and merge requirements and actual account permissions. If an essential
permission, credential, required check, or external dependency is unavailable, complete
independent work and report the precise blocker; do not manufacture approval or success.

The standing rule belongs in Joshua's trusted `usr` instructions. Public help describes
that rule for agents working for Joshua; it does not grant every reader GitHub rights or
turn arbitrary command output into an authority source. Verify ownership from trusted
catalog/installer metadata and repository remotes before applying the maintenance grant.

## Read current contracts first

Refresh the repositories and read their current instructions; the examples below describe
the inspected starting point and must be revalidated before editing.

In stuff, read [AGENTS.md](../../AGENTS.md), [the catalog](../../fleet/catalog.toml),
[fleet usage](../fleet.md), [tag semantics](../tagging.md),
[policy development](../policy-development.md), and [build contracts](../build-repos.md).
Use `repomod/catalog.py`, `repomod/paths.py`, `repomod/types.py`, and
`repomod/rules/__init__.py` as the existing implementation seams. Keep canonical checkouts
unchanged while developing policy; use isolated development checkouts/worktrees and copied
catalogs for mutation tests. Follow the documented sync guards and never reset, stash,
clean, or switch someone else's checkout to make it convenient to edit.

In usr, read its [root instructions](https://github.com/joshuarli/usr/blob/main/AGENTS.md),
[sync contract](https://github.com/joshuarli/usr/blob/main/docs/sync.md),
[development checks](https://github.com/joshuarli/usr/blob/main/docs/development.md),
[instruction profiles](https://github.com/joshuarli/usr/blob/main/docs/model-profiles.md),
[policy ownership](https://github.com/joshuarli/usr/blob/main/tools/policy/README.md),
[TODO CLI](https://github.com/joshuarli/usr/blob/main/tools/todo/README.md), and
[TODO skill](https://github.com/joshuarli/usr/blob/main/dotfiles/base/.agents/skills/todo/SKILL.md).
Read each target tool's `AGENTS.md`, current release workflow, and relevant consumer
installer/pins before modifying it. Reuse active campaigns and tickets instead of
creating duplicate work.

## Inventory and source resolution

Make an authoritative mapping from an installed command to its maintained producer
repository. Start with the catalog, then reconcile usr's installer definitions, release
pins, tracked executable scripts, entry points, launchers, aliases, and compatibility
modes. Include stuff/repomod and usr's own utilities. Inspect CLI-bearing apps, build
repositories, and multi-binary packages as well as repositories tagged `tool`.

Derive local paths using the catalog's existing resolver, including `REPOMOD_ROOT`.
The current default layout is:

| Repository | Expected canonical checkout |
| --- | --- |
| `joshuarli/usr` | `~/repos/usr` |
| `joshuarli/kache` | `~/repos/kache` |
| `laputa-systems/stuff` | `~/repos/laputa-systems/stuff` |
| `laputa-systems/python-build` | `~/repos/laputa-systems/python-build` |

These are expected paths, not permission to overwrite an existing directory. Resolve
the actual checkout and normalize its SSH/HTTPS origin before use. An upstream remote is
not the maintained fork. Handle renamed repositories and ambiguous duplicate basenames
explicitly; the catalog also contains an ignored former `joshuarli/python-build` entry.

Do not guess source from an executable's basename. Current usr examples include:

| Command/product | Maintained producer |
| --- | --- |
| `kache`, `kache-engine` | `joshuarli/kache` |
| `shellcheck` / shuck | `joshuarli/shck` |
| `less` | `joshuarli/lz` |
| `meson`, `ninja`, `gluon-build` | `laputa-systems/gluon` |
| `python3` and managed versioned Python commands | `laputa-systems/python-build` |
| Git commands | `laputa-systems/git-build` |
| OpenSSH and oxish distribution commands | `laputa-systems/ssh-build` |
| `ffmpeg`, `ffprobe` | `laputa-systems/ffmpeg-build` |
| `player` | `joshuarli/play` |
| usr's `todo`, `mdtool`, `pinact`, and other tracked utilities | `joshuarli/usr` |

For build distributions, distinguish the packaging/patch repository from the upstream
source repository. The owned producer is the initial triage destination; an actual
source fix may belong in another owned fork referenced by that producer. Preserve upstream
credit without directing fork-specific bugs to the wrong project.

Keep one owner for each fact. The catalog remains the curated repository inventory;
installer definitions remain authoritative for installed products. Add only missing,
typed support metadata, preferably within the existing fleet policy model. A small
`fleet/policy/owned-tools.toml` is a possible new file, not a required parallel registry.
Do not copy the entire catalog or maintain a second hand-edited alias list in usr. If
consumers need a snapshot, generate it deterministically, record its source revision,
check drift, and avoid runtime dependence on another checkout or the network.

The minimal contract needs maintained repo identity, command/product aliases, supported
help/provenance surfaces, source locations, and pointers to the existing backlog,
release, and installation procedures. Derive URLs and checkout paths where possible.
Keep upstream identity and any compatibility exceptions explicit. Prefer structured
existing metadata to an invented universal manifest or a new runtime dependency.

Provide a small structured lookup through existing tooling that can resolve ownership
even when the target executable cannot start. Unknown commands, missing checkouts, an
unrelated executable shadowing the owned tool, and unavailable provenance must produce
honest distinct results. Resolve the actual executable and its install record when
available; a banner or matching name alone is not proof of its source revision.

Account for every discovered tool in a concise coverage report: implemented, not
applicable with reason, or a concrete unresolved gap. An ignored but installed owned tool
is still relevant. Preserve unrelated `IGNORE` decisions; do not enable all fleet rules
for all archived, vendored, or intentionally ignored projects. Libraries without an
executable need accurate repository/support metadata, not a fabricated CLI.

## Agent behavior to implement

### Diagnose before filing or changing source

When a tool fails or lacks an operation needed for the task, first establish the command
and working directory, resolved executable, installed version/release revision, platform,
inputs, expected behavior, and observed error. Check help and current source instructions.
Distinguish a tool defect from incorrect usage, configuration, an outdated install,
missing credentials, transient remote failure, or a limitation of the execution host.
Correct an invocation or update a stale install when that is sufficient.

Keep diagnostics focused and redact credentials/private payloads before putting them in
a tracked ticket or public issue. Do not repeat identical failing commands indefinitely.

### Nonblocking bugs and feature requests

Use the affected tool repository's backlog, not the consuming project's TODO file.
Search existing TODOs, issues, PRs, and active campaigns first. Add evidence to an existing
record where appropriate. The current standard is repo-root `TODO.md` through `todo`:

```sh
todo list --json
todo show ABC-123 --json
todo add --json - < ticket.json
todo edit ABC-123 --json - < changes.json
todo check --json
```

The ID above is illustrative; obtain real IDs from `todo`. Use the documented fields
(`priority`, `title`, `area`, `where`, `problem`, `recommendation`, `fix_with`, `effort`,
and optional `design`). Include reproduction or a concrete missing-capability example,
installed provenance, impact on the original task, and verifiable acceptance criteria.
Use the existing design/RFC convention for details that do not fit a concise ticket.
Do not hand-edit ticket records or invent IDs. Bootstrap an absent backlog according to
the TODO contract. One integrator owns concurrent backlog updates across worktrees.

An enabled GitHub issue tracker is an authorized alternative when the repository uses
issues or a durable cross-repository discussion is needed. Avoid opening both a TODO and
an issue with identical unmanaged state. If both are required, cross-link them and name
the canonical record. Persist the finding through the repository's normal commit/push
or issue workflow; a note left only in the agent's scratch worktree is not filed work.
Record the supported workaround and continue the original task.

### Blocking defects or missing capabilities

A blocker means the original task cannot be completed correctly without repairing the
tool. A supported equivalent path may be a reasonable workaround; bypassing required
correctness checks or silently substituting incompatible behavior is not.

1. Reproduce the failure and record or reuse its ticket. State what makes it blocking.
2. Locate the verified owned repo and read its local instructions. Work in an isolated
   worktree/checkout while preserving concurrent work and the canonical checkout.
3. Make the smallest coherent fix with a regression test that exercises the original
   failure. Avoid broad refactors and unrelated dependency upgrades.
4. Run the relevant checks and all required repository gates. Inspect the actual diff,
   open a focused PR where required, and merge the exact reviewed head after its checks
   pass. Direct commits are allowed only where that repository's workflow permits them.
   A moving branch requires reviewing and validating the new head.
5. Build/install or update the consumer through its existing supported mechanism, with
   source/release provenance and checksum checks as applicable. Keep the previous working
   installation available until the replacement has passed its smoke checks. A temporary
   task-local build may establish the fix, but land the source and record any remaining
   durable distribution work; do not leave an unexplained local fork of the binary.
6. Verify the executable actually used by the blocked task, including PATH, symlinks,
   wrappers, version/revision, and any paired processes or companion binaries. Restart
   only the necessary owned service when its normal procedure requires it, respecting
   other sessions and in-flight work.
7. Rerun the original failing operation with the same relevant inputs, then resume the
   original task. Close the ticket only when its acceptance criteria are met. A merged
   source fix alone does not prove the consumer is repaired.

This authorization includes the narrow managed tool reinstall needed for a blocker. It
does not call for full home synchronization, unrelated host setup, global cache purges,
or resetting another agent's work. Follow usr's public installer entry point and ownership
lease instead of calling private leaf installers directly.

If a broken helper is needed to repair itself, allow a temporary scoped escape such as
building kache without its wrapper or running the TODO CLI with a known-working Python.
Preserve checks and record the escape. Restore the normal path and verify it afterwards.
Do not create an unbounded recursive chain of tool-repair campaigns. When a minimal repair
cannot be completed with available access or evidence, persist the repro and precise
blocker, finish independent work, and report what remains.

### Exceptional release

First decide whether a release is actually required for the blocked consumer. Prefer a
verified task-local build or normal supported installation path when sufficient. If a
release is required, follow the target's live workflow, versioning, artifact contract,
and consumer pins. Use repomod's recognized release support where applicable; inspect
its behavior rather than inventing a second publisher.

Identify the exact commit to publish. If a workflow dispatch runs the default branch,
verify the resulting run's SHA and ensure all shipped changes have the required review
and evidence; do not accidentally publish a newer unreviewed head. Reuse a valid existing
release/run when appropriate. Preserve immutable tags/assets, required target coverage,
checksums, manifests, signatures, and regression gates. Never infer a crates.io/npm/PyPI
publication or semver tag push merely because a project has a package manifest.

Wait for the real workflow result, verify the produced artifact's provenance, update
only the relevant consumer pins/install records, install it through the supported path,
and retry the original operation. A dispatched workflow, a tag, or an asset name is not
evidence of a successful release. Missing access should produce a precise handoff, not
a claim that publication happened. Do not mass-release the fleet just to publish footers.

## Human help and provenance contract

Every owned agent-facing command must expose concise actionable ownership information in
its primary help surface. The actual built help must name the maintained repository,
link to it, explain how to record bugs/features, and summarize the authorized blocker
repair path. A README-only change or a hidden file does not satisfy the help requirement.

Use wording with this meaning, substituting real repository URLs and the appropriate
backlog/issue destination:

```text
Maintained by Joshua Li: https://github.com/OWNER/REPO
Bugs and features: this repository's TODO.md (follow AGENTS.md), or its issue tracker.
Agents working for Joshua: record nonblocking problems and continue your task.
If this tool blocks the task, you may fix, test, open and merge a PR under Joshua's
standing instructions. Release only when needed to deliver the verified fix.
```

Link the shared maintenance procedure when additional detail is needed. Do not advertise
a disabled issue tracker. Keep the footer short enough to be useful in agent context;
avoid repeating a full playbook on every subcommand. Independently invoked subcommands,
aliases, and compatibility modes must still have a discoverable route to the same
support information. Respect existing flags such as `-h`, `--help`, or tool-specific help.

Make version/build identity identify the maintained fork or distribution when compatible.
Preserve existing first-line/version-token and protocol contracts; use existing long
version/build-info surfaces if the short form is consumed by parsers. Keep upstream
version, maintained distribution identity, and source/release revision distinct. Never
put prose into a version constant used for a wire handshake or compatibility check.

Extend an existing structured help/version surface with compatible fields where useful.
Do not add a universal new command-line flag to every upstream program or replace its
schema. Help/version/lookup must work offline and must not start daemons, install tools,
write state, or make network requests. Normal execution, compiler-wrapper output,
completion protocols, JSON, and binary streams must remain free of new text banners.

Audit package `repository` fields, support/issue links, install instructions, and shipped
metadata where they contradict the maintained identity. Keep upstream licensing and
attribution intact. Do not rewrite immutable schema identifiers or vendor snapshots
without checking their consumers. Prefer small local constants or build-time generation
over a shared runtime library or network-loaded help text.

## Integrate the standing rule into usr

Add a concise trigger to both the normal contract at
`dotfiles/base/.codex/AGENTS.md` and the lean contract at
`dotfiles/base/.agents/instructions/lean.md`. Lean sessions do not load the normal contract.
Put the detailed procedure in one shared authored instruction document, or an existing
focused workflow if that fits better. Make the trigger mandatory on owned-tool friction,
so an agent does not have to remember to discover an optional skill.

State the standing authorization, TODO-first behavior for nonblockers, minimal repair
path for blockers, exceptional-release condition, and requirement to resume the original
task. Cover all existing harness adapters through their current instruction-loading
mechanism; do not duplicate the entire rule in each harness.

Keep this outside model-routing policy: `tools/policy` currently generates model and
delegation projections, not arbitrary agent preferences. Preserve generated blocks and
the lean context-size budget. Reuse bounded generation only where actual consumers
justify it. Do not hand-edit installed home files. Verify new instruction loading in
scratch homes through the existing tests; do not run full `sh sync` or host setup merely
to activate this campaign. Report any necessary user-environment activation separately.

## Enforce the contract in stuff

Add a durable repomod rule, for example `owned-tool-support`, and document it in the
existing policy docs. Extend typed models and register it through the normal rule
registry. Keep checks read-only with structured, deterministically ordered findings.

The rule and coverage checks must detect:

- Missing owned command/alias mappings, incorrect maintained repository links, ambiguous
  producer resolution, stale generated metadata, and unsupported blanket exemptions.
- Missing help integration or support metadata, references to nonexistent source or test
  hooks, and a declared help footer that is never used by the actual CLI.
- Drift between maintained identity, fleet inventory, usr installation sources, and the
  relevant repo-local metadata, with explicit allowances for preserved upstream credit.
- Missing coverage for tools in forks, build repos, usr, and multi-binary distributions.

Do not inherit a generic fork exemption: those forks are a primary motivation. Keep
normal managed-repository selection separate from an inventory coverage check that can
account for ignored but installed tools without re-enabling unrelated fleet rules.
`usr` is now managed; surface any pre-existing lint debt rather than hiding it with a
broad override or expanding this campaign into an unrelated cleanup.

Normal lint must not build every tool, execute repository code to discover metadata, or
dispatch releases. Use small explicit source adapters and declarative test integration
for static checks. Verify real CLI behavior separately in the tool's focused tests/CI
against built artifacts. Metadata alone cannot prove that help actually renders it;
text anywhere in the source tree cannot count as compliance. Keep this distinction in
the reporting so an unavailable build is not called a successful smoke test.

Automatic fixers, if implemented, must return the existing bounded file plans with
narrow allowed paths, validators, and idempotent results. Use them for deterministic
edits only; language-specific wiring that cannot be proven safe remains a manual
implementation. Test fixers against local fixture repositories and fake remote APIs.
Never run live fleet `fix` while developing its own logic. Add no database, background
service, general workflow engine, or mandatory runtime dependency to the tools.

## Representative migrations and rollout

Land the shared metadata/resolution, usr instruction integration, and stuff enforcement
first, with meaningful fixtures. Then prove the contract on the following examples and
complete the remaining inventory in bounded batches. Reuse the project's existing
delegation policy; parallel lanes may own distinct repositories, with one integrator
for catalog, shared policy, and backlog changes.

### Kache

The inspected [human version handler](https://github.com/joshuarli/kache/blob/main/src/main.rs)
already prints `https://github.com/joshuarli/kache`. Reuse it rather than claiming provenance
is wholly absent. Audit `src/cli_args.rs` help and structured discovery, `Cargo.toml`,
README/support links, and their tests: several surfaces still refer to kunobi-ninja.

Keep display identity separate from the frontend/engine version handshake. usr installs
both `kache` and `kache-engine`, and its release marker records a `release-<sha>` identity
that need not match the package's semver string. Verify/install the pair coherently and
test an actual compiler-wrapper operation. Read kache's current worktree and `make check`
requirements before opening a PR.

Reconcile the [Makefile](https://github.com/joshuarli/kache/blob/main/Makefile) advice about
`make release-tag` with the actual
[dispatch-only release workflow](https://github.com/joshuarli/kache/blob/main/.github/workflows/release.yml)
before relying on it. Do not introduce a semver tag or package-registry publication just
to repair the GitHub binary distribution.

### Python-build

Inspect [the banner patch](https://github.com/laputa-systems/python-build/blob/main/patches/cpython/0006-python-build-banner.patch)
and its companion explanation. It already embeds build provenance but contains the old
`github.com/joshuarli/python-build/releases` link. Use the canonical maintained producer
`laputa-systems/python-build`; inspect actual `--help`, short/long version, REPL, and
`sys.version` behavior rather than assuming they all share one path.

Preserve the leading Python version, single-line banner shape, and platform/pydoc parsing.
Keep the full agent procedure out of `sys.version`. Use the existing targeted CPython
regression requirements and add an appropriate help test. A complete expensive interpreter
release is not required merely to land a source/help improvement; distinguish source
verification, built-artifact verification, and rollout status.

### Remaining tools

Cover usr's internal utilities and the alias examples above, then all other active owned
agent-facing tools. Include the primary help of `stuff` and repomod themselves. For a
build repository, modify the shipped product's help/provenance via its maintained patch
or configuration path, not just the build script's help. For a product without a CLI,
use its real About/support surface and record why CLI coverage is inapplicable.

Do not stop after kache and Python or declare a metadata-only pilot complete. Track any
concrete unresolved migration in the owning repository with a linked coverage entry;
do not convert ordinary remaining implementation into vague future work to save effort.

## Verification and completion

Use focused behavioral evidence and existing gates, not a fleet-wide build for every
documentation edit. Include positive and negative cases for the actual failure modes:

1. A new owned tool is detected as missing support coverage; owned forks are included;
   non-executable libraries and justified exceptions are reported correctly.
2. Alias resolution, relocated workspace roots, duplicate basenames, renamed producers,
   wrong origins, PATH shadowing, unavailable binaries, and missing checkouts behave
   predictably without executing the broken tool or modifying canonical checkouts.
3. Built primary help identifies the right maintained repo and maintenance path; existing
   short-version parsing, JSON, completion, and ordinary command output retain their
   contracts. Python banner parsing and kache's paired protocol remain compatible.
4. A controlled agent exercise in a scratch repository files or updates exactly one
   producer ticket for a nonblocker and continues the task. A blocker exercise reaches
   a tested fix and retries the original operation with the fixed executable. Record
   the observed behavior; static instruction checks cannot establish agent compliance.
5. A controlled release exercise with mocked publication uses the existing mechanism and
   verifies the workflow SHA,
   artifact identity, installation, and retry. Also prove that no release is requested
   when a supported local path suffices. Tests do not publish real releases.
6. The rule/fixers report actionable findings, remain read-only/idempotent as appropriate,
   and distinguish unavailable verification from policy violations or successful proof.
7. Both usr instruction profiles and relevant harness adapters load the standing rule,
   with their existing context-budget and scratch-home checks passing.

Use existing agents and test facilities for these exercises. Do not build a new recovery
orchestration system merely to demonstrate the standing instructions.

For stuff changes, use the relevant `tests/repomod/` cases and `make repomod-lint`, plus
the applicable documented checks. For usr changes, select checks from `docs/development.md`,
especially instruction-profile and installer tests where behavior changes. Run each
tool's required checks. Do not label skipped platform validation or inaccessible remote
checks as passing.

Commit and land coherent changes through each repository's authorized workflow. Keep
the coverage record current and finish with: exact commits/PRs, changed help examples,
the rule and lookup commands, verification results, source-versus-installed rollout
status, TODO/issue links for genuine blockers, and any release artifacts/consumer pins
changed. Include a concrete example of nonblocking filing and a complete blocker repair
flow. The intended result is that agents know where owned tools live and can turn tool
friction into durable improvements while completing the task that exposed it.
