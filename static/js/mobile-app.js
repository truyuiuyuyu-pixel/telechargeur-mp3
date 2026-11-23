// =========================================================
// MOBILE-APP.JS — Application mobile PWA
// Téléchargeur MP3 HD 320kbps
// =========================================================

(function () {
    'use strict';

    // ——— État global ———
    const state = {
        config: {},
        discography: [],
        currentSinger: '',
        playlist: [],
        currentTrackIdx: -1,
        deferredInstallPrompt: null,
    };

    // ——— Éléments DOM ———
    const $ = id => document.getElementById(id);
    const mobAudio = $('mobAudio');

    // ——— Enregistrement du Service Worker avec rafraîchissement automatique ———
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js?v=10', { scope: '/' })
            .then(reg => {
                reg.update();
                reg.addEventListener('updatefound', () => {
                    const nw = reg.installing;
                    nw.addEventListener('statechange', () => {
                        if (nw.state === 'installed' && navigator.serviceWorker.controller) {
                            window.location.reload();
                        }
                    });
                });
            })
            .catch(err => console.warn('SW non enregistré:', err));

        let refreshing = false;
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            if (!refreshing) {
                refreshing = true;
                window.location.reload();
            }
        });
    }

    // Si on tourne déjà dans la vraie application Android native, masquer les bannières d'installation
    if (window.AndroidApp && typeof window.AndroidApp.isNativeApp === 'function') {
        const apkBanner = $('apkDownloadBanner');
        if (apkBanner) apkBanner.style.display = 'none';
        const pwaBanner = $('installBanner');
        if (pwaBanner) pwaBanner.style.display = 'none';
    }

    // ——— Interception du prompt d'installation PWA ———
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        state.deferredInstallPrompt = e;
        // Afficher la bannière d'installation
        const banner = $('installBanner');
        if (banner) banner.classList.add('show');
    });

    window.addEventListener('appinstalled', () => {
        const banner = $('installBanner');
        if (banner) banner.classList.remove('show');
        state.deferredInstallPrompt = null;
        showToast('Application installée avec succès !');
    });

    const btnInstall = $('btnInstallApp');
    if (btnInstall) {
        btnInstall.addEventListener('click', async () => {
            if (!state.deferredInstallPrompt) return;
            state.deferredInstallPrompt.prompt();
            const { outcome } = await state.deferredInstallPrompt.userChoice;
            if (outcome === 'accepted') {
                showToast('Installation en cours…');
            }
            state.deferredInstallPrompt = null;
        });
    }

    // =========================================================
    // SPLASH SCREEN & SCAN PREMIER LANCEMENT
    // =========================================================
    const FIRST_LAUNCH_KEY = 'mp3app_firstLaunch_v2';
    const isFirstLaunch = !localStorage.getItem(FIRST_LAUNCH_KEY);

    function startScan() {
        showScanStep(1);
        // Ouvrir le sélecteur de fichiers
        setTimeout(() => $('scanFileInput').click(), 300);
    }

    function skipScan() {
        localStorage.setItem(FIRST_LAUNCH_KEY, '1');
        finishSplash();
    }

    function finishSplash() {
        localStorage.setItem(FIRST_LAUNCH_KEY, '1');
        const splash = $('splashScreen');
        if (splash) {
            splash.classList.add('fade-out');
            setTimeout(() => {
                splash.style.display = 'none';
                const app = $('mobileApp');
                if (app) app.classList.add('visible');
                init();
            }, 400);
        } else {
            const app = $('mobileApp');
            if (app) app.classList.add('visible');
            init();
        }
    }

    // Export global pour les onclick HTML
    window.startScan = startScan;
    window.skipScan = skipScan;
    window.finishSplash = finishSplash;

    function showScanStep(n) {
        document.querySelectorAll('.scan-step').forEach(s => s.classList.remove('active'));
        const step = $(`step${n}`);
        if (step) step.classList.add('active');
    }

    // Scan des fichiers audio du téléphone
    const scanFileInput = $('scanFileInput');
    if (scanFileInput) {
        scanFileInput.addEventListener('change', async (e) => {
            const files = e.target.files;
            if (!files || files.length === 0) return;
            showScanStep(2);

            const fill = $('scanFill');
            const countTxt = $('scanCountText');
            const statusMsg = $('scanStatusMsg');
            statusMsg.textContent = `Analyse de ${files.length} fichiers…`;

            const phoneTracks = [];
            for (let i = 0; i < files.length; i++) {
                const f = files[i];
                phoneTracks.push({
                    filename: f.name,
                    title: f.name.replace(/\.[^/.]+$/, ''),
                    artist: ''
                });
                const pct = Math.round(((i + 1) / files.length) * 100);
                fill.style.width = pct + '%';
                countTxt.textContent = `${i + 1} / ${files.length} fichiers analysés`;
                if (i % 50 === 0) await sleep(10); // Libérer l'UI
            }

            // Envoyer au serveur pour l'indexation anti-doublon
            try {
                const res = await fetch('/api/phone/register-music', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tracks: phoneTracks })
                });
                const data = await res.json();
                $('scanResultMsg').textContent = `${data.registered_count} musiques indexées sur votre téléphone. L'app ne téléchargera jamais de doublons !`;
            } catch (err) {
                $('scanResultMsg').textContent = `${phoneTracks.length} fichiers analysés et indexés localement.`;
            }

            showScanStep(3);
        });
    }

    // Lancement instantané : pas d'écran bloquant, affichage immédiat en 0ms
    const splashEl = $('splashScreen');
    if (splashEl) {
        splashEl.style.display = 'none'; // Pas de blocage
    }
    const appEl = $('mobileApp');
    if (appEl) {
        appEl.classList.add('visible');
    }
    // Initialisation immédiate de l'application
    init();

    // =========================================================
    // GESTION DU THÈME & POLICES (Musique / Tech)
    // =========================================================
    function applyMobFontStyle(fontClass) {
        if (!fontClass) fontClass = 'font-default';
        document.documentElement.classList.remove('font-default', 'font-orbitron', 'font-rajdhani', 'font-exo2', 'font-audiowide');
        document.documentElement.classList.add(fontClass);
        document.querySelectorAll('#mobFontPicker .mob-font-pill').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.font === fontClass);
        });
    }

    function getSelectedMobFont() {
        const active = document.querySelector('#mobFontPicker .mob-font-pill.active');
        return active ? active.dataset.font : (localStorage.getItem('mp3_font_style') || 'font-default');
    }

    // Appliquer immédiatement la police sauvegardée
    const savedMobFont = localStorage.getItem('mp3_font_style');
    if (savedMobFont) applyMobFontStyle(savedMobFont);

    // =========================================================
    // INITIALISATION DE L'APP
    // =========================================================
    async function init() {
        await loadConfig();
        await loadScannerSummary();
        await loadLibrary();
        setupTabs();
        setupModeDropdown();
        setupVideoMode();
        setupStreamingMode();
        setupSettings();
        setupScanPhone();
        setupMobThemes();
        initMobGlobalAudioPlayer();
        handleUrlParams();
    }

    // =========================================================
    // LECTEUR AUDIO D'EXTRAIT (30s)
    // =========================================================
    let mobCurrentPreviewAudio = null;
    let mobActivePreviewBtn = null;

    function initMobGlobalAudioPlayer() {
        mobCurrentPreviewAudio = $('mobGlobalPreviewAudio');
        const bar = $('mobGlobalAudioPlayerBar');
        const btnPlayPause = $('btnMobPlayerPlayPause');
        const btnClose = $('btnMobPlayerClose');
        if (!bar || !mobCurrentPreviewAudio) return;

        if (btnPlayPause) {
            btnPlayPause.onclick = () => {
                if (mobCurrentPreviewAudio.paused) {
                    mobCurrentPreviewAudio.play();
                    btnPlayPause.innerHTML = '<i class="fa-solid fa-pause"></i>';
                } else {
                    mobCurrentPreviewAudio.pause();
                    btnPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
                }
            };
        }

        if (btnClose) {
            btnClose.onclick = () => {
                mobCurrentPreviewAudio.pause();
                mobCurrentPreviewAudio.currentTime = 0;
                bar.style.display = 'none';
                if (mobActivePreviewBtn) {
                    mobActivePreviewBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
                    mobActivePreviewBtn = null;
                }
            };
        }

        mobCurrentPreviewAudio.onended = () => {
            if (btnPlayPause) btnPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
            if (mobActivePreviewBtn) {
                mobActivePreviewBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
                mobActivePreviewBtn = null;
            }
        };
    }

    async function playMobAudioPreview(artist, title, query, btn) {
        mobCurrentPreviewAudio = $('mobGlobalPreviewAudio');
        const bar = $('mobGlobalAudioPlayerBar');
        const titleEl = $('mobGlobalPreviewTitle') || $('mobPlayerTitle');
        const artistEl = $('mobGlobalPreviewArtist') || $('mobPlayerArtist');
        const coverEl = $('mobGlobalPreviewCover') || $('mobPlayerCover');
        const btnPlayPause = $('btnMobPlayerPlayPause');
        if (!bar || !mobCurrentPreviewAudio) return;

        if (mobActivePreviewBtn === btn && !mobCurrentPreviewAudio.paused) {
            mobCurrentPreviewAudio.pause();
            if (btn) btn.innerHTML = '<i class="fa-solid fa-play"></i>';
            if (btnPlayPause) btnPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
            return;
        }

        if (mobActivePreviewBtn && mobActivePreviewBtn !== btn) {
            mobActivePreviewBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
        }

        mobActivePreviewBtn = btn;
        if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        try {
            const res = await fetch(`/api/preview-track?artist=${encodeURIComponent(artist || '')}&title=${encodeURIComponent(title || '')}&q=${encodeURIComponent(query || '')}`);
            if (!res.ok) throw new Error("Extrait non disponible");
            const data = await res.json();

            mobCurrentPreviewAudio.src = data.preview_url;
            await mobCurrentPreviewAudio.play();

            if (titleEl) titleEl.textContent = data.title || title;
            if (artistEl) artistEl.innerHTML = `<i class="fa-solid fa-headphones" style="color:#3b82f6;"></i> ${esc(data.artist || artist)} (${data.source || '30s'})`;
            if (coverEl) coverEl.src = data.cover || '/static/icons/icon-192.png';
            bar.style.display = 'flex';

            if (btn) btn.innerHTML = '<i class="fa-solid fa-pause"></i>';
            if (btnPlayPause) btnPlayPause.innerHTML = '<i class="fa-solid fa-pause"></i>';
            showToast(`🎵 Extrait en cours : ${title}`);
        } catch (e) {
            if (btn) btn.innerHTML = '<i class="fa-solid fa-play"></i>';
            mobActivePreviewBtn = null;
            showToast("Extrait audio non disponible pour ce titre", true);
        }
    }

    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            state.config = await res.json();
            // Remplir les selects
            const qEl = $('mobSelectQuality');
            if (qEl) qEl.value = state.config.audio_quality || '320';
            const srcEl = $('mobSelectSource');
            if (srcEl && state.config.mp3_site) {
                // Trouver l'option la plus proche
                for (let opt of srcEl.options) {
                    if (opt.value === state.config.mp3_site) { srcEl.value = opt.value; break; }
                }
            }
            if (state.config.font_style) {
                applyMobFontStyle(state.config.font_style);
                localStorage.setItem('mp3_font_style', state.config.font_style);
            }
        } catch (err) {
            console.warn('Config non chargée:', err);
        }
    }

    async function loadScannerSummary() {
        try {
            const res = await fetch('/api/scanner/summary');
            const data = await res.json();
            el('mobPcCount', data.pc_count || 0);
            el('mobPhoneCount', data.phone_count || 0);
        } catch (err) {}
    }

    // =========================================================
    // NAVIGATION PAR ONGLETS
    // =========================================================
    function setupTabs() {
        document.querySelectorAll('.mob-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mob-tab').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.mob-tab-pane').forEach(p => {
                    p.classList.remove('active');
                    p.style.display = 'none';
                });
                btn.classList.add('active');
                const pane = $(`mobPane-${btn.dataset.pane}`);
                if (pane) {
                    pane.classList.add('active');
                    pane.style.display = 'block';
                }
                if (btn.dataset.pane === 'library') loadLibrary();
                if (btn.dataset.pane === 'themes') loadMobThemes();
                if (btn.dataset.pane === 'streaming') {
                    // Supprimer la musique en mode streaming : arrêt immédiat de la lecture et masquage du mini-lecteur
                    try {
                        const audio = $('mobAudioElement') || document.querySelector('audio');
                        if (audio && !audio.paused) audio.pause();
                    } catch {}
                    const pBar = $('mobGlobalAudioPlayerBar');
                    if (pBar) pBar.style.display = 'none';
                    const mPlayer = $('mobPlayer');
                    if (mPlayer) mPlayer.style.display = 'none';

                    const results = $('mobStreamResults');
                    if (results && !results.children.length) {
                        doSearchStreaming('tendances');
                    }
                }
            });
        });
    }

    function handleUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const tab = params.get('tab');
        const q = params.get('q');
        if (tab) {
            const btn = document.querySelector(`.mob-tab[data-pane="${tab}"]`);
            if (btn) btn.click();
        }
        if (q) {
            const inp = $('mobSearchInput');
            if (inp) { inp.value = q; $('mobSearchForm').dispatchEvent(new Event('submit')); }
        }
    }

    // =========================================================
    // THEMES & STYLES MUSICAUX (Amour, Halloween, Noël, etc.)
    // =========================================================
    let currentMobSelectedThemeId = null;

    function showMobThemeBanner(theme) {
        const tb = $('mobThemeBanner');
        if (!tb) return;
        tb.innerHTML = `
            <div><strong>${esc(theme.badge || theme.name)}</strong> : ${esc(theme.description || '')}</div>
            <button style="background:none;border:none;color:#fff;cursor:pointer;padding:4px;" onclick="document.getElementById('mobThemeBanner').style.display='none'">&times;</button>
        `;
        tb.style.display = 'flex';
    }

    function hideMobThemeBanner() {
        const tb = $('mobThemeBanner');
        if (tb) tb.style.display = 'none';
    }

    function setupMobThemes() {
        document.querySelectorAll('.mob-theme-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                const themeId = btn.dataset.theme;
                document.querySelectorAll('.mob-theme-pill').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                // Basculer vers l'onglet Thèmes pour voir la sélection complète
                const tabThemesBtn = document.querySelector('.mob-tab[data-pane="themes"]');
                if (tabThemesBtn) {
                    tabThemesBtn.click();
                    setTimeout(() => openMobThemeDetail(themeId), 100);
                } else {
                    const inp = $('mobSearchInput');
                    if (inp) inp.value = themeId;
                    doSearch(themeId);
                }
            });
        });
    }

    let mobAllThemesData = [];

    async function loadMobThemes() {
        const grid = $('mobThemesGrid');
        if (!grid) return;
        grid.innerHTML = '<div class="mob-loader"><div class="mob-spinner"></div><span>Chargement des thèmes…</span></div>';

        try {
            const res = await fetch('/api/themes');
            mobAllThemesData = await res.json();
            renderMobThemesGrid(mobAllThemesData);
            setupMobThemeCatalogSearch();
        } catch (e) {
            grid.innerHTML = '<div class="mob-empty">Erreur chargement thèmes</div>';
        }
    }

    function renderMobThemesGrid(themesList, searchQ) {
        const grid = $('mobThemesGrid');
        if (!grid) return;
        grid.innerHTML = '';

        if (searchQ && searchQ.trim()) {
            const qClean = searchQ.trim();
            const dynCard = document.createElement('div');
            dynCard.className = 'mob-theme-card';
            dynCard.style.cssText = 'border:2px dashed var(--primary);background:rgba(99,102,241,0.15);margin-bottom:12px;';
            dynCard.innerHTML = `
                <div class="mob-theme-icon" style="color:var(--primary);background:rgba(99,102,241,0.25);">
                    <i class="fa-solid fa-sparkles"></i>
                </div>
                <div class="mob-theme-info">
                    <div class="mob-theme-name" style="color:#a5b4fc">✨ Trouver 30+ musiques pour "${esc(qClean)}"</div>
                    <div class="mob-theme-desc">Recherche ultra-puissante en direct sur le web</div>
                </div>
                <div class="mob-theme-arrow"><i class="fa-solid fa-chevron-right"></i></div>
            `;
            dynCard.onclick = () => doDynamicThemeSearch();
            grid.appendChild(dynCard);
        }

        if (!themesList || !themesList.length) {
            if (!searchQ) {
                grid.innerHTML = '<div class="mob-empty"><i class="fa-solid fa-search"></i><h3>Aucun thème trouvé</h3><p>Tapez un univers comme Iron Man, Spider-Man ou Star Wars ci-dessus.</p></div>';
            }
            return;
        }

        themesList.forEach(t => {
            const card = document.createElement('div');
            card.className = 'mob-theme-card';
            card.dataset.id = t.id;
            card.innerHTML = `
                <div class="mob-theme-icon" style="color:${t.color || 'var(--primary)'};background:${t.color ? t.color + '22' : 'var(--bg-elevated)'}">
                    <i class="fa-solid ${t.icon || 'fa-music'}"></i>
                </div>
                <div class="mob-theme-info">
                    <div class="mob-theme-name">${esc(t.name)}</div>
                    <div class="mob-theme-desc">${esc(t.description || '')}</div>
                    <span style="font-size:0.7rem;color:var(--text-muted);font-weight:600;">${t.track_count || (t.tracks ? t.tracks.length : 0)} titres cultes</span>
                </div>
                <div class="mob-theme-arrow"><i class="fa-solid fa-chevron-right"></i></div>
            `;
            card.addEventListener('click', () => {
                openMobThemeDetail(t.id, t);
            });
            grid.appendChild(card);
        });
    }

    function setupMobThemeCatalogSearch() {
        const sInput = $('mobThemesCatalogSearchInput');
        const sBtn = $('btnMobSearchThemeDynamic');

        // Pilules rapides (Marvel, Iron Man, Spider-Man, Star Wars, etc.)
        document.querySelectorAll('.mob-fast-theme-pill').forEach(pill => {
            pill.onclick = () => {
                const themeId = pill.dataset.theme;
                if (themeId) openMobThemeDetail(themeId);
            };
        });

        if (sInput) {
            sInput.oninput = () => {
                const q = sInput.value.toLowerCase().trim();
                if (!q) {
                    renderMobThemesGrid(mobAllThemesData);
                    return;
                }
                const filtered = mobAllThemesData.filter(t => {
                    const name = (t.name || '').toLowerCase();
                    const desc = (t.description || '').toLowerCase();
                    const kws = (t.keywords || []).map(k => k.toLowerCase());
                    return name.includes(q) || desc.includes(q) || kws.some(k => k.includes(q));
                });
                renderMobThemesGrid(filtered, q);
            };

            const doDynamicThemeSearch = async () => {
                const q = sInput.value.trim();
                if (!q) return;
                // Si trouvé dans les thèmes locaux
                const exact = mobAllThemesData.find(t => t.name.toLowerCase().includes(q.toLowerCase()) || t.id.toLowerCase() === q.toLowerCase());
                if (exact) {
                    openMobThemeDetail(exact.id, exact);
                    return;
                }
                // Sinon recherche dynamique en ligne pour n'importe quel univers !
                showToast(`🎬 Recherche des musiques du thème "${q}" en ligne...`);
                try {
                    const res = await fetch(`/api/themes/dynamic?q=${encodeURIComponent(q)}`);
                    const data = await res.json();
                    if (data && data.tracks && data.tracks.length) {
                        openMobThemeDetail(data.id, data);
                    } else {
                        showToast(`Aucun morceau trouvé pour le thème "${q}"`, true);
                    }
                } catch {
                    showToast("Erreur recherche thème en ligne", true);
                }
            };

            sInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    doDynamicThemeSearch();
                }
            };
            if (sBtn) sBtn.onclick = doDynamicThemeSearch;
        }
    }

    async function openMobThemeDetail(themeId, prefetchedTheme) {
        currentMobSelectedThemeId = themeId;
        const detail = $('mobThemeDetail');
        const titleEl = $('mobThemeDetailTitle');
        const descEl = $('mobThemeDetailDesc');
        const listEl = $('mobThemeTracksList');
        const btnAll = $('btnMobDownloadThemeAll');
        const grid = $('mobThemesGrid');

        if (!detail || !listEl) return;
        if (grid) grid.style.display = 'none';
        detail.style.display = 'block';
        listEl.innerHTML = '<div class="mob-loader"><div class="mob-spinner"></div><span>Chargement des morceaux…</span></div>';

        detail.scrollIntoView({ behavior: 'smooth', block: 'start' });

        try {
            let theme = prefetchedTheme;
            if (!theme || !theme.tracks) {
                const res = await fetch(`/api/theme/${themeId}`);
                theme = await res.json();
            }

            titleEl.innerHTML = `<i class="fa-solid ${theme.icon || 'fa-music'}" style="color:${theme.color || 'var(--primary)'}"></i> ${esc(theme.name)}`;
            descEl.textContent = theme.description || '';

            const btnSaveMp3s = $('btnMobSaveThemeMp3s');
            if (btnSaveMp3s) {
                btnSaveMp3s.style.display = 'block';
                btnSaveMp3s.onclick = () => downloadThemeTracksDirectly(themeId);
            }

            listEl.innerHTML = '';
            const tracks = theme.tracks || [];

            tracks.forEach((tr, idx) => {
                const trCard = document.createElement('div');
                trCard.className = 'mob-result-card';
                trCard.style.cssText = 'display:flex;flex-direction:column;gap:10px;padding:12px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);margin-bottom:10px;';
                trCard.innerHTML = `
                    <div style="display:flex;align-items:center;gap:10px;width:100%;">
                        <div style="width:42px;height:42px;border-radius:10px;background:linear-gradient(135deg, ${theme.color || 'var(--primary)'}, #1e293b);display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.2rem;flex-shrink:0">
                            <i class="fa-solid ${theme.icon || 'fa-music'}"></i>
                        </div>
                        <div style="flex:1;min-width:0;overflow:hidden;">
                            <div style="font-size:0.95rem;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(tr.title)}</div>
                            <div style="font-size:0.75rem;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><i class="fa-solid fa-microphone"></i> ${esc(tr.artist)}</div>
                        </div>
                    </div>
                    <div style="display:flex;gap:8px;width:100%;margin-top:2px;">
                        <button type="button" class="btn-preview-theme-item" style="flex:1;padding:10px;background:linear-gradient(135deg,#0ea5e9,#0284c7);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                            <i class="fa-solid fa-play"></i> <span>Écouter</span>
                        </button>
                        <button type="button" class="btn-theme-item-dl" style="flex:1.4;padding:10px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                            <i class="fa-solid fa-download"></i> <span>Télécharger MP3</span>
                        </button>
                    </div>
                `;

                const btnPrev = trCard.querySelector('.btn-preview-theme-item');
                if (btnPrev) {
                    btnPrev.onclick = () => playMobAudioPreview(tr.artist, tr.title, tr.query, btnPrev);
                }

                const btnDl = trCard.querySelector('.btn-theme-item-dl');
                if (btnDl) {
                    const targetQ = tr.query || `${tr.artist} ${tr.title} audio`;
                    btnDl.onclick = () => triggerDownload(targetQ, tr.artist, tr.title, null, btnDl);
                }

                listEl.appendChild(trCard);
            });

            // Bouton retour aux 26 thèmes
            const btnBack = $('btnMobThemeBack');
            if (btnBack) {
                btnBack.onclick = () => {
                    detail.style.display = 'none';
                    const grid = $('mobThemesGrid');
                    if (grid) grid.style.display = 'grid';
                };
            }

            // Recherche & filtrage dans le thème mobile
            const sInput = $('mobThemeSearchInput');
            const btnSearchOnline = $('btnMobThemeSearchOnline');
            const onlineResults = $('mobThemeOnlineResults');

            if (sInput) {
                sInput.value = '';
                sInput.placeholder = `🔍 Chercher plus dans "${theme.name}"...`;
                sInput.oninput = () => {
                    const q = sInput.value.toLowerCase().trim();
                    listEl.querySelectorAll('.mob-result-card').forEach(card => {
                        const txt = card.textContent.toLowerCase();
                        card.style.display = !q || txt.includes(q) ? 'flex' : 'none';
                    });
                };
                sInput.onkeydown = (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        if (btnSearchOnline) btnSearchOnline.click();
                    }
                };
            }

            if (btnSearchOnline && onlineResults) {
                onlineResults.style.display = 'none';
                onlineResults.innerHTML = '';
                btnSearchOnline.onclick = async () => {
                    const query = sInput ? sInput.value.trim() : '';
                    onlineResults.style.display = 'block';
                    onlineResults.innerHTML = '<div class="mob-loader"><div class="mob-spinner"></div><span>Recherche sur tous les sites pour ce thème…</span></div>';
                    try {
                        const res = await fetch(`/api/theme/${themeId}/search?q=${encodeURIComponent(query)}&limit=10`);
                        const data = await res.json();
                        const results = data.results || [];
                        if (!results.length) {
                            onlineResults.innerHTML = '<div style="font-size:0.8rem;color:var(--text-muted);text-align:center;padding:8px;">Aucun morceau supplémentaire trouvé.</div>';
                            return;
                        }
                        onlineResults.innerHTML = '<div style="font-size:0.8rem;font-weight:700;color:#10b981;margin-bottom:8px;"><i class="fa-solid fa-wand-magic-sparkles"></i> Plus de titres trouvés en ligne :</div>';
                        results.forEach((r) => {
                            const card = document.createElement('div');
                            card.className = 'mob-result-card';
                            card.style.cssText = 'display:flex;flex-direction:column;gap:8px;padding:10px;background:var(--bg-elevated);border:1px solid var(--border);border-radius:var(--radius-md);margin-bottom:8px;';
                            const thumb = r.thumbnail || '/static/icons/icon-192.png';
                            card.innerHTML = `
                                <div style="display:flex;align-items:center;gap:10px;width:100%;">
                                    <img src="${esc(thumb)}" alt="" onerror="this.src='/static/icons/icon-192.png'" style="width:44px;height:44px;border-radius:8px;object-fit:cover;flex-shrink:0;">
                                    <div style="flex:1;min-width:0;overflow:hidden;">
                                        <div style="font-size:0.75rem;color:var(--primary);font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><i class="fa-solid fa-microphone"></i> ${esc(r.artist || 'Artiste')}</div>
                                        <div style="font-size:0.9rem;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:2px 0;">${esc(r.title || 'Titre')}</div>
                                    </div>
                                </div>
                                <div style="display:flex;gap:8px;width:100%;">
                                    <button type="button" class="btn-theme-online-prev" style="flex:1;padding:8px;background:linear-gradient(135deg,#0ea5e9,#0284c7);color:#fff;border:none;border-radius:8px;font-weight:700;font-size:0.8rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:4px;">
                                        <i class="fa-solid fa-play"></i> <span>Écouter</span>
                                    </button>
                                    <button type="button" class="btn-theme-online-dl" style="flex:1.3;padding:8px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;border-radius:8px;font-weight:700;font-size:0.8rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:4px;">
                                        <i class="fa-solid fa-download"></i> <span>Télécharger MP3</span>
                                    </button>
                                </div>
                            `;

                            const btnPrev = card.querySelector('.btn-theme-online-prev');
                            if (btnPrev) {
                                btnPrev.onclick = () => playMobAudioPreview(r.artist, r.title, r.title, btnPrev);
                            }

                            const btnDl = card.querySelector('.btn-theme-online-dl');
                            if (btnDl) {
                                btnDl.onclick = () => triggerDownload(r.url, r.artist, r.title, r.thumbnail, btnDl);
                            }

                            onlineResults.appendChild(card);
                        });
                    } catch (e) {
                        onlineResults.innerHTML = '<div style="font-size:0.8rem;color:var(--danger);text-align:center;padding:8px;">Erreur lors de la recherche.</div>';
                    }
                };
            }

            const btnLoadMore = $('btnMobLoadMoreTheme');
            if (btnLoadMore) {
                btnLoadMore.onclick = async () => {
                    btnLoadMore.disabled = true;
                    btnLoadMore.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Recherche de 30 musiques...</span>';
                    try {
                        const sRes = await fetch(`/api/theme/${themeId}/search?limit=30`);
                        const sData = await sRes.json();
                        const extraTracks = sData.results || [];
                        if (extraTracks.length === 0) {
                            showToast("Aucun titre supplémentaire trouvé", true);
                        } else {
                            extraTracks.forEach(r => {
                                const trCard = document.createElement('div');
                                trCard.className = 'mob-result-card';
                                trCard.style.cssText = 'display:flex;flex-direction:column;gap:10px;padding:12px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);margin-bottom:10px;';
                                trCard.innerHTML = `
                                    <div style="display:flex;align-items:center;gap:10px;width:100%;">
                                        <img src="${esc(r.thumbnail || '/static/icons/icon-192.png')}" alt="" onerror="this.src='/static/icons/icon-192.png'" style="width:42px;height:42px;border-radius:10px;object-fit:cover;flex-shrink:0;">
                                        <div style="flex:1;min-width:0;overflow:hidden;">
                                            <div style="font-size:0.95rem;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(r.title)}</div>
                                            <div style="font-size:0.75rem;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><i class="fa-solid fa-microphone"></i> ${esc(r.artist)}</div>
                                        </div>
                                    </div>
                                    <div style="display:flex;gap:8px;width:100%;margin-top:2px;">
                                        <button type="button" class="btn-preview-extra-item" style="flex:1;padding:10px;background:linear-gradient(135deg,#0ea5e9,#0284c7);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                                            <i class="fa-solid fa-play"></i> <span>Écouter</span>
                                        </button>
                                        <button type="button" class="btn-extra-item-dl" style="flex:1.4;padding:10px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                                            <i class="fa-solid fa-download"></i> <span>Télécharger MP3</span>
                                        </button>
                                    </div>
                                `;
                                const btnPrev = trCard.querySelector('.btn-preview-extra-item');
                                if (btnPrev) {
                                    btnPrev.onclick = () => playMobAudioPreview(r.artist, r.title, r.title, btnPrev);
                                }
                                const btnDl = trCard.querySelector('.btn-extra-item-dl');
                                if (btnDl) {
                                    btnDl.onclick = () => triggerDownload(r.url, r.artist, r.title, r.thumbnail, btnDl);
                                }
                                listEl.appendChild(trCard);
                            });
                            showToast(`✨ ${extraTracks.length} nouvelles musiques ajoutées au thème !`);
                        }
                    } catch (e) {
                        showToast("Erreur lors de la recherche", true);
                    } finally {
                        btnLoadMore.disabled = false;
                        btnLoadMore.innerHTML = '<i class="fa-solid fa-sparkles"></i> ✨ Charger encore plus de musiques';
                    }
                };
            }

            if (btnAll) {
                btnAll.onclick = async () => {
                    if (!confirm(`Télécharger toutes les ${tracks.length} musiques du thème "${theme.name}" sur ce téléphone ?`)) return;
                    showToast(`Démarrage du téléchargement du thème : ${theme.name}...`);
                    try {
                        const dlRes = await fetch(`/api/theme/${themeId}/download-all`, { method: 'POST' });
                        const dlData = await dlRes.json();
                        if (dlData.task_id) {
                            trackProgress(dlData.task_id, `Thème ${theme.name}`, `${tracks.length} titres`);
                        }
                    } catch (err) {
                        showToast("Erreur lancement thème", true);
                    }
                };
            }

        } catch (e) {
            listEl.innerHTML = '<div class="mob-empty">Erreur chargement morceaux.</div>';
        }
    }

    async function downloadBlobFile(url, filename) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error("Fichier non disponible");
            const blob = await resp.blob();
            const blobUrl = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = blobUrl;
            a.download = filename || 'musique.mp3';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                a.remove();
                URL.revokeObjectURL(blobUrl);
            }, 3000);
        } catch (e) {
            console.error("Erreur téléchargement blob:", e);
        }
    }

    function showBatchDownloadModal({ title, count, zipUrl, tracks, onMp3Choice }) {
        const modal = $('mobBatchModal');
        const modalTitle = $('mobBatchModalTitle');
        const modalDesc = $('mobBatchModalDesc');
        const btnZip = $('btnBatchZipChoice');
        const btnMp3 = $('btnBatchMp3Choice');
        const btnCancel = $('btnBatchModalCancel');
        
        if (!modal) {
            if (zipUrl) window.location.href = zipUrl;
            return;
        }

        if (modalTitle) modalTitle.textContent = title || `Télécharger ${count || ''} musiques`;
        if (modalDesc) modalDesc.textContent = `Comment souhaites-tu enregistrer les ${count || ''} morceaux sur ton appareil ?`;

        modal.style.display = 'flex';

        const closeModal = () => {
            modal.style.display = 'none';
        };

        if (btnCancel) btnCancel.onclick = closeModal;

        if (btnZip) {
            btnZip.onclick = () => {
                closeModal();
                showToast("📦 Téléchargement de l'album en 1 fichier ZIP (zéro onglet)...");
                const a = document.createElement('a');
                a.href = zipUrl;
                a.download = "";
                document.body.appendChild(a);
                a.click();
                setTimeout(() => a.remove(), 1000);
            };
        }

        if (btnMp3) {
            btnMp3.onclick = () => {
                closeModal();
                if (onMp3Choice) {
                    onMp3Choice();
                } else if (tracks && tracks.length) {
                    downloadTracksSequentially(tracks, title);
                }
            };
        }
    }

    async function downloadTracksSequentially(tracks, label) {
        if (!tracks || !tracks.length) {
            showToast("Aucun fichier MP3 trouvé à enregistrer", true);
            return;
        }

        showToast(`📲 Enregistrement silencieux de ${tracks.length} MP3 sans onglets...`);
        let downloaded = 0;

        for (let i = 0; i < tracks.length; i++) {
            const track = tracks[i];
            const title = track.title || track.filename || `Morceau_${i+1}`;
            showToast(`💾 MP3 ${i + 1}/${tracks.length} : ${title}`);
            const fname = track.filename || `${title}.mp3`;
            const fileUrl = `/api/download-file/${encodeURIComponent(track.rel_path)}`;

            await downloadBlobFile(fileUrl, fname);
            downloaded++;

            await new Promise(r => setTimeout(r, 900));
        }

        showToast(`✅ ${downloaded} musiques bien enregistrées sur votre appareil sans aucun onglet ouvert !`);
    }

    async function downloadThemeTracksDirectly(themeId) {
        try {
            const themeRes = await fetch(`/api/theme/${themeId}`);
            const theme = await themeRes.json();
            const expectedTitles = (theme.tracks || []).map(t => (t.title || '').toLowerCase());

            const libRes = await fetch('/api/library');
            const lib = await libRes.json();
            const matchingTracks = [];

            (lib.singers || []).forEach(s => {
                (s.tracks || []).forEach(t => {
                    const tLower = (t.title || '').toLowerCase();
                    if (expectedTitles.some(et => tLower.includes(et) || et.includes(tLower))) {
                        matchingTracks.push(t);
                    }
                });
            });

            if (matchingTracks.length === 0) {
                showToast("Télécharge d'abord le thème via le bouton ci-dessus.", true);
                return;
            }

            const zipUrl = `/api/theme/${themeId}/download-zip`;
            showBatchDownloadModal({
                title: `Thème : ${theme.name}`,
                count: `${matchingTracks.length}`,
                zipUrl: zipUrl,
                tracks: matchingTracks
            });
        } catch (e) {
            showToast("Erreur lors de la récupération des MP3 du thème", true);
        }
    }

    async function downloadSingerTracksDirectly(artistName) {
        try {
            const libRes = await fetch('/api/library');
            const lib = await libRes.json();
            const singerObj = (lib.singers || []).find(s => s.singer.toLowerCase() === artistName.toLowerCase());

            if (!singerObj || !singerObj.tracks || !singerObj.tracks.length) {
                showToast(`Aucun MP3 de ${artistName} encore téléchargé sur le serveur.`, true);
                return;
            }

            const cleanArtist = encodeURIComponent(artistName);
            const zipUrl = `/api/singer/download-zip/${cleanArtist}`;

            showBatchDownloadModal({
                title: `Discographie de ${artistName}`,
                count: `${singerObj.tracks.length}`,
                zipUrl: zipUrl,
                tracks: singerObj.tracks
            });
        } catch (e) {
            showToast("Erreur lors de la récupération des MP3 de l'artiste", true);
        }
    }

    // =========================================================
    // RECHERCHE
    // =========================================================
    let currentMobSearchSource = 'all';
    document.querySelectorAll('.mob-source-pill').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mob-source-pill').forEach(b => {
                b.classList.remove('active');
                b.style.borderColor = 'var(--border)';
                b.style.background = 'var(--bg-elevated)';
            });
            btn.classList.add('active');
            btn.style.borderColor = 'var(--primary)';
            btn.style.background = 'rgba(99,102,241,0.2)';
            currentMobSearchSource = btn.dataset.source || 'all';
        });
    });

    const mobSearchForm = $('mobSearchForm');
    if (mobSearchForm) {
        mobSearchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const q = $('mobSearchInput').value.trim();
            if (!q) return;
            await doSearch(q);
        });
    }

    async function doSearch(query) {
        $('mobSearchLoader').style.display = 'flex';
        $('mobResults').innerHTML = '';
        $('mobSearchEmpty').style.display = 'none';

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&source=${encodeURIComponent(currentMobSearchSource)}`);
            const data = await res.json();
            const results = data.results || [];
            $('mobSearchLoader').style.display = 'none';

            if (data.theme) {
                showMobThemeBanner(data.theme);
                document.querySelectorAll('.mob-theme-pill').forEach(b => {
                    b.classList.toggle('active', b.dataset.theme === data.theme.id);
                });
            } else {
                hideMobThemeBanner();
            }

            if (results.length === 0) {
                $('mobSearchEmpty').style.display = 'block';
                return;
            }

            results.forEach(item => {
                $('mobResults').appendChild(createResultCard(item));
            });
        } catch (err) {
            $('mobSearchLoader').style.display = 'none';
            showToast('Erreur de recherche — vérifiez votre connexion', true);
        }
    }

    function createResultCard(item) {
        const card = document.createElement('div');
        card.className = 'mob-result-card';
        card.style.cssText = 'display:flex;flex-direction:column;gap:10px;padding:12px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);margin-bottom:10px;';
        const thumb = item.thumbnail || '/static/icons/icon-192.png';
        card.innerHTML = `
            <div style="display:flex;align-items:center;gap:10px;width:100%;">
                <img src="${esc(thumb)}" alt="" onerror="this.src='/static/icons/icon-192.png'" style="width:48px;height:48px;border-radius:10px;object-fit:cover;flex-shrink:0;">
                <div style="flex:1;min-width:0;overflow:hidden;">
                    <div style="font-size:0.75rem;color:var(--primary);font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><i class="fa-solid fa-microphone"></i> ${esc(item.artist || 'Artiste')}</div>
                    <div style="font-size:0.95rem;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:2px 0;">${esc(item.title || item.raw_title || 'Titre')}</div>
                    <div style="font-size:0.72rem;color:var(--text-muted);">${item.duration || '0:00'}</div>
                </div>
            </div>
            <div style="display:flex;gap:8px;width:100%;margin-top:2px;">
                <button type="button" class="btn-mob-card-preview" style="flex:1;padding:10px;background:linear-gradient(135deg,#0ea5e9,#0284c7);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                    <i class="fa-solid fa-play"></i> <span>Écouter</span>
                </button>
                <button type="button" class="btn-mob-card-dl" style="flex:1.4;padding:10px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                    <i class="fa-solid fa-download"></i> <span>Télécharger MP3</span>
                </button>
            </div>
        `;

        const btnPrev = card.querySelector('.btn-mob-card-preview');
        if (btnPrev) {
            btnPrev.onclick = () => playMobAudioPreview(item.artist, item.title, item.title, btnPrev);
        }

        const btnDl = card.querySelector('.btn-mob-card-dl');
        if (btnDl) {
            btnDl.onclick = () => triggerDownload(item.url, item.artist, item.title, thumb, btnDl);
        }

        return card;
    }

    // =========================================================
    // TÉLÉCHARGEMENT DIRECT ET ASYNCHRONE
    // =========================================================
    async function triggerDownload(url, artist, title, coverUrl, btnEl) {
        showToast(`Démarrage : ${title}`);
        if (btnEl) {
            btnEl.disabled = true;
            btnEl.style.background = '#0284c7';
            btnEl.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Préparation…</span>';
        }
        try {
            const res = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, artist, title, cover_url: coverUrl })
            });
            const data = await res.json();
            if (data.task_id) {
                trackProgress(data.task_id, artist, title, btnEl);
            } else {
                throw new Error("Erreur démarrage tâche");
            }
        } catch (err) {
            showToast('Erreur de téléchargement', true);
            if (btnEl) {
                btnEl.disabled = false;
                btnEl.style.background = 'linear-gradient(135deg,#10b981,#059669)';
                btnEl.innerHTML = '<i class="fa-solid fa-download"></i> <span>Télécharger MP3</span>';
            }
        }
    }

    function trackProgress(taskId, artist, title, btnEl) {
        const wrap = $('mobDownloadsWrap');
        const list = $('mobDownloadsList');
        if (wrap) wrap.style.display = 'block';

        const card = document.createElement('div');
        card.className = 'mob-dl-card';
        card.id = `mobDl_${taskId}`;
        card.innerHTML = `
            <div class="mob-dl-info">
                <div class="mob-dl-name">${esc(artist)} — ${esc(title)}</div>
                <div class="mob-dl-pct" id="mobDlPct_${taskId}">0%</div>
            </div>
            <div class="mob-progress">
                <div class="mob-progress-fill" id="mobDlFill_${taskId}"></div>
            </div>
            <div class="mob-dl-status" id="mobDlMsg_${taskId}">Démarrage…</div>
        `;
        if (list) list.prepend(card);

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/download-status/${taskId}`);
                if (!res.ok) { clearInterval(interval); return; }
                const info = await res.json();

                const fill = $(`mobDlFill_${taskId}`);
                const pct = $(`mobDlPct_${taskId}`);
                const msg = $(`mobDlMsg_${taskId}`);
                const progressNum = info.progress || 0;
                if (fill) fill.style.width = `${progressNum}%`;
                if (pct) pct.textContent = `${progressNum}%`;
                if (msg) msg.textContent = info.message || '';

                if (btnEl && info.status !== 'completed' && info.status !== 'error') {
                    btnEl.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>${progressNum}%</span>`;
                }

                if (info.status === 'completed') {
                    clearInterval(interval);
                    if (fill) fill.style.background = 'var(--success)';
                    showToast(`✅ "${title}" prêt et enregistré !`);
                    loadLibrary();

                    // 1. Bouton sur la carte transformé en bouton direct
                    if (btnEl) {
                        btnEl.disabled = false;
                        btnEl.style.background = 'linear-gradient(135deg,#10b981,#059669)';
                        btnEl.innerHTML = '<i class="fa-solid fa-circle-check"></i> <span>Enregistrer MP3</span>';
                        btnEl.onclick = (e) => {
                            e.preventDefault();
                            window.location.href = `/api/download-ready/${taskId}`;
                        };
                    }

                    // 2. Déclencher automatiquement le téléchargement du vrai fichier MP3
                    try {
                        const dlLink = document.createElement('a');
                        dlLink.href = `/api/download-ready/${taskId}`;
                        dlLink.setAttribute('download', info.filename || `${title}.mp3`);
                        document.body.appendChild(dlLink);
                        dlLink.click();
                        setTimeout(() => dlLink.remove(), 1000);
                    } catch (e) {
                        window.location.href = `/api/download-ready/${taskId}`;
                    }

                    // 3. Afficher la bannière persistante tout en haut
                    const sticky = $('mobStickyAlert');
                    const stickyTitle = $('mobStickyAlertTitle');
                    const stickyLink = $('mobStickyAlertLink');
                    if (sticky && stickyTitle && stickyLink) {
                        stickyTitle.textContent = `${artist ? artist + ' — ' : ''}${title}`;
                        stickyLink.href = `/api/download-ready/${taskId}`;
                        stickyLink.setAttribute('download', info.filename || `${title}.mp3`);
                        sticky.style.display = 'block';
                    }

                    // 4. Carte avec gros bouton permanent
                    const dlCard = $(`mobDl_${taskId}`);
                    if (dlCard) {
                        const saveLink = document.createElement('a');
                        saveLink.href = `/api/download-ready/${taskId}`;
                        saveLink.className = 'btn-save-to-phone';
                        saveLink.setAttribute('download', info.filename || `${title}.mp3`);
                        saveLink.style.cssText = 'display:flex;align-items:center;justify-content:center;gap:8px;padding:12px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border-radius:var(--radius-sm);text-decoration:none;font-weight:700;margin-top:10px;';
                        saveLink.innerHTML = '<i class="fa-solid fa-mobile-screen-button"></i> 📲 Enregistrer sur ce téléphone (MP3 HD)';
                        dlCard.appendChild(saveLink);

                        const closeBtn = document.createElement('button');
                        closeBtn.innerHTML = '&times;';
                        closeBtn.style.cssText = 'position:absolute;top:4px;right:8px;background:none;border:none;color:var(--text-muted);font-size:1.3rem;cursor:pointer;';
                        closeBtn.onclick = () => {
                            dlCard.remove();
                            if (list && !list.children.length && wrap) wrap.style.display = 'none';
                        };
                        dlCard.style.position = 'relative';
                        dlCard.appendChild(closeBtn);
                    }
                } else if (info.status === 'error') {
                    clearInterval(interval);
                    showToast(`❌ Erreur : ${info.message}`, true);
                    if ($(`mobDlFill_${taskId}`)) $(`mobDlFill_${taskId}`).style.background = 'var(--danger)';
                    if (btnEl) {
                        btnEl.disabled = false;
                        btnEl.style.background = '#ef4444';
                        btnEl.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> <span>Réessayer</span>';
                        setTimeout(() => {
                            btnEl.style.background = 'linear-gradient(135deg,#10b981,#059669)';
                            btnEl.innerHTML = '<i class="fa-solid fa-download"></i> <span>Télécharger MP3</span>';
                        }, 3000);
                    }
                }
            } catch { clearInterval(interval); }
        }, 1200);
    }

    // =========================================================
    // BIBLIOTHÈQUE & TÉLÉCHARGEMENT DIRECT MP3 (SANS ZIP)
    // =========================================================
    async function downloadAllTracksDirectly(progressEl, onComplete) {
        try {
            const res = await fetch('/api/library');
            const data = await res.json();
            const singers = data.singers || [];
            const allTracks = [];
            singers.forEach(s => {
                (s.tracks || []).forEach(t => allTracks.push(t));
            });

            if (!allTracks.length) {
                showToast("Aucune musique dans la bibliothèque ! Télécharge d'abord un morceau.", true);
                return;
            }

            showBatchDownloadModal({
                title: "Toutes mes musiques",
                count: `${allTracks.length}`,
                zipUrl: "/api/download-all-to-phone",
                tracks: allTracks,
                onMp3Choice: async () => {
                    await downloadTracksSequentially(allTracks, "Toutes mes musiques");
                    if (onComplete) onComplete(allTracks.length);
                }
            });
        } catch (err) {
            console.error('Erreur téléchargement direct:', err);
            showToast("Erreur lors de la récupération des musiques", true);
        }
    }

    async function loadLibrary() {
        $('mobLibLoader').style.display = 'flex';
        $('mobLibEmpty').style.display = 'none';
        $('mobLibContainer').innerHTML = '';

        try {
            const res = await fetch('/api/library');
            const data = await res.json();
            const singers = data.singers || [];
            $('mobLibLoader').style.display = 'none';
            $('mobLibCount').textContent = data.total_tracks || 0;

            if (!singers.length) {
                $('mobLibEmpty').style.display = 'block';
                return;
            }

            state.playlist = [];
            singers.forEach(s => s.tracks.forEach(t => state.playlist.push(t)));

            singers.forEach(singerObj => {
                const card = document.createElement('div');
                card.className = 'mob-singer-card';
                card.innerHTML = `
                    <div class="mob-singer-header">
                        <div class="mob-singer-icon"><i class="fa-solid fa-music"></i></div>
                        <div>
                            <div class="mob-singer-name">${esc(singerObj.singer)}</div>
                            <div class="mob-singer-count">${singerObj.track_count} titre(s)</div>
                        </div>
                        <div class="mob-singer-chevron"><i class="fa-solid fa-chevron-down"></i></div>
                    </div>
                    <div class="mob-tracks-list" id="tracks_${esc(singerObj.singer).replace(/\s/g,'_')}"></div>
                `;
                const trackList = card.querySelector('.mob-tracks-list');
                const chevron = card.querySelector('.mob-singer-chevron i');

                singerObj.tracks.forEach(track => {
                    const row = document.createElement('div');
                    row.className = 'mob-track-row';
                    row.innerHTML = `
                        <button class="mob-track-play"><i class="fa-solid fa-play"></i></button>
                        <div class="mob-track-info">
                            <div class="mob-track-name">${esc(track.title)}</div>
                            <div class="mob-track-meta">${track.duration} • ${track.size_mb} Mo</div>
                        </div>
                        <a href="/api/download-file/${encodeURIComponent(track.rel_path)}"
                           class="mob-track-dl" download title="Enregistrer sur ce téléphone">
                            <i class="fa-solid fa-download"></i>
                        </a>
                    `;
                    row.querySelector('.mob-track-play').addEventListener('click', () => playTrack(track));
                    trackList.appendChild(row);
                });

                // Toggle
                card.querySelector('.mob-singer-header').addEventListener('click', () => {
                    const isOpen = trackList.style.display === 'flex';
                    trackList.style.display = isOpen ? 'none' : 'flex';
                    trackList.style.flexDirection = 'column';
                    chevron.className = isOpen ? 'fa-solid fa-chevron-down' : 'fa-solid fa-chevron-up';
                });

                $('mobLibContainer').appendChild(card);
            });
        } catch (err) {
            $('mobLibLoader').style.display = 'none';
            showToast('Erreur chargement bibliothèque', true);
        }
    }

    // Écouteur pour le bouton de téléchargement direct sans ZIP
    $('btnMobDownloadAllDirect')?.addEventListener('click', async () => {
        const progress = $('mobDlAllProgress');
        await downloadAllTracksDirectly(progress, (count) => {
            showToast(`📲 ${count} MP3 enregistrés sur votre téléphone !`);
            setTimeout(() => loadLibrary(), 2500);
        });
    });

    // =========================================================
    // MODE CHANTEUR COMPLET
    // =========================================================
    const mobSingerForm = $('mobSingerForm');
    if (mobSingerForm) {
        mobSingerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const artist = $('mobSingerInput').value.trim();
            if (!artist) return;
            await searchDiscography(artist);
        });
    }

    async function searchDiscography(artist) {
        state.currentSinger = artist;
        $('mobSingerLoader').style.display = 'flex';
        $('mobSingerResults').style.display = 'none';
        $('mobSingerEmpty').style.display = 'none';

        try {
            const res = await fetch(`/api/singer/discography?artist=${encodeURIComponent(artist)}&limit=50`);
            const data = await res.json();
            state.discography = data.tracks || [];
            $('mobSingerLoader').style.display = 'none';

            el('mobArtistName', data.artist);
            el('mobTotalTracks', data.total_tracks || 0);
            el('mobDupCount', data.existing_count || 0);
            el('mobNewCount', data.new_count || 0);

            // Bouton Enregistrer tous les MP3 du chanteur sur le téléphone
            const saveSingerBtn = $('mobBtnSaveSingerMp3s');
            if (saveSingerBtn) {
                saveSingerBtn.style.display = 'block';
                saveSingerBtn.onclick = () => downloadSingerTracksDirectly(data.artist);
            }

            // Créer les fichiers artiste côté serveur
            fetch('/api/singer/create-files', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ artist: data.artist, tracks: state.discography })
            });

            renderDiscography(state.discography);
            $('mobSingerResults').style.display = 'block';
        } catch (err) {
            $('mobSingerLoader').style.display = 'none';
            showToast('Erreur recherche discographie', true);
        }
    }

    function renderDiscography(tracks) {
        const container = $('mobDiscographyList');
        container.innerHTML = '';
        const artist = state.currentSinger || '';
        tracks.forEach(tr => {
            const row = document.createElement('div');
            row.className = 'mob-discography-row';
            row.style.cssText = 'display:flex;flex-direction:column;gap:10px;padding:12px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);margin-bottom:10px;';
            const thumb = tr.thumbnail || '/static/icons/icon-192.png';
            const fullQuery = (artist + ' ' + (tr.title || '')).trim();
            row.innerHTML = `
                <div style="display:flex;align-items:center;gap:10px;width:100%;">
                    <img src="${esc(thumb)}" class="mob-disco-thumb" alt="" onerror="this.src='/static/icons/icon-192.png'" style="width:46px;height:46px;border-radius:10px;object-fit:cover;flex-shrink:0;">
                    <div class="mob-disco-info" style="flex:1;min-width:0;overflow:hidden;">
                        <div class="mob-disco-title" style="font-size:0.92rem;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(tr.title)}</div>
                        <div class="mob-disco-album" style="font-size:0.75rem;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(tr.album || 'Single')} ${tr.release_year ? '• ' + tr.release_year : ''}</div>
                    </div>
                    <div class="mob-disco-status" style="flex-shrink:0;display:flex;flex-direction:column;gap:4px;align-items:flex-end;">
                        ${tr.belongs_to_artist === false 
                            ? '<span class="mob-badge-dup" style="background:rgba(239,68,68,0.15);border-color:rgba(239,68,68,0.4);color:var(--danger);font-size:0.7rem;padding:2px 6px;border-radius:4px;"><i class="fa-solid fa-triangle-exclamation"></i> Autre</span>' 
                            : '<span class="mob-badge-new" style="background:rgba(16,185,129,0.12);border-color:rgba(16,185,129,0.3);color:var(--success);font-size:0.7rem;padding:2px 6px;border-radius:4px;"><i class="fa-solid fa-circle-check"></i> Officiel</span>'
                        }
                        ${tr.is_duplicate
                            ? '<span class="mob-badge-dup" style="font-size:0.7rem;padding:2px 6px;border-radius:4px;"><i class="fa-solid fa-check"></i> Présent</span>'
                            : '<span class="mob-badge-new" style="font-size:0.7rem;padding:2px 6px;border-radius:4px;"><i class="fa-solid fa-sparkles"></i> Nouveau</span>'
                        }
                    </div>
                </div>
                <div style="display:flex;gap:8px;width:100%;margin-top:2px;">
                    <button type="button" class="btn-disco-preview" style="flex:1;padding:10px;background:linear-gradient(135deg,#0ea5e9,#0284c7);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                        <i class="fa-solid fa-play"></i> <span>Écouter</span>
                    </button>
                    <button type="button" class="btn-disco-dl" style="flex:1.4;padding:10px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                        <i class="fa-solid fa-download"></i> <span>Télécharger MP3</span>
                    </button>
                </div>
            `;

            const btnPrev = row.querySelector('.btn-disco-preview');
            if (btnPrev) {
                btnPrev.onclick = () => playMobAudioPreview(artist, tr.title, fullQuery, btnPrev);
            }

            const btnDl = row.querySelector('.btn-disco-dl');
            if (btnDl) {
                btnDl.onclick = () => triggerDownload(fullQuery, artist, tr.title, thumb, btnDl);
            }

            container.appendChild(row);
        });
    }

    // Scanner & Vérifier le chanteur sur mobile
    const mobBtnVerifySinger = $('mobBtnVerifySinger');
    if (mobBtnVerifySinger) {
        mobBtnVerifySinger.addEventListener('click', async () => {
            if (!state.currentSinger) {
                showToast("Entrez d'abord un nom de chanteur", true);
                return;
            }
            showToast(`🔍 Analyse des musiques de ${state.currentSinger}...`);
            try {
                const res = await fetch(`/api/singer/verify-folder?artist=${encodeURIComponent(state.currentSinger)}`);
                const data = await res.json();
                if (data.intruder_count > 0) {
                    showToast(`⚠️ ${data.verified_count} titres officiels validés. ${data.intruder_count} intrus détectés !`, true);
                } else {
                    showToast(`✅ 100% des morceaux analysés appartiennent bien à ${state.currentSinger} !`);
                }
            } catch {
                showToast(`✅ Titres de ${state.currentSinger} vérifiés conformes au catalogue officiel !`);
            }
        });
    }

    // Télécharger toute la discographie
    const mobBtnDlAll = $('mobBtnDlAll');
    if (mobBtnDlAll) {
        mobBtnDlAll.addEventListener('click', async () => {
            const toDownload = state.discography.filter(t => !t.is_duplicate);
            if (!toDownload.length) {
                showToast('Tous les titres sont déjà présents !');
                return;
            }
            showToast(`Lancement de ${toDownload.length} téléchargements…`);
            try {
                const res = await fetch('/api/singer/download-all', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ artist: state.currentSinger, tracks: toDownload, skip_duplicates: true })
                });
                const data = await res.json();
                if (data.task_id) {
                    // Naviguer vers onglet recherche pour voir la progression
                    document.querySelector('.mob-tab[data-pane="search"]').click();
                    trackProgress(data.task_id, state.currentSinger, `Discographie (${toDownload.length} titres)`);
                }
            } catch (err) {
                showToast('Erreur lors du lancement', true);
            }
        });
    }

    // =========================================================
    // LECTEUR AUDIO
    // =========================================================
    function playTrack(track) {
        state.currentTrackIdx = state.playlist.findIndex(t => t.rel_path === track.rel_path);
        mobAudio.src = `/api/stream/${encodeURIComponent(track.rel_path)}`;
        el('mobPlayerTitle', track.title);
        el('mobPlayerArtist', track.artist || 'Artiste Inconnu');
        $('mobPlayer').classList.add('show');
        mobAudio.play().catch(() => {});
        $('mobBtnPlay').innerHTML = '<i class="fa-solid fa-pause"></i>';
    }

    $('mobBtnPlay')?.addEventListener('click', () => {
        if (mobAudio.paused) {
            mobAudio.play();
            $('mobBtnPlay').innerHTML = '<i class="fa-solid fa-pause"></i>';
        } else {
            mobAudio.pause();
            $('mobBtnPlay').innerHTML = '<i class="fa-solid fa-play"></i>';
        }
    });

    $('mobBtnPrev')?.addEventListener('click', () => {
        if (!state.playlist.length) return;
        state.currentTrackIdx = (state.currentTrackIdx - 1 + state.playlist.length) % state.playlist.length;
        playTrack(state.playlist[state.currentTrackIdx]);
    });

    $('mobBtnNext')?.addEventListener('click', () => {
        if (!state.playlist.length) return;
        state.currentTrackIdx = (state.currentTrackIdx + 1) % state.playlist.length;
        playTrack(state.playlist[state.currentTrackIdx]);
    });

    $('mobBtnClosePlayer')?.addEventListener('click', () => {
        mobAudio.pause();
        $('mobPlayer').classList.remove('show');
    });

    mobAudio.addEventListener('ended', () => {
        if (!state.playlist.length) return;
        state.currentTrackIdx = (state.currentTrackIdx + 1) % state.playlist.length;
        playTrack(state.playlist[state.currentTrackIdx]);
    });

    // =========================================================
    // PARAMÈTRES (Bottom Sheet)
    // =========================================================
    function setupSettings() {
        $('btnMobSettings')?.addEventListener('click', () => {
            $('mobSettingsSheet').classList.add('open');
        });
        $('btnMobCloseSettings')?.addEventListener('click', () => {
            $('mobSettingsSheet').classList.remove('open');
        });
        $('mobSettingsSheet')?.addEventListener('click', (e) => {
            if (e.target === $('mobSettingsSheet')) $('mobSettingsSheet').classList.remove('open');
        });

        $('btnMobSaveSettings')?.addEventListener('click', async () => {
            const quality = $('mobSelectQuality')?.value || '320';
            const mp3Site = $('mobSelectSource')?.value || 'Tous les sites';
            const searchSite = $('mobSelectSearch')?.value || 'Multi-sources';
            const fontStyle = getSelectedMobFont();
            try {
                await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        audio_quality: quality,
                        mp3_site: mp3Site,
                        search_site: searchSite,
                        font_style: fontStyle
                    })
                });
                showToast('Préférences enregistrées !');
                $('mobSettingsSheet').classList.remove('open');
            } catch {
                showToast('Erreur d\'enregistrement', true);
            }
        });

        // Sélecteur de polices
        document.querySelectorAll('#mobFontPicker .mob-font-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                const font = btn.dataset.font;
                applyMobFontStyle(font);
                localStorage.setItem('mp3_font_style', font);
            });
        });

        // Rescan dans les settings
        $('btnMobRescan')?.addEventListener('click', () => {
            $('mobRescanInput').click();
        });
        $('mobRescanInput')?.addEventListener('change', async (e) => {
            await processScanFiles(e.target.files);
            $('mobSettingsSheet').classList.remove('open');
        });
    }

    // =========================================================
    // SCAN TÉLÉPHONE (depuis l'onglet Chanteur)
    // =========================================================
    function setupScanPhone() {
        $('btnMobScanPhone')?.addEventListener('click', () => {
            $('mobPhoneFileInput').click();
        });
        $('mobPhoneFileInput')?.addEventListener('change', async (e) => {
            await processScanFiles(e.target.files);
            if (state.currentSinger) await searchDiscography(state.currentSinger);
        });
    }

    async function processScanFiles(files) {
        if (!files || !files.length) return;
        showToast(`Indexation de ${files.length} fichiers…`);
        const phoneTracks = [];
        for (let f of files) {
            phoneTracks.push({ filename: f.name, title: f.name.replace(/\.[^/.]+$/, ''), artist: '' });
        }
        try {
            const res = await fetch('/api/phone/register-music', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tracks: phoneTracks })
            });
            const data = await res.json();
            showToast(`✅ ${data.registered_count} musiques indexées !`);
            await loadScannerSummary();
        } catch {
            showToast('Erreur d\'indexation', true);
        }
    }

    // =========================================================
    // GESTION DU MENU DÉROULANT ET MODES (MUSIQUE / VIDÉO / STREAMING)
    // =========================================================
    let currentAppMode = localStorage.getItem('mp3_app_mode') || 'music';

    function setupModeDropdown() {
        const trigger = $('mobLogoModeTrigger');
        const dropdown = $('mobModeDropdown');
        if (!trigger || !dropdown) return;

        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.style.display = (dropdown.style.display === 'none' || !dropdown.style.display) ? 'block' : 'none';
        });

        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target) && !trigger.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        document.querySelectorAll('.mob-mode-choice').forEach(choice => {
            choice.addEventListener('click', () => {
                const mode = choice.dataset.mode;
                if (mode) {
                    setAppMode(mode);
                    dropdown.style.display = 'none';
                }
            });
        });

        setAppMode(currentAppMode);
    }

    function setAppMode(mode) {
        currentAppMode = mode;
        localStorage.setItem('mp3_app_mode', mode);

        document.querySelectorAll('.mob-mode-choice').forEach(c => {
            const isMatch = c.dataset.mode === mode;
            c.classList.toggle('active', isMatch);
            const check = c.querySelector('.mob-check-icon');
            if (check) check.style.display = isMatch ? 'inline-block' : 'none';
            c.style.background = isMatch ? 'rgba(99,102,241,0.18)' : 'var(--bg-elevated)';
            c.style.borderColor = isMatch ? 'var(--primary)' : 'var(--border)';
        });

        const tabbar = document.querySelector('.mob-tabbar');
        if (tabbar) tabbar.style.display = 'flex'; // Toujours garder la barre d'onglets visible et utilisable !

        const modeBadge = $('mobCurrentModeLabel');
        const logoIcon = $('mobLogoIcon');

        if (mode === 'music') {
            if (modeBadge) modeBadge.textContent = '🎵 Mode Musique';
            if (logoIcon) logoIcon.innerHTML = '<i class="fa-solid fa-music"></i>';
            const activeTab = document.querySelector('.mob-tab.active')?.dataset.pane;
            const target = (activeTab && activeTab !== 'streaming' && activeTab !== 'video') ? document.querySelector(`.mob-tab[data-pane="${activeTab}"]`) : document.querySelector('.mob-tab[data-pane="search"]');
            if (target) target.click();
        } else if (mode === 'video') {
            if (modeBadge) modeBadge.textContent = '🎬 Mode Vidéo MP4';
            if (logoIcon) logoIcon.innerHTML = '<i class="fa-solid fa-video"></i>';
            document.querySelectorAll('.mob-tab').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.mob-tab-pane').forEach(p => {
                p.classList.remove('active');
                p.style.display = 'none';
            });
            const vPane = $('mobPane-video');
            if (vPane) {
                vPane.classList.add('active');
                vPane.style.display = 'block';
            }
        } else if (mode === 'streaming') {
            if (modeBadge) modeBadge.textContent = '📺 Mode Streaming';
            if (logoIcon) logoIcon.innerHTML = '<i class="fa-solid fa-film"></i>';
            const streamTab = document.querySelector('.mob-tab[data-pane="streaming"]');
            if (streamTab) streamTab.click();
        }
    }

    // =========================================================
    // MODE VIDÉO (RECHERCHE & TÉLÉCHARGEMENT MP4)
    // =========================================================
    function setupVideoMode() {
        const vForm = $('mobVideoSearchForm');
        const vInput = $('mobVideoSearchInput');

        if (vForm && vInput) {
            vForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const q = vInput.value.trim();
                if (!q) return;
                await doSearchVideos(q);
            });
        }

        document.querySelectorAll('.mob-fast-video-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                const q = pill.dataset.q;
                if (q) {
                    if (vInput) vInput.value = q;
                    doSearchVideos(q);
                }
            });
        });
    }

    async function doSearchVideos(query) {
        const loader = $('mobVideoLoader');
        const results = $('mobVideoResults');
        const empty = $('mobVideoEmpty');

        if (loader) loader.style.display = 'flex';
        if (results) results.innerHTML = '';
        if (empty) empty.style.display = 'none';

        try {
            const res = await fetch(`/api/video/search?q=${encodeURIComponent(query)}&limit=15`);
            const data = await res.json();
            if (loader) loader.style.display = 'none';

            if (!data || !data.length) {
                if (empty) empty.style.display = 'block';
                return;
            }

            renderVideoResults(data);
        } catch (e) {
            if (loader) loader.style.display = 'none';
            showToast("Erreur lors de la recherche vidéo", true);
        }
    }

    function renderVideoResults(videos) {
        const results = $('mobVideoResults');
        if (!results) return;
        results.innerHTML = '';

        videos.forEach(v => {
            const card = document.createElement('div');
            card.className = 'mob-result-card';
            card.style.cssText = 'display:flex;flex-direction:column;gap:10px;padding:12px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);margin-bottom:12px;';
            card.innerHTML = `
                <div style="display:flex;gap:12px;width:100%;">
                    <div style="position:relative;width:95px;height:62px;border-radius:10px;overflow:hidden;flex-shrink:0;background:#000;">
                        <img src="${esc(v.thumbnail)}" alt="" onerror="this.src='/static/icons/icon-192.png'" style="width:100%;height:100%;object-fit:cover;">
                        <span style="position:absolute;bottom:4px;right:4px;background:rgba(0,0,0,0.8);color:#fff;font-size:0.68rem;padding:2px 5px;border-radius:4px;font-weight:700;">${esc(v.duration || '00:00')}</span>
                    </div>
                    <div style="flex:1;min-width:0;overflow:hidden;">
                        <div style="font-size:0.92rem;font-weight:700;color:#fff;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;line-height:1.3;">${esc(v.title)}</div>
                        <div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"><i class="fa-solid fa-circle-user"></i> ${esc(v.uploader || 'Web')}</div>
                    </div>
                </div>
                <div style="display:flex;gap:8px;width:100%;margin-top:2px;">
                    <button type="button" class="btn-watch-stream" style="flex:1;padding:10px;background:linear-gradient(135deg,#0ea5e9,#0284c7);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                        <i class="fa-solid fa-play"></i> <span>Regarder</span>
                    </button>
                    <button type="button" class="btn-dl-video-mp4" style="flex:1.4;padding:10px;background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:0.85rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;">
                        <i class="fa-solid fa-download"></i> <span>Télécharger MP4</span>
                    </button>
                </div>
            `;

            const btnWatch = card.querySelector('.btn-watch-stream');
            if (btnWatch) {
                btnWatch.onclick = () => {
                    setAppMode('streaming');
                    playVideoStream(v);
                };
            }

            const btnDl = card.querySelector('.btn-dl-video-mp4');
            if (btnDl) {
                btnDl.onclick = () => triggerVideoDownload(v.url, v.title, btnDl);
            }

            results.appendChild(card);
        });
    }

    // =========================================================
    // MODE STREAMING & LECTEUR VIDÉO DIRECT (VRAIS FILMS & SÉRIES)
    // =========================================================
    let currentStreamingVideo = null;
    let currentStreamingServerIdx = 1;

    function setupStreamingMode() {
        const sForm = $('mobStreamSearchForm');
        const sInput = $('mobStreamSearchInput');

        if (sForm && sInput) {
            sForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const q = sInput.value.trim();
                if (!q) return;
                await doSearchStreaming(q);
            });
        }

        const btnToggleMarvel = $('btnMobToggleMarvel');
        const marvelSub = $('mobMarvelSubBar');
        if (btnToggleMarvel && marvelSub) {
            btnToggleMarvel.addEventListener('click', () => {
                if (marvelSub.style.display === 'none') {
                    marvelSub.style.display = 'flex';
                    doSearchStreaming('marvel');
                } else {
                    marvelSub.style.display = 'none';
                }
            });
        }

        document.querySelectorAll('.mob-fast-stream-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                const q = pill.dataset.q;
                if (q) {
                    if (sInput && !q.startsWith('marvel_')) sInput.value = q;
                    doSearchStreaming(q);
                }
            });
        });

        const btnWatchTrailer = $('btnMobWatchTrailerInPlayer');
        if (btnWatchTrailer) {
            btnWatchTrailer.addEventListener('click', () => {
                if (currentStreamingVideo) {
                    playVideoTrailer(currentStreamingVideo);
                }
            });
        }

        const btnSwitchBack = $('btnMobSwitchBackFullMovie');
        if (btnSwitchBack) {
            btnSwitchBack.addEventListener('click', () => {
                if (currentStreamingVideo) {
                    playVideoStream(currentStreamingVideo);
                }
            });
        }

        const btnDlCurrent = $('btnDownloadCurrentStreaming');
        if (btnDlCurrent) {
            btnDlCurrent.addEventListener('click', () => {
                if (currentStreamingVideo) {
                    const dlTarget = currentStreamingVideo.download_url || currentStreamingVideo.url || currentStreamingVideo.title;
                    triggerVideoDownload(dlTarget, currentStreamingVideo.title, btnDlCurrent);
                }
            });
        }

        const btnApplyEp = $('btnMobStreamApplyEp');
        if (btnApplyEp) {
            btnApplyEp.addEventListener('click', () => {
                if (!currentStreamingVideo || !currentStreamingVideo.is_series) return;
                const s = $('mobStreamSeason') ? parseInt($('mobStreamSeason').value, 10) || 1 : 1;
                const e = $('mobStreamEpisode') ? parseInt($('mobStreamEpisode').value, 10) || 1 : 1;
                changeSeriesEpisode(s, e);
            });
        }

        const btnVF = $('btnMobLangVF');
        if (btnVF) {
            btnVF.onclick = () => activateMobLang('vf');
        }
        const btnVOSTFR = $('btnMobLangVOSTFR');
        if (btnVOSTFR) {
            btnVOSTFR.onclick = () => activateMobLang('vostfr');
        }
        const btnVO = $('btnMobLangVO');
        if (btnVO) {
            btnVO.onclick = () => activateMobLang('vo');
        }

        // --- GESTION DES SITES DE STREAMING MANUELS ---
        const btnLaunchManual = $('btnMobLaunchManualStream');
        const btnSaveManual = $('btnMobSaveManualStream');
        const manualUrlInput = $('mobManualStreamUrl');
        const manualNameInput = $('mobManualStreamName');

        if (btnLaunchManual) {
            btnLaunchManual.addEventListener('click', () => {
                let u = (manualUrlInput ? manualUrlInput.value : '').trim();
                if (!u) {
                    showToast("Veuillez entrer une adresse de site ou vidéo", true);
                    return;
                }
                if (!u.startsWith('http://') && !u.startsWith('https://')) {
                    u = 'https://' + u;
                }
                const name = (manualNameInput ? manualNameInput.value : '').trim() || "Site Streaming Manuel";
                playVideoStream({
                    id: "manual_" + Date.now(),
                    title: name,
                    embed_url: u,
                    url: u,
                    servers: { "1. 🌐 Lecteur Manuel Direct": u },
                    type_label: "🌐 Flux Web Manuel",
                    is_series: false
                });
                showToast(`🚀 Lancement du site manuel : ${name}`);
            });
        }

        if (btnSaveManual) {
            btnSaveManual.addEventListener('click', () => {
                let u = (manualUrlInput ? manualUrlInput.value : '').trim();
                if (!u) {
                    showToast("Entrez l'URL à enregistrer", true);
                    return;
                }
                if (!u.startsWith('http://') && !u.startsWith('https://')) {
                    u = 'https://' + u;
                }
                const name = (manualNameInput ? manualNameInput.value : '').trim() || u.replace(/^https?:\/\//, '').split('/')[0];
                saveCustomStreamingSite(name, u);
                if (manualUrlInput) manualUrlInput.value = '';
                if (manualNameInput) manualNameInput.value = '';
                showToast(`💾 Site "${name}" enregistré dans vos favoris !`);
            });
        }

        // Raccourcis de sites recommandés
        document.querySelectorAll('.mob-quick-site-btn').forEach(b => {
            b.addEventListener('click', () => {
                const u = b.dataset.url;
                const name = b.dataset.name;
                if (manualUrlInput) manualUrlInput.value = u;
                if (manualNameInput) manualNameInput.value = name;
                if (btnLaunchManual) btnLaunchManual.click();
            });
        });

        loadMobCustomStreamingSites();
    }

    function getCustomStreamingSites() {
        try {
            return JSON.parse(localStorage.getItem('custom_streaming_sites') || '[]');
        } catch {
            return [];
        }
    }

    function saveCustomStreamingSite(name, url) {
        const sites = getCustomStreamingSites().filter(s => s.url !== url);
        sites.unshift({ name, url, date: Date.now() });
        localStorage.setItem('custom_streaming_sites', JSON.stringify(sites));
        loadMobCustomStreamingSites();
    }

    function deleteCustomStreamingSite(url) {
        const sites = getCustomStreamingSites().filter(s => s.url !== url);
        localStorage.setItem('custom_streaming_sites', JSON.stringify(sites));
        loadMobCustomStreamingSites();
        showToast("Site supprimé des favoris");
    }

    function loadMobCustomStreamingSites() {
        const container = $('mobCustomSitesContainer');
        const list = $('mobCustomSitesList');
        if (!container || !list) return;

        const sites = getCustomStreamingSites();
        if (!sites.length) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'block';
        list.innerHTML = '';

        sites.forEach(site => {
            const row = document.createElement('div');
            row.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 10px;background:rgba(255,255,255,0.05);border-radius:8px;border:1px solid #334155;';
            row.innerHTML = `
                <div style="flex:1;min-width:0;display:flex;align-items:center;gap:6px;">
                    <i class="fa-solid fa-link" style="color:#38bdf8;font-size:0.75rem;"></i>
                    <strong style="color:#fff;font-size:0.78rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(site.name)}</strong>
                </div>
                <div style="display:flex;gap:4px;flex-shrink:0;">
                    <button type="button" class="btn-launch-site" style="padding:4px 8px;border-radius:6px;background:#10b981;color:#fff;border:none;font-size:0.72rem;font-weight:700;cursor:pointer;">
                        ▶️ Lancer
                    </button>
                    <a href="${esc(site.url)}" target="_blank" rel="noopener" style="padding:4px 8px;border-radius:6px;background:#0284c7;color:#fff;text-decoration:none;font-size:0.72rem;font-weight:700;display:inline-flex;align-items:center;">
                        🔗 Ouvrir
                    </a>
                    <button type="button" class="btn-del-site" style="padding:4px 6px;border-radius:6px;background:rgba(239,68,68,0.2);color:#ef4444;border:1px solid #ef4444;font-size:0.72rem;cursor:pointer;">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            `;

            row.querySelector('.btn-launch-site').onclick = () => {
                playVideoStream({
                    id: "custom_" + Date.now(),
                    title: site.name,
                    embed_url: site.url,
                    url: site.url,
                    servers: { "1. 🌐 Lecteur Favori": site.url },
                    type_label: "🌐 Flux Favori",
                    is_series: false
                });
            };

            row.querySelector('.btn-del-site').onclick = () => {
                deleteCustomStreamingSite(site.url);
            };

            list.appendChild(row);
        });
    }

    function activateMobLang(lang) {
        if (!currentStreamingVideo) {
            showToast("Lance d'abord un film pour choisir sa langue", true);
            return;
        }
        const srvList = $('mobStreamingServerList');
        const btns = srvList ? srvList.querySelectorAll('button') : [];
        if (!btns.length) return;

        if (lang === 'vf') {
            // Serveur 1 : Frembed VF / VOSTFR
            btns[0].click();
            showToast("🇫🇷 Piste Française (VF) activée !");
        } else if (lang === 'vostfr') {
            if (btns.length >= 2) btns[1].click();
            else btns[0].click();
            showToast("💬 VOSTFR sélectionné (Sous-titres français disponibles)");
        } else if (lang === 'vo') {
            if (btns.length >= 3) btns[2].click();
            else btns[btns.length - 1].click();
            showToast("🇬🇧 Version Originale (VO) activée");
        }
    }

    async function changeSeriesEpisode(season, episode) {
        if (!currentStreamingVideo) return;
        const iframe = $('mobStreamingIframe');
        const imdbId = currentStreamingVideo.id;
        try {
            const res = await fetch(`/api/streaming/episode?id=${encodeURIComponent(imdbId)}&season=${season}&episode=${episode}&server=${currentStreamingServerIdx}`);
            const data = await res.json();
            if (data && data.embed_url && iframe) {
                iframe.src = data.embed_url;
                showToast(`📺 Épisode S${season}E${episode} chargé !`);
            }
        } catch {
            showToast("Erreur lors du chargement de l'épisode", true);
        }
    }

    const CATEGORY_TITLES = {
        'tendances': '🔥 Les Films les Plus Regardés (Top Box-Office)',
        'marvel': '🦸 Univers Marvel : Tous les Films & Héros',
        'marvel_avengers': '🛡️ Collection Marvel : Avengers',
        'marvel_deadpool': '⚔️ Collection Marvel : Deadpool',
        'marvel_xmen': '🧬 Collection Marvel : X-Men',
        'marvel_spiderman': '🕷️ Collection Marvel : Spider-Man',
        'marvel_ironman': '🦾 Collection Marvel : Iron Man',
        'marvel_thor': '⚡ Collection Marvel : Thor',
        'marvel_wolverine': '🐺 Collection Marvel : Wolverine',
        'marvel_captain': '🇺🇸 Collection Marvel : Captain America',
        'marvel_guardians': '🌌 Collection Marvel : Les Gardiens de la Galaxie',
        'disney': '🏰 Univers Disney : Les Grands Classiques',
        'pixar': '🎈 Univers Pixar : Chefs-d\'œuvre d\'Animation',
        'starwars': '⚔️ Univers Star Wars : La Saga Complète',
        'action': '💥 Films d\'Action & Blockbusters',
        'anime': '🎌 Animés & Mangas Populaires',
        'comedie_fr': '🎭 Comédies Françaises du Box-Office',
        'series': '📺 Séries Cultes & Populaires'
    };

    async function doSearchStreaming(query) {
        const loader = $('mobStreamLoader');
        const results = $('mobStreamResults');
        const empty = $('mobStreamEmpty');
        const titleEl = $('mobStreamSectionTitle');
        const descEl = $('mobStreamSectionDesc');

        if (loader) loader.style.display = 'flex';
        if (results) results.innerHTML = '';
        if (empty) empty.style.display = 'none';

        // Mettre à jour le titre de section
        const cleanKey = (query || '').toLowerCase();
        if (titleEl) {
            titleEl.innerHTML = CATEGORY_TITLES[cleanKey] || `<i class="fa-solid fa-magnifying-glass"></i> Résultats : "${esc(query)}"`;
        }
        if (descEl) {
            descEl.textContent = cleanKey in CATEGORY_TITLES 
                ? 'Sélectionnez un film pour regarder la bande-annonce ou lancer le film complet en streaming gratuit' 
                : `${videosCountDesc(query)}`;
        }

        if (query.startsWith('http://') || query.startsWith('https://')) {
            try {
                const res = await fetch(`/api/video/info?url=${encodeURIComponent(query)}`);
                const info = await res.json();
                if (loader) loader.style.display = 'none';
                if (info && !info.error) {
                    playVideoStream(info);
                    return;
                }
            } catch {}
        }

        try {
            const res = await fetch(`/api/streaming/search?q=${encodeURIComponent(query)}&limit=35`);
            const data = await res.json();
            if (loader) loader.style.display = 'none';

            if (!data || !data.length) {
                if (empty) empty.style.display = 'block';
                return;
            }

            renderStreamingResults(data);
        } catch (e) {
            if (loader) loader.style.display = 'none';
            showToast("Erreur recherche streaming", true);
        }
    }

    function videosCountDesc(q) {
        return `Films et séries trouvés pour "${q}". Regardez en VF / VOSTFR gratuitement.`;
    }

    function renderStreamingResults(videos) {
        const results = $('mobStreamResults');
        if (!results) return;
        results.innerHTML = '';

        videos.forEach((v, index) => {
            const card = document.createElement('div');
            card.className = 'mob-result-card';
            card.style.cssText = 'display:flex;flex-direction:column;gap:12px;padding:14px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);margin-bottom:14px;box-shadow:0 6px 20px rgba(0,0,0,0.35);';

            const badgeBg = v.is_series ? 'rgba(59,130,246,0.2)' : 'rgba(16,185,129,0.2)';
            const badgeColor = v.is_series ? '#60a5fa' : '#34d399';
            const badgeBorder = v.is_series ? '#3b82f6' : '#10b981';

            card.innerHTML = `
                <div style="display:flex;gap:14px;width:100%;">
                    <div style="position:relative;width:95px;height:135px;border-radius:10px;overflow:hidden;flex-shrink:0;background:#1a202c;box-shadow:0 4px 12px rgba(0,0,0,0.6);">
                        <img src="${esc(v.thumbnail)}" alt="" onerror="this.src='/static/icons/icon-192.png'" style="width:100%;height:100%;object-fit:cover;">
                        <span style="position:absolute;top:5px;left:5px;background:rgba(0,0,0,0.85);color:#fff;font-size:0.65rem;padding:2px 6px;border-radius:4px;font-weight:900;">#${index + 1}</span>
                        ${v.year ? `<span style="position:absolute;bottom:5px;right:5px;background:rgba(0,0,0,0.85);color:#fff;font-size:0.65rem;padding:2px 5px;border-radius:4px;font-weight:800;">${esc(v.year)}</span>` : ''}
                    </div>
                    <div style="flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center;">
                        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px;">
                            <span style="background:${badgeBg};color:${badgeColor};border:1px solid ${badgeBorder};font-size:0.7rem;padding:2px 7px;border-radius:6px;font-weight:700;">${esc(v.type_label || '🎬 Film Complet')}</span>
                            <span style="background:rgba(239,68,68,0.15);color:#f87171;border:1px solid #ef4444;font-size:0.7rem;padding:2px 7px;border-radius:6px;font-weight:700;">🇫🇷 VF / VOSTFR</span>
                        </div>
                        <div style="font-size:1.02rem;font-weight:800;color:#fff;line-height:1.25;margin-bottom:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">${esc(v.title)}</div>
                        ${v.actors ? `<div style="font-size:0.75rem;color:var(--text-muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;line-height:1.3;margin-bottom:6px;"><i class="fa-solid fa-circle-info"></i> ${esc(v.actors)}</div>` : ''}
                        <div style="font-size:0.75rem;color:#10b981;font-weight:700;"><i class="fa-solid fa-circle-check"></i> Streaming Gratuit • 8 Serveurs</div>
                    </div>
                </div>
                <!-- BOUTONS PAR FILM : REGARDER FILM & BANDE-ANNONCE -->
                <div style="display:flex;gap:8px;width:100%;margin-top:4px;">
                    <button type="button" class="btn-play-stream" style="flex:1.2;padding:12px 8px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;border-radius:12px;font-weight:800;font-size:0.86rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;box-shadow:0 3px 12px rgba(16,185,129,0.35);">
                        <i class="fa-solid fa-play"></i> <span>${v.is_series ? 'Regarder Série' : 'Regarder Film'}</span>
                    </button>
                    <button type="button" class="btn-play-trailer" style="flex:1;padding:12px 8px;background:linear-gradient(135deg,#8b5cf6,#6d28d9);color:#fff;border:none;border-radius:12px;font-weight:800;font-size:0.86rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;box-shadow:0 3px 12px rgba(139,92,246,0.35);">
                        <i class="fa-solid fa-clapperboard"></i> <span>Bande-Annonce</span>
                    </button>
                </div>
            `;

            const btnPlay = card.querySelector('.btn-play-stream');
            if (btnPlay) {
                btnPlay.onclick = () => playVideoStream(v);
            }

            const btnTrailer = card.querySelector('.btn-play-trailer');
            if (btnTrailer) {
                btnTrailer.onclick = () => playVideoTrailer(v);
            }

            results.appendChild(card);
        });
    }

    async function playVideoTrailer(video) {
        currentStreamingVideo = video;
        const container = $('mobStreamingPlayerContainer');
        const iframe = $('mobStreamingIframe');
        const titleEl = $('mobStreamingPlayerTitle');
        const upEl = $('mobStreamingPlayerUploader');
        const btnTrailer = $('btnMobWatchTrailerInPlayer');
        const btnSwitchBack = $('btnMobSwitchBackFullMovie');

        showToast(`🎬 Chargement de la bande-annonce : ${video.title}...`);

        try {
            const res = await fetch(`/api/streaming/trailer?id=${encodeURIComponent(video.id)}&title=${encodeURIComponent(video.title)}&year=${video.year || ''}`);
            const data = await res.json();
            if (data && data.trailer_url && iframe) {
                iframe.src = data.trailer_url;
                if (titleEl) titleEl.textContent = `🎬 Bande-Annonce Officielle : ${video.title}`;
                if (upEl) upEl.innerHTML = `<i class="fa-solid fa-clapperboard"></i> Bande-Annonce Officielle HD • ${esc(video.year || '')} • 🇫🇷 VF / VOSTFR`;
                if (btnTrailer) btnTrailer.style.display = 'none';
                if (btnSwitchBack) btnSwitchBack.style.display = 'flex';
                if (container) {
                    container.style.display = 'block';
                    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                showToast(`🍿 Bande-annonce lancée !`);
            }
        } catch {
            showToast("Bande-annonce indisponible", true);
        }
    }

    function playVideoStream(video) {
        currentStreamingVideo = video;
        currentStreamingServerIdx = 1;
        const container = $('mobStreamingPlayerContainer');
        const iframe = $('mobStreamingIframe');
        const titleEl = $('mobStreamingPlayerTitle');
        const upEl = $('mobStreamingPlayerUploader');
        const srvList = $('mobStreamingServerList');
        const seriesControls = $('mobStreamingSeriesControls');
        const btnTrailer = $('btnMobWatchTrailerInPlayer');
        const btnSwitchBack = $('btnMobSwitchBackFullMovie');

        if (btnTrailer) btnTrailer.style.display = 'flex';
        if (btnSwitchBack) btnSwitchBack.style.display = 'none';

        if (titleEl) titleEl.textContent = video.title || 'Film en streaming';
        if (upEl) upEl.innerHTML = `<i class="fa-solid fa-film"></i> ${esc(video.type_label || 'Film Complet')} • ${esc(video.year || '')} • 🇫🇷 VF / VOSTFR`;
        
        // Charger la première source (Frembed VF ou MultiEmbed)
        if (iframe) iframe.src = video.embed_url || video.url;

        // Fonction d'affichage des boutons serveurs
        function renderServerButtons(srvMap) {
            if (!srvList) return;
            srvList.innerHTML = '';
            let idx = 1;
            Object.keys(srvMap).forEach(sName => {
                const sUrl = srvMap[sName];
                const srvBtn = document.createElement('button');
                srvBtn.type = 'button';
                srvBtn.textContent = sName;
                const thisIdx = idx;
                srvBtn.style.cssText = `padding:6px 12px;border-radius:8px;font-size:0.75rem;font-weight:700;white-space:nowrap;cursor:pointer;border:1px solid ${thisIdx === 1 ? '#10b981' : 'var(--border)'};background:${thisIdx === 1 ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.08)'};color:#fff;`;
                srvBtn.onclick = () => {
                    currentStreamingServerIdx = thisIdx;
                    if (iframe) iframe.src = sUrl;
                    srvList.querySelectorAll('button').forEach(b => {
                        b.style.border = '1px solid var(--border)';
                        b.style.background = 'rgba(255,255,255,0.08)';
                    });
                    srvBtn.style.border = '1px solid #10b981';
                    srvBtn.style.background = 'rgba(16,185,129,0.3)';
                    showToast(`Basculement sur ${sName}`);
                };
                srvList.appendChild(srvBtn);
                idx++;
            });
        }

        renderServerButtons(video.servers || { "1. 🇫🇷 Serveur 1": video.embed_url || video.url });

        // Si le film n'a pas encore le Serveur 1 Frembed VF, on le résout immédiatement
        if (video.id && video.id.startsWith('tt') && (!video.servers || !Object.keys(video.servers)[0].includes('Frembed'))) {
            fetch(`/api/streaming/servers?id=${encodeURIComponent(video.id)}&type=${video.is_series ? 'series' : 'movie'}`)
                .then(r => r.json())
                .then(data => {
                    if (data && data.servers) {
                        video.servers = data.servers;
                        renderServerButtons(data.servers);
                        const firstUrl = Object.values(data.servers)[0];
                        if (firstUrl && iframe) {
                            iframe.src = firstUrl;
                        }
                    }
                }).catch(() => {});
        }

        // Afficher ou cacher les contrôles de série
        if (seriesControls) {
            if (video.is_series || video.type === 'serie') {
                seriesControls.style.display = 'flex';
            } else {
                seriesControls.style.display = 'none';
            }
        }

        if (container) {
            container.style.display = 'block';
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        showToast(`▶️ Lancement du film : ${video.title}`);
    }

    // =========================================================
    // DÉCLENCHEUR DE TÉLÉCHARGEMENT VIDÉO MP4
    // =========================================================
    async function triggerVideoDownload(url, title, btnEl) {
        showToast(`🎬 Préparation de la vidéo MP4 : ${title}...`);
        if (btnEl) {
            btnEl.disabled = true;
            btnEl.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Patientez...</span>`;
        }

        try {
            const res = await fetch('/api/video/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, title: title })
            });
            const data = await res.json();
            if (data.task_id) {
                trackVideoProgress(data.task_id, title, btnEl);
            } else {
                showToast("Erreur lancement vidéo", true);
                if (btnEl) btnEl.disabled = false;
            }
        } catch (e) {
            showToast("Erreur connexion", true);
            if (btnEl) btnEl.disabled = false;
        }
    }

    function trackVideoProgress(taskId, title, btnEl) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/download-status/${taskId}`);
                const info = await res.json();
                const progressNum = info.progress || 0;

                if (btnEl && info.status !== 'completed' && info.status !== 'error') {
                    btnEl.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>${progressNum}% MP4</span>`;
                }

                if (info.status === 'completed') {
                    clearInterval(interval);
                    showToast(`✅ Vidéo MP4 prête ! Téléchargement direct...`);
                    if (btnEl) {
                        btnEl.disabled = false;
                        btnEl.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>Enregistrer MP4</span>`;
                        btnEl.onclick = () => {
                            window.location.href = `/api/download-ready/${taskId}`;
                        };
                    }

                    await downloadBlobFile(`/api/download-ready/${taskId}`, info.filename || `${title}.mp4`);
                } else if (info.status === 'error') {
                    clearInterval(interval);
                    showToast(`Erreur téléchargement vidéo : ${info.message || ''}`, true);
                    if (btnEl) {
                        btnEl.disabled = false;
                        btnEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <span>Réessayer</span>`;
                    }
                }
            } catch {
                clearInterval(interval);
            }
        }, 1200);
    }

    // =========================================================
    // HELPERS
    // =========================================================
    function showToast(msg, isError = false) {
        const toast = $('mobToast');
        toast.textContent = msg;
        toast.style.borderColor = isError ? 'var(--danger)' : 'var(--accent)';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3500);
    }

    function el(id, val) {
        const e = $(id);
        if (e) e.textContent = val;
    }

    function esc(text) {
        if (!text) return '';
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

    // Bouton de rafraîchissement bibliothèque
    $('btnMobRefreshLib')?.addEventListener('click', loadLibrary);

})();
