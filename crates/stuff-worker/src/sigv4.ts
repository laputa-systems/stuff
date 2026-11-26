export const bytes = (value: string): Uint8Array<ArrayBuffer> => new TextEncoder().encode(value);
export const hex = (value: ArrayBuffer): string => Array.from(new Uint8Array(value), b => b.toString(16).padStart(2, "0")).join("");
export const sha = async (value: string): Promise<string> => hex(await crypto.subtle.digest("SHA-256", bytes(value)));
const mac = async (key: string | ArrayBuffer, value: string): Promise<ArrayBuffer> => {
  const imported = await crypto.subtle.importKey("raw", typeof key === "string" ? bytes(key) : key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return crypto.subtle.sign("HMAC", imported, bytes(value));
};
export const quote = (s: string): string => encodeURIComponent(s).replace(/[!'()*]/g, c => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);
function query(url: URL): string {
  return [...url.searchParams.entries()].map(([k, v]) => [quote(k), quote(v)] as const)
    .sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0)
    .map(([k, v]) => `${k}=${v}`).join("&");
}
const SIGNING_KEYS_LIMIT = 16;
const signingKeys = new Map<string, Promise<CryptoKey>>();
function signingKey(secret: string, day: string, region: string): Promise<CryptoKey> {
  const cacheKey = `${day}\n${region}\n${secret}`;
  let key = signingKeys.get(cacheKey);
  if (key === undefined) {
    key = (async () => crypto.subtle.importKey("raw", await mac(await mac(await mac(await mac(`AWS4${secret}`, day), region), "s3"), "aws4_request"), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]))();
    key.catch(() => signingKeys.delete(cacheKey));
    if (signingKeys.size >= SIGNING_KEYS_LIMIT) signingKeys.delete(signingKeys.keys().next().value!);
    signingKeys.set(cacheKey, key);
  }
  return key;
}
export async function signingMaterial(method: string, url: URL, headers: Headers, names: string[], payload: string, date: string, region: string, secret: string): Promise<{ key: CryptoKey; message: Uint8Array<ArrayBuffer> }> {
  const canonical = `${method}\n${url.pathname}\n${query(url)}\n${names.map(n => `${n}:${headers.get(n)!.trim().replace(/\s+/g, " ")}\n`).join("")}\n${names.join(";")}\n${payload}`;
  const scope = `${date.slice(0, 8)}/${region}/s3/aws4_request`;
  return { key: await signingKey(secret, date.slice(0, 8), region), message: bytes(`AWS4-HMAC-SHA256\n${date}\n${scope}\n${await sha(canonical)}`) };
}
