# Dependency dashboard

`repomod deps render` writes a static dashboard that works offline once generated. Generation
reads the inventory and enrichment cache, and consults GitHub visibility, cached for an hour.
`--status` also fetches live repository status. The default output
is `.work/dependencies/dashboard/`, which is disposable and not tracked.

```sh
uv run repomod deps render
open .work/dependencies/dashboard/index.html
```

The `open` command is for macOS; on Linux, open that file in your browser.

For a local server, `make deps` syncs the checkouts, re-snapshots the tracked inventory
(committing any changes under `fleet/dependencies/v1/` and `fleet/loc/v1/`), renders the dashboard with live status,
and serves it at `http://127.0.0.1:8765` with `srv`; use `make deps PORT=9000` for another
port.

`make preview` renders the dashboard from its canonical preview dataset and serves it, with no sync,
network, or live status. The dataset in `tests/fixtures/dashboard/` is a frozen slice of the real
fleet: the inventory and line counts of 18 public repositories, the enrichment entries they
reference, their status as last collected, an earlier snapshot scripted in
`repomod/dependencies/preview.py` for the Changes page, and a fixed render time.
`tests/repomod/test_dashboard_preview.py` renders the same dataset and compares what every page
presents (title, headings, tables, list rows, tiles, navigation counts) with
`tests/fixtures/dashboard/golden.json`.
After an intended change, run `REPOMOD_UPDATE_GOLDEN=1 uv run pytest tests/repomod/test_dashboard_preview.py`
and review the golden diff. `uv run python -m repomod.dependencies.preview freeze` rebuilds the
dataset from the current fleet. `make preview-check` renders the same dataset and checks every page in
agent-browser at 390 and 1440 px: no horizontal page overflow, no empty state beside matching
rows, no panel title over its meta, and no clipped heading or link.

Private repositories are left out of every page, count, and change list by default. Repositories
says how many are hidden. Use `make deps PRIVATE=1`, or `deps render --include-private`, to include
them. Repositories the catalog no longer manages, including those marked `IGNORE`, are left out of
every page as well. Their inventory files remain until the next unfiltered `deps snapshot` deletes
them. With `--repo` or `--tag`, pages, search, counts, changes, and status include only the selected
reportable repositories. Explicit `--repo` selection includes that repository even when it is private.

The site needs no runtime data fetch, CDN, or web font, and works from `file://`. Python prepares
the pages and data. Explore renders its graph with the vendored Sigma.js and Graphology bundle
described below; the other pages use static markup and browser filters.

The pages use the CSS-only mode of `@laputa-systems/ui-dashboard`. `repomod/dependencies/ui.py`
owns the `ui-*` markup. `assets/app.css` holds only what the library lacks, built from `--ui-*`
tokens.

## Pages

The sidebar groups pages by the work they support. A page shows something only when it tells
you what to change or decide. Everything else is a counter or is left out. Package pages are the
one lookup surface, reached through search. World is the orientation page and sits under
Overview next to Explore, the interactive dependency graph.

- **To do** (`index.html`) starts with open work per repository, then groups each change once:
  **Fix now** for vulnerable packages with a clean upgrade, **Decide** for those without one,
  and **Clear in one pass** for lockfiles, pinned Python tools, fleet migrations, and all upgrades. Forks are left
  out. `triage.py` builds this list. Migrations are direct dependencies the fleet replaces
  rather than bumps: `rustix` (the laputa-systems fork, through `laputa-rustix`) and
  `oxlint-tsgolint` (Oxlint loads tsrs-lint from the `tsrs` package). They appear on To do and
  under **Migrate, don't bump** on Upgrades, never as an upgrade.
- **Repositories** ranks every owned repository in three panels, Vulnerable, Maintenance and
  Clean, one row each: its open work in words with a bar on one scale, and beside it whatever
  `repomod status` flags with `--status` (CI and workflows, releases, upstreams, pull request
  conflicts, and local checkout state). Within a panel, a repository with failing checks comes
  first. Status text shows commit ids to 12 characters, plain states (`Lint running`,
  `ci failed`), and data ages (`checked 78 min ago`). A dot carries the state, and a pulsing dot
  marks CI or a workflow that was running when the page was rendered. Forks appear only when
  they carry vulnerable versions.
