export interface ExecutionContext {
  waitUntil(promise: Promise<unknown>): void;
}

declare global {
  interface Crypto {
    readonly DigestStream: new (algorithm: string) => WritableStream<ArrayBuffer | ArrayBufferView> & { readonly digest: Promise<ArrayBuffer> };
  }
}
