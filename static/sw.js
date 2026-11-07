// Service Worker — Téléchargeur MP3
// Version du cache : incrémenter à chaque mise à jour
const CACHE_VERSION = 'mp3dl-v2';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;

// Ressources à mettre en cache pour fonctionner hors-ligne
const STATIC_ASSETS = [
    '/',
    '/mobile',
    '/static/css/style.css',
    '/static/css/mobile.css',
    '/static/js/app.js',
    '/static/js/mobile-app.js',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/static/icons/favicon.png',
    '/manifest.json',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css'
];

// ——— Installation du Service Worker ———
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE).then((cache) => {
            return cache.addAll(STATIC_ASSETS).catch((err) => {
                console.warn('SW: Certaines ressources non cachées:', err);
            });
        })
    );
    self.skipWaiting();
});

// ——— Activation & nettoyage des anciens caches ———
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter(key => !key.startsWith(CACHE_VERSION))
                    .map(key => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

// ——— Stratégie de fetch : Network-first pour les API, Cache-first pour les assets ———
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Ne pas intercepter les requêtes de téléchargement de fichiers (MP3, ZIP)
    if (url.pathname.startsWith('/api/download-file') ||
        url.pathname.startsWith('/api/download-ready') ||
        url.pathname.startsWith('/api/singer/download-zip') ||
        url.pathname.startsWith('/api/stream')) {
        return; // Laisser passer directement au réseau
    }

    // Pour les API dynamiques : Network First
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    return new Response(
                        JSON.stringify({ error: 'Hors-ligne — connexion réseau requise', offline: true }),
                        { headers: { 'Content-Type': 'application/json' } }
                    );
                })
        );
        return;
    }

    // Pour les pages HTML et navigations : Network First immédiat (jamais bloqué)
    if (event.request.mode === 'navigate' || event.request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    const clone = response.clone();
                    caches.open(DYNAMIC_CACHE).then((cache) => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match('/mobile') || caches.match('/'))
        );
        return;
    }

    // Pour les assets statiques : Cache First avec fallback réseau
    event.respondWith(
        caches.match(event.request).then((cached) => {
            if (cached) return cached;
            return fetch(event.request).then((response) => {
                if (response && response.status === 200 && response.type !== 'opaque') {
                    const clone = response.clone();
                    caches.open(DYNAMIC_CACHE).then((cache) => cache.put(event.request, clone));
                }
                return response;
            }).catch(() => {
                // Page d'erreur hors-ligne pour les pages HTML
                if (event.request.headers.get('accept').includes('text/html')) {
                    return caches.match('/mobile') || caches.match('/');
                }
            });
        })
    );
});

// ——— Messages depuis l'app (ex: mise à jour) ———
self.addEventListener('message', (event) => {
    if (event.data === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
