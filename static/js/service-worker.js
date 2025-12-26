// Service Worker for Skanda Credit & Billing System
// Version: 1.0.0
const CACHE_NAME = 'skanda-v1.0.0';
const STATIC_CACHE_NAME = 'skanda-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'skanda-dynamic-v1.0.0';

// Assets to cache immediately on install
const STATIC_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/css/calendar.css',
  '/static/js/main.js',
  '/static/js/calendar.js',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS.map(url => {
          try {
            return new Request(url, { mode: 'no-cors' });
          } catch (e) {
            return url;
          }
        })).catch((err) => {
          console.log('[Service Worker] Cache addAll error (some assets may fail):', err);
          // Continue even if some assets fail to cache
          return Promise.resolve();
        });
      })
  );
  self.skipWaiting(); // Activate immediately
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME && cacheName.startsWith('skanda-')) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim(); // Take control of all pages immediately
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests (except CDN assets we control)
  if (url.origin !== location.origin && !url.href.includes('cdn.jsdelivr.net') && !url.href.includes('fonts.googleapis.com')) {
    return;
  }

  // Strategy: Cache First for static assets, Network First for API/HTML
  if (request.url.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|ico)$/)) {
    // Static assets: Cache First
    event.respondWith(
      caches.match(request)
        .then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return fetch(request).then((response) => {
            // Don't cache if not a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            // Clone the response
            const responseToCache = response.clone();
            caches.open(DYNAMIC_CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
            return response;
          }).catch(() => {
            // If fetch fails and it's an image, return a placeholder
            if (request.url.match(/\.(png|jpg|jpeg|gif|svg)$/)) {
              return new Response('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="#e2e8f0"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#94a3b8">Image not available offline</text></svg>', {
                headers: { 'Content-Type': 'image/svg+xml' }
              });
            }
          });
        })
    );
  } else {
    // HTML and API: Network First with cache fallback
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone the response
          const responseToCache = response.clone();
          // Cache successful responses
          if (response.status === 200) {
            caches.open(DYNAMIC_CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        })
        .catch(() => {
          // Network failed, try cache
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // If it's a navigation request and we have the root cached, return that
            if (request.mode === 'navigate') {
              return caches.match('/');
            }
            // Return offline page
            return new Response(
              '<!DOCTYPE html><html><head><title>Offline</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:Inter,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f1f5f9;color:#334155}.container{text-align:center;padding:2rem}.icon{font-size:4rem;margin-bottom:1rem}h1{font-size:1.5rem;margin-bottom:0.5rem}p{color:#64748b}</style></head><body><div class="container"><div class="icon">📡</div><h1>You are offline</h1><p>Please check your internet connection and try again.</p></div></body></html>',
              {
                headers: { 'Content-Type': 'text/html' }
              }
            );
          });
        })
    );
  }
});

// Background sync for offline actions (optional enhancement)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-forms') {
    event.waitUntil(syncForms());
  }
});

function syncForms() {
  // This would sync any pending form submissions when back online
  // Implementation depends on your specific needs
  return Promise.resolve();
}

// Push notifications (optional enhancement)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New update available',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    tag: 'skanda-notification',
    requireInteraction: false
  };

  event.waitUntil(
    self.registration.showNotification('Skanda Credit & Billing System', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/')
  );
});

