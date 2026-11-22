const VERSION="dealradar-v3";const ASSETS=["./","./index.html","./styles.css","./app.js","./manifest.webmanifest","./icon.svg"];
self.addEventListener("install",event=>event.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener("activate",event=>event.waitUntil(self.clients.claim()));
self.addEventListener("fetch",event=>{if(event.request.method!=="GET")return;const url=new URL(event.request.url);if(url.pathname.includes("/data/"))return;event.respondWith(fetch(event.request).then(r=>{if(r.ok){const c=r.clone();caches.open(VERSION).then(cache=>cache.put(event.request,c))}return r}).catch(()=>caches.match(event.request)))});
