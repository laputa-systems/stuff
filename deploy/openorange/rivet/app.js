'use strict';
const $ = (id) => {
    const element = document.getElementById(id);
    if (element === null) {
        throw new Error(`rivet explorer: missing #${id}`);
    }
    return element;
};
let generation = 0;
let controller;
let actorRows = [];
let actorTruncated = false;
function selection() {
    const hash = new URLSearchParams(location.hash.slice(1));
    return { namespace: hash.get('namespace') || '', name: hash.get('name') || '' };
}
function saveSelection(replace = false) {
    const p = new URLSearchParams();
    const namespace = $('namespace');
    const name = $('actor-name');
    if (namespace.value)
        p.set('namespace', namespace.value);
    if (name.value)
        p.set('name', name.value);
    const hash = p.toString() ? '#' + p : location.pathname;
    if (replace)
        history.replaceState(null, '', hash);
    else if (location.hash !== '#' + p)
        history.pushState(null, '', hash);
}
function begin() {
    if (controller)
        controller.abort();
    controller = new AbortController();
    return { id: ++generation, signal: controller.signal };
}
function current(job) {
    return job.id === generation && !job.signal.aborted;
}
async function get(job, path, params = {}) {
    const query = new URLSearchParams(params).toString();
    const response = await fetch('/rivet/api/' + path + (query ? '?' + query : ''), { cache: 'no-store', signal: job.signal });
    if (!response.ok)
        throw new Error('Unable to load ' + path + ' (' + response.status + ')');
    return (await response.json());
}
function options(select, values, old) {
    select.replaceChildren();
    for (const value of values) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value;
        select.append(option);
    }
    if (values.includes(old))
        select.value = old;
}
function detail(row) {
    const dl = $('detail');
    dl.replaceChildren();
    for (const [key, value] of Object.entries(row)) {
        const dt = document.createElement('dt');
        const dd = document.createElement('dd');
        dt.textContent = key;
        dd.textContent = String(value ?? '—');
        dl.append(dt, dd);
    }
}
function table(id, rows, fields) {
    const body = $(id);
    body.replaceChildren();
    for (const row of rows) {
        const tr = document.createElement('tr');
        tr.tabIndex = 0;
        for (const field of fields) {
            const td = document.createElement('td');
            td.textContent = typeof field === 'function' ? String(field(row)) : String(row[field] ?? '—');
            tr.append(td);
        }
        tr.addEventListener('click', () => detail(row));
        tr.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                detail(row);
            }
        });
        body.append(tr);
    }
}
function lifecycle(row) {
    if (row.lifecycle_phase != null) {
        return `Engine: ${row.lifecycle_phase}${row.lifecycle_epoch == null ? '' : ` · epoch ${row.lifecycle_epoch}`}`;
    }
    const events = [
        ['destroy_ts', 'Destroyed'],
        ['sleep_ts', 'Sleep reported'],
        ['connectable_ts', 'Connectable'],
        ['start_ts', 'Started'],
        ['reschedule_ts', 'Rescheduled'],
        ['pending_allocation_ts', 'Pending allocation'],
        ['create_ts', 'Created'],
    ];
    const reported = events
        .filter(([key]) => row[key] != null)
        .sort((left, right) => {
        const a = BigInt(String(row[left[0]]));
        const b = BigInt(String(row[right[0]]));
        return a === b ? 0 : a > b ? -1 : 1;
    });
    return reported[0]?.[1] ?? 'Unavailable';
}
function renderActors() {
    const query = $('actor-search').value.toLowerCase();
    const rows = actorRows.filter((row) => String(row.actor_id).toLowerCase().includes(query) || String(row.key ?? '').toLowerCase().includes(query));
    table('actors', rows, ['actor_id', 'key', 'pool', lifecycle, 'create_ts']);
    $('actor-count').textContent = `${rows.length} of ${actorRows.length} actors on the displayed page for ${$('actor-name').value}${actorTruncated ? ' (more pages available)' : ''}`;
}
function clear() {
    $('nodes').replaceChildren();
    $('actors').replaceChildren();
    $('detail').replaceChildren();
    actorRows = [];
    $('actor-search').disabled = true;
}
function fail(job, error) {
    if (!current(job))
        return;
    if (error instanceof Error && error.name === 'AbortError')
        return;
    clear();
    $('namespace').disabled = true;
    $('actor-name').disabled = true;
    $('health').textContent = 'Engine unavailable';
    $('message').textContent = error instanceof Error ? error.message : String(error);
    $('pools').textContent = 'Unavailable';
    $('node-status').textContent = 'Unavailable';
    $('actor-count').textContent = 'Unavailable';
}
async function loadActors(job, namespace, name) {
    $('actors').replaceChildren();
    $('detail').replaceChildren();
    $('actor-search').disabled = true;
    $('actor-count').textContent = 'Loading actors…';
    if (!name) {
        $('actor-count').textContent = 'No actor names in this namespace.';
        return;
    }
    const data = await get(job, 'actors', { namespace, name });
    if (!current(job))
        return;
    actorRows = data.actors;
    actorTruncated = data.truncated ?? false;
    $('actor-search').disabled = false;
    renderActors();
}
async function loadNamespace(job, wantedName) {
    const namespace = $('namespace').value;
    clear();
    $('actor-name').disabled = true;
    $('pools').textContent = 'Loading…';
    $('node-status').textContent = 'Loading…';
    $('actor-count').textContent = 'Loading…';
    if (!namespace) {
        $('pools').textContent = 'No namespaces.';
        $('node-status').textContent = 'No namespace selected.';
        $('actor-count').textContent = 'No namespace selected.';
        return;
    }
    const [pools, names] = await Promise.all([
        get(job, 'pools', { namespace }),
        get(job, 'names', { namespace }),
    ]);
    if (!current(job))
        return;
    const nodes = await Promise.all(pools.pools.map((pool) => get(job, 'nodes', { namespace, pool: pool.name })));
    if (!current(job))
        return;
    $('pools').textContent = pools.pools.map((p) => p.name).join(', ') || 'No pools.';
    const rows = nodes.flatMap((x) => x.nodes);
    table('nodes', rows, [
        'key',
        'pool',
        (r) => (r.stopping ? 'Stopping' : r.connected === true ? 'Connected' : r.connected === false ? 'Disconnected' : 'Unknown'),
        'datacenter',
        'last_ping_ts',
    ]);
    $('node-status').textContent = rows.length
        ? `${rows.length} nodes shown${nodes.some((x) => x.truncated) ? ' (more pages available)' : ''}`
        : 'No nodes on the displayed page.';
    if (pools.truncated)
        $('message').textContent = 'More pools are available.';
    options($('actor-name'), names.names, wantedName);
    $('actor-name').disabled = !names.names.length;
    saveSelection(true);
    await loadActors(job, namespace, $('actor-name').value);
}
async function refresh(wanted = selection()) {
    const job = begin();
    clear();
    $('namespace').disabled = true;
    $('actor-name').disabled = true;
    $('message').textContent = 'Loading…';
    $('health').textContent = 'Loading engine…';
    $('pools').textContent = 'Loading…';
    $('node-status').textContent = 'Loading…';
    $('actor-count').textContent = 'Loading…';
    try {
        const [health, namespaces] = await Promise.all([
            get(job, 'health'),
            get(job, 'namespaces'),
        ]);
        if (!current(job))
            return;
        $('health').textContent = `${health.status} · observed Rivet ${health.version}`;
        $('version-note').textContent = health.configuredImageTag
            ? `Configured image tag: ${health.configuredImageTag}. Reported binary version: ${health.version}. The tag does not establish source identity.`
            : 'Configured image tag unavailable. The Engine version is reported live.';
        options($('namespace'), namespaces.namespaces.map((x) => x.name), wanted.namespace || (namespaces.namespaces.some((x) => x.name === 'stats-prod') ? 'stats-prod' : ''));
        $('namespace').disabled = !namespaces.namespaces.length;
        $('message').textContent = namespaces.truncated ? 'More namespaces are available.' : '';
        await loadNamespace(job, wanted.name);
    }
    catch (error) {
        fail(job, error);
    }
}
$('refresh').addEventListener('click', () => refresh({ namespace: $('namespace').value, name: $('actor-name').value }));
$('namespace').addEventListener('change', () => {
    const job = begin();
    $('actor-name').replaceChildren();
    saveSelection();
    $('message').textContent = '';
    loadNamespace(job, '').catch((error) => fail(job, error));
});
$('actor-name').addEventListener('change', () => {
    const job = begin();
    saveSelection();
    loadActors(job, $('namespace').value, $('actor-name').value)
        .catch((error) => fail(job, error));
});
$('actor-search').addEventListener('input', renderActors);
window.addEventListener('popstate', () => refresh(selection()));
refresh();
