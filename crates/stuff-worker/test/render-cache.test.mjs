import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import { createContext, runInContext } from "node:vm";
import test from "node:test";

test("concurrent cold renders charge stored bytes once and retain fitting pages", async () => {
  const source = readFileSync(new URL("../entry.ts", import.meta.url), "utf8");
  const start = source.indexOf("const RENDER_CACHE_ENTRIES");
  const end = source.indexOf("function ociPlanResponse", start);
  let renders = 0;
  let release;
  const loaded = new Promise(resolve => { release = resolve; });
  const context = createContext({
    URL, Headers, Response, TextEncoder,
    UNIFIED_BINDINGS: ["MYCRATES"],
    currentGeneration: async () => "g1",
    generationCatalog: async () => { await loaded; return "{}"; },
    unifiedNotReady: () => { throw new Error("unexpected missing catalog"); },
    renderUnified: () => { renders++; return "x".repeat(1024 * 1024); },
  });
  runInContext(stripTypeScriptTypes(source.slice(start, end)), context);
  const request = path => context.unifiedIndex(new Request("https://stuff.test" + path), { STUFF_RELEASE: "test" });
  const burst = Array.from({ length: 16 }, () => request("/"));
  release();
  for (const response of await Promise.all(burst)) {
    assert.equal(response.status, 200);
    assert.equal((await response.text()).length, 1024 * 1024);
  }
  assert.equal(renders, 1);
  assert.equal(runInContext("renderedPageBytes", context), 1024 * 1024);
  await request("/llms.txt");
  assert.equal(renders, 2);
  assert.equal(runInContext("renderedPageBytes", context), 2 * 1024 * 1024);
  assert.equal(runInContext("[...renderedPages.values()].reduce((sum, page) => sum + page.size, 0)", context), 2 * 1024 * 1024);
  await request("/");
  await request("/llms.txt");
  assert.equal(renders, 2);
});
