import { type Diagnostics, type Trace } from "./protocol.ts";
export type { Diagnostics, EventError, OperationEvent, Trace } from "./protocol.ts";
export { MAX_BATCH_BYTES, MAX_EVENTS, SCHEMA_VERSION } from "./protocol.ts";
export interface ProducerConfig {
    readonly endpoint: string;
    readonly service: string;
    readonly token: string | (() => string);
    readonly release: string;
    readonly instance?: string;
    readonly host?: string;
    readonly queueLimit?: number;
    readonly batchSize?: number;
    readonly flushIntervalMs?: number;
    readonly timeoutMs?: number;
    readonly maxRetries?: number;
    readonly backoffBaseMs?: number;
    readonly maxRetryAfterMs?: number;
    readonly fetch?: typeof fetch;
    readonly random?: () => number;
    readonly sleep?: (ms: number) => Promise<void>;
    readonly now?: () => number;
    readonly newEventId?: () => string;
}
export interface OperationInput {
    readonly operation: string;
    readonly outcome: string;
    readonly durationMs: number;
    readonly work?: Readonly<Record<string, number>>;
    readonly eventId?: string;
    readonly atMs?: number;
    readonly instance?: string;
    readonly host?: string;
    readonly trace?: Trace;
    readonly errorCode?: string;
    readonly diagnostics?: Diagnostics;
}
export interface ProducerStats {
    readonly queued: number;
    readonly dropped: number;
    readonly sent: number;
    readonly duplicates: number;
    readonly batches: number;
    readonly retries: number;
    readonly lastError: string | null;
}
export interface Producer {
    record(event: OperationInput): void;
    flush(): Promise<void>;
    shutdown(): Promise<void>;
    stats(): ProducerStats;
}
export declare function createProducer(config?: ProducerConfig | null): Producer;
