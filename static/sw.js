// Service Worker — Téléchargeur MP3 HD
// Version du cache : mp3dl-v30-fullscreen-chars
const CACHE_VERSION = 'mp3dl-v30-fullscreen-chars';

// ——— Installation : Activer immédiatement sans attendre ———
self.addEventListener('install', (event) => {
    self.skipWaiting();
});

// ——— Activation : Supprimer TOUS les anciens caches immédiatement ———
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(keys.map(key => caches.delete(key)));
        })
    );
    self.clients.claim();
});

// ——— Fetch : Network-First systématique (aucun blocage de mise à jour) ———
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Ne JAMAIS intercepter ni bloquer les flux MP3, vidéos, téléchargements ou streaming
    if (url.pathname.startsWith('/api/download') ||
        url.pathname.startsWith('/api/direct-download') ||
        url.pathname.startsWith('/api/preview-track') ||
        url.pathname.startsWith('/api/stream') ||
        url.pathname.startsWith('/api/theme') ||
        url.pathname.startsWith('/api/search') ||
        url.pathname.startsWith('/api/singer') ||
        url.pathname.startsWith('/api/video')) {
        return; // Passer directement au réseau natif
    }

    // Pour les fichiers de l'application (HTML, JS, CSS) : Toujours chercher sur le réseau en premier
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                return response;
            })
            .catch(() => {
                // En cas de panne de réseau totale uniquement, chercher en cache
                return caches.match(event.request);
            })
    );
});

self.addEventListener('message', (event) => {
    if (event.data === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
