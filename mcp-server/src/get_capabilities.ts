// src/get_capabilities.ts
import fetch from "node-fetch";
import { createHash } from "node:crypto";

/**
 * Fetch a URL and return a small capability summary.
 * Adjust fields to whatever your index.ts expects.
 */
export interface CapabilitiesResult {
  ok: boolean;
  url: string;
  status: number;
  contentType?: string;
  sha256Hex?: string;   // hash of body (text form) for determinism
  length?: number;      // byte length of body
}

/**
 * Get capabilities from a target URL. Safe for strict TS.
 * - Validates input (no null/undefined)
 * - Uses response.text()/arrayBuffer() instead of response.body
 * - Hashes via Node crypto (accepts string/Buffer/Uint8Array cleanly)
 */
export async function getCapabilities(targetUrl: string): Promise<CapabilitiesResult> {
  const raw = (targetUrl ?? "").toString().trim();
  if (!raw) {
    throw new Error("getCapabilities: missing targetUrl");
  }

  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new Error(`getCapabilities: invalid URL: ${raw}`);
  }

  const res = await fetch(url);
  const contentType = res.headers.get("content-type") ?? undefined;

  // Read the response body safely:
  // If you need a text digest, use .text() (deterministic across platforms)
  const bodyText = await res.text();

  // Compute a SHA-256 over the text (works with Node's crypto):
  const sha256Hex = createHash("sha256").update(bodyText).digest("hex");
  const length = Buffer.byteLength(bodyText, "utf8");

  return {
    ok: res.ok,
    url: url.toString(),
    status: res.status,
    contentType,
    sha256Hex,
    length,
  };
}