- **World** (`world.html`) shows every package that owned repositories reach, split into yours,
  third-party, and owner unknown. Forks are left out. Yours means a package built inside one of
  your repositories, a package `graph.is_first_party` recognizes, or one whose source repository
  belongs to a catalog owner (`joshuarli`, `laputa-systems`). Owners come from Git and download
  URLs, Go module paths, image names, toolchain names, and the repository and homepage URLs that
  `deps enrich` caches for Cargo, npm, and PyPI packages. A package with none of these stays
  owner unknown rather than being guessed. Bars compare ownership by package and by package
  use. **Mirrored on stuff** compares the Cargo, npm, and PyPI packages in use with the stuff
  catalogs behind `fleet/registries.toml`: on stuff when every version in use is served, versions
  missing when some are not, and not on stuff otherwise. It lists the gaps by repositories
  reached. Other ecosystems and packages built inside your repositories are not counted. A
  treemap groups packages by ecosystem and owner, with area proportional to repositories reached.
  It colors cells by ownership, with lighter cells for transitive-only packages and a red outline
  for vulnerable ones, or, with the toggle, by mirror state. Each cell opens the package. The
  **How much is yours** ecosystem bars are links: each opens a collapsed list of that
  ecosystem's packages, showing the versions in use with their per-version repository counts,
  the owner, the origin, and a per-package deep link to its package section. Reach
  buckets and an owner list, with direct and transitive-only counts, repeat the charted values
  as text.
- **Explore** (`explore.html`) is the fleet dependency graph, drawn with Sigma.js on WebGL2.
  The fleet overview groups repositories by owner and shows repositories, packages, and
  aggregate edges to ecosystem clusters — each aggregate sums a repository's edges whose target
  belongs to that ecosystem (direct and transitive counts included); they are not runtime
  linkage or first-party relationships. Selecting a repository focuses its exact, directed
  project → dependency subgraph: direct edges thicker, transitive thinner, and the inspector
  reports inbound/outbound optional, conditional, declared-only, and unknown-resolution edge
  counts plus scope tallies, with the same semantics as the inventory. Colour encodes ecosystem: cargo orange, npm blue, PyPI teal,
  Go yellow, other ecosystems ghost grey; near-black nodes are the repository's projects, and
  node size tracks recorded consumer counts. Coverage errors colour a repository orange.
  The layout is deterministic: aggregate view positions clusters on a fixed grid; focused
  views lay out nodes in BFS layers from the project roots (barycenter-ordered, no physics).
  Positions are stable across selections and filter changes. Controls fit, reset, filter by
  ecosystem and by direct/transitive, and search the visible graph. Escape clears the selection
  and then returns to the fleet overview. The URL carries `repo`, `node`, `ecosystem`, and
  `relation`, so a view is bookmarkable and browser back works. The page explains the graph
  when WebGL2 is unavailable and links to Repositories, World, and Packages instead of showing
  a blank canvas. Aggregates are labelled as aggregate everywhere they appear. With JavaScript
  disabled, the page links to the same three destinations and the graph never loads.
- **Repository pages** (`repos/OWNER/REPO/index.html`) hold the repository's status with
  `--status`, then one **To do here** panel with every item in that repository, most urgent kind
  first (security, coverage with a link to the file, migrations, role conflicts, version drift,
  upgrades), each kind in compact columns. Weight and Code panels follow; Code draws the
  repository's languages with the Lines colours.
- **Security** has one card per owned repository listing its vulnerable packages. A latest
  release counts as a clean upgrade only when it is newer than the vulnerable version and has no
  advisories of its own. Forks with vulnerable versions sit in a collapsed panel.
- **Upgrades** (`outdated.html`) lists every upgrade, most repositories first, with the versions
  in use, the latest release and the repositories, in a filterable list; the panel header counts
  them by ecosystem. Upgrades are not classified by version component, because packages do not
  reliably follow semver. Needs `repomod deps enrich`. A direct dependency the fleet replaces
  appears under **Migrate, don't bump** instead of as a release bump, and is left out of the
  upgrade counts.
- **Alignment** lists version drift, one row per package, most repositories off target first,
  leaving out repositories that an upgrade to the latest release already moves. Those appear on
  Upgrades. Each row gives the target first, with a green dot, then every other version with the
  repositories to move.
  The target is the approved pin, else the newest of the upstream release and versions in use,
  else the most common ref for tags and commits. Stale release metadata never recommends a downgrade.
  Rows state when the latest release is unconfirmed. Docker images prefer the newest versioned
  tag over the most common tag and are compared by tag and digest combined
  (a bare name counts as `latest`). Alpine (apk) packages follow their base image and are left
  out.
- **Choices** lists roles where a repository must change, one row per role: the preferred option
  with how many repositories use it, then each other option, marked other or banned, with the
  repositories to move and the packages that pull it in. Compliant repositories, accepted exceptions, and settled roles are
  not listed.
