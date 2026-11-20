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
