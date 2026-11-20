# Engine candidate qualification

The private candidate is based on Rivet
`e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9` with the six patches in
`rivet-engine-source` registry order. It has not been promoted. The comparison
image is `docker.io/rivetdev/engine@sha256:6e585002b700dd4d3630808eb67884aa15d1a602d83781984edac47023b6d40f`;
its `--version` exits 0 and reports `Rivet 3.1.1`.

The builder is
`ghcr.io/rivet-dev/rivet/engine-base-builder@sha256:61ba0bec231a20ebe8501be2d26b4649bbb74f31353d0ea8740785ee467d5d11`.
The Mac ran Linux x86-64 under Docker emulation. Each build used `--cpus 4`,
`--memory 8g`, `--network none`, Rust 1.99.0 (commit
`b940084d7eb6a299eb4bfeb8e34901bc051e7ac4`), `RUSTFLAGS='--cfg tokio_unstable'`
and four Cargo jobs. The patched Cargo.lock SHA-256 is
`c71ea82297a358a30d4d0e9c5f983ee9cac58e3e1e2d94de8bc628b7ff8ef7bb`.
The first release build exited 0 after Cargo reported 30m 07s; its binary
SHA-256 is `9c1f1c7a1b55b66d730ae6b483fe98a1b0d6b871a36f58bf09b27f5965a3db56`
and its build record SHA-256 is
`bd867994865b4c250f87683453e45cfbf78143aafe5201eaeff499b18244e620`.

The first acquisition placed Cargo's vendor output over an upstream `vendor/`
directory. The source-integrity check rejected that tree before compilation.
The next acquisition preserved that tree but its generated Cargo configuration
resolved the vendor directory incorrectly. That first build exited 1 before
compiling. Its configuration was corrected to `/src/cargo-vendor`; the final
acquisition command produces that path directly. These attempts made no depot.

The runtime workload used the Stats checkout's `open-orange 1.0.2-laputa.1`
closure and its `canary/workload.mts` helpers. Candidate and production each
completed ten requests, acknowledged two writes and verified two readbacks,
with zero failures, duplicate mismatches, body mismatches or lost writes. The
candidate completed ten Engine-only SIGTERM/start cycles, each followed by a
byte-for-byte history comparison and exact event comparison. Production opened
an isolated candidate-written depot copy, and the candidate opened an isolated
production-written depot copy; both readbacks matched. The run exited 0. It
uses a small fixed workload and does not prove sustained production availability
or cover every possible persisted value. The Engine processes and application
were local; no production host was contacted.

The runtime command was:

```sh
TMPDIR="$PWD/.work/tmp" node .work/tmp/engine-qualification-runner.mts "$PWD/.work/tmp/engine-qualification-build-v3/rivet-engine" "$PWD/.work/tmp/engine-qualification-runtime" > .work/tmp/engine-qualification-runtime.log 2>&1
```

The receipt SHA-256 is
`b0a557a0651d1d1f9ec6271d6bb7f306a5bdc9239a8e7a07f6a6d181678ea556`.
The runner SHA-256 is
`eaa096c7aaf256da70dc9197b42bd5a2ee0f00182573c996c6595dd2795a1a2a`;
its complete source follows so the scratch runner can be reconstructed.

