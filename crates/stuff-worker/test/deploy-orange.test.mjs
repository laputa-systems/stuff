import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../../..");
const deploy = join(root, "crates/stuff-worker/orange/deploy.sh");
const scratch = join(root, ".work/tmp");
mkdirSync(scratch, { recursive: true });

function run(t, scenario) {
  const dir = mkdtempSync(join(scratch, "deploy-test-"));

  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const bin = join(dir, "bin");
  mkdirSync(bin);
  mkdirSync(join(dir, "crates/stuff-worker/orange"), { recursive: true });
  const script = (path, body) => { writeFileSync(path, `#!/bin/sh\nset -eu\n${body}\n`); chmodSync(path, 0o755); };
  script(join(bin, "git"), `case "$*" in *--show-toplevel*) printf '%s\\n' "$TEST_ROOT";; *--short=12*) echo abcdef123456;; *) exit 1;; esac`);
  script(join(dir, "crates/stuff-worker/orange/build-image.sh"), `[ "$SCENARIO" != build-fail ] || exit 1\necho stuff:abcdef123456`);
  script(join(bin, "ssh"), `
printf '%s\\n' "$*" >> "$TEST_ROOT/log"
case "$*" in
  *'tailscale ip -4'*) if [ "$SCENARIO" = bad-ip ]; then echo invalid; else echo 100.64.1.2; fi ;;
  *'oo deployment stuff'*)
    image=$(cat "$TEST_ROOT/image")
    if [ "$SCENARIO" = stale ] && [ "$image" = stuff:abcdef123456 ]; then image=stuff:other; printf '%s' "$image" > "$TEST_ROOT/image"; fi
    printf '{"image":"%s"}\\n' "$image" ;;
  *'oo set-image stuff '*) [ "$(cat "$TEST_ROOT/image")" = "\${9}" ] || exit 1; printf '%s' "\${7}" > "$TEST_ROOT/image" ;;
  *'rc-service oo-app.stuff restart'*)
    if [ "$SCENARIO" = restart-fail ] && [ "$(cat "$TEST_ROOT/image")" = stuff:abcdef123456 ]; then exit 1; fi ;;
  *'oo wait app stuff 90'*) if [ "$SCENARIO" = term ] && [ "$(cat "$TEST_ROOT/image")" = stuff:abcdef123456 ]; then kill -TERM "$PPID"; fi ;;
  *'oo record-deployment stuff --if-current '*) [ "$SCENARIO" != marker-fail ] || exit 1 ;;
  *) exit 1 ;;
esac`);
  script(join(bin, "curl"), `printf '%s\\n' "$*" >> "$TEST_ROOT/log"\nif [ "$SCENARIO" = health-fail ]; then echo 503; else echo 200; fi`);
  writeFileSync(join(dir, "image"), "stuff:previous");
  const result = spawnSync("/bin/sh", [deploy, "test-host"], { env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, TEST_ROOT: dir, SCENARIO: scenario }, encoding: "utf8", timeout: 10000 });
  assert.equal(result.error, undefined);
  return { ...result, log: readFileSync(join(dir, "log"), "utf8"), image: readFileSync(join(dir, "image"), "utf8") };
}

test("preflight failure never changes the image", (t) => {
  for (const scenario of ["bad-ip", "build-fail"]) {
    const result = run(t, scenario);
    assert.notEqual(result.status, 0);
    assert.equal(result.image, "stuff:previous");
    assert.doesNotMatch(result.log, /set-image/);
  }
});

test("restart, readiness signal, stale selection and health failure restore the previous image", (t) => {
  for (const scenario of ["restart-fail", "term", "health-fail"]) {
    const result = run(t, scenario);
    assert.notEqual(result.status, 0, `${scenario}: ${result.stderr}`);
    assert.equal(result.image, "stuff:previous", scenario);
    assert.match(result.log, /set-image stuff stuff:previous/);
    assert.match(result.stderr, /restored the previous Orange image/);
    if (scenario === "term") assert.equal(result.status, 143);
  }
});

test("a concurrent image change is preserved when rollback is refused", t => {
  const result = run(t, "stale");
  assert.notEqual(result.status, 0);
  assert.equal(result.image, "stuff:other");
  assert.match(result.log, /--if-current stuff:abcdef123456/);
});

test("successful deploy verifies the selected image and routes HTTPS to the host", (t) => {
  const result = run(t, "success");
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.image, "stuff:abcdef123456");
  assert.match(result.log, /oo wait app stuff 90/);
  assert.match(result.log, /--resolve stuff\.17166969\.xyz:443:100\.64\.1\.2/);
  assert.match(result.log, /https:\/\/stuff\.17166969\.xyz\//);
  assert.equal((result.log.match(/oo deployment stuff/g) ?? []).length, 3);
  assert.match(result.log, /record-deployment stuff --if-current stuff:abcdef123456/);
});

test("a failed marker delivery leaves the healthy deployment selected", t => {
  const result = run(t, "marker-fail");
  assert.notEqual(result.status, 0);
  assert.equal(result.image, "stuff:abcdef123456");
  assert.doesNotMatch(result.log, /set-image stuff stuff:previous/);
});
