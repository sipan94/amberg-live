// Amberg Live service worker – version {{ version }}
// Pages: network first (always fresh), cached copy or offline page when there is no connection.
// Static files: cache first (their URLs contain a content hash, so they never go stale).
"use strict";

const VERSION = "{{ version }}";
const STATIC_CACHE = "al-static-" + VERSION;
const PAGE_CACHE = "al-pages-v1";
const OFFLINE_URL = "{{ precache[0] }}";
const PRECACHE = {{ precache|tojson }};
const MAX_PAGES = 40;
// Personal or form pages are never cached.
const NO_CACHE = ["/konto", "/admin", "/anmelden", "/abmelden", "/registrieren", "/passwort-",
                  "/bestaetigen", "/api/"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys
        .filter((key) => key.startsWith("al-static-") && key !== STATIC_CACHE)
        .map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

async function trimPages() {
  const cache = await caches.open(PAGE_CACHE);
  const keys = await cache.keys();
  for (const key of keys.slice(0, Math.max(0, keys.length - MAX_PAGES))) await cache.delete(key);
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    const cacheControl = response.headers.get("Cache-Control") || "";
    // Logged-in pages are sent with "no-store" and stay out of the cache.
    if (response.ok && !cacheControl.includes("no-store")) {
      const cache = await caches.open(PAGE_CACHE);
      cache.put(request, response.clone()).then(trimPages);
    }
    return response;
  } catch (err) {
    return (await caches.match(request)) || (await caches.match(OFFLINE_URL));
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) (await caches.open(STATIC_CACHE)).put(request, response.clone());
  return response;
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;  // map tiles etc. go straight to the network
  if (NO_CACHE.some((prefix) => url.pathname.startsWith(prefix))) return;

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(request));
  } else if (url.pathname.startsWith("/static/")) {
    event.respondWith(cacheFirst(request));
  }
});
