# Campaign: Dependency Atlas MVP for make deps

**State:** Provisional; ready for an unattended execution run, **not implemented by this document**.
**Research snapshot:** 2026-11-14. Starting observed stuff/main: 64b06213e8b8d0d2c2505b1ee2ef1f2de692216f; re-read HEAD and rebase these assumptions before implementation.
**Owner review gate:** The first genuinely usable web design is the terminal deliverable. **STOP after MVP** and return screenshots, a local preview link/command, metrics, and a handoff. Do not continue into a second design iteration without a fresh user request.

## Mission

Add a **dependency-only**, interactive, GPU-accelerated network visualization to the existing static dependency dashboard opened by `make deps`. Integrate it as an **Explore** navigation page at `explore.html`. This is a way to see **actual dependency relationships** throughout the repository fleet at a glance, then focus on a repository and follow its direct and transitive package relationships. The goal is a beautiful and fast, CodeCanvas-like *dependency atlas*, **not** a code editor or a source browser.

Use the existing graph inventory and enrichment. Prioritize a crisp, minimal web experience worthy of design review over speculative completeness. Implement the minimum coherent product, prove it works, commit the changes, and stop.

This is a campaign for an agent to execute **when invoked**. The document itself is not evidence the MVP exists.

## Verified starting point / contract owners

Read current `AGENTS.md`, `docs/fleet.md`, `docs/dependency-dashboard.md`, `docs/dependency-inventory.md`, `Makefile`, `docs/campaigns/`, and the applicable tests before coding. Read `fleet/catalog.toml` without editing curated entries.

- `make deps` currently syncs repositories, refreshes Git-tracked `fleet/dependencies/v1` and `fleet/loc/v1` (and **can auto-commit their changes**), renders the static site, and serves it using `srv` on port 8765.
- `repomod/cmd/deps.py` already filters out private, ignored/unmanaged, and unselected repositories **before** `repomod.dependencies.render.render`; explicit private inclusion is opt-in. Never render the unfiltered `built` graph for this feature.
- `repomod/dependencies/graph.py` has `Graph` with projects, instances, components, typed directed edges, and per-repository edge scope. `repomod/dependencies/model.py` models source kind, resolution, optionality, condition, scope, and direct/transitive relationship. Reuse these, do not replace dependency extraction.
- `repomod/dependencies/render.py` owns page generation, navigation, static assets, and the output marker safety contract. `repomod/dependencies/ui.py` and the copied pinned `@laputa-systems/ui-dashboard` CSS own the established visual system.
- `repomod/dependencies/world.py`, `weight.py`, `insights.py` and `analysis.py` already implement package ownership, reach, importance, weight, and consumers. Reuse exact existing semantics where relevant.
- `tests/repomod/test_deps_render.py` includes XSS, offline/no-fetch, asset, navigation, and zero/unknown tests; `test_deps_privacy.py` covers secret-bearing dependency URLs.
- A freshly inspected `fleet/dependencies/v1/index.json` contains 64 repositories, but that number is not a fixed contract. Measure the current fleet instead of assuming its size.
- The dashboard works from `file://` without a running API, CDN, webfont, or chart library. Dashboard generation should remain network-free; the existing dashboard target is 10 MB of output and ~1.5 seconds for initial overview rendering. Record the pre-change baseline and deltas.

Do not touch the registry publishing subsystem, OpenOrange deployment, catalog formats, loc snapshots, repo policy, or release workflow for this campaign.

## Research and engine decision (provisional, bounded)

**Default MVP engine: Sigma.js v4 + Graphology (WebGL2).** As of research, Sigma 4.0.6 and Graphology 0.26.0 are MIT and actively supported. Sigma v4 draws nodes, edges, curved paths and SDF labels on the GPU, with GPU picking, interaction, and declarative styling. It is an excellent fit for a **readable graph with a stable layout**, not a permanently animated physics demo.

References:
- Sigma: https://github.com/jacomyal/sigma.js ; docs https://www.sigmajs.org/concepts/rendering/ ; v4 migration https://www.sigmajs.org/how-to/technical/migration-v3-v4/ ; package https://www.npmjs.com/package/sigma
- Graphology: https://github.com/graphology/graphology ; https://www.npmjs.com/package/graphology

**Single fallback only: @cosmos.gl/graph v3**, currently 3.5.1, MIT, https://github.com/cosmosgl/graph . It has a compelling GPU-based large-graph rendering and physics pipeline, flat typed-array input, and scale claims of hundreds of thousands of links. Its luma.gl peers and reliance on force-simulation paradigms may cost extra complexity for the small, deterministic first view; review its pinned WebGL2 compatibility and actual peer versions before adopting.

