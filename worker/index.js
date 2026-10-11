// worker/index.js
//
// Cloudflare Worker — signed proxy for payload delivery.
// Client sends /?id=<object_key>&ts=<unix>&sig=<hmac>
// Worker validates HMAC, reads the R2 object by key, streams bytes back.

const FRESHNESS_WINDOW_SEC = 300;

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

  // id is the R2 object key. Direct read from the binding.
  const obj = await env.PAYLOAD_BUCKET.get(id);
  if (!obj) return notFound();

  const blob = await obj.arrayBuffer();

  return new Response(blob, {
    headers: {
      "Content-Type": "application/octet-stream",
      "Content-Length": String(blob.byteLength),
      "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
    },
  });
}

export default {
  async fetch(request, env) {
    return handleRequest(request, env);
  },
};
