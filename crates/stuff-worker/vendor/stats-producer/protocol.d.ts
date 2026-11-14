export declare const SCHEMA_VERSION = 1;
export declare const MAX_BATCH_BYTES: number;
export declare const MAX_EVENTS = 128;
export declare const MAX_WORK_MEASUREMENTS = 16;
export declare const MAX_DURATION_MS = 86400000;
export declare const MAX_WORK_VALUE = 1000000000000;
export declare const SERVICE: RegExp;
export declare const EVENT_ID: RegExp;
export declare const OPERATION: RegExp;
export declare const OUTCOME: RegExp;
export declare const RELEASE: RegExp;
export declare const INSTANCE: RegExp;
export declare const HOST: RegExp;
export declare const WORK_KEY: RegExp;
export declare const TRACE_ID: RegExp;
export declare const SPAN_ID: RegExp;
export declare const ERROR_CODE: RegExp;
export declare const SUCCESS_OUTCOME = "ok";
export interface Trace {
    readonly traceId: string;
    readonly spanId: string;
}
export interface EventError {
    readonly code: string;
}
export interface Diagnostics {
    readonly version: 1;
    readonly name: string;
    readonly message: string;
    readonly frames: readonly string[];
}
export declare function boundedDiagnostics(value: Diagnostics): Diagnostics;
export interface ProducerDelivery {
    readonly id: string;
    readonly sequence: number;
    readonly accepted: number;
    readonly dropped: number;
    readonly queued: number;
    readonly startedAtMs: number;
    readonly atMs: number;
}
export interface OperationEvent {
    readonly delivery?: ProducerDelivery;
    readonly schemaVersion: typeof SCHEMA_VERSION;
    readonly eventId: string;
    readonly atMs: number;
    readonly operation: string;
    readonly outcome: string;
    readonly durationMs: number;
    readonly work: Readonly<Record<string, number>>;
    readonly release: string;
    readonly service: string;
    readonly instance?: string;
    readonly host?: string;
    readonly trace?: Trace;
    readonly error?: EventError;
    readonly diagnostics?: Diagnostics;
}
export declare function workOf(value: Readonly<Record<string, number>>): Readonly<Record<string, number>> | null;
export declare function encodeEvent(event: OperationEvent): string;
export declare function encodeBatch(events: readonly OperationEvent[]): string;