**Not selected:** CodeFlow and sprawlens are useful UX/layout references, not the highest-confidence large-scale GPU renderer. GPUI, iced_nodegraph, wgpu, and Rust renderers add unnecessary native ownership for a browser dashboard. Cytoscape.js is mature and MIT but its conventional Canvas renderer is not the first choice for this GPU-first requirement. GitNexus has a PolyForm Noncommercial license, so is not an unrestricted OSS foundation.

**Decision protocol:** Begin with a short Sigma spike on **real filtered fleet data**, including focus, selection, 2-level visibility and labels. Measure before refactoring. Switch to cosmos.gl **only if a reproduced material blocker** (correctness, label readability, browser support or measured responsiveness) cannot be repaired through public Sigma APIs within one bounded attempt. Keep a short factual decision record in this document or the MVP handoff. Never start a third engine comparison, vendor a new renderer, modify upstream renderer internals, or write bespoke GLSL/WGSL. No generalized benchmark framework.

Prefer pinned, self-hosted **browser-ready vendor bundles**, including upstream MIT notices, versions, provenance/sha256 recorded in an asset manifest or comment. If a build step is actually needed, use a tiny **build-only** TypeScript/npm/pnpm workspace with locked versions and checked-in compiled browser artifacts; there must be **no Node/pnpm dependency at dashboard-render time**. Don't add React, a client app framework, a new API/server, a charting framework, or arbitrary polyfills. Check that the pinned Sigma v4 browser bundle and Graphology bundle actually load together; do not assume v3 config/extension APIs. Never load code from CDNs at runtime.

## Scope and core interaction contract

### Dependency semantics

The only authoritative data comes from the **already filtered** `Graph` and optional existing enrichment; no static source-code analysis. Keep node/edge kinds explicit and typed:

1. Repository identity = owner/repository. Project identity is repository-scoped.
2. Package *component* identity (PURL) is different from a resolved *instance* identity (source, version, context). Do not collapse multiple versions into one exact instance or confuse same-named packages across ecosystems.
3. A **direct** edge is a project declaration; **transitive** edges connect the exact instances the inventory reports. Never draw a fake direct repo→transitive-package relationship, nor a speculative repo→repo arrow merely because two projects share a dependency.
4. Aggregated edges are permitted at overview level only when **explicitly marked as aggregate**, with an accurate count and underlying exact edge IDs/relation types recoverable in the repository focus. Do not interpret shared dependencies as a runtime linkage or first-party source dependency.
5. Preserve and expose resolution (resolved/declared-only/unknown), scope (runtime/dev/build/CI/etc.), optionality, conditions, provenance/source kind, and coverage issues when available. Unknown is **not** zero or verified clean.
6. Multiple repositories can reach one package, but adjacency and traversal must remain repository-scoped where the underlying inventory's edges are repository-scoped. Prevent cross-repo phantom paths by joining on a global instance ID without context.
7. Links into existing `repos/OWNER/REPO/index.html` and `packages.html#pkg=...` must be canonical, escaped, privacy-safe, and navigate normally; never take an arbitrary package URL as executable HTML or script.

**MVP UI (one page, not a dashboard rewrite):**

- New **Explore** entry in the existing **Overview** navigation group, alongside World. Preserve World, To do, Weight, Packages, and all other pages, links, existing search, and their styles.
- A generous, responsive graph viewport, calm background, subtle grouping and restrained strokes/labels consistent with existing `ui-dashboard` tokens. No game-like 3D, glow, gaudy particle effects, constant layout motion, or decorative chrome.
- **Fleet overview (initial view):** repository nodes organized by the existing owner/ecosystem classifications. Show meaningful *aggregate* dependency connections or counts to ecosystem clusters, not thousands of hairline edges. Show the number of repositories/packages and the selection/coverage state. A clean overview is more important than every edge being visible at once.
- **Repository focus (click or search):** draw the actual directed project → direct dependency → transitive dependency subgraph, using the existing inventory. It must be possible to inspect a selected node's immediate incoming/outgoing neighbors and its true consumers, and to reach the existing repository/package detail pages. Highlight selected relationships and de-emphasize unrelated ones.
- **Two bounded semantic-detail levels**, not a new rendering engine: at low zoom show clusters, meaningful labels and no full-edge hairball; at higher zoom reveal focused packages and edge detail. Stable coordinates across minor selection/filter changes. Pan/zoom-to-cursor, fit/reset, click focus, Escape/back, selection and hover, lightweight search, ecosystem filter, and a clear direct/transitive toggle. Controls must actually work and be keyboard-operable where meaningful.
- When zoom alone would change the graph's meaning, require a deliberate focus action instead; don't surprise users with edges appearing to imply new relationships. Label the aggregate vs exact state plainly.
- Minimal inspector in the existing visual language, with type, version/source if known, exact edge/scope, in/out degree/consumer count and appropriate existing-page link. Not an embedded code window.
- Shareable URL state for selected repo, node and filters (stable, encoded, bounded input), with useful browser back behavior. No full client router.
- Mobile (390px): scroll-free horizontal page, graph gets the available width, inspector becomes stacked or collapsible, controls do not cover graph/pick targets. A desktop screenshot at 1440×900 must look intentional.

