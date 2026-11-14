import assert from "node:assert/strict";
import test from "node:test";
import { createHash, createHmac } from "node:crypto";
import { spawn, execFileSync } from "node:child_process";
import { createServer, request } from "node:http";
import { mkdirSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { resolve, join } from "node:path";
import { generate } from "../scripts/orange.mjs";
const root = resolve(import.meta.dirname, "../../..");
const workerDir = resolve(import.meta.dirname, "..");
const hash = value => createHash("sha256").update(value).digest("hex");
const hmac = (key, value) => createHmac("sha256", key).update(value).digest();
const quote = value => encodeURIComponent(value).replace(/[!'()*]/g, c => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);
function signature(method, path, headers, signed, secret) {
  const url = new URL(path, "http://test.invalid");
  const date = headers["x-amz-date"];
  const query = [...url.searchParams].map(([k,v]) => [quote(k),quote(v)]).sort(([ak,av],[bk,bv]) => ak.localeCompare(bk) || av.localeCompare(bv)).map(pair => pair.join("=")).join("&");
  const canonical = [method,url.pathname,query,signed.map(key => `${key}:${headers[key].trim().replace(/\s+/g," ")}\n`).join(""),signed.join(";"),headers["x-amz-content-sha256"]].join("\n");
  const scope = `${date.slice(0,8)}/auto/s3/aws4_request`;
  const key = hmac(hmac(hmac(hmac(`AWS4${secret}`,date.slice(0,8)),"auto"),"s3"),"aws4_request");
  return createHmac("sha256",key).update(["AWS4-HMAC-SHA256",date,scope,hash(canonical)].join("\n")).digest("hex");
}
async function listen(server) { await new Promise(ok => server.listen(0,"127.0.0.1",ok)); return server.address().port; }
function signed(method,path,body,token,overrides={}) {
  const date = new Date().toISOString().replace(/[-:]/g,"").replace(/\.\d{3}/,"");
  const headers = {host:"stuff.17166969.xyz","x-amz-date":date,"x-amz-content-sha256":hash(body),...(token ? {"x-amz-security-token":token}:{}),...(body.length || method === "PUT" || method === "POST" ? {"content-length":String(body.length)}:{}),...overrides};
  const names = Object.keys(headers).sort();
  headers.authorization = `AWS4-HMAC-SHA256 Credential=service/${date.slice(0,8)}/auto/s3/aws4_request, SignedHeaders=${names.join(";")}, Signature=${signature(method,path,headers,names,"service-secret")}`;
  return headers;
}

test("Orange S3 gateway verifies signatures, streams bytes and fences mutations", {timeout:120000}, async t => {
  execFileSync("pnpm",["run","build"],{cwd:workerDir,stdio:"inherit"});
  mkdirSync(join(root,".work/tmp"),{recursive:true});
  const directory = mkdtempSync(join(root,".work/tmp/gateway-orange-"));
  const objects = new Map();
  let firstBytes;
  let signalFirstBytes = () => {};
  const backend = createServer((req,res) => {
    const auth = /Credential=backend\/[^,]+, SignedHeaders=([^,]+), Signature=([a-f0-9]{64})/.exec(req.headers.authorization ?? "");
    if (!auth || auth[2] !== signature(req.method,req.url,req.headers,auth[1].split(";"),"backend-secret")) {res.writeHead(403);res.end();req.resume();return;}
    const key = new URL(req.url,"http://backend").pathname;
    if ((req.method === "PUT" || req.method === "POST") && req.headers["if-none-match"] === "*" && objects.has(key)) {res.writeHead(412);res.end();req.resume();return;}
    const chunks = [];
    req.on("error",()=>{});
    req.on("data",chunk => { chunks.push(chunk); if (key.endsWith("/stream")) signalFirstBytes(); });
    req.on("end",()=>{
      const body = Buffer.concat(chunks);
      if (hash(body) !== req.headers["x-amz-content-sha256"]) {res.writeHead(400);res.end();return;}
      if (req.method === "PUT" || req.method === "POST") {objects.set(key,body);res.writeHead(200,{etag:`"${createHash("md5").update(body).digest("hex")}"`});res.end();return;}
      const found = objects.get(key);
      if (!found) {res.writeHead(404);res.end();return;}
      res.writeHead(200,{"content-length":found.length,etag:`"${createHash("md5").update(found).digest("hex")}"`});res.end(req.method === "HEAD" ? undefined : found);
    });
  });
  const backendPort = await listen(backend);
  const holder = createServer();const port = await listen(holder);await new Promise(ok=>holder.close(ok));
  let child;
  t.after(async()=>{
    if (child) {
      const close = child.exitCode === null ? new Promise(ok=>child.once("close",ok)) : Promise.resolve();
      if (child.pid) {try {process.kill(-child.pid,"SIGTERM");}catch{}}
      const timer=setTimeout(()=>{try{process.kill(-child.pid,"SIGKILL");}catch{}},5000);
      await close;clearTimeout(timer);
    }
    backend.closeAllConnections();await new Promise(ok=>backend.close(ok));rmSync(directory,{recursive:true,force:true});
  });
  const file=join(directory,"orange.jsonc");const config=generate(file,"gateway-test");
  const mapping=Object.fromEntries(config.r2_buckets.map(value=>[value.binding,`custom-${value.binding.toLowerCase().replaceAll("_","-")}`]));
  for(const binding of config.r2_buckets)binding.bucket_name=mapping[binding.binding];
  Object.assign(config.vars,{STUFF_S3_BUCKET_BINDINGS:JSON.stringify(mapping),STUFF_COORDINATOR_ENABLED:"true",STUFF_COORDINATOR_TOKEN:"management",STUFF_S3_ACCESS_KEY_ID:"service",STUFF_S3_SECRET_ACCESS_KEY:"service-secret",S3_ENDPOINT:`http://127.0.0.1:${backendPort}`,S3_REGION:"auto",S3_ACCESS_KEY_ID:"backend",S3_SECRET_ACCESS_KEY:"backend-secret"});
  const wrapper=join(directory,"wrapper.mjs");
  writeFileSync(wrapper,`import worker from ${JSON.stringify(join(workerDir,".cloudflare/output/v0/workers/default/bundle/entry.js"))};export {PublicationCoordinator} from ${JSON.stringify(join(workerDir,".cloudflare/output/v0/workers/default/bundle/entry.js"))};let offset=0;const now=Date.now;Date.now=()=>now()+offset;export default {async fetch(req,env,ctx){const path=new URL(req.url).pathname;if(path==="/__clock"){offset+=600000;return new Response("ok");}if(path==="/__seed"){await env.MYCRATES.put("current","g0");await env.MYCRATES.put("manifests/g0.json",JSON.stringify({schemaVersion:1,objects:[]}));return new Response("ok");}return worker.fetch(req,env,ctx);}};`);
  config.main=wrapper;writeFileSync(file,JSON.stringify(config));
  child=spawn(process.execPath,[join(workerDir,"orange/node_modules/open-orange/dist/bin.js"),"dev","--json","--ip","127.0.0.1","--port",String(port),"--config",file],{cwd:directory,detached:true,stdio:["ignore","pipe","pipe"]});
  let logs="";
  await new Promise((ok,fail)=>{const timer=setTimeout(()=>fail(new Error(logs)),60000);child.stdout.on("data",chunk=>{logs=(logs+chunk).slice(-32768);if(logs.includes('"type":"ready"')){clearTimeout(timer);ok();}});child.stderr.on("data",chunk=>{logs=(logs+chunk).slice(-32768);});child.once("exit",code=>{clearTimeout(timer);fail(new Error(`Orange exit ${code}: ${logs}`));});});
  const call=(method,path,body=Buffer.alloc(0),headers={})=>new Promise((ok,fail)=>{
    const req=request({host:"127.0.0.1",port,path,method,headers:{host:"stuff.17166969.xyz",...headers}},res=>{const chunks=[];res.on("data",chunk=>chunks.push(chunk));res.on("end",()=>ok({status:res.statusCode,headers:res.headers,body:Buffer.concat(chunks)}));});req.on("error",fail);req.end(body);
  });
  assert.equal((await call("POST","/__seed")).status,200);
  const lease=JSON.parse((await call("POST","/_publication/cargo/begin",Buffer.from("{}"),{authorization:"Bearer management"})).body);
  assert.ok(lease.token);
  const path="/_s3/custom-mycrates/generations/g1/data";const body=Buffer.from("immutable bytes");
  assert.equal((await call("PUT",path,body,signed("PUT",path,body,lease.token))).status,200,logs);
  assert.deepEqual(objects.get("/custom-mycrates/generations/g1/data"),body);
  assert.equal((await call("PUT",path,body,signed("PUT",path,body,lease.token))).status,412);
  assert.equal((await call("GET",path,Buffer.alloc(0),signed("GET",path,Buffer.alloc(0)))).body.toString(),body.toString());
  assert.equal((await call("HEAD",path,Buffer.alloc(0),signed("HEAD",path,Buffer.alloc(0)))).headers["content-length"],String(body.length));
  for(const method of ["PUT","DELETE"]) {const current="/_s3/custom-mycrates/current";assert.equal((await call(method,current,body,signed(method,current,body,lease.token))).status,403);}
  const marker="/_s3/custom-mycrates/current";assert.equal((await call("GET",marker,Buffer.alloc(0),signed("GET",marker,Buffer.alloc(0)))).body.toString(),"g0");
  const bad={...signed("PUT",path,body,lease.token)};bad["x-amz-security-token"]="modified";assert.equal((await call("PUT",path,body,bad)).status,403);
  const old=signed("GET",path,Buffer.alloc(0),undefined,{"x-amz-date":"20000101T000000Z"});assert.equal((await call("GET",path,Buffer.alloc(0),old)).status,403);
  const corrupt="/_s3/custom-mycrates/generations/g1/corrupt";assert.equal((await call("PUT",corrupt,Buffer.from("changed bytes!!"),signed("PUT",corrupt,body,lease.token))).status,400);
  assert.equal(objects.has("/custom-mycrates/generations/g1/corrupt"),false);
  firstBytes=new Promise(ok=>{signalFirstBytes=ok;});
  const streamed=Buffer.alloc(256*1024,7);const streamPath="/_s3/custom-mycrates/generations/g1/stream";
  const streamedResponse=new Promise((ok,fail)=>{
    const req=request({host:"127.0.0.1",port,path:streamPath,method:"PUT",headers:signed("PUT",streamPath,streamed,lease.token)},res=>{res.resume();res.on("end",()=>ok(res.statusCode));});req.on("error",fail);req.write(streamed.subarray(0,128*1024));
    void firstBytes.then(()=>req.end(streamed.subarray(128*1024))).catch(fail);
  });
  assert.equal(await streamedResponse,200,"backend receives bytes before the client finishes uploading");
  assert.deepEqual(objects.get("/custom-mycrates/generations/g1/stream"),streamed);
  const complete=path+"?uploadId=existing";assert.equal((await call("POST",complete,body,signed("POST",complete,body,lease.token))).status,412,"multipart completion is conditional");
  await call("POST","/__clock");const expired="/_s3/custom-mycrates/generations/g2/data";assert.equal((await call("PUT",expired,body,signed("PUT",expired,body,lease.token))).status,403);
});
