'use strict';
const vm = require('node:vm'), fs = require('node:fs'), assert = require('node:assert/strict');
class Element {
    tag;
    children;
    value;
    textContent;
    listeners;
    disabled;
    tabIndex;
    constructor(tag) {
        this.tag = tag;
        this.children = [];
        this.value = '';
        this.textContent = '';
        this.listeners = {};
        this.disabled = false;
        this.tabIndex = 0;
    }
    replaceChildren() {
        this.children = [];
        if (this.tag === 'select')
            this.value = '';
    }
    append(...items) {
        this.children.push(...items);
        if (this.tag === 'select' && !this.value && items.length)
            this.value = items[0].value;
    }
    addEventListener(event, callback) {
        this.listeners[event] = callback;
    }
}
const ids = {};
for (const id of ['namespace', 'actor-name', 'actor-search', 'refresh', 'health', 'message', 'nodes', 'actors', 'detail', 'pools', 'node-status', 'actor-count', 'version-note']) {
    ids[id] = new Element(['namespace', 'actor-name'].includes(id) ? 'select' : 'div');
}
const location = { hash: '#namespace=old&name=actor', pathname: '/rivet/' };
const history = {
    replaceState(_a, _b, url) {
        location.hash = url.startsWith('#') ? url : '';
    },
    pushState(_a, _b, url) {
        location.hash = url.startsWith('#') ? url : '';
    },
};
let pendingOld;
function fetch(url) {
    const u = new URL(url, 'http://local');
    const namespace = u.searchParams.get('namespace');
    const path = u.pathname.split('/').pop();
    let data;
    if (path === 'health')
        data = { status: 'ok', version: '3.1.1' };
    if (path === 'namespaces')
        data = { namespaces: [{ name: 'old' }, { name: 'new' }], truncated: false };
    if (path === 'pools' && namespace === 'old') {
        return new Promise((resolve) => {
            pendingOld = () => resolve({ ok: true, json: async () => ({ pools: [{ name: 'old-pool' }], truncated: false }) });
        });
    }
    if (path === 'pools')
        data = { pools: [{ name: 'new-pool' }], truncated: false };
    if (path === 'names')
        data = { names: ['actor'] };
    if (path === 'nodes')
        data = { nodes: [{ key: 'new-node', pool: 'new-pool', connected: true }], truncated: false };
    if (path === 'actors')
        data = { actors: [{ actor_id: 'new-id', name: 'actor', key: 'needle', create_ts: 1 }], truncated: false };
    return Promise.resolve({ ok: true, json: async () => data });
}
const events = {};
const context = {
    document: {
        getElementById: (id) => ids[id],
        createElement: (tag) => new Element(tag),
    },
    location,
    history,
    URLSearchParams,
    AbortController,
    fetch,
    window: { addEventListener: (name, fn) => { events[name] = fn; } },
};
vm.runInNewContext(fs.readFileSync(__dirname + '/app.js', 'utf8'), context);
const tick = () => new Promise((resolve) => { setImmediate(() => resolve()); });
(async () => {
    await tick();
    ids.namespace.value = 'new';
    ids.namespace.listeners.change();
    await tick();
    await tick();
    assert.equal(ids.pools.textContent, 'new-pool');
    if (pendingOld === undefined) {
        throw new Error('the old-pools request was not parked');
    }
    pendingOld();
    await tick();
    await tick();
    assert.equal(ids.pools.textContent, 'new-pool');
    assert.equal(ids.nodes.children[0].children[0].textContent, 'new-node');
    assert.match(location.hash, /namespace=new/);
    ids['actor-search'].value = 'missing';
    ids['actor-search'].listeners.input();
    assert.equal(ids.actors.children.length, 0);
    ids['actor-search'].value = 'needle';
    ids['actor-search'].listeners.input();
    assert.equal(ids.actors.children.length, 1);
    location.hash = '#namespace=new&name=actor';
    events.popstate();
    await tick();
    await tick();
    assert.equal(ids.namespace.value, 'new');
    assert.equal(ids['actor-name'].value, 'actor');
    console.log('UI race, hash restoration, and page search: ok');
})().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