```typescript
import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import { cpSync, mkdirSync, writeFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';
import { generate, ORANGE_ROOT } from '/Users/josh/repos/stats/deploy/orange/generate.mts';
import { freePort } from '/Users/josh/repos/stats/deploy/orange/session.mts';
import { prepare, runWorkload } from '/Users/josh/repos/stats/deploy/orange/canary/workload.mts';

const [binary, root] = process.argv.slice(2);
if (!binary || !root) throw new Error('binary and root required');
const image = 'docker.io/rivetdev/engine@sha256:6e585002b700dd4d3630808eb67884aa15d1a602d83781984edac47023b6d40f';
const delay = (ms: number) => new Promise(r => setTimeout(r, ms));
const docker = (...args: string[]) => execFileSync('docker', args, {encoding:'utf8'}).trim();
const evidence = (data: unknown) => appendFileSync(join(root, 'receipt.jsonl'), JSON.stringify(data) + '\n');
mkdirSync(root, {recursive:true});

async function engine(kind: string, data: string) {
  const [guard, peer, metrics] = await Promise.all([freePort(), freePort(), freePort()]);
  mkdirSync(join(data, 'log'), {recursive:true});
  writeFileSync(join(data, 'config.json'), JSON.stringify({topology:{datacenter_label:1,datacenters:{default:{datacenter_label:1,is_leader:true,peer_url:`http://127.0.0.1:${peer}/`,public_url:`http://127.0.0.1:${guard}/`}}}}));
  const name = `engine-qual-${process.pid}-${kind}-${Date.now()}`;
  const env = { RIVET__API_PEER__HOST:'127.0.0.1', RIVET__API_PEER__PORT:String(peer), RIVET__AUTH__ADMIN_TOKEN:'canary', RIVET__GUARD__HOST:'0.0.0.0', RIVET__GUARD__PORT:String(guard), RIVET__METRICS__HOST:'127.0.0.1', RIVET__METRICS__PORT:String(metrics), RIVET__PEGBOARD__NODE_LOST_THRESHOLD:'7000', RIVET__OBJECT_STORAGE__PRIMARY__FILE_SYSTEM__PATH:'/data/objects', RIVET__STORAGE__AUTO_PROVISION_PARTITIONS:'1', RIVET__STORAGE__BALANCING__ENABLED:'false', RIVET__STORAGE__COLD_STORE__DISK_CACHE_BYTES:'0', RIVET__STORAGE__LOG_DIRECTORY:'/data/log', RIVET__STORAGE__LOG_SHARD__MAX_DISK_BYTES:String(1024*1024*1024) };
  const args = ['run','-d','--platform','linux/amd64','--name',name,'--cpus','2','--memory','3g','-p',`127.0.0.1:${guard}:${guard}`,'-v',`${data}:/data`,'-w','/data', ...Object.entries(env).flatMap(([k,v]) => ['-e',`${k}=${v}`])];
  if (kind === 'candidate') args.push('-v',`${binary}:/usr/bin/rivet-engine:ro`);
  args.push(image, '--config', '/data/config.json');
  docker(...args);
  async function ready() {
    const deadline = Date.now() + 120000;
    for (;;) {
      const state = docker('inspect','--format','{{.State.Running}} {{.State.ExitCode}}',name);
      if (!state.startsWith('true')) throw new Error(`engine ${name} exited: ${state}\n${docker('logs',name)}`);
      const response = await fetch(`http://127.0.0.1:${guard}/actors/names?namespace=default`, {headers:{authorization:'Bearer canary'}, signal:AbortSignal.timeout(2000)}).catch(() => undefined);
      if (response?.status === 200) return;
      if (Date.now() > deadline) throw new Error(`engine ${name} readiness timeout`);
      await delay(250);
    }
  }
  async function stop() { docker('stop','-t','30',name); const exit = docker('inspect','--format','{{.State.ExitCode}}',name); if (exit !== '0') throw new Error(`engine ${name} exited ${exit}`); }
  await ready();
  return {name, guard, ready, stop};
}
async function serve(data: string, guard: number) {
  const state = join(data,'state'); mkdirSync(state,{recursive:true});
  generate(state,{kind:'dev',release:'engine-qualification',gatewaySecret:'engine-qualification-secret',nowMs:null});
  const port = await freePort();
  let output = '';
  const child = spawn(process.execPath,[join(ORANGE_ROOT,'node_modules/open-orange/dist/bin.js'),'serve','--config',join(state,'stats.jsonc'),'--config',join(state,'observe.jsonc')],{cwd:state,env:{...process.env,PORT:String(port),RIVET_ENDPOINT:`http://default:canary@127.0.0.1:${guard}`},stdio:['ignore','pipe','pipe']});
  child.stdout.on('data', c => {output += c;}); child.stderr.on('data', c => {output += c;});
  const deadline=Date.now()+120000;
  while (!output.includes('orange serve listening on')) { if (child.exitCode !== null || Date.now()>deadline) throw new Error(`serve failed ${output}`); await delay(250); }
  return {origin:`http://127.0.0.1:${port}`,release:'engine-qualification',headers:{'Stats-Gateway-Secret':'engine-qualification-secret','Stats-Tailnet-Identity':'user:canary@example.com'},stop:async()=>{if(child.exitCode===null){const exited=new Promise<void>(r=>child.once('exit',()=>r())); child.kill('SIGTERM'); await exited;}}};
}
async function verify(stack: any, result: any) {
 const h=await fetch(stack.origin+result.historyPath,{headers:{...stack.headers,'accept-encoding':'identity'}}); const hb=Buffer.from(await h.arrayBuffer());
 const e=await fetch(stack.origin+result.eventReadPath,{headers:stack.headers}); const body=await e.json() as any;
 assert.equal(h.status,200); assert.ok(hb.equals(result.historyBytes),'history differs'); assert.equal(e.status,200); assert.deepEqual(body.events[0]?.event,result.event);
}
async function run(kind: string) {
 const data=join(root,kind); mkdirSync(data,{recursive:true});
 const eng=await engine(kind,data); let app=await serve(data,eng.guard);
 const credentials=await prepare(app as any); const result=await runWorkload(app as any,credentials,app.origin);
 assert.equal(result.ledger.lostWrites,0); assert.equal(result.ledger.acknowledgedWrites,2); assert.equal(result.ledger.readbackVerified,2); assert.equal(result.ledger.bodyMismatches,0); assert.deepEqual(result.ledger.failures,{}); assert.equal(result.ledger.duplicateMismatches,0); await verify(app,result); evidence({kind,workload:result.ledger});
 if(kind==='candidate') for(let cycle=1;cycle<=10;cycle++){await eng.stop(); docker('start',eng.name); await eng.ready(); await verify(app,result); evidence({kind,cycle,readback:true});}
 await app.stop(); await eng.stop();
 const copy=join(root,`${kind}-to-${kind==='candidate'?'production':'candidate'}`); cpSync(data,copy,{recursive:true});
 const other=kind==='candidate'?'production':'candidate'; const reopened=await engine(other,copy); app=await serve(copy,reopened.guard); await verify(app,result); evidence({from:kind,to:other,readback:true}); await app.stop(); await reopened.stop();
}
await run('candidate'); await run('production');