**Explicitly out of scope:** source files/symbols, source-code panes, AST/tree-sitter, LSP, call graphs, co-change/semantic similarity, real-time agent activity, git-history animation, graph editing, CI/release dashboard overhaul, new remote endpoints, new databases, collaborative features, production hosting, custom GPU shaders, Rust renderer, general graph visualization SDK, or a phase-2 redesign.

### Performance and data architecture

- Treat **dependency extraction as completed**. Add a small, versioned, deterministic projection from the filtered `Graph` into the view's nodes/edges/aggregates; one owner for semantics, no duplicate inventory. Keep the adapter separate from `ui.py` and from the rendering engine (e.g., `repomod/dependencies/atlas.py`), but don't build a framework.
- Prefer compact JSON-like data as sorted tuples/dictionaries over verbose repeated objects. Generate a local JS data asset safely (or segmented JS assets if needed) so `file://` works with **no fetch/XHR**; use DOM-script injection rather than file-origin fetch if lazily loading chunks. JSON-in-JS must escape `<`, U+2028, U+2029, quotes, and hostile PURLs; no raw unsafe interpolation. No secret-bearing fields beyond the existing sanitized inventory.
- Keep stable graph IDs independent of display labels and deterministic node order. Favor a **library-provided** existing layout (Graphology's layout helpers / bounded ForceAtlas2 on a selected subgraph) or a trivial stable grid/ring grouping of clusters over a custom physics solver. Seed or persist positions where feasible so identical inputs generate identical coordinates. Run expensive layout only on graph changes and freeze it when idle.
- Compute/reduce overview clusters **before** uploading graph data. Do not render every transitive edge in the default fleet scene. Reuse Sigma's GPU rendering, picking, styles/label thresholds, and graph updates. Implement only minimal view-model transformations and event handlers.
- Initialize/render the heavy visualization only on Explore; other existing dashboard pages must not pay its JavaScript/GPU cost. Disable simulation/animation when the graph is idle. Context loss or absent WebGL2 should show an honest explanation plus existing **Repositories**, **World**, and **Packages** links, never a blank canvas or a false 'zero dependencies'.
- No network requests from rendering, no runtime CDN/fonts, no private-data leakage through hidden graph nodes or search indexes, no persistent writable client cache. Build artifacts should be deterministic and small; keep the dashboard's **10 MB total output budget** and measure the existing **1.5 s overview render target** rather than quietly increasing either.
- UI must never use unbounded graph traversal, quadratic edge enumeration or repeated per-frame full graph copies. Guard unknown/empty/malformed data and cap focus/neighbor expansion; indicate visible/collapsed counts rather than silently truncating.

## Unattended execution sequence (one writer; commit each green slice)

**Authority:** User authorized an unattended MVP and direct commits to stuff. Follow the repository's actual branch protection/CI contract; commit directly to main when permitted, otherwise create/merge the smallest compliant PR. This does **not** authorize production deployments, publication, changes to other repositories, or extending past the MVP. Work from a fresh clone or isolated development checkout; preserve other agents' branches, the canonical checkouts and all uncommitted work. `make deps` itself can auto-commit refreshed inventories, so inspect its side effects and do not run it casually against the owner's canonical working tree. For tests, prefer a fixture/isolated checkout and `uv run repomod deps render` first.

**S0 — baseline + bounded engine spike (no architecture detours).**
- Record current HEAD, output bytes, baseline `uv run repomod deps render` timing, visible repository/package/project/instance/edge counts, privacy selection, and browser assumptions. Record Sigma v4 + Graphology versions, MIT notices, shipping bundle sizes, browser entrypoint viability, and pinned hashes. Evaluate actual client graph construction and label/selection interaction on filtered fleet data in a scratch preview.
- If Sigma has a material blocker, document a short reproducer and **at most one** cosmos.gl comparison before deciding. No arbitrary multi-library bake-off. Refuse to invent graph benchmark results.
- Acceptance: written engine rationale, working local proof with real graph semantics, and a crisp initial UI sketch/state contract. Move on without asking the user to pick a library.

**S1 — authoritative data projection and safety.**
- Add an atlas serialization/projection module consuming the exact same visible graph the dashboard renders. Add clear aggregates for overview, exact repository-focused edges, typed stable IDs, deterministic sorting, unknown/coverage representation, and metadata links.
- Preserve existing `render` marker/symlink protections and no-fetch generation; do not change inventory schemas. Include tests for cross-repo shared-instance false paths, multiple package versions, optional/transitive scopes, hostile label/PURL injection, missing/unknown versus empty, ignored/unmanaged/private exclusions, and explicit private inclusion.
- Acceptance: deterministic fixture bytes, no cross-view privacy drift, direct/indirect edge truth, zero new extractor/network calls.

**S2 — GPU page and interaction.**
- Add `explore.html` through the existing dashboard renderer and a nav entry in Overview. Ship locally vendored pinned MIT browser assets, including license/provenance, and the smallest graph-view JS/CSS; do not introduce a runtime bundler or new backend. Keep current pages unchanged.
- Implement the initial fleet aggregate view, focused real dependency graph, fit/pan/zoom, selection and highlighted adjacency, search, ecosystem/direct/transitive filters, inspector and links, bookmarkable state, keyboard/back navigation, and mobile layout. Library handles GPU drawing, picking, labels, and graph management; keep first-party code as data transformation and UI coordination.
- Acceptance: render opens both via `file://.../explore.html` and `http://127.0.0.1:8765/explore.html`, works offline, shows understandable meaning for every edge, and has no browser console errors or layout overflow at 1440×900 / 390×844.

**S3 — evidence, polish only to acceptance, and HARD STOP.**
- Run focused `uv run --group dev pytest tests/repomod/test_deps_render.py tests/repomod/test_deps_graph.py tests/repomod/test_deps_privacy.py` plus any new tests, `make repomod-lint`, and the relevant existing dashboard browser checks; do not needlessly run full registry or OCI suites. Record unsupported checks as unsupported, not passing.
- On an isolated, safe workspace validate the full `make deps` path **after** checking its sync/commit behavior; otherwise reproduce its exact render/serve path without touching canonical checkouts, and explain the limitation.
- Use a browser automation harness, ideally agent-browser, to test navigation, search, selection, zoom, labels, mobile layout, zero/unknown states, browser back and a real graph with shared dependencies. Capture actual screenshots under `.work/dependencies/shots/` for desktop and mobile (do not commit these generated artifacts unless a review workflow requires it). Attach or provide their accessible paths in the final handoff.
- Measure cold and warm render wall time; total dashboard bytes; browser startup time; p50/p95 pan/zoom frame durations; responsive focus latency; longest main-thread stalls; and GPU/CPU/memory observations if available. Use **real fleet** and two documented synthetic **10k/50k edges** stress scenes (not 10k/50k invented dependency relationships), with actual test hardware and graph counts stated. Target real-fleet p95 frame interval ≤33 ms and no repeatable >200 ms interaction stalls on the test machine. Synthetic runs are **diagnostic**, not a license to implement a new renderer. The dashboard output must stay ≤10 MB and the 1.5s overview render target must not regress materially from its measured baseline; explicitly flag any violation with numbers.
- Fix small in-scope bugs needed to make MVP demonstrably correct, readable and responsive. If the chosen library cannot meet the core experience, use the bounded S0 fallback; if that also fails, report a reproducible blocker instead of claiming success.
- Commit the validated MVP, update `docs/dependency-dashboard.md` with Explore use/semantics/engine/offline instructions and actual performance observations, and mark this campaign **MVP ready for design review** with commit SHA(s) and evidence. **Stop all feature development at this point**. Do not start source-code visualization, another frontend, a renderer rewrite, a redesign round, or any 'next improvements' campaign without an explicit new request.

## MVP review handoff (required, then terminate)

Return a concise report containing:

1. HEAD/commit links, which slices landed, chosen engine and pinned versions, whether the actual `make deps` path was verified, and the exact way to launch/open `explore.html`.
2. 1440×900 and 390×844 **real screenshots** and a short walkthrough: fleet → focused repository → selected dependency → existing package/repository page. Show at least one directed transitive path and identify aggregate versus exact edges.
3. Test pass/fail/skip list, measured dataset sizes, render/page-size/interaction metrics, whether the old dashboard remains unchanged, and any known limits (including offline/WebGL2 support).
4. A clear request for **web-design review**, offering at most a few concrete design choices; do not autonomously act on them.

**Definition of done:** Existing make-deps dashboard + a genuinely useful, accurate, readable, GPU-backed dependency Explore page; no code/source views; no unapproved side effects; review evidence and clear stop. A research-only spike, an empty mockup, or a pretty but fabricated dependency network is **not** the MVP.

## Operating discipline

Keep a single writer/integrator and tackle S0→S3 serially. For each slice, implement the smallest verified change, run its focused tests, inspect the diff, commit only green work, then move on without requiring routine confirmations. Diagnose a failing test from concrete evidence; after three genuine failed fixes or unavailable prerequisites, park the failed slice with precise reproduction and continue only independent safe work. Do not hide regressions by relaxing tests or exceptions. Re-read source and current upstream API on resume. Do not broaden authorization to external services or mutate other repositories. The owner explicitly requested **MVP and then human design review**, not a perpetual hill-climb.