- **Weight** (`weight.html`) shows which owned repositories carry the most third-party code, so you
  can choose where to slim and which dependency to drop. **By repository** draws one bar per
  repository, on one scale, largest first, with the value in text at the bar's end. Each bar stacks
  one segment per language: npm blue, Cargo vermillion, PyPI green, Go orange, and Other gray. A repository with
  no packages for the current selection has no bar: one muted line under the chart names them, and
  the table view still lists every repository. Each repository opens its direct dependencies by what
  removing one frees, then its heaviest packages: name, version, size, registry, and whether it is
  direct or transitive. **By dependency** ranks direct dependencies across repositories by the same
  measure, the top 30 shown. Removing a direct dependency frees it and the packages only it reaches.
  Bars are colored by the dependency's language; the part another counted
  direct dependency also reaches is drawn as a hatched segment of the same hue, and a package that is
  itself declared directly is never freed by removing another. Your own direct packages hold what
  they reach. Each repository keeps its 12 largest dependencies per language and filter
  combination. **Duplicate versions** lists repositories that build two versions of one package. A package counts once per repository however many lockfiles, targets, or projects
  list its version, and packages the World page classifies as yours are left out. Sizes come from
  `deps enrich`, and the page says so when none are cached.
  The sizes are not one unit, and the page states each measure: npm unpacked (installed) size,
  the compressed Cargo `.crate` archive, and a PyPI wheel download (macOS arm64, else Linux, else
  pure Python) or the sdist when there is no wheel. Go and other ecosystems report no size and
  count as size unknown. One filter row above the chart scopes everything below it:
  - **Languages**: TypeScript/JavaScript (npm), Rust (Cargo), Python (PyPI), Go, and Other, all on
    by default. Go and Other only add to the size-unknown counts.
  - **npm platform**: macOS arm64 (default), Linux x64 (musl), Linux arm64 (musl), or All platforms
    (upper bound). Lockfiles list every platform's optional binaries, such as esbuild's, which npm
    never installs on a given target. A package is left out for a platform when every edge reaching
    it is optional and its `os`, `cpu`, or `libc` lists, cached by `deps enrich`, exclude the
    platform under npm's rules: each list names the allowed values, and `!x` forbids `x`; `libc` is
    checked only on Linux. A package with any non-optional edge always counts, and platforms do not
    affect other ecosystems. All platforms counts everything, so it is an upper bound.
  - **Include dev dependencies**, off by default. A package is dev-only when no direct dependency
    with a non-dev scope reaches it. The scopes treated as dev are `dev`, `test`, `build`, and `ci`.
    Lockfiles record the transitive edges of a dev tool as `runtime`, so the page follows
    transitive edges from each direct dependency instead of reading the scope of the edge into a
    package. A package reached from both kinds of dependency counts as runtime. The inventory uses
    `dev` for npm and PyPI dev groups, and `dev` and `build` for Cargo.

  Python precomputes totals for every platform and scope, and the browser only switches between
  them, recomputing totals, bar lengths, order, the collapsed line, and package lists. The choice
  is written to the URL hash: `weight.html#lang=npm` opens TypeScript/JavaScript only,
  `#lang=npm&platform=linux-x64-musl&dev=1` adds a platform and dev dependencies, and
  `#repo=joshuarli/pi-build` opens that repository's row. Without JavaScript the page shows the
  default: every language, macOS arm64, no dev dependencies. A table view repeats the numbers.
  Each repository page links its per-language totals, for that default, to this page.
- **Coverage** has one card per fixable issue kind with the action and the repositories. Its
  **Source risk** panel has one row per kind and lists every git source, unpinned action, floating image, missing lock,
  unpinned artifact, and vendored tree, with the repositories that use it. Known limits, such as
  formats with no parser, are counts. In forks, only checkout problems count.
- **Changes** compares with `HEAD~1` of `data/`. **Needs a look** lists downgrades, changes
  whose versions cannot be ordered, source changes, and new issues; **Every change** lists each
  changed repository with every version upgraded, downgraded, added or removed, source changes,
  and new and resolved issues. The header counts each kind. It says `no baseline` when the
  previous revision has no inventory.
- **Packages** counts packages per ecosystem. Fleet-local packages are `local`; toolchains,
  downloads, system packages, service bindings, and git dependencies each have their own
  ecosystem. Search (`/`) finds any package.
  `packages.html#pkg=pkg:cargo/serde` deep-links to its versions and consumers.
