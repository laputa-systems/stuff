import { createHash } from "node:crypto";

const ALGORITHMS = { "SHA-1": "sha1", "SHA-256": "sha256", "SHA-384": "sha384", "SHA-512": "sha512", MD5: "md5" };

class DigestStream extends WritableStream {
  constructor(algorithm) {
    const name = ALGORITHMS[String(typeof algorithm === "object" ? algorithm?.name : algorithm).toUpperCase()];
    if (name === undefined) throw new TypeError("unsupported digest algorithm");
    const hash = createHash(name);
    let resolve;
    let reject;
    const digest = new Promise((ok, fail) => { resolve = ok; reject = fail; });
    super({
      write(chunk) {
        if (ArrayBuffer.isView(chunk)) hash.update(new Uint8Array(chunk.buffer, chunk.byteOffset, chunk.byteLength));
        else if (chunk instanceof ArrayBuffer) hash.update(new Uint8Array(chunk));
        else throw new TypeError("DigestStream accepts only binary chunks");
      },
      close() {
        const value = hash.digest();
        resolve(value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength));
      },
      abort(reason) { reject(reason); },
    });
    this.digest = digest;
  }
}

export function installDigestStream() {
  if (globalThis.crypto.DigestStream !== undefined) return;
  Object.defineProperty(globalThis.crypto, "DigestStream", { value: DigestStream, configurable: false, enumerable: false, writable: false });
}
