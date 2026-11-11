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

    // ——— Enregistrement du Service Worker ———
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js', { scope: '/' })
            .then(reg => {
                console.log('SW enregistré:', reg.scope);
                reg.addEventListener('updatefound', () => {
                    const nw = reg.installing;
                    nw.addEventListener('statechange', () => {
                        if (nw.state === 'installed' && navigator.serviceWorker.controller) {
                            showToast('Mise à jour disponible — Redémarrez l\'app');
                        }
                    });
                });
            })
            .catch(err => console.warn('SW non enregistré:', err));
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
        setupSettings();
        setupScanPhone();
        setupMobThemes();
        setupMobCloudCleaner();
        handleUrlParams();
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
                document.querySelectorAll('.mob-tab-pane').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                const pane = $(`mobPane-${btn.dataset.pane}`);
                if (pane) pane.classList.add('active');
                if (btn.dataset.pane === 'library') loadLibrary();
                if (btn.dataset.pane === 'themes') loadMobThemes();
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

    async function loadMobThemes() {
        const grid = $('mobThemesGrid');
        if (!grid) return;
        grid.innerHTML = '<div class="mob-loader"><div class="mob-spinner"></div><span>Chargement des thèmes…</span></div>';

        try {
            const res = await fetch('/api/themes');
            const list = await res.json();
            grid.innerHTML = '';

            list.forEach(t => {
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
                        <span style="font-size:0.7rem;color:var(--text-muted);font-weight:600;">${t.track_count || 0} titres cultes</span>
                    </div>
                    <div class="mob-theme-arrow"><i class="fa-solid fa-chevron-right"></i></div>
                `;
                card.addEventListener('click', () => {
                    openMobThemeDetail(t.id);
                });
                grid.appendChild(card);
            });

            if (!currentMobSelectedThemeId && list.length > 0) {
                openMobThemeDetail(list[0].id);
            } else if (currentMobSelectedThemeId) {
                openMobThemeDetail(currentMobSelectedThemeId);
            }
        } catch (e) {
            grid.innerHTML = '<div class="mob-empty">Erreur chargement thèmes</div>';
        }
    }

    async function openMobThemeDetail(themeId) {
        currentMobSelectedThemeId = themeId;
        const detail = $('mobThemeDetail');
        const titleEl = $('mobThemeDetailTitle');
        const descEl = $('mobThemeDetailDesc');
        const listEl = $('mobThemeTracksList');
        const btnAll = $('btnMobDownloadThemeAll');
        const btnZip = $('btnMobDownloadThemeZip');

        if (!detail || !listEl) return;
        detail.style.display = 'block';
        listEl.innerHTML = '<div class="mob-loader"><div class="mob-spinner"></div><span>Chargement des morceaux…</span></div>';

        detail.scrollIntoView({ behavior: 'smooth', block: 'start' });

        try {
            const res = await fetch(`/api/theme/${themeId}`);
            const theme = await res.json();

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
                trCard.style.padding = '10px 12px';
                trCard.style.marginBottom = '8px';
                trCard.innerHTML = `
                    <div style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg, ${theme.color || 'var(--primary)'}, #1e293b);display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.1rem;flex-shrink:0">
                        <i class="fa-solid ${theme.icon || 'fa-music'}"></i>
                    </div>
                    <div class="mob-card-info" style="margin-left:10px;flex:1;overflow:hidden;">
                        <div class="mob-card-title" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:700;">${esc(tr.title)}</div>
                        <div class="mob-card-artist" style="font-size:0.75rem;color:var(--text-muted);"><i class="fa-solid fa-microphone"></i> ${esc(tr.artist)}</div>
                    </div>
                    <button class="mob-btn mob-btn-sm mob-btn-primary btn-dl-theme-item" style="flex-shrink:0;">
                        <i class="fa-solid fa-download"></i> MP3
                    </button>
                `;

                trCard.querySelector('.btn-dl-theme-item').addEventListener('click', () => {
                    triggerDownload(tr.query || `${tr.artist} ${tr.title} lyrics`, tr.artist, tr.title, null);
                });

                listEl.appendChild(trCard);
            });

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

    async function downloadTracksSequentially(tracks, label) {
        if (!tracks || !tracks.length) {
            showToast("Aucun fichier MP3 trouvé à enregistrer", true);
            return;
        }

        showToast(`📲 Début de l'enregistrement de ${tracks.length} MP3 sur votre téléphone...`);
        let downloaded = 0;

        for (let i = 0; i < tracks.length; i++) {
            const track = tracks[i];
            const title = track.title || track.filename || `Morceau_${i+1}`;
            showToast(`📲 MP3 ${i + 1}/${tracks.length} : ${title}`);

            const link = document.createElement('a');
            link.href = `/api/download-file/${encodeURIComponent(track.rel_path)}`;
            link.setAttribute('download', track.filename || `${title}.mp3`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            downloaded++;

            await new Promise(r => setTimeout(r, 800));
        }

        showToast(`✅ ${downloaded} fichiers MP3 réels enregistrés directement dans votre téléphone !`);
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
                showToast("Téléchargez d'abord le thème via le bouton ci-dessus.", true);
                return;
            }

            await downloadTracksSequentially(matchingTracks, theme.name);
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

            await downloadTracksSequentially(singerObj.tracks, artistName);
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
        const thumb = item.thumbnail || '/static/icons/icon-192.png';
        card.innerHTML = `
            <img src="${esc(thumb)}" class="mob-result-thumb" alt="" onerror="this.src='/static/icons/icon-192.png'">
            <div class="mob-result-body">
                <div class="mob-result-artist">${esc(item.artist || 'Artiste')}</div>
                <div class="mob-result-title">${esc(item.title || item.raw_title || 'Titre')}</div>
                <div class="mob-result-dur">${item.duration || '0:00'}</div>
            </div>
            <div class="mob-result-actions">
                <button class="mob-btn mob-btn-sm mob-btn-primary btn-dl-track" title="Télécharger en MP3 HD">
                    <i class="fa-solid fa-cloud-arrow-down"></i>
                </button>
            </div>
        `;
        card.querySelector('.btn-dl-track').addEventListener('click', () => {
            triggerDownload(item.url, item.artist, item.title, item.thumbnail);
        });
        return card;
    }

    // =========================================================
    // TÉLÉCHARGEMENT
    // =========================================================
    async function triggerDownload(url, artist, title, coverUrl) {
        showToast(`Démarrage : ${title}`);
        try {
            const res = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, artist, title, cover_url: coverUrl })
            });
            const data = await res.json();
            if (data.task_id) {
                trackProgress(data.task_id, artist, title);
            }
        } catch (err) {
            showToast('Erreur de téléchargement', true);
        }
    }

    function trackProgress(taskId, artist, title) {
        const wrap = $('mobDownloadsWrap');
        const list = $('mobDownloadsList');
        wrap.style.display = 'block';

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
        list.prepend(card);

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/download-status/${taskId}`);
                if (!res.ok) { clearInterval(interval); return; }
                const info = await res.json();

                const fill = $(`mobDlFill_${taskId}`);
                const pct = $(`mobDlPct_${taskId}`);
                const msg = $(`mobDlMsg_${taskId}`);
                if (fill) fill.style.width = `${info.progress || 0}%`;
                if (pct) pct.textContent = `${info.progress || 0}%`;
                if (msg) msg.textContent = info.message || '';

                if (info.status === 'completed') {
                    clearInterval(interval);
                    if (fill) fill.style.background = 'var(--success)';
                    showToast(`✅ "${title}" téléchargé !`);
                    loadLibrary();

                    // ✅ Bouton permanent "Enregistrer sur ce téléphone"
                    const dlCard = $(`mobDl_${taskId}`);
                    if (dlCard) {
                        const saveLink = document.createElement('a');
                        saveLink.href = `/api/download-ready/${taskId}`;
                        saveLink.className = 'btn-save-to-phone';
                        saveLink.setAttribute('download', info.filename || `${title}.mp3`);
                        saveLink.style.cssText = 'display:flex;align-items:center;justify-content:center;gap:8px;padding:12px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border-radius:var(--radius-sm);text-decoration:none;font-weight:700;margin-top:10px;';
                        saveLink.innerHTML = '<i class="fa-solid fa-mobile-screen-button"></i> 📲 Enregistrer sur ce téléphone (MP3 HD)';
                        dlCard.appendChild(saveLink);

                        // Déclencher le téléchargement directement sur le smartphone
                        try {
                            saveLink.click();
                            showToast(`📲 Téléchargement direct sur votre téléphone démarré !`);
                        } catch (e) {}

                        // Bouton pour fermer manuellement la carte
                        const closeBtn = document.createElement('button');
                        closeBtn.innerHTML = '&times;';
                        closeBtn.style.cssText = 'position:absolute;top:4px;right:8px;background:none;border:none;color:var(--text-muted);font-size:1.3rem;cursor:pointer;';
                        closeBtn.onclick = () => {
                            dlCard.remove();
                            if (!list.children.length) wrap.style.display = 'none';
                        };
                        dlCard.style.position = 'relative';
                        dlCard.appendChild(closeBtn);
                    }
                } else if (info.status === 'error') {
                    clearInterval(interval);
                    showToast(`❌ Erreur : ${info.message}`, true);
                    if ($(`mobDlFill_${taskId}`)) $(`mobDlFill_${taskId}`).style.background = 'var(--danger)';
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
                showToast("Aucune musique dans la bibliothèque ! Téléchargez d'abord un morceau.", true);
                return;
            }

            if (progressEl) progressEl.style.display = 'block';

            let downloaded = 0;
            for (let i = 0; i < allTracks.length; i++) {
                const track = allTracks[i];
                const title = track.title || track.filename;
                if (progressEl) {
                    progressEl.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> MP3 ${i + 1}/${allTracks.length} : <strong>${esc(title)}</strong>...`;
                }

                // Déclencher le téléchargement du vrai MP3 natif
                const link = document.createElement('a');
                link.href = `/api/download-file/${encodeURIComponent(track.rel_path)}`;
                link.setAttribute('download', track.filename || `${title}.mp3`);
                document.body.appendChild(link);
                link.click();
                link.remove();
                downloaded++;

                // Pause de 750ms entre chaque morceau pour que le gestionnaire Android les télécharge tous
                await new Promise(resolve => setTimeout(resolve, 750));
            }

            if (progressEl) {
                progressEl.innerHTML = `✅ ${downloaded} vrai(s) MP3 téléchargé(s) directement dans votre téléphone !`;
                setTimeout(() => { progressEl.style.display = 'none'; }, 6000);
            }

            if (onComplete) onComplete(downloaded);
        } catch (err) {
            console.error('Erreur téléchargement direct:', err);
            if (progressEl) progressEl.innerHTML = `❌ Erreur téléchargement direct`;
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
        tracks.forEach(tr => {
            const row = document.createElement('div');
            row.className = 'mob-discography-row';
            const thumb = tr.thumbnail || '/static/icons/icon-192.png';
            row.innerHTML = `
                <img src="${esc(thumb)}" class="mob-disco-thumb" alt="" onerror="this.src='/static/icons/icon-192.png'">
                <div class="mob-disco-info">
                    <div class="mob-disco-title">${esc(tr.title)}</div>
                    <div class="mob-disco-album">${esc(tr.album || 'Single')} ${tr.release_year ? '• ' + tr.release_year : ''}</div>
                </div>
                <div class="mob-disco-status">
                    ${tr.belongs_to_artist === false 
                        ? '<span class="mob-badge-dup" style="background:rgba(239,68,68,0.15);border-color:rgba(239,68,68,0.4);color:var(--danger);"><i class="fa-solid fa-triangle-exclamation"></i> Autre</span>' 
                        : '<span class="mob-badge-new" style="background:rgba(16,185,129,0.12);border-color:rgba(16,185,129,0.3);color:var(--success);"><i class="fa-solid fa-circle-check"></i> Officiel</span>'
                    }
                    ${tr.is_duplicate
                        ? '<span class="mob-badge-dup"><i class="fa-solid fa-check"></i> Présent</span>'
                        : '<span class="mob-badge-new"><i class="fa-solid fa-sparkles"></i> Nouveau</span>'
                    }
                </div>
            `;
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
