#!/bin/sh
# Layout check over the dashboard preview: renders it, serves it, and checks
# every page at 390 and 1440 px in a real browser. It fails on horizontal
# page overflow, an empty state shown beside matching rows, a panel title
# overlapping its meta, and clipped headings or links. Wide lookup tables may
# scroll inside their own region. Needs srv and agent-browser.
set -eu

port=${PORT:-8797}
root=$(cd "$(dirname "$0")/.." && pwd)
out="$root/.work/preview/layout-check"
session="stuff-layout-check-$$"

cd "$root"
TMPDIR="$root/.work/tmp" uv run --quiet python -m repomod.dependencies.preview render --out "$out" >/dev/null
srv -p "$port" "$out" >/dev/null 2>&1 &
server=$!
trap 'kill "$server" 2>/dev/null; agent-browser --session "$session" close >/dev/null 2>&1 || true' EXIT INT TERM
sleep 1

probe='(() => {
  const found = [];
  const root = document.documentElement;
  if (root.scrollWidth > root.clientWidth + 1) found.push("page overflows to " + root.scrollWidth + "px");
  for (const empty of document.querySelectorAll("[data-empty]")) {
    const scope = empty.closest("[data-table-scope]");
    const shown = scope && [...scope.querySelectorAll("[data-item], tbody tr")].some((item) => item.offsetParent !== null);
    if (!empty.hidden && empty.offsetParent !== null && shown) found.push("empty state beside rows");
  }
  for (const head of document.querySelectorAll(".ui-panel-head")) {
    const title = head.querySelector(".ui-panel-title h2");
    const meta = head.querySelector(".ui-panel-meta");
    if (!title || !meta || meta.offsetParent === null) continue;
    const a = title.getBoundingClientRect();
    const b = meta.getBoundingClientRect();
    if (a.right > b.left + 1 && b.right > a.left + 1 && a.bottom > b.top + 1 && b.bottom > a.top + 1) {
      found.push("panel title overlaps meta: " + title.textContent.trim());
    }
  }
  for (const text of document.querySelectorAll("h1, h2, h3, a")) {
    if (text.offsetParent === null || getComputedStyle(text).overflow === "visible") continue;
    if (text.scrollWidth > text.clientWidth + 1) found.push("clipped: " + text.textContent.trim().slice(0, 40));
  }
  return found.join("; ");
})()'

pages=$(cd "$out" && ls ./*.html | sed 's|^\./||; s|\.html$||'; echo repos/laputa-systems/xsh/index)
failed=0
for width in 390 1440; do
  agent-browser --session "$session" set viewport "$width" 900 >/dev/null
  for page in $pages; do
    agent-browser --session "$session" open "http://127.0.0.1:$port/$page.html" >/dev/null
    sleep 0.5
    result=$(agent-browser --session "$session" eval "$probe" | tr -d '"')
    if [ -n "$result" ]; then
      echo "$width $page: $result"
      failed=1
    fi
  done
done
[ "$failed" -eq 0 ] && echo "layout check passed: $(echo "$pages" | wc -l | tr -d ' ') pages at 390 and 1440 px"
exit "$failed"
