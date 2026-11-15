"use strict";
(() => {
    const foundCanvas = document.getElementById("atlas-graph");
    if (foundCanvas === null) {
        return;
    }
    const canvas = foundCanvas;
    const loading = document.getElementById("atlas-loading");
    const fallback = document.getElementById("atlas-fallback");
    const empty = document.getElementById("atlas-empty");
    const inspector = document.getElementById("atlas-inspector");
    const caption = document.getElementById("atlas-caption");
    const searchInput = document.getElementById("atlas-search");
    const resultsBox = document.getElementById("atlas-search-results");
    const ecosystemSelect = document.getElementById("atlas-ecosystem");
    const relationToggle = document.getElementById("atlas-relation");
    const fitButton = document.getElementById("atlas-fit");
    const resetButton = document.getElementById("atlas-reset");
    const fleetButton = document.getElementById("atlas-fleet");
    const atlasData = window.DEPS_ATLAS;
    function fail(message) {
        if (loading !== null) {
            loading.hidden = true;
        }
        canvas.hidden = true;
        if (fallback !== null) {
            fallback.hidden = false;
            if (message) {
                fallback.dataset.reason = message;
            }
        }
    }
    if (atlasData === undefined || atlasData === null || atlasData.v !== 1) {
        fail("data");
        return;
    }
    const data = atlasData;
    const vendor = window.AtlasVendor;
    if (vendor === undefined || vendor === null) {
        fail("assets");
        return;
    }
    let probe = null;
    try {
        probe = document.createElement("canvas").getContext("webgl2");
    }
    catch {
        probe = null;
    }
    if (probe === null) {
        fail("webgl2");
        return;
    }
    const { Graph, Sigma, pathLine, extremityArrow, layerPlain } = vendor;
    const summary = data.summary;
    const ecosystems = data.ecosystems;
    const scopes = data.scopes;
    const relations = data.relations;
    const resolutions = data.resolutions;
    const sourceKinds = data.source_kinds;
    const strings = data.strings;
    const components = data.components.map((row) => ({
        purl: row[0],
        ecosystem: row[1],
        name: row[2],
        display: row[3],
    }));
    const instances = data.instances.map((row) => ({
        id: row[0],
        component: row[1],
        version: row[2],
        source: row[3],
        firstParty: row[4] === 1,
        consumers: row[5],
    }));
    const repos = data.repositories;
    const repoByName = new Map(repos.map((repo) => [repo.n, repo]));
    const ownerOf = (name) => name.split("/", 1)[0];
    const owners = [...new Set(repos.map((repo) => ownerOf(repo.n)))].sort();
    const ECOSYSTEM_COLORS = {
        cargo: "#d55e00",
        npm: "#2a78d6",
        pypi: "#009e73",
        golang: "#e69f00",
    };
    const OTHER_COLOR = "#9a9992";
    const PROJECT_COLOR = "#1c1c1a";
    const EDGE_COLOR = "#8f8e87";
    const OUTGOING_COLOR = "#2a78d6";
    const INCOMING_COLOR = "#d6570f";
    const ecoColor = (index) => ECOSYSTEM_COLORS[ecosystems[index]] ?? OTHER_COLOR;
    const maxConsumers = instances.reduce((top, item) => Math.max(top, item.consumers), 1);
    if (repos.length === 0) {
        canvas.hidden = true;
        if (loading !== null) {
            loading.hidden = true;
        }
        if (empty !== null) {
            empty.hidden = false;
        }
        if (caption !== null) {
            caption.textContent = "No repositories are visible in this inventory.";
        }
        if (inspector !== null) {
            inspector.textContent = "";
            const title = document.createElement("h2");
            title.className = "atlas-inspector-title";
            title.textContent = "Inspector";
            const text = document.createElement("p");
            text.className = "atlas-inspector-empty";
            text.textContent =
                "No repositories are visible. The catalog may hide every repository from dashboards, or the inventory is empty. Check the coverage page.";
            inspector.append(title, text);
        }
        return;
    }
    function repoInstanceSet(repo) {
        const used = new Set();
        for (const edge of repo.e) {
            if (edge[0] === 1)
                used.add(edge[1]);
            if (edge[2] === 1)
                used.add(edge[3]);
        }
        return used;
    }
    const modelCache = new Map();
    function repoModel(repo) {
        let model = modelCache.get(repo.n);
        if (model !== undefined) {
            return model;
        }
        const nodes = [];
        const adjacency = new Map();
        const addNode = (node) => {
            nodes.push(node);
            adjacency.set(node.key, new Set());
        };
        for (const [index, project] of repo.p.entries()) {
            addNode({
                key: "p" + index,
                kind: "project",
                ref: index,
                id: project[0],
                ecosystem: project[1],
                directory: project[2],
                label: project[2] === "." ? ". (root)" : project[2],
                color: PROJECT_COLOR,
                size: 17,
                zIndex: 4,
            });
        }
        for (const index of repoInstanceSet(repo)) {
            const item = instances[index];
            const component = components[item.component];
            addNode({
                key: "i" + index,
                kind: "instance",
                ref: index,
                id: item.id,
                ecosystem: component.ecosystem,
                label: item.version ? `${component.display}@${item.version}` : component.display,
                color: ecoColor(component.ecosystem),
                size: 8 + 9 * Math.log10(item.consumers + 1) / Math.log10(maxConsumers + 1),
                zIndex: 2,
            });
        }
        const nodeIndex = new Map(nodes.map((node) => [node.key, node]));
        const edges = [];
        for (const edge of repo.e) {
            const from = (edge[0] === 0 ? "p" : "i") + edge[1];
            const to = (edge[2] === 0 ? "p" : "i") + edge[3];
            if (!nodeIndex.has(from) || !nodeIndex.has(to)) {
                continue;
            }
            adjacency.get(from).add(to);
            adjacency.get(to).add(from);
            edges.push({
                from,
                to,
                relation: relations[edge[4]],
                scope: scopes[edge[5]],
                optional: edge[6] === 1,
                resolution: resolutions[edge[7]],
                source: sourceKinds[edge[8]],
                constraint: edge[9] === -1 ? null : strings[edge[9]],
                resolvedVersion: edge[10] === -1 ? null : strings[edge[10]],
                condition: edge[11] === -1 ? null : strings[edge[11]],
                targetEcosystem: edgesTargetEcosystem(edge, repo),
            });
        }
        const positions = layeredPositions(nodes, edges);
        model = { nodes, edges, positions, adjacency, nodeIndex };
        modelCache.set(repo.n, model);
        return model;
    }
    function layeredPositions(nodes, edges) {
        const outgoing = new Map();
        const incoming = new Map();
        for (const edge of edges) {
            if (!outgoing.has(edge.from))
                outgoing.set(edge.from, []);
            if (!incoming.has(edge.to))
                incoming.set(edge.to, []);
            outgoing.get(edge.from).push(edge.to);
            incoming.get(edge.to).push(edge.from);
        }
        const depth = new Map();
        const queue = [];
        for (const node of nodes) {
            if (node.kind === "project") {
                depth.set(node.key, 0);
                queue.push(node.key);
            }
        }
        let head = 0;
        while (head < queue.length) {
            const current = queue[head];
            head += 1;
            for (const next of outgoing.get(current) ?? []) {
                if (!depth.has(next)) {
                    depth.set(next, depth.get(current) + 1);
                    queue.push(next);
                }
            }
        }
        let maxDepth = 0;
        for (const value of depth.values()) {
            maxDepth = Math.max(maxDepth, value);
        }
        const detached = nodes.filter((node) => !depth.has(node.key));
        for (const node of detached) {
            depth.set(node.key, maxDepth + 1);
        }
        const layers = [];
        for (let index = 0; index <= maxDepth + (detached.length > 0 ? 1 : 0); index += 1) {
            layers.push([]);
        }
        for (const node of nodes) {
            layers[depth.get(node.key)].push(node);
        }
        const orderOf = new Map();
        layers[0].forEach((node, index) => orderOf.set(node.key, index));
        for (let level = 1; level < layers.length; level += 1) {
            layers[level].sort((left, right) => {
                const leftBary = barycenter(incoming.get(left.key), orderOf);
                const rightBary = barycenter(incoming.get(right.key), orderOf);
                return leftBary - rightBary
                    || left.ref - right.ref
                    || left.key.localeCompare(right.key);
            });
            layers[level].forEach((node, index) => orderOf.set(node.key, index));
        }
        const columnWidth = 400;
        const positions = new Map();
        layers.forEach((layer, level) => {
            const step = Math.min(150, 4400 / Math.max(1, layer.length));
            layer.forEach((node, index) => {
                positions.set(node.key, {
                    x: level * columnWidth,
                    y: (index - (layer.length - 1) / 2) * step,
                });
            });
        });
        return positions;
    }
    function barycenter(predecessors, orderOf) {
        let sum = 0;
        let count = 0;
        for (const key of predecessors ?? []) {
            const order = orderOf.get(key);
            if (order !== undefined) {
                sum += order;
                count += 1;
            }
        }
        return count === 0 ? Number.MAX_SAFE_INTEGER : sum / count;
    }
    function edgesTargetEcosystem(edge, repo) {
        if (edge[2] === 0) {
            const project = repo.p[edge[3]];
            return project === undefined ? null : project[1];
        }
        const item = instances[edge[3]];
        return item === undefined ? null : components[item.component].ecosystem;
    }
    function aggregateMax() {
        let top = 1;
        for (const repo of repos) {
            for (const row of repo.a) {
                top = Math.max(top, row[1] + row[2]);
            }
        }
        return top;
    }
    const maxAggregate = aggregateMax();
    const repoCounts = repos.map((repo) => repo.d + repo.x);
    const maxRepoEdges = Math.max(1, ...repoCounts);
    const ecoTotals = ecosystems.map((_, index) => ecosystemTotal(index));
    const visibleEcosystemIndexes = ecosystems.map((_, index) => index).filter((index) => ecoTotals[index] > 0);
    const maxEcosystemTotal = Math.max(1, ...ecoTotals);
    const view = {
        mode: "overview",
        repo: null,
        selected: null,
        neighbors: null,
        ecosystem: "all",
        relation: "all",
    };
    let hovered = null;
    let scene = { nodes: new Map(), edges: [], adjacency: new Map() };
    function fleetPositions() {
        const positions = new Map();
        const clusters = [];
        const columnWidth = 230;
        let cursor = 0;
        for (const owner of owners) {
            const group = repos.filter((repo) => ownerOf(repo.n) === owner);
            const cols = Math.max(1, Math.ceil(Math.sqrt(group.length)));
            const cellX = 130;
            const cellY = 108;
            let index = 0;
            for (const repo of group) {
                const column = index % cols;
                const row = Math.floor(index / cols);
                positions.set("repo:" + repo.n, {
                    x: cursor + column * cellX,
                    y: row * cellY,
                });
                index += 1;
            }
            const rows = Math.ceil(group.length / cols);
            clusters.push({
                owner,
                x: cursor + ((cols - 1) * cellX) / 2,
                y: ((rows - 1) * cellY) / 2,
                size: Math.max(cols * cellX, rows * cellY) * 0.34 + 65,
                count: group.length,
            });
            cursor += Math.max(cols * cellX, 320) + columnWidth;
        }
        const ecoX = cursor + 150;
        const ecoCellY = 96;
        visibleEcosystemIndexes.forEach((index, position) => {
            positions.set("eco:" + ecosystems[index], {
                x: ecoX,
                y: (position - (visibleEcosystemIndexes.length - 1) / 2) * ecoCellY,
            });
        });
        return { positions, clusters };
    }
    function ecosystemTotal(index) {
        let total = 0;
        for (const repo of repos) {
            for (const row of repo.a) {
                if (row[0] === index) {
                    total += row[1] + row[2];
                }
            }
        }
        return total;
    }
    function buildScene() {
        const nodes = new Map();
        const edges = [];
        const adjacency = new Map();
        const link = (from, to) => {
            if (!adjacency.has(from))
                adjacency.set(from, new Set());
            if (!adjacency.has(to))
                adjacency.set(to, new Set());
            adjacency.get(from).add(to);
            adjacency.get(to).add(from);
        };
        if (view.mode === "overview") {
            const { positions, clusters } = fleetPositions();
            for (const cluster of clusters) {
                const key = "cluster:" + cluster.owner;
                nodes.set(key, {
                    key,
                    kind: "cluster",
                    id: null,
                    label: cluster.owner.toUpperCase(),
                    labelPosition: "above",
                    x: cluster.x,
                    y: cluster.y,
                    size: cluster.size,
                    color: "#efede8",
                    labelColor: "#a8a69e",
                    labelSize: 15,
                    zIndex: 0,
                    repos: cluster.count,
                });
            }
            for (const repo of repos) {
                const total = repo.d + repo.x;
                const errors = repo.r;
                const position = positions.get("repo:" + repo.n);
                const key = "repo:" + repo.n;
                nodes.set(key, {
                    key,
                    kind: "repo",
                    id: repo.n,
                    label: repo.n.slice(repo.n.indexOf("/") + 1),
                    x: position.x,
                    y: position.y,
                    size: 6 + 17 * Math.sqrt(total / maxRepoEdges),
                    color: errors > 0 ? "#eb6834" : "#2a78d6",
                    labelColor: "#5d5d58",
                    labelSize: 11,
                    zIndex: 3,
                });
            }
            for (const index of visibleEcosystemIndexes) {
                const name = ecosystems[index];
                const total = ecoTotals[index];
                const position = positions.get("eco:" + name);
                const key = "eco:" + name;
                nodes.set(key, {
                    key,
                    kind: "ecosystem",
                    id: name,
                    label: name,
                    labelPosition: "left",
                    x: position.x,
                    y: position.y,
                    size: 12 + 22 * Math.sqrt(total / maxEcosystemTotal),
                    color: ecoColor(index),
                    labelColor: "#1c1c1a",
                    labelSize: 12,
                    zIndex: 3,
                    total,
                });
            }
            for (const repo of repos) {
                for (const row of repo.a) {
                    const [eco, dCount, tCount] = row;
                    const count = view.relation === "direct" ? dCount : view.relation === "transitive" ? tCount : dCount + tCount;
                    if (count === 0) {
                        continue;
                    }
                    const name = ecosystems[eco];
                    edges.push({
                        from: "repo:" + repo.n,
                        to: "eco:" + name,
                        relation: "aggregate",
                        kind: "aggregate",
                        count,
                        ecosystem: name,
                        direct: dCount,
                        transitive: tCount,
                        size: 1 + 6 * Math.sqrt(count / maxAggregate),
                        color: "#8f8e88",
                        opacity: 0.12 + 0.5 * Math.sqrt(count / maxAggregate),
                        zIndex: 1,
                        head: "arrow",
                    });
                    link("repo:" + repo.n, "eco:" + name);
                }
            }
        }
        else {
            const repo = view.repo === null ? undefined : repoByName.get(view.repo);
            if (repo !== undefined) {
                const model = repoModel(repo);
                const visible = [];
                for (const edge of model.edges) {
                    if (view.relation !== "all" && edge.relation !== view.relation) {
                        continue;
                    }
                    if (view.ecosystem !== "all") {
                        if (edge.targetEcosystem === null || ecosystems[edge.targetEcosystem] !== view.ecosystem) {
                            continue;
                        }
                    }
                    visible.push(edge);
                }
                const used = new Set();
                for (const edge of visible) {
                    used.add(edge.from);
                    used.add(edge.to);
                }
                const narrow = view.relation !== "all";
                for (const node of model.nodes) {
                    if (narrow && node.kind !== "project" && !used.has(node.key)) {
                        continue;
                    }
                    const position = model.positions.get(node.key);
                    nodes.set(node.key, {
                        ...node,
                        x: position.x,
                        y: position.y,
                        labelColor: "#5d5d58",
                        labelSize: 11,
                    });
                }
                for (const edge of visible) {
                    edges.push({
                        ...edge,
                        kind: "exact",
                        size: edge.relation === "direct" ? 3.1 : 1.5,
                        color: EDGE_COLOR,
                        opacity: edge.relation === "direct" ? 0.7 : 0.22,
                        zIndex: 1,
                        head: edge.relation === "direct" ? "arrow" : "none",
                    });
                    link(edge.from, edge.to);
                }
            }
        }
        return { nodes, edges, adjacency };
    }
    function neighborSet(key) {
        const set = new Set([key]);
        for (const neighbor of scene.adjacency.get(key) ?? []) {
            set.add(neighbor);
        }
        return set;
    }
    function defined(values) {
        const out = {};
        for (const [key, value] of Object.entries(values)) {
            if (value !== null && value !== undefined) {
                out[key] = value;
            }
        }
        return out;
    }
    function sceneGraph() {
        const graph = new Graph({ type: "mixed", multi: true });
        for (const [key, node] of scene.nodes) {
            graph.addNode(key, defined({
                x: node.x,
                y: node.y,
                size: node.size,
                color: node.color,
                label: node.label,
                labelColor: node.labelColor ?? "#5d5d58",
                labelSize: node.labelSize ?? 11,
                labelPosition: node.labelPosition,
                zIndex: node.zIndex,
                kind: node.kind,
                ref: node.ref,
                id: node.id,
                ecosystem: node.ecosystem,
                directory: node.directory,
                repos: node.repos,
                total: node.total,
            }));
        }
        let edgeIndex = 0;
        for (const edge of scene.edges) {
            edgeIndex += 1;
            graph.addEdgeWithKey("e" + edgeIndex, edge.from, edge.to, defined({
                size: edge.size,
                color: edge.color,
                opacity: edge.opacity,
                zIndex: edge.zIndex,
                depth: edge.depth,
                head: edge.head,
                relation: edge.relation,
                kind: edge.kind,
                ecosystem: edge.kind === "aggregate" ? edge.ecosystem : undefined,
                count: edge.kind === "aggregate" ? edge.count : undefined,
                direct: edge.kind === "aggregate" ? edge.direct : undefined,
                transitive: edge.kind === "aggregate" ? edge.transitive : undefined,
                scope: edge.kind === "exact" ? edge.scope : undefined,
                optional: edge.kind === "exact" ? edge.optional : undefined,
                resolution: edge.kind === "exact" ? edge.resolution : undefined,
                source: edge.kind === "exact" ? edge.source : undefined,
                constraint: edge.kind === "exact" ? edge.constraint : undefined,
                resolvedVersion: edge.kind === "exact" ? edge.resolvedVersion : undefined,
                condition: edge.kind === "exact" ? edge.condition : undefined,
                targetEcosystem: edge.kind === "exact" ? edge.targetEcosystem : undefined,
            }));
        }
        return graph;
    }
    const SIGMA_OPTIONS = {
        primitives: {
            edges: {
                paths: [pathLine()],
                extremities: [extremityArrow()],
                layers: [layerPlain()],
            },
        },
        settings: {
            autoRescale: "once",
            hideEdgesOnMove: true,
            hideLabelsOnMove: true,
            labelRenderedSizeThreshold: 6,
            labelDensity: 0.5,
            labelSize: 11,
            minCameraRatio: 0.05,
            maxCameraRatio: 3,
            enableNodeDrag: false,
            stagePadding: 30,
            antialiasEdges: false,
            antialiasNodes: false,
        },
        styles: {
            nodes: {
                size: { attribute: "size", defaultValue: 6 },
                color: { attribute: "color", defaultValue: "#9a9992" },
                label: { attribute: "label" },
                labelColor: { attribute: "labelColor", defaultValue: "#5d5d58" },
                labelSize: { attribute: "labelSize", defaultValue: 11 },
                labelPosition: { attribute: "labelPosition", defaultValue: "right" },
                zIndex: { attribute: "zIndex", defaultValue: 1 },
                visibility: { whenState: "isHidden", then: "hidden", else: "visible" },
            },
            edges: {
                size: { attribute: "size", defaultValue: 1 },
                color: { attribute: "color", defaultValue: "#c7c6c0" },
                opacity: { attribute: "opacity", defaultValue: 0.5 },
                zIndex: { attribute: "zIndex", defaultValue: 1 },
                visibility: { whenState: "isHidden", then: "hidden", else: "visible" },
                path: "line",
                head: { attribute: "head", defaultValue: "none" },
            },
        },
        nodeReducer(key, data, attrs) {
            const out = {};
            if (key === hovered) {
                out.zIndex = 9;
                out.depth = "topNodes";
                out.labelVisibility = "visible";
                if (view.mode === "overview" && attrs.kind === "repo")
                    out.labelPosition = "above";
            }
            if (view.mode === "overview" && (attrs.kind === "ecosystem" || attrs.kind === "cluster")) {
                out.labelVisibility = "visible";
            }
            else if (view.mode === "overview" && attrs.kind === "repo" && key !== view.selected && key !== hovered) {
                out.labelVisibility = "hidden";
            }
            if (view.selected !== null) {
                if (key === view.selected) {
                    out.size = attrs.size * 1.4;
                    out.labelVisibility = "visible";
                    out.zIndex = 9;
                    out.depth = "topNodes";
                }
                else if (view.neighbors?.has(key)) {
                    out.zIndex = 6;
                }
                else {
                    out.opacity = 0.12;
                    out.labelVisibility = "hidden";
                    out.zIndex = 0;
                }
            }
            if (view.mode === "focus" && view.ecosystem !== "all" && attrs.kind === "instance") {
                if (attrs.ecosystem === null || attrs.ecosystem === undefined || ecosystems[attrs.ecosystem] !== view.ecosystem) {
                    out.visibility = "hidden";
                }
            }
            return out;
        },
        edgeReducer(key, data, attrs, state, graphState, liveGraph) {
            const out = {};
            const endpoints = edgeEndpoints.get(key);
            const from = endpoints?.[0];
            const to = endpoints?.[1];
            if (view.mode === "focus" && view.ecosystem !== "all") {
                const targetEco = attrs.targetEcosystem === null || attrs.targetEcosystem === undefined
                    ? null
                    : ecosystems[attrs.targetEcosystem];
                if (targetEco !== view.ecosystem) {
                    out.visibility = "hidden";
                    return out;
                }
            }
            if (view.ecosystem !== "all" && attrs.kind === "aggregate" && attrs.ecosystem !== view.ecosystem) {
                out.visibility = "hidden";
                return out;
            }
            if (view.selected !== null) {
                if (from === view.selected) {
                    out.color = OUTGOING_COLOR;
                    out.opacity = 0.95;
                    out.size = Math.max(3.2, attrs.size + 1.4);
                    out.zIndex = 7;
                    out.depth = "topEdges";
                }
                else if (to === view.selected) {
                    out.color = INCOMING_COLOR;
                    out.opacity = 0.95;
                    out.size = Math.max(3.2, attrs.size + 1.4);
                    out.zIndex = 7;
                    out.depth = "topEdges";
                }
                else {
                    out.opacity = 0.06;
                    out.zIndex = 0;
                }
            }
            return out;
        },
    };
    let sigma = null;
    let edgeEndpoints = new Map();
    function sigmaOrThrow() {
        if (sigma === null) {
            throw new Error("atlas sigma is not mounted");
        }
        return sigma;
    }
    function onClickNode({ node }) {
        const entry = scene.nodes.get(node);
        if (entry === undefined) {
            return;
        }
        if (entry.kind === "repo") {
            focusRepo(entry.id ?? node.slice(5));
            return;
        }
        if (entry.kind === "ecosystem") {
            setEcosystem(entry.id ?? node.slice(4));
            return;
        }
        if (entry.kind === "cluster") {
            return;
        }
        if (view.selected === node) {
            clearSelection();
            return;
        }
        selectNode(node, true);
    }
    function mount() {
        if (sigma !== null) {
            sigma.kill();
            sigma = null;
        }
        const graph = sceneGraph();
        edgeEndpoints = new Map();
        for (const key of graph.edges()) {
            edgeEndpoints.set(key, [graph.source(key), graph.target(key)]);
        }
        sigma = new Sigma(graph, canvas, SIGMA_OPTIONS);
        let contextLossPending = false;
        sigma.on("webglContextLost", () => {
            contextLossPending = true;
            canvas.hidden = true;
            if (fallback !== null) {
                fallback.hidden = false;
            }
        });
        sigma.on("webglContextRestored", () => {
            if (!contextLossPending) {
                return;
            }
            contextLossPending = false;
            canvas.hidden = false;
            if (fallback !== null) {
                fallback.hidden = true;
            }
        });
        sigma.on("enterNode", ({ node }) => {
            canvas.style.cursor = "pointer";
            hovered = node;
            sigmaOrThrow().refresh();
        });
        sigma.on("leaveNode", () => {
            canvas.style.cursor = "";
            hovered = null;
            sigmaOrThrow().refresh();
        });
        sigma.on("clickNode", onClickNode);
        sigma.on("clickStage", () => clearSelection());
    }
    function rebuild() {
        view.neighbors = view.selected === null ? null : neighborSet(view.selected);
        mount();
    }
    function setCaption(text) {
        if (caption !== null) {
            caption.textContent = text;
        }
    }
    function captionText() {
        if (view.mode === "overview") {
            const suffixParts = [];
            if (view.ecosystem !== "all") {
                suffixParts.push(`ecosystem: ${view.ecosystem}`);
            }
            if (view.relation !== "all") {
                suffixParts.push(`${view.relation} only`);
            }
            const suffix = suffixParts.length > 0 ? ` · ${suffixParts.join(" · ")}` : "";
            return `Fleet overview · ${summary.repositories} repositories · ${summary.components} packages · aggregate edges${suffix}`;
        }
        const repo = view.repo === null ? undefined : repoByName.get(view.repo);
        if (repo === undefined) {
            return "Repository not visible";
        }
        const parts = [`${repo.n} · ${repo.p.length} projects/workspaces`];
        parts.push(`${repo.d} direct · ${repo.x} transitive edges`);
        if (view.relation !== "all") {
            parts.push(`showing ${view.relation} only`);
        }
        if (view.ecosystem !== "all") {
            parts.push(`ecosystem: ${view.ecosystem}`);
        }
        return parts.join(" · ");
    }
    function pushURL(replace) {
        const params = new URLSearchParams();
        if (view.mode === "focus" && view.repo !== null) {
            params.set("repo", view.repo);
            if (view.selected !== null) {
                const node = scene.nodes.get(view.selected);
                if (node !== undefined && node.id !== null) {
                    params.set("node", node.id);
                }
            }
        }
        if (view.ecosystem !== "all") {
            params.set("ecosystem", view.ecosystem);
        }
        if (view.relation !== "all") {
            params.set("relation", view.relation);
        }
        const query = params.toString();
        const url = query ? `${location.pathname}?${query}` : location.pathname;
        if (replace) {
            history.replaceState({ atlas: true }, "", url);
        }
        else {
            history.pushState({ atlas: true }, "", url);
        }
    }
    function applyParams(params) {
        const relation = params.get("relation");
        view.relation = relation === "direct" || relation === "transitive" ? relation : "all";
        const ecosystem = params.get("ecosystem");
        view.ecosystem = ecosystem !== null && data.ecosystems.includes(ecosystem) ? ecosystem : "all";
        const repo = params.get("repo");
        if (repo !== null) {
            const entry = repoByName.get(repo);
            if (entry !== undefined) {
                view.mode = "focus";
                view.repo = repo;
                view.selected = null;
                scene = buildScene();
                setCaption(captionText());
                rebuild();
                updateFleetButton();
                if (ecosystemSelect !== null) {
                    ecosystemSelect.value = view.ecosystem;
                }
                syncRelationButtons();
                const node = params.get("node");
                let selected = false;
                if (node !== null && node.length <= 512) {
                    const key = findNodeKey(node);
                    const candidate = key === null ? undefined : scene.nodes.get(key);
                    if (key !== null && candidate !== undefined && nodeSelectable(candidate)) {
                        selectNode(key, false);
                        selected = true;
                    }
                }
                if (!selected) {
                    renderInspector(null);
                }
                return;
            }
            const clean = new URLSearchParams();
            if (view.ecosystem !== "all")
                clean.set("ecosystem", view.ecosystem);
            if (view.relation !== "all")
                clean.set("relation", view.relation);
            const query = clean.toString();
            history.replaceState({ atlas: true }, "", query ? `${location.pathname}?${query}` : location.pathname);
        }
        view.mode = "overview";
        view.repo = null;
        view.selected = null;
        scene = buildScene();
        setCaption(captionText());
        rebuild();
        updateFleetButton();
        if (ecosystemSelect !== null) {
            ecosystemSelect.value = view.ecosystem;
        }
        syncRelationButtons();
        renderInspector(null);
    }
    function nodeSelectable(node) {
        if (view.mode === "focus" &&
            view.ecosystem !== "all" &&
            node.kind === "instance") {
            return (node.ecosystem !== null &&
                node.ecosystem !== undefined &&
                ecosystems[node.ecosystem] === view.ecosystem);
        }
        return true;
    }
    function findNodeKey(id) {
        for (const [key, node] of scene.nodes) {
            if (node.id === id) {
                return key;
            }
        }
        return null;
    }
    function updateFleetButton() {
        if (fleetButton !== null) {
            fleetButton.hidden = view.mode === "overview";
        }
    }
    function syncRelationButtons() {
        if (relationToggle === null)
            return;
        for (const button of relationToggle.querySelectorAll("button[data-relation]")) {
            button.setAttribute("aria-pressed", String(button.dataset.relation === view.relation));
        }
    }
    function enterOverview(push) {
        view.mode = "overview";
        view.repo = null;
        view.selected = null;
        scene = buildScene();
        setCaption(captionText());
        rebuild();
        updateFleetButton();
        if (push) {
            pushURL(false);
        }
        else {
            pushURL(true);
        }
        renderInspector(null);
    }
    function focusRepo(name, options) {
        const entry = repoByName.get(name);
        if (entry === undefined) {
            return;
        }
        view.mode = "focus";
        view.repo = name;
        view.selected = null;
        scene = buildScene();
        setCaption(captionText());
        rebuild();
        updateFleetButton();
        if (options?.push !== false) {
            pushURL(false);
        }
        renderInspector(null);
    }
    function selectNode(key, push) {
        view.selected = key;
        view.neighbors = neighborSet(key);
        const node = scene.nodes.get(key);
        setCaption(captionText());
        sigmaOrThrow().refresh();
        if (push) {
            pushURL(false);
        }
        else {
            pushURL(true);
        }
        renderInspector(node ?? null);
    }
    function clearSelection() {
        view.selected = null;
        view.neighbors = null;
        sigmaOrThrow().refresh();
        renderInspector(null);
        pushURL(true);
    }
    function element(tag, className, text) {
        const node = document.createElement(tag);
        if (className !== null)
            node.className = className;
        if (text !== undefined)
            node.textContent = text;
        return node;
    }
    function link(className, href, text) {
        const node = element("a", className, text);
        node.href = href;
        return node;
    }
    function requiredInspector() {
        if (inspector === null) {
            throw new Error("atlas inspector element is missing");
        }
        return inspector;
    }
    function renderInspector(node) {
        const target = requiredInspector();
        target.textContent = "";
        const title = element("h2", "atlas-inspector-title", "Inspector");
        target.append(title);
        if (node === null) {
            target.append(element("p", "atlas-inspector-empty", view.mode === "overview"
                ? "Select a repository to focus its dependency graph. Selecting an ecosystem filters the view to it. Aggregate edges sum a repository's target ecosystem; they are not runtime linkage."
                : "Select a project or package in the graph. Escape clears the selection and then returns to the fleet overview."));
            if (view.mode === "overview") {
                const list = element("ul", "atlas-repo-list");
                const ranked = [...repos].sort((left, right) => right.d + right.x - (left.d + left.x) || left.n.localeCompare(right.n));
                for (const repo of ranked) {
                    const item = element("li", null);
                    const button = element("button", "atlas-repo-button", repo.n);
                    button.type = "button";
                    button.append(element("span", "atlas-repo-count", String(repo.d + repo.x)));
                    button.addEventListener("click", () => focusRepo(repo.n));
                    item.append(button);
                    list.append(item);
                }
                target.append(element("p", "atlas-inspector-kind", "Repositories, most edges first"), list);
            }
            if (view.mode === "focus" && view.repo !== null && repoByName.has(view.repo)) {
                const linkRow = element("p", "atlas-inspector-actions");
                linkRow.append(link("atlas-inspector-link", reposPage(view.repo), "Open repository page →"));
                target.append(linkRow);
            }
            return;
        }
        if (node.kind !== "project" && node.kind !== "instance") {
            target.append(element("p", "atlas-inspector-empty", "Select a project or package in the graph."));
            return;
        }
        if (node.kind === "project") {
            const repo = view.repo === null ? undefined : repoByName.get(view.repo);
            const ref = node.ref;
            const project = ref === undefined ? undefined : repo?.p[ref];
            if (project === undefined) {
                target.append(element("p", "atlas-inspector-empty", "Select a project or package in the graph."));
                return;
            }
            target.append(element("p", "atlas-inspector-kind", "Project"));
            target.append(element("h3", "atlas-inspector-heading", project[2] === "." ? ". (repository root)" : project[2]));
            const list = element("dl", "atlas-inspector-grid");
            addRow(list, "Ecosystem", ecosystems[project[1]]);
            addRow(list, "Directory", project[2]);
            addRow(list, "Declares", `${countEdges(node.key, "out", repo)} direct dependencies`);
            appendSemantics(list, "declared", edgeSemantics(node.key, repo, "out"));
            target.append(list);
            return;
        }
        const ref = node.ref;
        if (ref === undefined) {
            target.append(element("p", "atlas-inspector-empty", "Select a project or package in the graph."));
            return;
        }
        const item = instances[ref];
        const component = components[item.component];
        target.append(element("p", "atlas-inspector-kind", item.firstParty ? "Package · first party" : "Package"));
        target.append(element("h3", "atlas-inspector-heading", item.version ? `${component.display} @ ${item.version}` : component.display));
        const list = element("dl", "atlas-inspector-grid");
        addRow(list, "Ecosystem", ecosystems[component.ecosystem]);
        addRow(list, "Source", sourceKinds[item.source]);
        addRow(list, "Version", item.version ?? "not recorded");
        addRow(list, "Consumers", `${item.consumers} of the ${summary.repositories} visible repositories`);
        const repo = view.repo === null ? undefined : repoByName.get(view.repo);
        const stats = degreeSplit(node.key, repo);
        addRow(list, "Direct dependents (this repository)", String(stats.direct));
        addRow(list, "Transitive dependents (this repository)", String(stats.transitive));
        appendSemantics(list, "inbound", edgeSemantics(node.key, repo, "in"));
        target.append(list);
        const idRow = element("p", "atlas-inspector-id mono");
        idRow.textContent = item.id;
        target.append(idRow);
        const linkRow = element("p", "atlas-inspector-actions");
        linkRow.append(link("atlas-inspector-link", `packages.html#pkg=${encodeURIComponent(component.purl)}`, "Open package page →"));
        target.append(linkRow);
    }
    function reposPage(name) {
        return "repos/" + name.split("/").map(encodeURIComponent).join("/") + "/index.html";
    }
    function addRow(list, term, value) {
        const wrapper = element("div", "atlas-inspector-row");
        wrapper.append(element("dt", null, term), element("dd", null, value));
        list.append(wrapper);
    }
    function countEdges(projectKey, direction, repo) {
        let count = 0;
        for (const edge of repo?.e ?? []) {
            const from = (edge[0] === 0 ? "p" : "i") + edge[1];
            if (direction === "out" && from === projectKey) {
                count += 1;
            }
        }
        return count;
    }
    function degreeSplit(key, repo) {
        const split = { direct: 0, transitive: 0 };
        if (repo === undefined) {
            return split;
        }
        for (const edge of repo.e) {
            const to = (edge[2] === 0 ? "p" : "i") + edge[3];
            if (to !== key) {
                continue;
            }
            if (relations[edge[4]] === "direct") {
                split.direct += 1;
            }
            else {
                split.transitive += 1;
            }
        }
        return split;
    }
    function edgeSemantics(key, repo, direction) {
        const counts = { optional: 0, conditional: 0, unknown: 0, declaredOnly: 0 };
        const scopeTally = new Map();
        if (repo === undefined) {
            return { counts, scopes: [] };
        }
        for (const edge of repo.e) {
            const endpoint = direction === "out"
                ? (edge[0] === 0 ? "p" : "i") + edge[1]
                : (edge[2] === 0 ? "p" : "i") + edge[3];
            if (endpoint !== key) {
                continue;
            }
            if (edge[6] === 1) {
                counts.optional += 1;
            }
            const resolution = resolutions[edge[7]];
            if (resolution === "conditional" || edge[11] !== -1) {
                counts.conditional += 1;
            }
            if (resolution === "unknown") {
                counts.unknown += 1;
            }
            if (resolution === "declared_only") {
                counts.declaredOnly += 1;
            }
            const scope = scopes[edge[5]];
            scopeTally.set(scope, (scopeTally.get(scope) ?? 0) + 1);
        }
        const scopeSummary = [...scopeTally.entries()]
            .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
            .map(([scope, count]) => `${scope} ×${count}`);
        return { counts, scopes: scopeSummary };
    }
    function appendSemantics(list, label, semantics) {
        const { counts, scopes: scopeSummary } = semantics;
        if (counts.optional > 0) {
            addRow(list, `Optional ${label}`, String(counts.optional));
        }
        if (counts.conditional > 0) {
            addRow(list, `Conditional ${label}`, String(counts.conditional));
        }
        if (counts.unknown > 0) {
            addRow(list, `Unknown resolution ${label}`, String(counts.unknown));
        }
        if (counts.declaredOnly > 0) {
            addRow(list, `Declared only ${label}`, String(counts.declaredOnly));
        }
        if (scopeSummary.length > 0) {
            addRow(list, `Scopes ${label}`, scopeSummary.join(", "));
        }
    }
    function setEcosystem(name) {
        view.ecosystem = data.ecosystems.includes(name) || name === "all" ? name : "all";
        if (ecosystemSelect !== null) {
            ecosystemSelect.value = view.ecosystem;
        }
        scene = buildScene();
        view.selected = null;
        setCaption(captionText());
        rebuild();
        closeResults();
        pushURL(true);
        renderInspector(null);
    }
    function setRelation(value) {
        if (value !== "all" && value !== "direct" && value !== "transitive") {
            return;
        }
        view.relation = value;
        scene = buildScene();
        view.selected = null;
        setCaption(captionText());
        rebuild();
        closeResults();
        syncRelationButtons();
        pushURL(true);
        renderInspector(null);
    }
    if (ecosystemSelect !== null) {
        ecosystemSelect.addEventListener("change", () => setEcosystem(ecosystemSelect.value));
    }
    if (relationToggle !== null) {
        relationToggle.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) {
                return;
            }
            const button = target.closest("button[data-relation]");
            if (button !== null) {
                setRelation(button.dataset.relation ?? "");
            }
        });
    }
    if (fitButton !== null) {
        fitButton.addEventListener("click", () => {
            sigmaOrThrow().setCustomBBox(null);
            void sigmaOrThrow().getCamera().reset({ duration: 260 });
        });
    }
    if (resetButton !== null) {
        resetButton.addEventListener("click", () => {
            clearSelection();
            sigmaOrThrow().setCustomBBox(null);
            void sigmaOrThrow().getCamera().reset({ duration: 260 });
        });
    }
    if (fleetButton !== null) {
        fleetButton.addEventListener("click", () => enterOverview(true));
    }
    document.addEventListener("keydown", (event) => {
        const target = event.target;
        const typing = target instanceof HTMLElement &&
            (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);
        if (event.key === "Escape") {
            if (resultsBox !== null && !resultsBox.hidden) {
                closeResults();
                return;
            }
            if (view.selected !== null) {
                clearSelection();
                return;
            }
            if (view.mode === "focus") {
                enterOverview(false);
            }
            return;
        }
        if (event.key === "/" && !typing) {
            if (searchInput !== null) {
                event.preventDefault();
                searchInput.focus();
            }
        }
    });
    window.addEventListener("popstate", () => {
        applyParams(new URLSearchParams(location.search));
    });
    let results = [];
    let activeResult = -1;
    function closeResults() {
        results = [];
        activeResult = -1;
        if (resultsBox !== null) {
            resultsBox.hidden = true;
            resultsBox.textContent = "";
        }
        if (searchInput !== null) {
            searchInput.setAttribute("aria-expanded", "false");
            searchInput.removeAttribute("aria-activedescendant");
        }
    }
    function openResults(items) {
        results = items;
        activeResult = items.length > 0 ? 0 : -1;
        if (resultsBox === null)
            return;
        resultsBox.textContent = "";
        items.forEach((item, index) => {
            const row = element("button", "atlas-result");
            row.type = "button";
            row.dataset.index = String(index);
            row.id = `atlas-result-${index}`;
            row.setAttribute("role", "option");
            row.append(element("span", "atlas-result-label", item.label));
            if (item.hint) {
                row.append(element("span", "atlas-result-hint", item.hint));
            }
            row.addEventListener("mousedown", (event) => {
                event.preventDefault();
                activateResult(index);
            });
            resultsBox.append(row);
        });
        resultsBox.hidden = items.length === 0;
        if (searchInput !== null) {
            searchInput.setAttribute("aria-expanded", String(items.length > 0));
        }
        highlightResult();
    }
    function highlightResult() {
        if (resultsBox === null)
            return;
        for (const row of resultsBox.querySelectorAll(".atlas-result")) {
            row.classList.toggle("active", Number(row.dataset.index) === activeResult);
        }
        if (searchInput === null)
            return;
        if (activeResult >= 0) {
            searchInput.setAttribute("aria-activedescendant", `atlas-result-${activeResult}`);
        }
        else {
            searchInput.removeAttribute("aria-activedescendant");
        }
    }
    function activateResult(index) {
        const item = results[index];
        if (item === undefined) {
            return;
        }
        closeResults();
        if (item.type === "repo") {
            focusRepo(item.key.slice(5));
            return;
        }
        if (item.type === "ecosystem") {
            setEcosystem(item.key.slice(4));
            return;
        }
        if (item.type === "node") {
            const candidate = scene.nodes.get(item.key);
            if (candidate !== undefined && nodeSelectable(candidate)) {
                selectNode(item.key, true);
            }
        }
    }
    function searchAll(query) {
        const q = query.trim().toLowerCase();
        if (q.length < 2) {
            closeResults();
            return;
        }
        const items = [];
        if (view.mode === "overview") {
            for (const repo of repos) {
                if (repo.n.toLowerCase().includes(q)) {
                    items.push({
                        type: "repo",
                        key: "repo:" + repo.n,
                        label: repo.n,
                        hint: `${repo.d + repo.x} edges`,
                    });
                    if (items.length >= 8)
                        break;
                }
            }
            for (const name of ecosystems) {
                if (items.length >= 11)
                    break;
                if (name.toLowerCase().includes(q)) {
                    items.push({ type: "ecosystem", key: "eco:" + name, label: name, hint: "ecosystem" });
                }
            }
        }
        else {
            const repo = view.repo === null ? undefined : repoByName.get(view.repo);
            let projectHits = 0;
            for (const [index, project] of (repo?.p ?? []).entries()) {
                if (projectHits >= 4)
                    break;
                if (project[2].toLowerCase().includes(q) || project[0].toLowerCase().includes(q)) {
                    items.push({
                        type: "node",
                        key: "p" + index,
                        label: project[2] === "." ? ". (repository root)" : project[2],
                        hint: ecosystems[project[1]] + " project",
                    });
                    projectHits += 1;
                }
            }
            for (const [key, node] of scene.nodes) {
                if (items.length >= 12)
                    break;
                if (node.kind !== "instance" || node.ref === undefined) {
                    continue;
                }
                if (!nodeSelectable(node)) {
                    continue;
                }
                const item = instances[node.ref];
                const component = components[item.component];
                const haystack = `${component.display} ${item.version ?? ""} ${component.purl}`.toLowerCase();
                if (haystack.includes(q)) {
                    items.push({
                        type: "node",
                        key,
                        label: node.label,
                        hint: ecosystems[component.ecosystem],
                    });
                }
            }
        }
        openResults(items);
    }
    if (searchInput !== null) {
        searchInput.addEventListener("input", () => searchAll(searchInput.value));
        searchInput.addEventListener("focus", () => searchAll(searchInput.value));
        searchInput.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                if (resultsBox !== null && !resultsBox.hidden) {
                    closeResults();
                }
                else {
                    searchInput.blur();
                }
                return;
            }
            if (resultsBox === null || resultsBox.hidden) {
                return;
            }
            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                event.preventDefault();
                const direction = event.key === "ArrowDown" ? 1 : -1;
                activeResult = (activeResult + direction + results.length) % results.length;
                highlightResult();
                return;
            }
            if (event.key === "Enter") {
                event.preventDefault();
                event.stopPropagation();
                if (activeResult >= 0) {
                    activateResult(activeResult);
                }
                return;
            }
        });
        document.addEventListener("click", (event) => {
            if (resultsBox !== null &&
                !resultsBox.hidden &&
                !(event.target instanceof Node && resultsBox.contains(event.target)) &&
                event.target !== searchInput) {
                closeResults();
            }
        });
    }
    applyParams(new URLSearchParams(location.search));
    if (loading !== null) {
        loading.hidden = true;
    }
})();
