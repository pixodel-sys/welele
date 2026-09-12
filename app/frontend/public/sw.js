const CACHE_NAME = 'welele-pwa-v3';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/welele_logo_mark.jpg',
  '/splash_story_bg.jpg',
  '/videos/welele_ident_v2.mp4',
  '/videos/welele_ident.mp4',
];

// Install: Cache critical shell assets and global brand ident
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[Welele SW] Precaching partial failure:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch: Aggressive cache for brand ident & static shell; Network-first for dynamic API and large story streams
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  const isBrandIdent = url.pathname.includes('welele_ident') || url.pathname.includes('welele-ident');

  // For API and large non-ident video requests, let network handle directly
  if (!isBrandIdent && (url.pathname.startsWith('/api') || url.pathname.endsWith('.mp4') || url.pathname.endsWith('.m3u8') || url.pathname.endsWith('.ts'))) {
    return;
  }

  // Navigation and asset caching
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // Fetch fresh in background
        fetch(event.request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, networkResponse);
              });
            }
          })
          .catch(() => {});
        return cachedResponse;
      }

      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });
        return networkResponse;
      }).catch(() => {
        // Fallback to cached index.html for SPA routes
        if (event.request.mode === 'navigate') {
          return caches.match('/index.html');
        }
      });
    })
  );
});
