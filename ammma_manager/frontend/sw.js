const CACHE_NAME = 'ammma-manager-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/login',
  '/static/style.css',
  '/logo/logo-vazado.png',
  '/logo/icon-192.png',
  '/logo/icon-512.png'
];

// Install event: cache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate event: clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event: network first, fallback to cache
self.addEventListener('fetch', event => {
  // Only cache GET requests
  if (event.request.method !== 'GET') return;

  // Don't cache API requests
  if (event.request.url.includes('/stats') || 
      event.request.url.includes('/orders') || 
      event.request.url.includes('/inventory') ||
      event.request.url.includes('/clients') ||
      event.request.url.includes('/finance') ||
      event.request.url.includes('/gallery')) {
    return;
  }

  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});
