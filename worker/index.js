// worker/index.js
//
// Cloudflare Worker — signed proxy for update blobs.
// Client sends /?id=<token>&ts=<unix>&sig=<hmac>
// Worker validates HMAC, resolves upstream from KV, proxies bytes.

const FRESHNESS_WINDOW_SEC = 300;

// Optional: legacy fallback for tokens not yet in KV. Empty for production.
const LEGACY_MAP = {};

async function hmacHex(secret, message) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(message));
  return [...new Uint8Array(sig)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function notFound() {
  return new Response("Not Found", { status: 404 });
}

async function resolveTarget(id, env) {
  // KV first
  if (env && env.TOKENS) {
    try {
      const hit = await env.TOKENS.get(id);
      if (hit) {
        // Support both plain-string values and JSON values with expiry:
        //   "https://..."
        //   {"url":"https://...","exp":1735689600}
        let entry;
        try {
          entry = JSON.parse(hit);
        } catch (_) {
          return hit;
        }
        if (entry && typeof entry === "object") {
          if (entry.exp && Math.floor(Date.now() / 1000) > entry.exp) {
            return null;
          }
          return entry.url || null;
        }
        return hit;
      }
    } catch (_) {
      // fall through to legacy
    }
  }
  // Legacy fallback
  return LEGACY_MAP[id] || null;
}

async function handleRequest(request, env) {
  if (request.method !== "GET") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const url = new URL(request.url);
  const id = url.searchParams.get("id");
  const ts = url.searchParams.get("ts");
  const sig = url.searchParams.get("sig");

  if (!id || !ts || !sig) return notFound();

  const now = Math.floor(Date.now() / 1000);
  const tsNum = parseInt(ts, 10);
  if (!Number.isFinite(tsNum)) return notFound();
  if (Math.abs(now - tsNum) > FRESHNESS_WINDOW_SEC) {
    return new Response("Expired", { status: 410 });
  }

  const secret = env && env.SHARED_SECRET;
  if (!secret) return new Response("Misconfigured", { status: 500 });

  const expected = await hmacHex(secret, `${id}:${ts}`);
  if (expected !== sig) return notFound();

  const target = await resolveTarget(id, env);
  if (!target) return notFound();

  const upstream = await fetch(target, {
    cf: { cacheTtl: 0, cacheEverything: false },
  });
  if (!upstream.ok) {
    return new Response("Upstream error", { status: 502 });
  }

  const blob = await upstream.arrayBuffer();

  return new Response(blob, {
    headers: {
      "Content-Type": "application/octet-stream",
      "Content-Length": String(blob.byteLength),
      "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
      "Server": "cloudflare",
    },
  });
}

export default {
  async fetch(request, env) {
    return handleRequest(request, env);
  },
};
