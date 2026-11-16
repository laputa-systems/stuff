'use strict';

const vm = require('node:vm'), fs = require('node:fs'), assert = require('node:assert/strict');

type Listener = (...args: any[]) => void;

class Element {
  tag: string;
  children: Element[];
  value: string;
  textContent: string;
  listeners: Record<string, Listener>;
  disabled: boolean;
  tabIndex: number;

  constructor(tag: string) {
    this.tag = tag;
    this.children = [];
    this.value = '';
    this.textContent = '';
    this.listeners = {};
    this.disabled = false;
    this.tabIndex = 0;
  }
  replaceChildren(): void {
    this.children = [];
    if (this.tag === 'select') this.value = '';
  }
  append(...items: Element[]): void {
    this.children.push(...items);
    if (this.tag === 'select' && !this.value && items.length) this.value = items[0].value;
  }
  addEventListener(event: string, callback: Listener): void {
    this.listeners[event] = callback;
  }
}

const ids: Record<string, Element> = {};
for (const id of ['namespace','actor-name','actor-search','refresh','health','message','nodes','actors','detail','pools','node-status','actor-count','version-note']) {
  ids[id] = new Element(['namespace','actor-name'].includes(id) ? 'select' : 'div');
}
const location = { hash: '#namespace=old&name=actor', pathname: '/rivet/' };
const history = {
  replaceState(_a: unknown, _b: unknown, url: string): void {
    location.hash = url.startsWith('#') ? url : '';
  },
  pushState(_a: unknown, _b: unknown, url: string): void {
    location.hash = url.startsWith('#') ? url : '';
  },
};

interface FetchResponse {
  ok: boolean;
  json(): Promise<unknown>;
}

let pendingOld: (() => void) | undefined;

function fetch(url: string): Promise<FetchResponse> {
  const u = new URL(url, 'http://local');
  const namespace = u.searchParams.get('namespace');
  const path = u.pathname.split('/').pop();
  let data: unknown;
  if (path === 'health') data = { status: 'ok', version: '3.1.1' };
  if (path === 'namespaces') data = { namespaces: [{ name: 'old' }, { name: 'new' }], truncated: false };
  if (path === 'pools' && namespace === 'old') {
    return new Promise((resolve) => {
      pendingOld = () => resolve({ ok: true, json: async () => ({ pools: [{ name: 'old-pool' }], truncated: false }) });
    });
  }
  if (path === 'pools') data = { pools: [{ name: 'new-pool' }], truncated: false };
  if (path === 'names') data = { names: ['actor'] };
  if (path === 'nodes') data = { nodes: [{ key: 'new-node', pool: 'new-pool', connected: true }], truncated: false };
  if (path === 'actors') data = { actors: [{ actor_id: 'new-id', name: 'actor', key: 'needle', create_ts: 1 }], truncated: false };
  return Promise.resolve({ ok: true, json: async () => data });
}

const events: Record<string, Listener> = {};
const context = {
  document: {
    getElementById: (id: string) => ids[id],
    createElement: (tag: string) => new Element(tag),
  },
  location,
  history,
  URLSearchParams,
  AbortController,
  fetch,
  window: { addEventListener: (name: string, fn: Listener) => { events[name] = fn; } },
};

vm.runInNewContext(fs.readFileSync(__dirname + '/app.js', 'utf8'), context);

assert.equal(vm.runInNewContext('lifecycle({ lifecycle_phase: "sleeping", lifecycle_epoch: 7, create_ts: 123 })', context), 'Engine: sleeping · epoch 7');
assert.equal(vm.runInNewContext('lifecycle({ lifecycle_phase: "running", lifecycle_epoch: 7, sleep_ts: 123 })', context), 'Engine: running · epoch 7');
assert.equal(vm.runInNewContext('lifecycle({ lifecycle_phase: "migrating_from_v2", lifecycle_epoch: null })', context), 'Engine: migrating_from_v2');
assert.equal(vm.runInNewContext('lifecycle({ lifecycle_phase: null, lifecycle_epoch: null })', context), 'Unavailable');
assert.equal(vm.runInNewContext('lifecycle({})', context), 'Unavailable');
assert.equal(vm.runInNewContext('lifecycle({ sleep_ts: 123 })', context), 'Sleep reported');

const tick = (): Promise<void> => new Promise((resolve) => { setImmediate(() => resolve()); });

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
})().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
