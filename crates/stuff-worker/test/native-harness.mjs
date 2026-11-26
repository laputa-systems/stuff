import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { request as httpRequest } from "node:http";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { fakeS3 } from "./native-s3.mjs";

const app = fileURLToPath(new URL("../build/native/app", import.meta.url));
const scratch = fileURLToPath(new URL("../../../.work/tmp", import.meta.url));
export const BINDINGS = { MYCRATES: "mycrates", MYNPM: "mynpm", PYPI: "pypi", OCI: "oci", OCI_BLOBS: "oci-blobs", MIRROR: "mirror" };
const ROUTES = JSON.stringify([
  { host: "crates.test", bucket_binding: "MYCRATES", key_prefix: "" },
  { host: "npm.test", bucket_binding: "MYNPM", key_prefix: "" },
  { host: "pypi.test", bucket_binding: "PYPI", key_prefix: "" },
  { host: "oci.test", bucket_binding: "OCI", key_prefix: "" },
  { host: "mirror.test", bucket_binding: "MIRROR", key_prefix: "" },
]);

export function send(port, url, init = {}) {
  const target = new URL(url);
  const headers = new Headers(init.headers);
  headers.set("host", target.host);
  if (target.protocol === "https:") headers.set("x-forwarded-proto", "https");
  return new Promise((resolve, reject) => {
    const req = httpRequest({ host: "127.0.0.1", port, method: init.method ?? "GET", path: `${target.pathname}${target.search}`, headers: Object.fromEntries(headers) }, res => {
      const chunks = [];
      res.on("data", chunk => chunks.push(chunk));
      res.on("end", () => {
        const responseHeaders = new Headers();
        for (let i = 0; i + 1 < res.rawHeaders.length; i += 2) responseHeaders.append(res.rawHeaders[i], res.rawHeaders[i + 1]);
        const status = res.statusCode;
        const body = status === 204 || status === 304 || (init.method ?? "GET") === "HEAD" ? null : Buffer.concat(chunks);
        resolve(new Response(body, { status, headers: responseHeaders }));
      });
      res.on("error", reject);
    });
    req.on("error", reject);
    if (init.body !== undefined && init.body !== null) req.end(typeof init.body === "string" || init.body instanceof Uint8Array ? init.body : String(init.body));
    else req.end();
  });
}

export function nativeHarness(vars = {}, options = {}) {
  const s3 = options.s3 ?? fakeS3();
  let child;
  let ports;
  let directory;
  let output = "";
  const env = {};
  const harness = {
    s3,
    get output() { return output; },
    get ports() { return ports; },
    async listen() {
      mkdirSync(scratch, { recursive: true });
      directory = options.directory ?? mkdtempSync(join(scratch, "native-"));
      const endpoint = options.endpoint ?? await s3.listen();
      const varsFile = join(directory, "vars.json");
      writeFileSync(varsFile, JSON.stringify({ STUFF_ROUTES: ROUTES, STUFF_UNIFIED_HOST: "stuff.test", STUFF_OCI_HOST: "oci.test", STUFF_S3_BUCKET_BINDINGS: JSON.stringify(BINDINGS), ...vars }));
      Object.assign(env, { S3_ENDPOINT: endpoint, S3_REGION: "us-east-1", S3_ACCESS_KEY_ID: "test", S3_SECRET_ACCESS_KEY: "test" });
      const childEnv = {
        PATH: process.env.PATH, ...env, STUFF_NATIVE_ROLE: options.role ?? "reader", STUFF_RELEASE: "test", STUFF_NATIVE_VARS_FILE: varsFile,
        STUFF_NATIVE_LISTEN: "127.0.0.1:0", STUFF_NATIVE_CONTROL: "127.0.0.1:0", STUFF_NATIVE_DRAIN_S: String(options.drainS ?? 30),
        ...(options.role === "publisher" ? { STUFF_PUBLISH_HOST: "publish.test", STUFF_NATIVE_STATE: join(directory, "state"), STUFF_NATIVE_CONTROL_TOKEN: "control", STUFF_COORDINATOR_TOKEN: "coordinator", STUFF_S3_ACCESS_KEY_ID: "service", STUFF_S3_SECRET_ACCESS_KEY: "service-secret" } : {}),
        ...options.env,
      };
      child = spawn(process.execPath, [join(app, "native/main.mjs")], { env: childEnv, stdio: ["ignore", "pipe", "pipe"] });
      child.stderr.on("data", chunk => { output += chunk; });
      ports = await new Promise((resolve, reject) => {
        let buffered = "";
        child.stdout.on("data", chunk => {
          output += chunk;
          buffered += chunk;
          for (const line of buffered.split("\n")) {
            if (!line.startsWith("{")) continue;
            try { const event = JSON.parse(line); if (event.event === "listening") resolve(event); } catch { continue; }
          }
        });
        child.once("exit", code => reject(new Error(`native host exited ${code}: ${output}`)));
      });
      return ports;
    },
    exited: () => new Promise(resolve => child.exitCode !== null || child.signalCode !== null ? resolve(child.exitCode ?? child.signalCode) : child.once("exit", (code, signal) => resolve(code ?? signal))),
    stop(signal = "SIGTERM") { child.kill(signal); return harness.exited(); },
    async close() {
      if (child && child.exitCode === null && child.signalCode === null) await harness.stop();
      if (!options.s3) await s3.close();
      if (!options.directory && directory) rmSync(directory, { recursive: true, force: true });
    },
    fetch: (url, init) => send(ports.listen.port, url, init),
    control(path, init = {}) {
      return send(ports.control.port, `http://control${path}`, { ...init, headers: { authorization: "Bearer control", ...(init.headers ?? {}) } });
    },
    getWorker() {
      return {
        fetch: (url, init) => send(ports.listen.port, url, init),
        async getEnv() {
          const { s3Bucket } = await import(join(app, "native/bucket.mjs"));
          return Object.fromEntries(Object.entries(BINDINGS).map(([binding, name]) => [binding, s3Bucket(env, name)]));
        },
      };
    },
  };
  return harness;
}
