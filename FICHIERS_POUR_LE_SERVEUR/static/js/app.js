document.addEventListener('DOMContentLoaded', () => {
    // State
    let currentConfig = {};
    let activeDownloads = {};
    let libraryData = [];
    let currentPlaylist = [];
    let currentTrackIndex = -1;

    // Elements
    const audio = document.getElementById('audioElement');
    const toast = document.getElementById('toast');
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const btnClearSearch = document.getElementById('btnClearSearch');
    const resultsGrid = document.getElementById('resultsGrid');
    const resultsHeader = document.getElementById('resultsHeader');
    const resultsCount = document.getElementById('resultsCount');
    const searchLoader = document.getElementById('searchLoader');
    const searchEmptyState = document.getElementById('searchEmptyState');
    const activeDownloadsContainer = document.getElementById('activeDownloadsContainer');
    const downloadsList = document.getElementById('downloadsList');

    const libraryContainer = document.getElementById('libraryContainer');
    const libraryLoader = document.getElementById('libraryLoader');
    const libraryEmptyState = document.getElementById('libraryEmptyState');
    const libraryCount = document.getElementById('libraryCount');
    const btnRefreshLibrary = document.getElementById('btnRefreshLibrary');

    // Modals
    const modalSettings = document.getElementById('modalSettings');
    const btnSettings = document.getElementById('btnSettings');
    const btnCloseSettings = document.getElementById('btnCloseSettings');
    const btnCancelSettings = document.getElementById('btnCancelSettings');
    const btnSaveSettings = document.getElementById('btnSaveSettings');
    const inputMp3Site = document.getElementById('inputMp3Site');
    const inputSearchSite = document.getElementById('inputSearchSite');
    const checkCreateArtistFolder = document.getElementById('checkCreateArtistFolder');
    const selectAudioQuality = document.getElementById('selectAudioQuality');
    const inputMusicFolder = document.getElementById('inputMusicFolder');
    const badgeMp3Site = document.getElementById('badgeMp3Site');
    const badgeSearchSite = document.getElementById('badgeSearchSite');

    const modalQR = document.getElementById('modalQR');
    const btnMobileQR = document.getElementById('btnMobileQR');
    const btnCloseQR = document.getElementById('btnCloseQR');
    const btnCloseQROk = document.getElementById('btnCloseQROk');
    const inputMobileUrl = document.getElementById('inputMobileUrl');
    const btnCopyMobileUrl = document.getElementById('btnCopyMobileUrl');

    const modalEdit = document.getElementById('modalEdit');
    const btnCloseEdit = document.getElementById('btnCloseEdit');
    const btnCancelEdit = document.getElementById('btnCancelEdit');
    const btnSaveEdit = document.getElementById('btnSaveEdit');
    const editRelPath = document.getElementById('editRelPath');
    const editArtist = document.getElementById('editArtist');
    const editTitle = document.getElementById('editTitle');
    const editAlbum = document.getElementById('editAlbum');

    // Singer Full Mode Elements
    const singerForm = document.getElementById('singerForm');
    const singerInput = document.getElementById('singerInput');
    const btnClearSinger = document.getElementById('btnClearSinger');
    const btnSingerSubmit = document.getElementById('btnSingerSubmit');
    const singerResultsContainer = document.getElementById('singerResultsContainer');
    const singerLoader = document.getElementById('singerLoader');
    const singerEmptyState = document.getElementById('singerEmptyState');
    const artistNameDisplay = document.getElementById('artistNameDisplay');
    const badgeTotalFound = document.getElementById('badgeTotalFound');
    const badgeAlreadyPresent = document.getElementById('badgeAlreadyPresent');
    const badgeNewToDownload = document.getElementById('badgeNewToDownload');
    const createdArtistFolder = document.getElementById('createdArtistFolder');
    const createdDiscographyFile = document.getElementById('createdDiscographyFile');
    const createdPlaylistFile = document.getElementById('createdPlaylistFile');
    const createdTxtFile = document.getElementById('createdTxtFile');
    const checkSelectAll = document.getElementById('checkSelectAll');
    const selectedCountText = document.getElementById('selectedCountText');
    const btnDownloadAllSinger = document.getElementById('btnDownloadAllSinger');
    const discographyList = document.getElementById('discographyList');
    const btnScanPhone = document.getElementById('btnScanPhone');
    const phoneFileInput = document.getElementById('phoneFileInput');
    const pcTrackCount = document.getElementById('pcTrackCount');
    const phoneTrackCount = document.getElementById('phoneTrackCount');

    let currentDiscography = [];
    let currentSingerName = '';

    // Player Elements
    const musicPlayer = document.getElementById('musicPlayer');
    const playerTitle = document.getElementById('playerTitle');
    const playerArtist = document.getElementById('playerArtist');
    const btnPlayPause = document.getElementById('btnPlayPause');
    const btnPrevTrack = document.getElementById('btnPrevTrack');
    const btnNextTrack = document.getElementById('btnNextTrack');
    const btnClosePlayer = document.getElementById('btnClosePlayer');
    const btnDownloadCurrent = document.getElementById('btnDownloadCurrent');
    const currentTimeEl = document.getElementById('currentTime');
    const totalDurationEl = document.getElementById('totalDuration');
    const seekSlider = document.getElementById('seekSlider');

    // --- Helpers ---
    function showToast(message, isError = false) {
        toast.textContent = message;
        toast.style.borderColor = isError ? 'var(--danger)' : 'var(--accent)';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3500);
    }

    function formatTime(seconds) {
        if (isNaN(seconds) || seconds < 0) return "0:00";
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    // --- Initialization & Config ---
    async function init() {
        // Apply saved font immediately to avoid flicker
        const savedFont = localStorage.getItem('mp3_font_style');
        if (savedFont) applyFontStyle(savedFont);

        await loadConfiguration();
        await loadLibrary();
        await loadScannerSummary();
        setupTabs();
        setupPresets();
        setupSingerMode();
        setupThemes();
        setupCloudCleaner();
    }

    function applyFontStyle(fontClass) {
        if (!fontClass) fontClass = 'font-default';
        document.documentElement.classList.remove('font-default', 'font-orbitron', 'font-rajdhani', 'font-exo2', 'font-audiowide');
        document.documentElement.classList.add(fontClass);
        document.querySelectorAll('#fontPicker .font-pill').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.font === fontClass);
        });
    }

    function getSelectedFont() {
        const active = document.querySelector('#fontPicker .font-pill.active');
        return active ? active.dataset.font : (localStorage.getItem('mp3_font_style') || 'font-default');
    }

    async function loadConfiguration() {
        try {
            const res = await fetch('/api/config');
            currentConfig = await res.json();

            // Remplir les champs du modal
            inputMp3Site.value = currentConfig.mp3_site || '';
            inputSearchSite.value = currentConfig.search_site || '';
            checkCreateArtistFolder.checked = currentConfig.create_artist_folder !== false;
            selectAudioQuality.value = currentConfig.audio_quality || '192';
            inputMusicFolder.value = currentConfig.music_folder || '';

            // Mettre à jour les badges
            if (badgeMp3Site) {
                badgeMp3Site.innerHTML = `<i class="fa-solid fa-download"></i> Source MP3 : <strong>${escapeHtml(currentConfig.mp3_site || 'Auto')}</strong>`;
            }
            if (badgeSearchSite) {
                badgeSearchSite.innerHTML = `<i class="fa-solid fa-compass"></i> Recherche : <strong>${escapeHtml(currentConfig.search_site || 'Auto')}</strong>`;
            }

            // Si première ouverture (non configuré), ouvrir automatiquement l'assistant
            if (currentConfig.font_style) {
                applyFontStyle(currentConfig.font_style);
                localStorage.setItem('mp3_font_style', currentConfig.font_style);
            }

            if (!currentConfig.configured) {
                document.getElementById('settingsModalTitle').textContent = "Bienvenue ! Configurons votre application MP3";
                modalSettings.style.display = 'flex';
            }
        } catch (err) {
            console.error('Erreur chargement config:', err);
        }
    }

    function setupPresets() {
        // ✅ Bouton "Utiliser TOUS les sites" — Mode Maximal
        const btnAllSources = document.getElementById('btnAllSources');
        const allSourcesBadge = document.getElementById('allSourcesBadge');
        let allSourcesActive = false;

        if (btnAllSources) {
            btnAllSources.addEventListener('click', () => {
                allSourcesActive = !allSourcesActive;

                if (allSourcesActive) {
                    // Activer le mode multi-source : YouTube + SoundCloud + Deezer + tous les autres
                    btnAllSources.classList.add('active');
                    if (allSourcesBadge) allSourcesBadge.textContent = '✅ Activé';
                    inputMp3Site.value = 'Tous les sites (YouTube · SoundCloud · Deezer · Dailymotion · Bandcamp · +1000 sites)';
                    inputSearchSite.value = 'Multi-sources (YouTube Music · Deezer · iTunes · Spotify)';
                    // Désactiver les presets individuels visuellement
                    document.querySelectorAll('#mp3Presets .preset-pill').forEach(b => b.classList.remove('active'));
                    document.querySelectorAll('#searchPresets .preset-pill').forEach(b => b.classList.remove('active'));
                    showToast('⚡ Mode TOUS les sites activé — Téléchargement maximal !');
                } else {
                    // Désactiver le mode multi-source
                    btnAllSources.classList.remove('active');
                    if (allSourcesBadge) allSourcesBadge.textContent = 'Désactivé';
                    inputMp3Site.value = currentConfig.mp3_site || '';
                    inputSearchSite.value = currentConfig.search_site || '';
                    showToast('Mode sélection manuelle réactivé');
                }
            });

            // Rétablir l'état si le config est déjà en mode tous les sites
            if (currentConfig.mp3_site && currentConfig.mp3_site.includes('Tous les sites')) {
                btnAllSources.classList.add('active');
                allSourcesActive = true;
                if (allSourcesBadge) allSourcesBadge.textContent = '✅ Activé';
            }
        }

        // Presets MP3
        document.querySelectorAll('#mp3Presets .preset-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#mp3Presets .preset-pill').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                inputMp3Site.value = btn.dataset.val;
            });
        });

        // Presets Search
        document.querySelectorAll('#searchPresets .preset-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#searchPresets .preset-pill').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                inputSearchSite.value = btn.dataset.val;
            });
        });

        // Presets Font / Style
        document.querySelectorAll('#fontPicker .font-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                const font = btn.dataset.font;
                applyFontStyle(font);
                localStorage.setItem('mp3_font_style', font);
            });
        });
    }

    // Save Settings
    btnSaveSettings.addEventListener('click', async () => {
        const payload = {
            mp3_site: inputMp3Site.value.trim() || "YouTube MP3",
            search_site: inputSearchSite.value.trim() || "YouTube Music",
            create_artist_folder: checkCreateArtistFolder.checked,
            audio_quality: selectAudioQuality.value,
            music_folder: inputMusicFolder.value.trim(),
            font_style: getSelectedFont()
        };

        try {
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                currentConfig = data.config;
                showToast("Préférences enregistrées avec succès !");
                modalSettings.style.display = 'none';
                loadConfiguration();
            }
        } catch (err) {
            showToast("Erreur lors de l'enregistrement", true);
        }
    });

    btnSettings.addEventListener('click', () => {
        document.getElementById('settingsModalTitle').textContent = "Paramètres de l'application";
        modalSettings.style.display = 'flex';
    });

    btnCloseSettings.addEventListener('click', () => modalSettings.style.display = 'none');
    btnCancelSettings.addEventListener('click', () => modalSettings.style.display = 'none');

    // --- Mobile QR Modal ---
    btnMobileQR.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/network-info');
            const data = await res.json();
            inputMobileUrl.value = data.mobile_url;
            document.getElementById('qrImage').src = `/api/qr?t=${Date.now()}`;
            modalQR.style.display = 'flex';
        } catch (err) {
            showToast("Impossible de charger les informations réseau", true);
        }
    });

    btnCloseQR.addEventListener('click', () => modalQR.style.display = 'none');
    btnCloseQROk.addEventListener('click', () => modalQR.style.display = 'none');

    btnCopyMobileUrl.addEventListener('click', () => {
        navigator.clipboard.writeText(inputMobileUrl.value).then(() => {
            showToast("Adresse copiée dans le presse-papier !");
        }).catch(() => {
            inputMobileUrl.select();
            document.execCommand('copy');
            showToast("Adresse copiée !");
        });
    });

    // --- Tabs Navigation ---
    function setupTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

                btn.classList.add('active');
                const targetPane = document.getElementById(btn.dataset.tab);
                if (targetPane) targetPane.classList.add('active');

                if (btn.dataset.tab === 'tab-library') {
                    loadLibrary();
                }
                if (btn.dataset.tab === 'tab-themes') {
                    loadThemesCatalog();
                }
            });
        });
    }

    // --- Multi-Source Selection (Tous les sites, YouTube, SoundCloud) ---
    let currentSearchSource = 'all';
    document.querySelectorAll('.source-pill').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.source-pill').forEach(b => {
                b.classList.remove('active');
                b.style.borderColor = 'var(--border)';
                b.style.background = 'var(--bg-elevated)';
            });
            btn.classList.add('active');
            btn.style.borderColor = 'var(--primary)';
            btn.style.background = 'var(--primary-light)';
            currentSearchSource = btn.dataset.source || 'all';
        });
    });

    // --- Themes & Ambiances (Halloween, Noël, Soirée, etc.) ---
    let currentSelectedThemeId = null;

    function showThemeBanner(theme) {
        const tb = document.getElementById('themeBanner');
        if (!tb) return;
        tb.innerHTML = `
            <div>
                <strong>${escapeHtml(theme.badge || theme.name)}</strong> : ${escapeHtml(theme.description || '')}
            </div>
            <button type="button" class="theme-banner-close" onclick="document.getElementById('themeBanner').style.display='none'">&times;</button>
        `;
        tb.style.display = 'flex';
    }

    function hideThemeBanner() {
        const tb = document.getElementById('themeBanner');
        if (tb) tb.style.display = 'none';
    }

    function setupThemes() {
        document.querySelectorAll('.theme-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                const themeId = btn.dataset.theme;
                document.querySelectorAll('.theme-pill').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                // Basculer vers l'onglet Thèmes pour voir tous les morceaux du thème
                const tabThemeBtn = document.querySelector('[data-tab="tab-themes"]');
                if (tabThemeBtn) {
                    tabThemeBtn.click();
                    setTimeout(() => openThemeDetail(themeId), 100);
                } else {
                    searchInput.value = themeId;
                    btnClearSearch.style.display = 'block';
                    searchForm.dispatchEvent(new Event('submit'));
                }
            });
        });
    }

    async function loadThemesCatalog() {
        const grid = document.getElementById('themesCatalogGrid');
        if (!grid) return;
        grid.innerHTML = '<div class="loader-box"><div class="spinner"></div><p>Chargement des styles et thèmes...</p></div>';

        try {
            const res = await fetch('/api/themes');
            const list = await res.json();
            grid.innerHTML = '';

            list.forEach(t => {
                const card = document.createElement('div');
                card.className = 'theme-card-box';
                card.dataset.id = t.id;
                card.innerHTML = `
                    <div class="theme-card-header">
                        <div class="theme-card-icon" style="color:${t.color || 'var(--primary)'};background:${t.color ? t.color + '22' : 'var(--primary-light)'}">
                            <i class="fa-solid ${t.icon || 'fa-music'}"></i>
                        </div>
                        <div>
                            <div class="theme-card-name">${escapeHtml(t.name)}</div>
                            <span class="theme-card-badge" style="color:var(--text-muted);font-size:0.8rem;">${t.track_count || 0} titres cultes</span>
                        </div>
                    </div>
                    <p class="theme-card-desc" style="font-size:0.85rem;color:var(--text-muted);margin-top:6px;">${escapeHtml(t.description || '')}</p>
                `;
                card.addEventListener('click', () => {
                    document.querySelectorAll('.theme-card-box').forEach(c => c.classList.remove('active'));
                    card.classList.add('active');
                    openThemeDetail(t.id);
                });
                grid.appendChild(card);
            });

            if (!currentSelectedThemeId && list.length > 0) {
                openThemeDetail(list[0].id);
            } else if (currentSelectedThemeId) {
                openThemeDetail(currentSelectedThemeId);
            }
        } catch (e) {
            grid.innerHTML = '<div class="empty-state"><p>Erreur lors du chargement des thèmes.</p></div>';
        }
    }

    async function openThemeDetail(themeId) {
        currentSelectedThemeId = themeId;
        const section = document.getElementById('themeDetailSection');
        const titleEl = document.getElementById('themeDetailHeaderTitle');
        const descEl = document.getElementById('themeDetailHeaderDesc');
        const tracksGrid = document.getElementById('themeTracksGrid');
        const btnDlAll = document.getElementById('btnDownloadThemeAll');
        const btnZip = document.getElementById('btnDownloadThemeZip');

        if (!section || !tracksGrid) return;
        section.style.display = 'block';
        tracksGrid.innerHTML = '<div class="loader-box"><div class="spinner"></div><p>Chargement des titres du thème...</p></div>';

        try {
            const res = await fetch(`/api/theme/${themeId}`);
            const theme = await res.json();

            titleEl.innerHTML = `<i class="fa-solid ${theme.icon || 'fa-music'}" style="color:${theme.color || 'var(--primary)'}"></i> ${escapeHtml(theme.name)}`;
            descEl.textContent = theme.description || '';

            if (btnZip) {
                btnZip.href = `/api/theme/${themeId}/download-zip`;
            }

            tracksGrid.innerHTML = '';
            const tracks = theme.tracks || [];

            tracks.forEach((tr, idx) => {
                const trCard = document.createElement('div');
                trCard.className = 'result-card theme-track-card';
                trCard.innerHTML = `
                    <div class="result-thumb-wrapper">
                        <div class="result-thumb-placeholder" style="background:linear-gradient(135deg, ${theme.color || '#6366f1'}, #1e293b);display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.8rem;border-radius:var(--radius-sm);height:140px;">
                            <i class="fa-solid ${theme.icon || 'fa-music'}"></i>
                        </div>
                    </div>
                    <div class="result-body">
                        <div class="result-source-badge" style="color:${theme.color || 'var(--primary)'};font-size:0.75rem;font-weight:700;">
                            <i class="fa-solid fa-compact-disc"></i> ${escapeHtml(theme.badge || theme.name)}
                        </div>
                        <h4 class="result-title" style="margin:4px 0;">${escapeHtml(tr.title)}</h4>
                        <div class="result-artist" style="color:var(--text-muted);font-size:0.85rem;"><i class="fa-solid fa-microphone"></i> ${escapeHtml(tr.artist)}</div>
                        <div class="result-actions" style="margin-top:12px;">
                            <button type="button" class="btn-download" id="btnDlThemeTr_${idx}">
                                <i class="fa-solid fa-cloud-arrow-down"></i>
                                <span>Télécharger MP3</span>
                            </button>
                        </div>
                    </div>
                `;

                trCard.querySelector(`#btnDlThemeTr_${idx}`).addEventListener('click', () => {
                    triggerDownload(tr.query || `${tr.artist} ${tr.title} lyrics`, tr.artist, tr.title, null);
                });

                tracksGrid.appendChild(trCard);
            });

            if (btnDlAll) {
                btnDlAll.onclick = async () => {
                    if (!confirm(`Télécharger toutes les musiques (${tracks.length}) du thème "${theme.name}" ?`)) return;
                    showToast(`Démarrage du téléchargement du thème : ${theme.name}...`);
                    try {
                        const dlRes = await fetch(`/api/theme/${themeId}/download-all`, { method: 'POST' });
                        const dlData = await dlRes.json();
                        if (dlData.task_id) {
                            trackDownloadProgress(dlData.task_id, `Thème ${theme.name}`, `${tracks.length} titres`);
                        }
                    } catch (err) {
                        showToast("Erreur lancement téléchargement thème", true);
                    }
                };
            }

        } catch (e) {
            tracksGrid.innerHTML = '<p>Erreur chargement morceaux du thème.</p>';
        }
    }

    // --- Gestion du Stockage Local (Neutralisé : pas de destruction de fichiers) ---
    function setupCloudCleaner() {
        const btnLocal = document.getElementById('btnLocalMusic');
        if (btnLocal) {
            btnLocal.addEventListener('click', () => {
                const libTab = document.querySelector('[data-tab="tab-library"]');
                if (libTab) libTab.click();
            });
        }
    }

    // --- Search Logic ---
    searchInput.addEventListener('input', () => {
        btnClearSearch.style.display = searchInput.value ? 'block' : 'none';
    });

    btnClearSearch.addEventListener('click', () => {
        searchInput.value = '';
        btnClearSearch.style.display = 'none';
        searchInput.focus();
    });

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (!query) return;

        searchLoader.style.display = 'block';
        resultsGrid.innerHTML = '';
        resultsHeader.style.display = 'none';
        searchEmptyState.style.display = 'none';

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&source=${encodeURIComponent(currentSearchSource)}`);
            const data = await res.json();
            const results = data.results || [];

            searchLoader.style.display = 'none';
            resultsHeader.style.display = 'flex';
            resultsCount.textContent = `${results.length} morceau(x) trouvé(s)`;

            if (data.theme) {
                showThemeBanner(data.theme);
                document.querySelectorAll('.theme-pill').forEach(b => {
                    b.classList.toggle('active', b.dataset.theme === data.theme.id);
                });
            } else {
                hideThemeBanner();
            }

            if (results.length === 0) {
                resultsGrid.innerHTML = `
                    <div class="empty-state" style="grid-column: 1/-1;">
                        <div class="empty-icon"><i class="fa-solid fa-face-frown"></i></div>
                        <h3>Aucun résultat trouvé</h3>
                        <p>Vérifiez l'orthographe du chanteur ou du morceau, ou collez directement un lien web.</p>
                    </div>
                `;
            } else {
                results.forEach((item, index) => {
                    resultsGrid.appendChild(createResultCard(item, index));
                });
            }
        } catch (err) {
            searchLoader.style.display = 'none';
            showToast("Erreur lors de la recherche", true);
        }
    });

    function createResultCard(item, index) {
        const card = document.createElement('div');
        card.className = 'result-card';

        const thumbSrc = item.thumbnail || '/static/icons/icon-192.png';
        const artist = item.artist || 'Artiste Inconnu';
        const title = item.title || item.raw_title || 'Titre inconnu';

        card.innerHTML = `
            <div class="result-thumb-wrapper">
                <img src="${thumbSrc}" alt="Pochette" class="result-thumb" onerror="this.src='/static/icons/icon-192.png'">
                <span class="result-duration">${item.duration || '0:00'}</span>
            </div>
            <div class="result-body">
                <div class="singer-tag-box" title="Chanteur détecté pour le dossier et l'application musique">
                    <i class="fa-solid fa-user-music"></i>
                    <span>Chanteur : </span>
                    <strong id="singerDisplay_${index}">${escapeHtml(artist)}</strong>
                </div>
                <h4 class="result-title" id="titleDisplay_${index}">${escapeHtml(title)}</h4>
                <div class="result-footer">
                    <button class="btn-download-action" id="btnDl_${index}">
                        <i class="fa-solid fa-cloud-arrow-down"></i>
                        <span>Télécharger MP3</span>
                    </button>
                    <button class="btn-edit-singer" id="btnEditPre_${index}" title="Modifier le chanteur ou le titre avant téléchargement">
                        <i class="fa-solid fa-pen"></i>
                    </button>
                </div>
            </div>
        `;

        // Action de modification avant téléchargement
        const btnEditPre = card.querySelector(`#btnEditPre_${index}`);
        btnEditPre.addEventListener('click', () => {
            const newArtist = prompt("Nom du Chanteur (dossier et lecteur musique) :", item.artist);
            if (newArtist !== null && newArtist.trim()) {
                item.artist = newArtist.trim();
                card.querySelector(`#singerDisplay_${index}`).textContent = item.artist;
            }
            const newTitle = prompt("Titre de la chanson :", item.title);
            if (newTitle !== null && newTitle.trim()) {
                item.title = newTitle.trim();
                card.querySelector(`#titleDisplay_${index}`).textContent = item.title;
            }
        });

        // Action de téléchargement
        const btnDl = card.querySelector(`#btnDl_${index}`);
        btnDl.addEventListener('click', () => {
            triggerDownload(item.url, item.artist, item.title, item.thumbnail);
        });

        return card;
    }

    // --- Trigger Download ---
    async function triggerDownload(url, artist, title, coverUrl) {
        try {
            showToast(`Démarrage du téléchargement : ${title}`);
            const res = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url,
                    artist: artist,
                    title: title,
                    cover_url: coverUrl
                })
            });
            const data = await res.json();
            if (data.task_id) {
                trackDownloadProgress(data.task_id, artist, title);
            }
        } catch (err) {
            showToast("Erreur lors du lancement du téléchargement", true);
        }
    }

    function trackDownloadProgress(taskId, artist, title) {
        activeDownloadsContainer.style.display = 'block';

        const downloadEl = document.createElement('div');
        downloadEl.className = 'download-card';
        downloadEl.id = `dlCard_${taskId}`;
        downloadEl.innerHTML = `
            <div class="download-meta">
                <div>
                    <span class="download-artist">${escapeHtml(artist)}</span> - 
                    <span class="download-title">${escapeHtml(title)}</span>
                </div>
                <span class="download-pct" id="dlPct_${taskId}">0%</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="dlFill_${taskId}"></div>
            </div>
            <div class="download-status-text" id="dlMsg_${taskId}">Démarrage...</div>
        `;
        downloadsList.prepend(downloadEl);

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/download-status/${taskId}`);
                if (!res.ok) {
                    clearInterval(interval);
                    return;
                }
                const info = await res.json();
                const fill = document.getElementById(`dlFill_${taskId}`);
                const pct = document.getElementById(`dlPct_${taskId}`);
                const msg = document.getElementById(`dlMsg_${taskId}`);

                if (fill && pct && msg) {
                    fill.style.width = `${info.progress || 0}%`;
                    pct.textContent = `${info.progress || 0}%`;
                    msg.textContent = info.message || '';
                }

                if (info.status === 'completed') {
                    clearInterval(interval);
                    showToast(`✅ "${title}" téléchargé et prêt !`);
                    if (fill) fill.style.background = 'var(--success)';
                    loadLibrary();

                    // ✅ Déclencher immédiatement le téléchargement dans le navigateur
                    try {
                        const directLink = document.createElement('a');
                        directLink.href = `/api/download-ready/${taskId}`;
                        directLink.setAttribute('download', info.filename || `${title}.mp3`);
                        document.body.appendChild(directLink);
                        directLink.click();
                        directLink.remove();
                    } catch(e_dl) {}

                    // ✅ Bouton permanent de téléchargement direct sans expiration
                    const card = document.getElementById(`dlCard_${taskId}`);
                    if (card) {
                        const saveBtn = document.createElement('a');
                        saveBtn.href = `/api/download-ready/${taskId}`;
                        saveBtn.className = 'btn-save-phone';
                        saveBtn.setAttribute('download', info.filename || `${title}.mp3`);
                        saveBtn.innerHTML = '<i class="fa-solid fa-download"></i> Enregistrer le MP3 HD (320 kbps)';
                        saveBtn.style.display = 'inline-flex';
                        saveBtn.style.marginTop = '8px';
                        card.appendChild(saveBtn);

                        // Bouton pour fermer la carte manuellement
                        const closeBtn = document.createElement('button');
                        closeBtn.className = 'btn-close-card';
                        closeBtn.innerHTML = '&times;';
                        closeBtn.style.cssText = 'position:absolute;top:6px;right:8px;background:none;border:none;color:var(--text-muted);font-size:1.2rem;cursor:pointer;';
                        closeBtn.onclick = () => {
                            card.remove();
                            if (downloadsList.children.length === 0) {
                                activeDownloadsContainer.style.display = 'none';
                            }
                        };
                        card.style.position = 'relative';
                        card.appendChild(closeBtn);
                    }
                } else if (info.status === 'error') {
                    clearInterval(interval);
                    showToast(`❌ Erreur : ${info.message}`, true);
                    if (fill) fill.style.background = 'var(--danger)';
                }
            } catch (err) {
                clearInterval(interval);
            }
        }, 1200);
    }

    // --- Library (Folders by Singer) ---
    async function loadLibrary() {
        libraryLoader.style.display = 'block';
        try {
            const res = await fetch('/api/library');
            const data = await res.json();
            libraryData = data.singers || [];
            libraryCount.textContent = data.total_tracks || 0;

            renderLibrary(libraryData);
        } catch (err) {
            showToast("Erreur lors du chargement de la bibliothèque", true);
        } finally {
            libraryLoader.style.display = 'none';
        }
    }

    btnRefreshLibrary.addEventListener('click', loadLibrary);

    const btnDownloadAllDirectMp3 = document.getElementById('btnDownloadAllDirectMp3');
    if (btnDownloadAllDirectMp3) {
        btnDownloadAllDirectMp3.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/library');
                const data = await res.json();
                const singers = data.singers || [];
                const allTracks = [];
                singers.forEach(s => {
                    (s.tracks || []).forEach(t => allTracks.push(t));
                });

                if (!allTracks.length) {
                    showToast("Aucune musique dans la bibliothèque pour l'instant !", true);
                    return;
                }

                showToast(`📲 Début du téléchargement de ${allTracks.length} fichiers MP3 directs...`);

                let downloaded = 0;
                for (let i = 0; i < allTracks.length; i++) {
                    const track = allTracks[i];
                    const title = track.title || track.filename;
                    showToast(`MP3 ${i + 1}/${allTracks.length} : ${title}`);

                    const link = document.createElement('a');
                    link.href = `/api/download-file/${encodeURIComponent(track.rel_path)}`;
                    link.setAttribute('download', track.filename || `${title}.mp3`);
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    downloaded++;

                    await new Promise(r => setTimeout(r, 750));
                }

                showToast(`✅ ${downloaded} fichiers MP3 téléchargés directement sans ZIP !`);
                setTimeout(() => loadLibrary(), 2500);
            } catch (err) {
                showToast("Erreur lors du téléchargement des MP3", true);
            }
        });
    }

    function renderLibrary(singers) {
        libraryContainer.innerHTML = '';

        if (!singers || singers.length === 0) {
            libraryEmptyState.style.display = 'block';
            return;
        }

        libraryEmptyState.style.display = 'none';

        // Reconstruire la playlist complète
        currentPlaylist = [];
        singers.forEach(s => {
            s.tracks.forEach(t => currentPlaylist.push(t));
        });

        singers.forEach(singerItem => {
            const folderCard = document.createElement('div');
            folderCard.className = 'singer-folder-card';

            const tracksCount = singerItem.track_count || 0;

            folderCard.innerHTML = `
                <div class="singer-folder-header">
                    <div class="singer-info">
                        <div class="singer-folder-icon">
                            <i class="fa-solid fa-folder"></i>
                        </div>
                        <div>
                            <h3 class="singer-name">${escapeHtml(singerItem.singer)}</h3>
                            <span class="singer-track-count">${tracksCount} titre${tracksCount > 1 ? 's' : ''}</span>
                        </div>
                    </div>
                    <div class="folder-toggle-icon">
                        <i class="fa-solid fa-chevron-down"></i>
                    </div>
                </div>
                <div class="tracks-table"></div>
            `;

            const tracksTable = folderCard.querySelector('.tracks-table');
            const header = folderCard.querySelector('.singer-folder-header');
            const chevron = folderCard.querySelector('.folder-toggle-icon i');

            // Render tracks
            singerItem.tracks.forEach(track => {
                const row = document.createElement('div');
                row.className = 'track-row';
                row.innerHTML = `
                    <div class="track-main">
                        <button class="btn-play-mini" title="Écouter le morceau">
                            <i class="fa-solid fa-play"></i>
                        </button>
                        <div class="track-titles">
                            <span class="song-name">${escapeHtml(track.title)}</span>
                            <span class="song-details">${track.duration} • ${track.size_mb} Mo</span>
                        </div>
                    </div>
                    <div class="track-actions">
                        <a href="/api/download-file/${encodeURIComponent(track.rel_path)}" class="btn-track-action" title="Télécharger sur ce téléphone ou ordinateur" download>
                            <i class="fa-solid fa-download"></i>
                        </a>
                        <button class="btn-track-action btn-edit" title="Modifier chanteur / titre">
                            <i class="fa-solid fa-pen"></i>
                        </button>
                        <button class="btn-track-action btn-delete" title="Supprimer">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                `;

                // Play
                row.querySelector('.btn-play-mini').addEventListener('click', () => {
                    playTrack(track);
                });

                // Edit
                row.querySelector('.btn-edit').addEventListener('click', () => {
                    openEditModal(track);
                });

                // Delete
                row.querySelector('.btn-delete').addEventListener('click', async () => {
                    if (confirm(`Voulez-vous vraiment supprimer "${track.title}" ?`)) {
                        try {
                            const res = await fetch(`/api/track?path=${encodeURIComponent(track.rel_path)}`, {
                                method: 'DELETE'
                            });
                            const result = await res.json();
                            if (result.success) {
                                showToast(`"${track.title}" supprimé`);
                                loadLibrary();
                            }
                        } catch (err) {
                            showToast("Erreur lors de la suppression", true);
                        }
                    }
                });

                tracksTable.appendChild(row);
            });

            // Toggle folder collapse
            header.addEventListener('click', () => {
                const isHidden = tracksTable.style.display === 'none';
                tracksTable.style.display = isHidden ? 'flex' : 'none';
                chevron.className = isHidden ? 'fa-solid fa-chevron-up' : 'fa-solid fa-chevron-down';
            });

            libraryContainer.appendChild(folderCard);
        });
    }

    // --- Audio Player ---
    function playTrack(track) {
        currentTrackIndex = currentPlaylist.findIndex(t => t.rel_path === track.rel_path);
        audio.src = `/api/stream/${encodeURIComponent(track.rel_path)}`;
        playerTitle.textContent = track.title;
        playerArtist.textContent = track.artist || 'Artiste Inconnu';
        musicPlayer.style.display = 'block';

        btnDownloadCurrent.onclick = () => {
            window.location.href = `/api/download-file/${encodeURIComponent(track.rel_path)}`;
        };

        audio.play().then(() => {
            btnPlayPause.innerHTML = '<i class="fa-solid fa-pause"></i>';
        }).catch(err => {
            console.error('Audio play error:', err);
        });
    }

    btnPlayPause.addEventListener('click', () => {
        if (audio.paused) {
            audio.play();
            btnPlayPause.innerHTML = '<i class="fa-solid fa-pause"></i>';
        } else {
            audio.pause();
            btnPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
        }
    });

    btnNextTrack.addEventListener('click', () => {
        if (currentPlaylist.length === 0) return;
        currentTrackIndex = (currentTrackIndex + 1) % currentPlaylist.length;
        playTrack(currentPlaylist[currentTrackIndex]);
    });

    btnPrevTrack.addEventListener('click', () => {
        if (currentPlaylist.length === 0) return;
        currentTrackIndex = (currentTrackIndex - 1 + currentPlaylist.length) % currentPlaylist.length;
        playTrack(currentPlaylist[currentTrackIndex]);
    });

    audio.addEventListener('timeupdate', () => {
        if (audio.duration) {
            const pct = (audio.currentTime / audio.duration) * 100;
            seekSlider.value = pct;
            currentTimeEl.textContent = formatTime(audio.currentTime);
            totalDurationEl.textContent = formatTime(audio.duration);
        }
    });

    seekSlider.addEventListener('input', () => {
        if (audio.duration) {
            audio.currentTime = (seekSlider.value / 100) * audio.duration;
        }
    });

    audio.addEventListener('ended', () => {
        btnNextTrack.click();
    });

    btnClosePlayer.addEventListener('click', () => {
        audio.pause();
        musicPlayer.style.display = 'none';
    });

    // --- Edit Modal (Chanteur & Titre) ---
    function openEditModal(track) {
        editRelPath.value = track.rel_path;
        editArtist.value = track.artist;
        editTitle.value = track.title;
        editAlbum.value = track.album || '';
        modalEdit.style.display = 'flex';
    }

    btnCloseEdit.addEventListener('click', () => modalEdit.style.display = 'none');
    btnCancelEdit.addEventListener('click', () => modalEdit.style.display = 'none');

    btnSaveEdit.addEventListener('click', async () => {
        const payload = {
            path: editRelPath.value,
            artist: editArtist.value.trim(),
            title: editTitle.value.trim(),
            album: editAlbum.value.trim()
        };

        try {
            const res = await fetch('/api/retag', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                showToast("Morceau et dossier mis à jour !");
                modalEdit.style.display = 'none';
                loadLibrary();
            }
        } catch (err) {
            showToast("Erreur lors de la mise à jour des métadonnées", true);
        }
    });

    // --- Mode Chanteur Complet & Scanner Anti-Doublons ---
    async function loadScannerSummary() {
        try {
            const res = await fetch('/api/scanner/summary');
            const data = await res.json();
            if (pcTrackCount) pcTrackCount.textContent = data.pc_count || 0;
            if (phoneTrackCount) phoneTrackCount.textContent = data.phone_count || 0;
        } catch (err) {
            console.error('Erreur scan résumé:', err);
        }
    }

    function setupSingerMode() {
        if (!singerForm) return;

        singerInput.addEventListener('input', () => {
            btnClearSinger.style.display = singerInput.value ? 'block' : 'none';
        });

        btnClearSinger.addEventListener('click', () => {
            singerInput.value = '';
            btnClearSinger.style.display = 'none';
            singerInput.focus();
        });

        // Scan téléphone (sélection de dossiers / fichiers audios sur mobile)
        if (btnScanPhone && phoneFileInput) {
            btnScanPhone.addEventListener('click', () => {
                phoneFileInput.click();
            });

            phoneFileInput.addEventListener('change', async (e) => {
                const files = e.target.files;
                if (!files || files.length === 0) return;

                const phoneTracks = [];
                for (let i = 0; i < files.length; i++) {
                    const f = files[i];
                    const name = f.name;
                    // Découpage simple du nom de fichier
                    phoneTracks.push({
                        filename: name,
                        title: name.replace(/\.[^/.]+$/, ""),
                        artist: ""
                    });
                }

                try {
                    showToast(`Analyse de ${files.length} fichiers sur votre téléphone...`);
                    const res = await fetch('/api/phone/register-music', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tracks: phoneTracks })
                    });
                    const data = await res.json();
                    showToast(`✅ ${data.registered_count} musiques indexées depuis votre téléphone !`);
                    loadScannerSummary();

                    // Re-scanner la discographie si un chanteur est actuellement affiché
                    if (currentSingerName) {
                        searchSingerDiscography(currentSingerName);
                    }
                } catch (err) {
                    showToast("Erreur lors de l'enregistrement des musiques du téléphone", true);
                }
            });
        }

        // Soumission du formulaire Chanteur
        singerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const artist = singerInput.value.trim();
            if (!artist) return;
            searchSingerDiscography(artist);
        });

        // Bouton de vérification que les morceaux appartiennent bien au chanteur
        const btnVerifySinger = document.getElementById('btnVerifySinger');
        const verifyBanner = document.getElementById('singerVerificationBanner');
        const verifyTitle = document.getElementById('verifyBannerTitle');
        const verifySub = document.getElementById('verifyBannerSub');
        const btnFilterVerifiedOnly = document.getElementById('btnFilterVerifiedOnly');

        if (btnVerifySinger) {
            btnVerifySinger.addEventListener('click', async () => {
                if (!currentSingerName) {
                    showToast("Veuillez d'abord rechercher un chanteur", true);
                    return;
                }
                showToast(`🔍 Analyse et vérification des titres de ${currentSingerName}...`);
                try {
                    const res = await fetch(`/api/singer/verify-folder?artist=${encodeURIComponent(currentSingerName)}`);
                    const data = await res.json();
                    
                    if (verifyBanner) {
                        verifyBanner.style.display = 'block';
                        if (data.intruder_count > 0) {
                            verifyTitle.innerHTML = `⚠️ Scanner : ${data.verified_count} titres officiels de ${currentSingerName} validés (${data.intruder_count} intrus détectés)`;
                            verifySub.textContent = `Certains fichiers dans le dossier semblent appartenir à un autre artiste ou être des reprises non officielles.`;
                        } else {
                            verifyTitle.innerHTML = `✅ Scanner : 100% des morceaux appartiennent bien à ${currentSingerName} (Catalogue officiel validé)`;
                            verifySub.textContent = `Toutes les musiques analysées sont authentifiées conformes sans aucun intrus.`;
                        }
                    }
                    showToast(`✅ Analyse terminée : ${data.verified_count} titres certifiés officiels pour ${currentSingerName}`);
                } catch (err) {
                    showToast("Erreur lors de la vérification", true);
                }
            });
        }

        if (btnFilterVerifiedOnly) {
            btnFilterVerifiedOnly.addEventListener('click', () => {
                document.querySelectorAll('.chk-track').forEach(chk => {
                    const isVerified = chk.dataset.verified === 'true';
                    const isDup = chk.dataset.duplicate === 'true';
                    chk.checked = isVerified && !isDup;
                });
                updateSelectedCount();
                showToast("Filtre activé : seuls les titres officiels du chanteur sont sélectionnés !");
            });
        }

        // Sélectionner / Désélectionner
        if (checkSelectAll) {
            checkSelectAll.addEventListener('change', () => {
                const isChecked = checkSelectAll.checked;
                document.querySelectorAll('.chk-track').forEach(chk => {
                    const isDup = chk.dataset.duplicate === 'true';
                    // Si coché, ne cocher que les nouveaux morceaux
                    if (isChecked) {
                        chk.checked = !isDup;
                    } else {
                        chk.checked = false;
                    }
                });
                updateSelectedCount();
            });
        }

        // Bouton de téléchargement complet en lot
        if (btnDownloadAllSinger) {
            btnDownloadAllSinger.addEventListener('click', async () => {
                const selectedTracks = [];
                document.querySelectorAll('.chk-track:checked').forEach(chk => {
                    const index = parseInt(chk.dataset.index);
                    if (currentDiscography[index]) {
                        selectedTracks.push(currentDiscography[index]);
                    }
                });

                if (selectedTracks.length === 0) {
                    showToast("Aucun morceau sélectionné à télécharger", true);
                    return;
                }

                try {
                    showToast(`Démarrage du téléchargement pour ${currentSingerName} (${selectedTracks.length} titres)...`);
                    const res = await fetch('/api/singer/download-all', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            artist: currentSingerName,
                            tracks: selectedTracks,
                            skip_duplicates: true
                        })
                    });
                    const data = await res.json();
                    if (data.task_id) {
                        // Basculer sur l'onglet de téléchargement ou afficher la progression
                        trackDownloadProgress(data.task_id, currentSingerName, `Discographie complète (${selectedTracks.length} titres)`);
                        // Ouvrir également la section des téléchargements en cours
                        activeDownloadsContainer.style.display = 'block';
                    }
                } catch (err) {
                    showToast("Erreur lors du lancement du téléchargement complet", true);
                }
            });
        }
    }

    async function searchSingerDiscography(artist) {
        currentSingerName = artist;
        singerLoader.style.display = 'block';
        singerResultsContainer.style.display = 'none';
        singerEmptyState.style.display = 'none';

        try {
            const res = await fetch(`/api/singer/discography?artist=${encodeURIComponent(artist)}&limit=50`);
            const data = await res.json();
            currentDiscography = data.tracks || [];

            singerLoader.style.display = 'none';
            singerResultsContainer.style.display = 'block';

            // ✅ Afficher et wirer le bouton ZIP (télécharger dossier complet sur téléphone)
            const btnZip = document.getElementById('btnDownloadZip');
            if (btnZip) {
                btnZip.style.display = 'inline-flex';
                btnZip.onclick = () => {
                    showToast(`📦 Création du ZIP pour ${data.artist}... Cela peut prendre quelques secondes.`);
                    window.location.href = `/api/singer/download-zip/${encodeURIComponent(data.artist)}`;
                };
            }

            // Afficher le nom et badges
            artistNameDisplay.textContent = data.artist;
            badgeTotalFound.textContent = `${data.total_tracks} titres répertoriés`;
            badgeAlreadyPresent.innerHTML = `<i class="fa-solid fa-check"></i> ${data.existing_count} déjà présents sur vos appareils (0 doublon)`;
            badgeNewToDownload.innerHTML = `<i class="fa-solid fa-cloud-arrow-down"></i> ${data.new_count} nouveaux morceaux à télécharger`;

            // Mettre à jour les chemins des fichiers créés pour l'artiste
            const cleanFolder = data.artist.replace(/[<>:"/\\|?*]/g, '').trim();
            createdArtistFolder.textContent = `Musique/${cleanFolder}/`;
            createdDiscographyFile.textContent = `discographie.json`;
            createdPlaylistFile.textContent = `${cleanFolder} - Playlist.m3u8`;
            createdTxtFile.textContent = `liste_des_titres.txt`;

            // Créer automatiquement les fichiers pour le chanteur sur le serveur
            await fetch('/api/singer/create-files', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    artist: data.artist,
                    tracks: currentDiscography
                })
            });

            // Rendre la table des morceaux
            renderDiscographyList(currentDiscography);
            updateSelectedCount();

        } catch (err) {
            singerLoader.style.display = 'none';
            showToast("Erreur lors de la recherche de la discographie", true);
        }
    }

    function renderDiscographyList(tracks) {
        discographyList.innerHTML = '';

        if (!tracks || tracks.length === 0) {
            discographyList.innerHTML = `
                <div class="empty-state">
                    <h3>Aucun morceau trouvé pour cet artiste</h3>
                </div>
            `;
            return;
        }

        tracks.forEach((item, index) => {
            const row = document.createElement('div');
            row.className = `discography-row ${item.is_duplicate ? 'row-duplicate' : ''}`;

            const thumb = item.thumbnail || '/static/icons/icon-192.png';
            const yearStr = item.release_year ? ` • ${item.release_year}` : '';
            const albumStr = item.album ? `${escapeHtml(item.album)}` : 'Single';

            let statusHtml = '';
            const isVerifiedSinger = item.belongs_to_artist !== false;
            const verifyBadgeHtml = isVerifiedSinger 
                ? `<span style="display:inline-flex;align-items:center;gap:4px;color:var(--success);font-size:0.75rem;font-weight:600;margin-left:8px;" title="Vérifié : ce titre appartient officiellement au chanteur choisi"><i class="fa-solid fa-circle-check"></i> Chanteur vérifié</span>`
                : `<span style="display:inline-flex;align-items:center;gap:4px;color:var(--danger);font-size:0.75rem;font-weight:600;margin-left:8px;" title="Attention : ce titre semble être d'un autre interprète ou une reprise"><i class="fa-solid fa-triangle-exclamation"></i> Non officiel / Autre chanteur</span>`;

            if (item.is_duplicate) {
                const src = item.duplicate_info ? item.duplicate_info.source : 'Appareil';
                statusHtml = `
                    <span class="status-badge-dup" title="Morceau déjà détecté sur votre appareil. Sera ignoré pour éviter les doublons.">
                        <i class="fa-solid fa-check"></i> Déjà présent (${src})
                    </span>
                    ${verifyBadgeHtml}
                `;
            } else {
                statusHtml = `
                    <span class="status-badge-new">
                        <i class="fa-solid fa-sparkles"></i> Nouveau
                    </span>
                    ${verifyBadgeHtml}
                `;
            }

            row.innerHTML = `
                <div class="col-check">
                    <input type="checkbox" class="chk-track" data-index="${index}" data-duplicate="${item.is_duplicate}" data-verified="${isVerifiedSinger}" ${(!item.is_duplicate && isVerifiedSinger) ? 'checked' : ''}>
                </div>
                <div class="col-thumb">
                    <img src="${thumb}" alt="Pochette" onerror="this.src='/static/icons/icon-192.png'">
                </div>
                <div class="col-title">
                    <span class="track-name">${escapeHtml(item.title)}</span>
                    <span class="track-meta">${albumStr}${yearStr} • ${item.duration}</span>
                </div>
                <div class="col-status">
                    ${statusHtml}
                </div>
                <div class="col-actions">
                    ${item.preview_url ? `
                        <button class="btn-track-action btn-preview" title="Écouter un extrait de 30s">
                            <i class="fa-solid fa-volume-high"></i>
                        </button>
                    ` : ''}
                    <button class="btn-track-action btn-single-dl" title="${item.is_duplicate ? 'Télécharger quand même' : 'Télécharger ce morceau'}">
                        <i class="fa-solid fa-download"></i>
                    </button>
                </div>
            `;

            // Événement case à cocher
            const chk = row.querySelector('.chk-track');
            chk.addEventListener('change', updateSelectedCount);

            // Écoute extrait
            const btnPrev = row.querySelector('.btn-preview');
            if (btnPrev && item.preview_url) {
                btnPrev.addEventListener('click', () => {
                    audio.src = item.preview_url;
                    playerTitle.textContent = item.title;
                    playerArtist.textContent = `${item.artist} (Extrait)`;
                    musicPlayer.style.display = 'block';
                    audio.play();
                    btnPlayPause.innerHTML = '<i class="fa-solid fa-pause"></i>';
                });
            }

            // Téléchargement individuel
            const btnSingle = row.querySelector('.btn-single-dl');
            btnSingle.addEventListener('click', () => {
                const searchQ = `${item.artist} - ${item.title} audio`;
                triggerDownload(searchQ, item.artist, item.title, item.thumbnail);
            });

            discographyList.appendChild(row);
        });
    }

    function updateSelectedCount() {
        const checkedBoxes = document.querySelectorAll('.chk-track:checked');
        if (selectedCountText) {
            selectedCountText.textContent = checkedBoxes.length;
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Run
    init();

    // Enregistrer le Service Worker pour l'installation PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js', { scope: '/' })
            .catch(err => console.warn('SW:', err));
    }
});