```

## Commands and results

The local Python on PATH was CPython 3.13.18. Commands ran from this checkout
with `TMPDIR="$PWD/.work/tmp"`.

```sh
PATH="/Users/josh/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin:$PATH" TMPDIR="$PWD/.work/tmp" deploy/openorange/bin/build-rivet-engine acquire --out "$PWD/.work/tmp/engine-qualification-v3" > .work/tmp/engine-qualification-acquire-v3.log 2>&1
```

Exit 0. All six `git apply --check` operations preceded their corresponding
applications; Cargo vendored the locked dependencies. The earlier v2 source
used for the builds has the same lockfile and vendor configuration as v3;
`cmp` on their configuration files exited 0, and both configurations hash to
`e798fa13f40801ff7f4237c036b6beb88ae42ef1a7cb9b75640985bbd188f85a`.

```sh
PATH="/Users/josh/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin:$PATH" TMPDIR="$PWD/.work/tmp" deploy/openorange/bin/build-rivet-engine build --src "$PWD/.work/tmp/engine-qualification-v2" --out "$PWD/.work/tmp/engine-qualification-build-v3" > .work/tmp/engine-qualification-build-v3.log 2>&1
PATH="/Users/josh/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin:$PATH" TMPDIR="$PWD/.work/tmp" deploy/openorange/bin/build-rivet-engine build --src "$PWD/.work/tmp/engine-qualification-v2" --out "$PWD/.work/tmp/engine-qualification-build-v4" > .work/tmp/engine-qualification-build-v4.log 2>&1
```

The first command exited 0. Both runs use fresh target directories. The
validator was added while the second build was running; the produced records
are checked separately with the final validator.

```sh
mkdir -p .work/tmp/engine-qualification-tests/errors .work/tmp/engine-qualification-tests/target
docker run --rm --network none --platform linux/amd64 --cpus 4 --memory 8g -v "$PWD/.work/tmp/engine-qualification-v2/source:/src:ro" -v "$PWD/.work/tmp/engine-qualification-v2/rustup:/usr/local/rustup:ro" -v "$PWD/.work/tmp/engine-qualification-tests:/out" -w /src -e 'RUSTFLAGS=--cfg tokio_unstable' -e CARGO_TARGET_DIR=/out/target -e RIVET_ERROR_OUTPUT_DIR=/out/errors ghcr.io/rivet-dev/rivet/engine-base-builder@sha256:61ba0bec231a20ebe8501be2d26b4649bbb74f31353d0ea8740785ee467d5d11 sh -c 'cargo --config /src/vendor-config.toml test --locked --offline -j4 -p sqlite-embedded-filesystem && cargo --config /src/vendor-config.toml test --locked --offline -j4 -p rivet-api-public-shim' > .work/tmp/engine-qualification-tests.log 2>&1
PATH="/Users/josh/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin:$PATH" TMPDIR="$PWD/.work/tmp" python3 -m unittest deploy/openorange/tests/test_build_rivet_engine.py deploy/openorange/tests/test_sources.py
```

Both exited 0. The SQLite integration suite passed 8 tests; the public API
suite passed 9 tests. The Python suite passed 6 tests. The Rust test log
SHA-256 is `c9847d4da1c2b0b890f6febe1620abe068c11eae733cec93a28a41e4f4f19d66`.

The complete runtime receipt follows. The histogram records diagnostic
latencies only; it is not a performance acceptance measurement.

```jsonl
{"kind":"candidate","workload":{"releaseId":"engine-qualification","workloadId":"canary-v1","attempted":10,"succeeded":10,"failures":{},"bodyMismatches":0,"acknowledgedWrites":2,"readbackVerified":2,"lostWrites":0,"duplicateMismatches":0,"histogram":{"relativeError":0.01,"buckets":[[2011,1],[7052,1],[7713,1],[11138,1],[12291,1],[21041,1],[23430,1],[24946,1],[30382,1],[92284,1]]},"windowStartMs":0,"windowEndMs":0,"truncated":false}}
{"kind":"candidate","cycle":1,"readback":true}
{"kind":"candidate","cycle":2,"readback":true}
{"kind":"candidate","cycle":3,"readback":true}
{"kind":"candidate","cycle":4,"readback":true}
{"kind":"candidate","cycle":5,"readback":true}
{"kind":"candidate","cycle":6,"readback":true}
{"kind":"candidate","cycle":7,"readback":true}
{"kind":"candidate","cycle":8,"readback":true}
{"kind":"candidate","cycle":9,"readback":true}
{"kind":"candidate","cycle":10,"readback":true}
{"from":"candidate","to":"production","readback":true}
{"kind":"production","workload":{"releaseId":"engine-qualification","workloadId":"canary-v1","attempted":10,"succeeded":10,"failures":{},"bodyMismatches":0,"acknowledgedWrites":2,"readbackVerified":2,"lostWrites":0,"duplicateMismatches":0,"histogram":{"relativeError":0.01,"buckets":[[1154,1],[6743,1],[7442,1],[10092,1],[11238,1],[12402,1],[16819,1],[17432,1],[21041,1],[78539,1]]},"windowStartMs":0,"windowEndMs":0,"truncated":false}}
{"from":"production","to":"candidate","readback":true}
```

The second build command exited 0 after Cargo reported 23m 36s. Both binaries
have SHA-256 `9c1f1c7a1b55b66d730ae6b483fe98a1b0d6b871a36f58bf09b27f5965a3db56`;
`cmp .work/tmp/engine-qualification-build-v3/rivet-engine
.work/tmp/engine-qualification-build-v4/rivet-engine` exited 0. The two build
records also compare equal, with SHA-256
`bd867994865b4c250f87683453e45cfbf78143aafe5201eaeff499b18244e620`.
The final `validate_engine_record` accepted both. `file` identified the binary
as an x86-64 Linux ELF executable. No byte-level nondeterminism appeared in
these two builds.

**Recommendation: HOLD production promotion.** The fixed workload, the
cross-version copies and ten restarts passed, but this short run is not a
sustained availability qualification. The initial history assertion checks that points exist; subsequent recovery
comparisons match the complete returned history bytes, while the event
assertion compares the complete event to its input. A separate inspection of
isolated depot copies, described below, compares every stored host sample
field to the fixture-derived expected payload. The parent can weigh these
limits alongside the existing operational evidence.

The sample inspection copied each of the four stopped depots, started the
appropriate Engine and application, fenced only the copy's installation, and
exported its `samples` rows. It decoded the original fixture through the same
wire decoder and sample validator and compared canonical payloads exactly.
Both candidate-written payloads hash to
`33ef3ed22310a749868f19e988d340b7f0e8d38b3cbaa67b2e769d2f47fe2ac2` before
and after opening with production; both production-written payloads hash to
`6869cef3c75fb8d2fdd198b3a0a2e5fd8ebb949ece725b3059e1d37b8bccb935` before
and after opening with the candidate. Each hash covers the two canonical JSON
payloads separated and terminated by newlines. The inspection exited 0:

```sh
TMPDIR="$PWD/.work/tmp" node .work/tmp/engine-qualification-samples.mts "$PWD/.work/tmp/engine-qualification-build-v3/rivet-engine" "$PWD/.work/tmp/engine-qualification-samples-v2" "$PWD/.work/tmp/engine-qualification-runtime" > .work/tmp/engine-qualification-samples-v2.log 2>&1
```

Its receipt SHA-256 is
`2d56d6856b01e8b8943c9c2cf9309195860ca98daf0ef504619189ad7a2f3b67` and
its script SHA-256 is
`64e47faa2b4e1d68fe4b905f0c3013c8340e4ec0210251165fea4421095dc73a`.
The first auxiliary inspection exited 1 before comparison because it attempted
to JSON-serialize a BigInt from the wire decoder. Its copy was retained; the
successful inspection used the Stats sample validator before serialization.
To reconstruct the successful script, take the runtime runner above through
its `run` function, excluding its last `await run(...)` line, and append:

```typescript
const { fixtureSource } = await import('/Users/josh/repos/stats/cloudflare/test/node/support.ts');
const { encodeFrame } = await import('/Users/josh/repos/stats/cloudflare/src/ingest/encode.ts');
const { decodeFrame } = await import('/Users/josh/repos/stats/cloudflare/src/ingest/frame.ts');
const { canonicalJson } = await import('/Users/josh/repos/stats/cloudflare/src/protocol.ts');
const { validateSample } = await import('/Users/josh/repos/stats/cloudflare/src/ingest/sample.ts');
const { createHash } = await import('node:crypto');
for (const [directory, kind] of [['candidate','candidate'],['candidate-to-production','production'],['production','production'],['production-to-candidate','candidate']]) {
 const src=join(process.argv[4],directory), data=join(root,directory); cpSync(src,data,{recursive:true});
 const eng=await engine(kind,data), app=await serve(data,eng.guard);
 const base=app.origin+'/api/v1/admin/objects/installation';
 const call=async(path,init={})=>{const r=await fetch(base+path,{...init,headers:{...app.headers,...(init.headers??{})}}); const body=await r.text(); if(!r.ok) throw Error(`${directory} ${path}: ${r.status} ${body}`); return JSON.parse(body);};
 await call('/maintenance',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({fenced:true})});
 const manifest=await call('/export/manifest'); const table=manifest.tables.find(t=>t.name==='samples'); assert.ok(table);
 const page=await call('/export/rows?table=samples'); assert.equal(page.next,null); assert.equal(page.rows.length,2);
 const host=page.rows[0][table.columns.indexOf('host_id')]; const payloads=page.rows.map(row=>row[table.columns.indexOf('payload')]);
 const first=JSON.parse(payloads[0]); const input=fixtureSource('sources/linux-normal.json'); const start=Number(input.samples[0].atMs);
 const source={...input,hostId:host,samples:input.samples.map(sample=>({...sample,atMs:String(Number(first.atMs)+Number(sample.atMs)-start)}))};
 const decoded=decodeFrame(encodeFrame(source)); assert.ok(decoded.ok); const expected=decoded.batch.samples.map(sample=>{const validated=validateSample(sample); assert.ok(validated.ok); return canonicalJson(validated.sample);});
 assert.deepEqual(payloads,expected,`${directory}: acknowledged sample payload differs`);
 evidence({directory,kind,sampleCount:payloads.length,payloadSha256:createHash('sha256').update(payloads.join('\n')+'\n').digest('hex'),exact:true});
 await app.stop(); await eng.stop();
}

```

The Stats inputs used for this run had these SHA-256 digests:

| Input | SHA-256 |
| --- | --- |
| `deploy/orange/package.json` | `f7fc5c0d7daf7903ae40aa5b17d80d059a4c13ba433e454ef2cfb6524474ac41` |
| `deploy/orange/pnpm-lock.yaml` | `779de8eea54d956c2a3df84e50c3b691f5bc61fd5589354e2a0f30a227835fdc` |
| `deploy/orange/node_modules/open-orange/dist/bin.js` | `79bd3006dfdc92d96ab83c793d3a9c514106451a445f9db7bae328f1f4fa2232` |
| `deploy/orange/canary/workload.mts` | `d9727695e3637b97cc15c4cffb80600fbef9b3025fc01153de35a69e7edf8abc` |
| `fixtures/v2/sources/linux-normal.json` | `c98b6c6a93f516d18dd410e8d51c2460ef7bea56ba4c1e3d3a891531f51c6067` |