- **Lines** (`lines.html`) counts lines of code by language, from
  `fleet/loc/v1`, which `repomod loc snapshot` writes from `loc --git . -o json` in each
  selected catalogued checkout. Docs (Markdown and other prose) and data and config (JSON,
  YAML, TOML, lockfiles and similar) are counted apart from code. The page ranks the fleet's
  programming languages, then draws every repository's language mix as a full-width bar with its
  size in text, then the docs and data formats; an **Every language** table keeps the exact
  files, code, comment and blank counts for lookup. A language with a package ecosystem takes
  that ecosystem's colour from Weight (Rust vermillion, TypeScript blue, Python green, Go
  orange); the two leading languages without one take sky blue and purple, and the rest are grey.
  Forks and hidden private repositories are counted into the snapshot but left out of the page's
  totals and rows. `make deps` refreshes the snapshot alongside the dependency inventory; the committed
  files record each repository's commit and `loc` version, and re-running against an unchanged
  tree writes nothing.

Charts use status colors only where color means severity, and one hue or emphasis elsewhere; weight.html and
lines.html are the exceptions, coloring bar segments by language with colorblind-safe Okabe-Ito hues. The library's categorical
series colors fail the normal-vision separation check. Hovering a mark shows
its value, and every charted value also appears as text.

## Curated roles

`fleet/dependency-roles.toml` is curated user data. Each table is a role with an `ecosystem`, an
optional `preferred` option, optional `complements`, and `options` mapping each option to the
package names that mean a repository uses it. A complement is an option that may be used
alongside the preferred one, such as `libc` next to `rustix` for calls rustix does not cover;
it is flagged only in repositories that lack the preferred option. `exceptions` maps a
repository to the reason it keeps a non-preferred option; Choices lists it with that reason
instead of flagging it. The preferred option may be an empty list, which stands for the
standard library (`stdlib = []`): it is never in use itself, so every repository that declares
any other option of the role is off preferred, and repositories that declare none are not
counted. `ban` maps an option to `exact` or `prefix`; the audit fails
repositories that depend on a banned option's crates (see [audit](audit.md)).

Repositories tagged `fork` keep upstream's dependency choices. Outdated, Alignment,
Choices, and To do leave them out; Security and Repositories list them separately with
their vulnerable versions. A package may belong to one option per role. Only direct
declarations count. `repomod deps report` lists the repositories that mix options.

## Interaction

- `/` focuses search. Search matches package names, ecosystems, and PURLs. On Explore, `/` focuses
  the atlas search, which matches repositories and ecosystems in the fleet overview and projects
  and packages inside a focused repository. `Escape` closes the dropdown, then clears the
  selection, then returns to the fleet overview.
- Filter boxes and "Show N more" narrow long lists. Every item stays visible when JavaScript
  does not run.
- On Repositories, `j` and `k` move through the rows, and `Enter` opens the selected repository.
- Copy buttons copy a command or a PURL.
- Below 720 px the navigation is one scrolling row that opens on the current page. Below 560 px
  the World treemap gives way to a note, and Explore puts its inspector, which lists every
  repository as a way into focus mode, above a shorter graph.

## Coverage and zero states

A repository with no dependencies is `complete: zero dependencies`, not blank. An unavailable
or failed checkout is marked separately. Enrichment shows `not checked` or `stale` rather than a
clean zero. Tiles show `—` when registry data is missing. Only a fresh cache entry can say there
are no known vulnerabilities.

## Refreshing

Regenerate after a snapshot, enrichment, or adapter change:

```sh
uv run repomod deps snapshot
uv run repomod deps check --strict
uv run repomod deps enrich
uv run repomod deps render
```

Enrichment checks public upstream registries for current releases, consulting configured registries
when a package is unavailable upstream. Mirrors can need refreshing before a recommended version
is installable; `audit-upgrades` continues to check the repository's configured registry.

The renderer refuses to replace a directory that lacks its `.repomod-dashboard` marker, so a
mistyped `--output` cannot delete unrelated files.

## Source and verification

