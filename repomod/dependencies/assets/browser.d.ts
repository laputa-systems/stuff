interface DepsSearchEntry {
    purl: string;
    name: string;
    ecosystem: string;
    label: string;
}

interface DepsAtlasSummary {
    repositories: number;
    hidden: number;
    projects: number;
    instances: number;
    components: number;
    edges: number;
    direct: number;
    transitive: number;
    states: Record<string, number>;
}

type DepsAtlasProjectRow = readonly [id: string, ecosystem: number, directory: string];
type DepsAtlasAggregateRow = readonly [ecosystem: number, direct: number, transitive: number];
type DepsAtlasEdgeRow = readonly [
    number,
    number,
    number,
    number,
    number,
    number,
    number,
    number,
    number,
    number,
    number,
    number,
];

interface DepsAtlasRepository {
    n: string;
    s: string;
    t: string[];
    r: number;
    c: number;
    d: number;
    x: number;
    p: DepsAtlasProjectRow[];
    a: DepsAtlasAggregateRow[];
    e: DepsAtlasEdgeRow[];
}

type DepsAtlasComponentRow = readonly [purl: string, ecosystem: number, name: string, display: string];
type DepsAtlasInstanceRow = readonly [
    id: string,
    component: number,
    version: string | null,
    source: number,
    firstParty: number,
    consumers: number,
];

interface DepsAtlasData {
    v: number;
    summary: DepsAtlasSummary;
    ecosystems: string[];
    scopes: string[];
    relations: string[];
    resolutions: string[];
    source_kinds: string[];
    strings: string[];
    components: DepsAtlasComponentRow[];
    instances: DepsAtlasInstanceRow[];
    repositories: DepsAtlasRepository[];
}

interface AtlasGraph {
    addNode(key: string, attributes: Record<string, unknown>): void;
    addEdgeWithKey(key: string, source: string, target: string, attributes: Record<string, unknown>): void;
    edges(): string[];
    source(key: string): string;
    target(key: string): string;
}

interface AtlasCamera {
    reset(options: { duration: number }): Promise<void>;
}

interface AtlasSigmaEventMap {
    webglContextLost: Record<string, never>;
    webglContextRestored: Record<string, never>;
    enterNode: { node: string };
    leaveNode: Record<string, never>;
    clickNode: { node: string };
    clickStage: Record<string, never>;
}

interface AtlasSigma {
    kill(): void;
    refresh(): void;
    setCustomBBox(bbox: null): void;
    getCamera(): AtlasCamera;
    on<K extends keyof AtlasSigmaEventMap>(event: K, handler: (payload: AtlasSigmaEventMap[K]) => void): void;
}

interface AtlasSigmaNodeAttributes {
    size: number;
    kind?: string;
    ecosystem?: number | null;
    id?: string | null;
    ref?: number;
    repos?: number;
    total?: number;
}

interface AtlasSigmaEdgeAttributes {
    size: number;
    kind?: string;
    ecosystem?: string;
    targetEcosystem?: number | null;
}

interface AtlasSigmaReducerResult {
    [attribute: string]: string | number;
}

interface AtlasSigmaOptions {
    primitives: {
        edges: {
            paths: unknown[];
            extremities: unknown[];
            layers: unknown[];
        };
    };
    settings: Record<string, number | boolean | string>;
    styles: {
        nodes: Record<string, unknown>;
        edges: Record<string, unknown>;
    };
    nodeReducer(
        key: string,
        data: unknown,
        attributes: AtlasSigmaNodeAttributes,
    ): AtlasSigmaReducerResult;
    edgeReducer(
        key: string,
        data: unknown,
        attributes: AtlasSigmaEdgeAttributes,
        state: unknown,
        graphState: unknown,
        liveGraph: unknown,
    ): AtlasSigmaReducerResult;
}

interface AtlasVendorBundle {
    Graph: new (options: { type: "mixed"; multi: boolean }) => AtlasGraph;
    Sigma: new (graph: AtlasGraph, canvas: HTMLCanvasElement, options: AtlasSigmaOptions) => AtlasSigma;
    pathLine(): unknown;
    extremityArrow(): unknown;
    layerPlain(): unknown;
}

interface Window {
    DEPS_INDEX?: DepsSearchEntry[] | null;
    searchDeps?: (query: string) => DepsSearchEntry[];
    DEPS_ATLAS?: DepsAtlasData | null;
    AtlasVendor?: AtlasVendorBundle | null;
    depsWeight?: Record<string, unknown>;
}
