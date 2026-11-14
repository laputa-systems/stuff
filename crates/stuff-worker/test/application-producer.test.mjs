import assert from "node:assert/strict";
import { createServer } from "node:http";
import test from "node:test";
import { recordOperation, requestOperation, flushOperations } from "../src/telemetry.ts";

test("registry telemetry uses integer wall time, redacts errors and survives Stats failure", async () => {
  const requests=[];
  let status=200;
  const server=createServer((req,res)=>{const chunks=[];req.on("data",chunk=>chunks.push(chunk));req.on("end",()=>{requests.push({headers:req.headers,body:Buffer.concat(chunks).toString()});res.writeHead(status,{"content-type":"application/json"});res.end(JSON.stringify({accepted:1,duplicate:0}));});});
  await new Promise(ok=>server.listen(0,"127.0.0.1",ok));
  try {
    const config={APPLICATION_EVENTS_ENDPOINT:`http://127.0.0.1:${server.address().port}`,APPLICATION_EVENTS_SERVICE:"stuff",APPLICATION_EVENTS_TOKEN:"private-auth",STUFF_RELEASE:"test-release"};
    const error=new Error("private-auth\nprivate-auth");
    recordOperation(config,"registry.request",12.7,error);await flushOperations();
    assert.equal(requests.length,1);
    assert.equal(requests[0].headers.authorization,"Bearer private-auth");
    assert.equal(requests[0].body.includes("private-auth"),false);
    const body=JSON.parse(requests[0].body);
    assert.equal(body.events[0].durationMs,13);
    assert.equal(body.events[0].outcome,"error");
    assert.equal(body.events[0].cpuMs,undefined);
    status=503;recordOperation({...config,APPLICATION_EVENTS_TOKEN:"rotated-auth"},"registry.publication.attempt.npm",0.4,undefined);
    await assert.doesNotReject(flushOperations());
    assert.equal(requests.length,4);
    assert.equal(requests[1].headers.authorization,"Bearer rotated-auth");
    assert.equal(JSON.parse(requests[1].body).events[0].operation,"registry.publication.attempt.npm");
  }finally{server.closeAllConnections();await new Promise(ok=>server.close(ok));}
});

test("publication telemetry has bounded operation names and counts receipt retries as attempts", () => {
  for (const registry of ["cargo", "npm", "pypi", "oci", "mirror"]) {
    for (const operation of ["activate", "rollback"]) {
      assert.equal(requestOperation(new Request(`https://registry/_publication/${registry}/${operation}`, {method:"POST"})), `registry.publication.attempt.${registry}`);
    }
  }
  assert.equal(requestOperation(new Request("https://registry/v2/private/repository/manifests/latest", {method:"PUT"})), "registry.publication.attempt.oci");
  for (const path of ["/_publication/untrusted/activate", "/_publication/npm/renew", "/_s3/private/path"]) {
    assert.equal(requestOperation(new Request(`https://registry${path}`, {method:"POST"})), "registry.request");
  }
});