The browser scripts under `repomod/dependencies/assets/` are TypeScript sources
(`app.ts`, `search.ts`, `weight.ts` — loaded only by the Weight page — and `atlas.ts`,
the Explore view controller). The adjacent `browser.d.ts` declares the globals they share
(`DEPS_INDEX`, `searchDeps`, `depsWeight`, `DEPS_ATLAS`, `AtlasVendor`). The committed
`.js` files beside them are the build artifacts emitted from those sources by
`make ts-assets`; edit the `.ts` sources and commit both together. The Explore
page loads `assets/atlas.js`, `assets/atlas.css`, a generated
`assets/atlas-data.js` (the filtered fleet projected to the graph format at render time;
regenerate by re-rendering), and `assets/vendor/atlas.vendor.js`. The vendor bundle is a
minified IIFE of pinned MIT packages (sigma 4.0.6, graphology 0.26.0, and their pinned
dependencies) built by `tools/atlas-vendor` with esbuild; the pins, license texts, and the
bundle's sha256 live in `repomod/dependencies/assets/vendor/VENDORED.md`. Rendering needs no
Node install; rebuilding the vendor bundle does (`cd tools/atlas-vendor && npm ci && npm run build`),
and so does `make ts-assets`.
The renderer copies the pinned library's base `styles.css` and `tokens.css` and the `layout.css`
and `data.css` family sheets from `crates/stuff-catalog/assets/ui-dashboard/`, refreshed from the
pinned `@laputa-systems/ui-dashboard` in `crates/stuff-worker/package.json` by `make catalog-css`.
`make deps` syncs the checkouts and re-snapshots the inventory
and line counts (committing any changes) before it renders; it does not run Node.

## Budgets and verification

The output budget is 10 MB. The initial overview-render target is 1.5 seconds.
Measure the generated fleet and the browser load when validating these targets; old fleet
sizes and timings are not current guarantees.

Measured on the current fleet (62 visible of 64 repositories, 726 projects, 3,084 components,
4,284 instances, 22,338 edges): the full render writes 75 pages totalling about 14.2 MB
(before Explore it wrote 74 pages totalling 12.3 MB), of which `assets/atlas-data.js` is
1.4 MB, the vendor bundle 0.45 MB, and the atlas controller and stylesheet 50 KB together.
Warm render is about 2.0 s (render only; the full `make deps` path was not re-measured). The
overview's load does not pay for the atlas on other pages.
Both figures breach the 10 MB budget: the pre-Explore dashboard already did (12.3 MB), and
Explore adds 1.9 MB on top; only dropping or moving dashboard output would close the gap.

The browser checks use agent-browser at 1440×900 and 390×844. They verify no console errors, no
horizontal page overflow, search for `serde`, the `#pkg=pkg:cargo/serde` route, a back link
on every repository page, and the Explore flows (fleet overview, repository focus, selection,
filters, back navigation, mobile layout). Screenshots are written under `.work/dependencies/shots/`. Tables
wider than a narrow viewport scroll inside their own container; the page itself must not
overflow. Measured on the fleet view with real data: 60 fps steady pan/zoom (p95 frame
interval 17.4 ms, max 17.5 ms), a 61 ms worst-case main-thread task entering the largest
repository's focus (2,484 transitive edges), and no long tasks switching views. Synthetic
stress scenes (see the campaign notes) show the renderer holding 60 fps at ~10k edges and
degrading to ~85–110 ms interaction frames at ~50k edges, far beyond any real repository.

## Measuring the render

`make deps` is `uv run repomod sync`, `uv run repomod deps snapshot` and
`uv run repomod loc snapshot` (committing any tracked data changes), then
`uv run repomod deps render --status` followed by `srv`. The render is the part
that varies: it reads the tracked inventory, collects live repository status, and writes the
dashboard. `bench/deps_perf.py` separates warm-cache behavior from an isolated cold run.

```sh
make bench              # live phase breakdown, cold and warm, 3 runs each
make bench-cli          # the real `uv run repomod deps render --status` command
make bench RUNS=1
make bench-list         # list isolated workloads
make bench-check        # dry selection and preflight (default: edit)
make bench TIER=edit
make bench TIER=change WORKLOAD=preview-render
```

The isolated tiered entrypoint requires the existing `uv` environment and tracked preview fixture.
`TIER` is a ceiling: `edit`, `change`, `scenario`, or `full`. `WORKLOAD` selects a named workload.
An unknown name or empty selection fails. Full requires `ALLOW_FULL=1` and is manual-only.
Scenario and Full currently add no workloads or comparison rounds. `selection` runs harness tests;
`preview-render` renders the canonical preview and checks its content against the golden fixture
before printing timing and process RSS JSON. Both take an estimated few seconds. These single-run
measurements are operability evidence, not a performance verdict. The isolated entrypoint uses no
canonical checkouts or GitHub; the default live commands above retain their existing behavior.


`warm` uses the real cache directory, as `make deps` does. `cold` points `XDG_CACHE_HOME` at a
scratch directory under `.work/tmp/` and clears it before each run, so it measures the first run
after the caches expire. The `work_*` columns sum operations that run concurrently, so they can
exceed the wall-clock `status` time; `load`, `visibility`, `status`, and `render` partition the
wall-clock `total`.
