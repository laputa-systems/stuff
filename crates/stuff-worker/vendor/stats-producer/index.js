import { encodeBatch, encodeEvent, ERROR_CODE, EVENT_ID, HOST, INSTANCE, MAX_BATCH_BYTES, MAX_DURATION_MS, MAX_EVENTS, OPERATION, OUTCOME, RELEASE, SERVICE, SUCCESS_OUTCOME, TRACE_ID, SPAN_ID, boundedDiagnostics, workOf } from "./protocol.js";
export { MAX_BATCH_BYTES, MAX_EVENTS, SCHEMA_VERSION } from "./protocol.js";
const MAX_ACK_BYTES = 4096;
const DEFAULT_QUEUE_LIMIT = 256;
const MAX_QUEUE_LIMIT = 256;
const DEFAULT_BATCH_SIZE = 64;
const DEFAULT_FLUSH_INTERVAL_MS = 5000;
const DEFAULT_TIMEOUT_MS = 5000;
const DEFAULT_MAX_RETRIES = 5;
const DEFAULT_BACKOFF_BASE_MS = 250;
const DEFAULT_MAX_RETRY_AFTER_MS = 30_000;
const EMPTY_STATS = { queued: 0, dropped: 0, sent: 0, duplicates: 0, batches: 0, retries: 0, lastError: null };
function disabledProducer() {
    return {
        record: () => { },
        flush: () => Promise.resolve(),
        shutdown: () => Promise.resolve(),
        stats: () => EMPTY_STATS
    };
}
function bound(value, fallback, low, high) {
    if (value === undefined)
        return fallback;
    if (!Number.isSafeInteger(value) || value < low || value > high)
        throw new TypeError(`producer limit must be an integer from ${low} to ${high}`);
    return value;
}
function defaultEventId() {
    const randomUUID = globalThis.crypto?.randomUUID;
    if (typeof randomUUID === "function")
        return randomUUID.call(globalThis.crypto);
    return `${Date.now().toString(36)}-${Math.floor(Math.random() * 1_000_000_000).toString(36)}`;
}
function serverMessage(error) {
    return error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError") ? "timeout" : "network";
}
export function createProducer(config) {
    if (config === undefined || config === null)
        return disabledProducer();
    const settings = config;
    const endpoint = settings.endpoint.trim();
    const service = settings.service.trim();
    const release = settings.release.trim();
    const staticToken = typeof settings.token === "string" ? settings.token.trim() : null;
    if (endpoint === "" || service === "" || release === "" || staticToken === "")
        return disabledProducer();
    if (!SERVICE.test(service))
        throw new TypeError("service must be 1-32 lowercase letters, digits, or hyphens, starting with a letter");
    if (!RELEASE.test(release))
        throw new TypeError("release must be 1-64 letters, digits, or ._:+- starting with a letter or digit");
    if (config.instance !== undefined && !INSTANCE.test(config.instance))
        throw new TypeError("instance must be 1-128 letters, digits, or ._:- starting with a letter or digit");
    if (config.host !== undefined && !HOST.test(config.host))
        throw new TypeError("host must be 1-128 letters, digits, or ._:- starting with a letter or digit");
    let base;
    try {
        base = new URL(endpoint);
    }
    catch {
        throw new TypeError("endpoint must be a URL");
    }
    if ((base.protocol !== "https:" && base.protocol !== "http:") || base.pathname !== "/" || base.search !== "" || base.hash !== "" || base.username !== "" || base.password !== "") {
        throw new TypeError("endpoint must be a bare http or https origin");
    }
    const fetchFn = config.fetch ?? globalThis.fetch;
    if (typeof fetchFn !== "function")
        return disabledProducer();
    const queueLimit = bound(config.queueLimit, DEFAULT_QUEUE_LIMIT, 1, MAX_QUEUE_LIMIT);
    const batchSize = bound(config.batchSize, DEFAULT_BATCH_SIZE, 1, MAX_EVENTS);
    const flushIntervalMs = bound(config.flushIntervalMs, DEFAULT_FLUSH_INTERVAL_MS, 1, 3_600_000);
    const timeoutMs = bound(config.timeoutMs, DEFAULT_TIMEOUT_MS, 1, 120_000);
    const maxRetries = bound(config.maxRetries, DEFAULT_MAX_RETRIES, 0, 10);
    const backoffBaseMs = bound(config.backoffBaseMs, DEFAULT_BACKOFF_BASE_MS, 1, 60_000);
    const maxRetryAfterMs = bound(config.maxRetryAfterMs, DEFAULT_MAX_RETRY_AFTER_MS, 1, 300_000);
    const random = config.random ?? Math.random;
    const sleep = config.sleep ?? ((ms) => new Promise(resolve => setTimeout(resolve, ms)));
    const now = config.now ?? Date.now;
    const newEventId = config.newEventId ?? defaultEventId;
    const tokenValue = () => typeof settings.token === "string" ? settings.token : settings.token();
    const target = new URL(`/ingest/observe/v1/${encodeURIComponent(service)}/batches`, base).toString();
    const encoder = new TextEncoder();
    const producerId = defaultEventId();
    const startedAtMs = now();
    let accepted = 0;
    const queue = [];
    let timer = null;
    let active = null;
    let closed = false;
    let dropped = 0;
    let sent = 0;
    let duplicates = 0;
    let batches = 0;
    let retries = 0;
    let lastError = null;
    function normalize(input) {
        const eventId = input.eventId ?? newEventId();
        const atMs = input.atMs ?? now();
        const durationMs = input.durationMs;
        const work = workOf(input.work ?? {});
        const instance = input.instance ?? settings.instance;
        const host = input.host ?? settings.host;
        if (!EVENT_ID.test(eventId) || !OPERATION.test(input.operation) || !OUTCOME.test(input.outcome))
            return null;
        if (!Number.isSafeInteger(atMs) || atMs <= 0 || !Number.isSafeInteger(durationMs) || durationMs < 0 || durationMs > MAX_DURATION_MS)
            return null;
        if (work === null)
            return null;
        if (instance !== undefined && !INSTANCE.test(instance))
            return null;
        if (host !== undefined && !HOST.test(host))
            return null;
        if (input.trace !== undefined && (!TRACE_ID.test(input.trace.traceId) || !SPAN_ID.test(input.trace.spanId)))
            return null;
        if (input.errorCode !== undefined && (typeof input.errorCode !== "string" || !ERROR_CODE.test(input.errorCode) || input.outcome === SUCCESS_OUTCOME))
            return null;
        if (input.diagnostics !== undefined && (input.diagnostics.version !== 1 || typeof input.diagnostics.name !== "string" || typeof input.diagnostics.message !== "string" || !Array.isArray(input.diagnostics.frames) || !input.diagnostics.frames.every(frame => typeof frame === "string")))
            return null;
        return {
            schemaVersion: 1,
            eventId,
            atMs,
            operation: input.operation,
            outcome: input.outcome,
            durationMs,
            work,
            release,
            service,
            ...(instance === undefined ? {} : { instance }),
            ...(host === undefined ? {} : { host }),
            ...(input.trace === undefined ? {} : { trace: input.trace }),
            ...(input.errorCode === undefined ? {} : { error: { code: input.errorCode } }),
            ...(input.diagnostics === undefined ? {} : { diagnostics: boundedDiagnostics(input.diagnostics) })
        };
    }
    function backoff(attempt, retryAfterMs) {
        if (retryAfterMs !== null)
            return Math.min(retryAfterMs, maxRetryAfterMs);
        const ceiling = Math.min(backoffBaseMs * 2 ** attempt, maxRetryAfterMs);
        return Math.max(1, Math.round(ceiling * (0.5 + random() * 0.5)));
    }
    function takeBatch() {
        const batch = [];
        let size = 13; // {"events":[]} plus one comma for each event after the first.
        while (queue.length > 0 && batch.length < batchSize) {
            const next = queue[0];
            const added = next.size + (batch.length === 0 ? 0 : 1);
            if (size + added > MAX_BATCH_BYTES)
                break;
            size += added;
            batch.push(queue.shift().event);
        }
        if (batch.length === 0 && queue.length > 0) {
            queue.shift();
            dropped += 1;
            lastError = "event_too_large";
        }
        const atMs = now();
        return batch.map(event => ({ ...event, delivery: { ...event.delivery, accepted, dropped, queued: queue.length, atMs } }));
    }
    async function readAck(response) {
        if (response.body === null)
            return null;
        const reader = response.body.getReader();
        const chunks = [];
        let size = 0;
        try {
            for (;;) {
                const step = await reader.read();
                if (step.done)
                    break;
                size += step.value.byteLength;
                if (size > MAX_ACK_BYTES) {
                    await reader.cancel();
                    return null;
                }
                chunks.push(step.value);
            }
        }
        catch {
            return null;
        }
        const bytes = new Uint8Array(size);
        let offset = 0;
        for (const chunk of chunks) {
            bytes.set(chunk, offset);
            offset += chunk.byteLength;
        }
        let value;
        try {
            value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
        }
        catch {
            return null;
        }
        if (typeof value !== "object" || value === null)
            return null;
        const { accepted, duplicate } = value;
        if (!Number.isSafeInteger(accepted) || accepted < 0 || !Number.isSafeInteger(duplicate) || duplicate < 0)
            return null;
        return { accepted: accepted, duplicate: duplicate };
    }
    function drop(batch, reason) {
        dropped += batch.length;
        lastError = reason;
    }
    async function send(batch) {
        const body = encodeBatch(batch);
        for (let attempt = 0; attempt <= maxRetries; attempt += 1) {
            let token;
            try {
                token = tokenValue();
            }
            catch {
                drop(batch, "token_unavailable");
                return;
            }
            let response;
            try {
                response = await fetchFn(target, {
                    method: "POST",
                    headers: { authorization: `Bearer ${token}`, "content-type": "application/json" },
                    body,
                    signal: AbortSignal.timeout(timeoutMs)
                });
            }
            catch (error) {
                if (attempt === maxRetries) {
                    drop(batch, serverMessage(error));
                    return;
                }
                await sleep(backoff(attempt, null));
                retries += 1;
                continue;
            }
            if (response.ok) {
                const ack = await readAck(response);
                if (ack !== null) {
                    sent += ack.accepted;
                    duplicates += ack.duplicate;
                    batches += 1;
                    return;
                }
                if (attempt === maxRetries) {
                    drop(batch, "malformed_response");
                    return;
                }
                await sleep(backoff(attempt, null));
                retries += 1;
                continue;
            }
            if (response.status === 401 || response.status === 403) {
                let next = null;
                try {
                    next = tokenValue();
                }
                catch {
                    next = null;
                }
                if (next !== null && next !== token && attempt < maxRetries) {
                    retries += 1;
                    continue;
                }
                drop(batch, `http_${response.status}`);
                return;
            }
            if (response.status === 408 || response.status === 425 || response.status === 429 || response.status >= 500) {
                if (attempt === maxRetries) {
                    drop(batch, `http_${response.status}`);
                    return;
                }
                const header = response.headers.get("retry-after");
                const retryAfter = header !== null && /^\d{1,10}$/u.test(header) ? Number(header) * 1000 : null;
                await sleep(backoff(attempt, retryAfter));
                retries += 1;
                continue;
            }
            drop(batch, `http_${response.status}`);
            return;
        }
    }
    function schedule() {
        if (timer !== null || closed)
            return;
        timer = setTimeout(() => {
            timer = null;
            void drain();
        }, flushIntervalMs);
        timer.unref?.();
    }
    function drain() {
        if (active !== null)
            return active;
        active = (async () => {
            for (;;) {
                const batch = takeBatch();
                if (batch.length === 0)
                    return;
                await send(batch);
            }
        })().finally(() => {
            active = null;
        });
        return active;
    }
    function record(input) {
        if (closed) {
            dropped += 1;
            lastError = "closed";
            return;
        }
        const event = normalize(input);
        if (event === null) {
            dropped += 1;
            lastError = "invalid_event";
            return;
        }
        if (queue.length >= queueLimit) {
            queue.shift();
            dropped += 1;
            lastError = "queue_overflow";
        }
        accepted += 1;
        const queuedEvent = { ...event, delivery: { id: producerId, sequence: accepted, accepted, dropped, queued: 0, startedAtMs, atMs: now() } };
        const sized = { ...queuedEvent, delivery: { ...queuedEvent.delivery, accepted: Number.MAX_SAFE_INTEGER, dropped: Number.MAX_SAFE_INTEGER, queued: MAX_QUEUE_LIMIT, atMs: Number.MAX_SAFE_INTEGER } };
        queue.push({ event: queuedEvent, size: encoder.encode(encodeEvent(sized)).byteLength });
        if (queue.length >= batchSize)
            void drain().catch(() => { lastError = "internal"; });
        else
            schedule();
    }
    async function flush() {
        if (timer !== null) {
            clearTimeout(timer);
            timer = null;
        }
        for (;;) {
            if (active !== null) {
                await active;
                continue;
            }
            if (queue.length === 0)
                return;
            await drain();
        }
    }
    return {
        record,
        flush,
        async shutdown() {
            closed = true;
            if (timer !== null) {
                clearTimeout(timer);
                timer = null;
            }
            await flush();
        },
        stats: () => ({ queued: queue.length, dropped, sent, duplicates, batches, retries, lastError })
    };
}
