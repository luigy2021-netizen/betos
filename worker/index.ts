/** Cloudflare Worker entry point for the vinext-starter template. */
import { handleImageOptimization, DEFAULT_DEVICE_SIZES, DEFAULT_IMAGE_SIZES } from "vinext/server/image-optimization";
import handler from "vinext/server/app-router-entry";

interface Env {
  ASSETS: Fetcher;
  DB: D1Database;
  GOOGLE_SERVICE_ACCOUNT_EMAIL: string;
  GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY: string;
  GOOGLE_SPREADSHEET_ID: string;
  IMAGES: {
    input(stream: ReadableStream): {
      transform(options: Record<string, unknown>): {
        output(options: { format: string; quality: number }): Promise<{ response(): Response }>;
      };
    };
  };
}

interface ExecutionContext {
  waitUntil(promise: Promise<unknown>): void;
  passThroughOnException(): void;
}

// Image security config. SVG sources with .svg extension auto-skip the
// optimization endpoint on the client side (served directly, no proxy).
// To route SVGs through the optimizer (with security headers), set
// dangerouslyAllowSVG: true in next.config.js and uncomment below:
// const imageConfig: ImageConfig = { dangerouslyAllowSVG: true };

const worker = {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/api/orders" && request.method === "POST") {
      return createOrder(request, env);
    }

    if (url.pathname === "/_vinext/image") {
      const allowedWidths = [...DEFAULT_DEVICE_SIZES, ...DEFAULT_IMAGE_SIZES];
      return handleImageOptimization(request, {
        fetchAsset: (path) => env.ASSETS.fetch(new Request(new URL(path, request.url))),
        transformImage: async (body, { width, format, quality }) => {
          const result = await env.IMAGES.input(body).transform(width > 0 ? { width } : {}).output({ format, quality });
          return result.response();
        },
      }, allowedWidths);
    }

    return handler.fetch(request, env, ctx);
  },
};

const PRODUCTS: Record<string, { name: string; price: number }> = {
  "f-carne": { name: "Flauta de carne", price: 45 },
  "f-papa": { name: "Flauta de papa", price: 40 },
  soda: { name: "Soda", price: 29 },
  cueritos: { name: "Cueritos", price: 10 },
  guacamole: { name: "Guacamole extra", price: 10 },
  salsa: { name: "Salsa extra", price: 10 },
  crema: { name: "Crema extra", price: 10 },
  "kg-carne": { name: "1 kg de carne asada", price: 400 },
  "medio-carne": { name: "½ kg de carne asada", price: 250 },
  "plato-carne": { name: "Platillo individual", price: 150 },
  "kg-costilla": { name: "1 kg de costilla", price: 300 },
  "medio-costilla": { name: "½ kg de costilla", price: 200 },
  "plato-costilla": { name: "Platillo individual de costilla", price: 120 },
  "soda-asada": { name: "Soda", price: 29 },
};

async function createOrder(request: Request, env: Env): Promise<Response> {
  try {
    const body = await request.json() as {
      name?: string; phone?: string; pickupTime?: string; notes?: string;
      items?: Array<{ id?: string; quantity?: number }>;
    };
    const name = clean(body.name, 80);
    const phone = String(body.phone ?? "").replace(/\D/g, "");
    const pickupTime = clean(body.pickupTime, 20);
    const notes = clean(body.notes, 300);
    if (name.length < 2 || phone.length !== 10 || !pickupTime) {
      return Response.json({ error: "Completa nombre, teléfono y hora de recogida." }, { status: 400 });
    }

    let total = 0;
    const lines: string[] = [];
    const normalizedItems: Array<{ id: string; quantity: number; name: string; price: number }> = [];
    for (const item of body.items ?? []) {
      const product = item.id ? PRODUCTS[item.id] : undefined;
      const quantity = Math.min(50, Math.max(0, Math.floor(Number(item.quantity) || 0)));
      if (!product || !item.id || quantity === 0) continue;
      total += product.price * quantity;
      lines.push(`${quantity} × ${product.name}`);
      normalizedItems.push({ id: item.id, quantity, ...product });
    }
    if (!lines.length) return Response.json({ error: "El pedido está vacío." }, { status: 400 });

    const folio = `BET-${Date.now().toString().slice(-8)}`;
    const now = new Date();
    const date = new Intl.DateTimeFormat("es-MX", { timeZone: "America/Ojinaga", year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
    const timestamp = new Intl.DateTimeFormat("es-MX", { timeZone: "America/Ojinaga", dateStyle: "short", timeStyle: "medium" }).format(now);
    const accessToken = await googleAccessToken(env);
    const endpoint = `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(env.GOOGLE_SPREADSHEET_ID)}/values/A:K:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS`;
    const sheetResponse = await fetch(endpoint, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({ values: [[timestamp, folio, name, phone, lines.join(" | "), total, date, pickupTime, notes, "Efectivo", "Nuevo"]] }),
    });
    if (!sheetResponse.ok) throw new Error(`Google Sheets respondió ${sheetResponse.status}`);
    return Response.json({ ok: true, folio, total, items: normalizedItems }, { status: 201 });
  } catch (error) {
    console.error("Order registration failed", error);
    return Response.json({ error: "No pudimos registrar el pedido. Intenta nuevamente." }, { status: 500 });
  }
}

function clean(value: unknown, max: number): string {
  const text = String(value ?? "").trim().slice(0, max);
  return /^[=+\-@]/.test(text) ? `'${text}` : text;
}

async function googleAccessToken(env: Env): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  const header = base64Url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const claim = base64Url(JSON.stringify({ iss: env.GOOGLE_SERVICE_ACCOUNT_EMAIL, scope: "https://www.googleapis.com/auth/spreadsheets", aud: "https://oauth2.googleapis.com/token", iat: now, exp: now + 3600 }));
  const unsigned = `${header}.${claim}`;
  const keyBytes = pemBytes(env.GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY);
  const key = await crypto.subtle.importKey("pkcs8", keyBytes, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
  const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(unsigned));
  const assertion = `${unsigned}.${base64UrlBytes(new Uint8Array(signature))}`;
  const tokenResponse = await fetch("https://oauth2.googleapis.com/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer", assertion }) });
  if (!tokenResponse.ok) throw new Error(`Google OAuth respondió ${tokenResponse.status}`);
  const token = await tokenResponse.json() as { access_token?: string };
  if (!token.access_token) throw new Error("Google OAuth no devolvió un token");
  return token.access_token;
}

function pemBytes(pem: string): Uint8Array {
  const normalized = pem.replace(/\\n/g, "\n").replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s/g, "");
  return Uint8Array.from(atob(normalized), c => c.charCodeAt(0));
}

function base64Url(text: string): string { return base64UrlBytes(new TextEncoder().encode(text)); }
function base64UrlBytes(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

export default worker;
