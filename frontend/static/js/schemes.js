/* ==================== */
/* Schemes Page JavaScript */
/* ==================== */
/*
 * All filtering (search, category, state, benefit) is done SERVER-SIDE.
 * The frontend never downloads the full scheme list and filters it locally
 * — every action below rebuilds the query string and re-fetches from
 * /api/schemes/. "Load More" pages through the API's own pagination
 * (data.next), it does not slice a locally-cached array.
 */

document.addEventListener('DOMContentLoaded', () => {
    const schemesGrid = document.getElementById('schemesGrid');
    const searchInput = document.getElementById('schemeSearch');
    const filterTabs = document.querySelectorAll('.filter-tab');
    const stateFilter = document.getElementById('stateFilter');
    const benefitFilter = document.getElementById('benefitFilter');
    const resetFilters = document.getElementById('resetFilters');
    const resultsCount = document.getElementById('resultsCount');
    const viewBtns = document.querySelectorAll('.view-btn');
    const loadMore = document.getElementById('loadMore');

    let currentFilter = 'all';   // category
    let currentView = 'grid';
    let loadedSchemes = [];      // the schemes currently on screen for THIS query
    let nextPageUrl = null;      // API's own "next page" link, or null
    let requestToken = 0;        // guards against out-of-order responses

    function toRelative(url) {
        return url ? url.replace(/^https?:\/\/[^/]+/, '') : null;
    }

    function buildQuery() {
        const params = new URLSearchParams();
        const searchTerm = searchInput.value.trim();
        if (searchTerm) params.set('search', searchTerm);
        if (currentFilter && currentFilter !== 'all') params.set('category', currentFilter);
        if (stateFilter.value) params.set('state', stateFilter.value);
        if (benefitFilter.value) params.set('benefit', benefitFilter.value);
        const qs = params.toString();
        return qs ? `/api/schemes/?${qs}` : '/api/schemes/';
    }

    function renderSchemeCard(scheme) {
        const docCount = (scheme.required_documents_list || []).length;
        const viewClass = currentView === 'list' ? ' list-view' : '';
        return `
            <div class="scheme-card slide-up${viewClass}" data-id="${scheme.id}">
                <span class="scheme-badge">${(scheme.category || '').charAt(0).toUpperCase() + (scheme.category || '').slice(1)}</span>
                <h3>${scheme.name}</h3>
                <p class="scheme-subtitle">${scheme.department || ''}</p>
                <p class="scheme-description">${scheme.description}</p>
                <div class="scheme-meta">
                    <div class="scheme-meta-item">
                        <i class="fa-solid fa-hand-holding-dollar"></i>
                        <span>${scheme.benefits}</span>
                    </div>
                    <div class="scheme-meta-item">
                        <i class="fa-solid fa-file"></i>
                        <span>${docCount} documents</span>
                    </div>
                    <div class="scheme-meta-item">
                        <i class="fa-solid fa-map-pin"></i>
                        <span>${scheme.state === 'all' ? 'All States' : (scheme.state || '').toUpperCase()}</span>
                    </div>
                </div>
                <div class="scheme-footer">
                    <div class="scheme-actions">
                        <a href="/schemes/${scheme.id}/" class="btn btn-primary btn-sm">View Details</a>
                        <button class="btn btn-outline btn-sm" onclick="listenToScheme('${scheme.name}')">
                            <i class="fa-solid fa-headphones"></i>
                        </button>
                    </div>
                    <button class="bookmark-btn ${scheme.bookmarked ? 'bookmarked' : ''}" onclick="toggleBookmark('${scheme.id}')">
                        <i class="fa-${scheme.bookmarked ? 'solid' : 'regular'} fa-bookmark"></i>
                    </button>
                </div>
            </div>
        `;
    }

    function renderSchemes(schemesToRender) {
        if (schemesToRender.length === 0) {
            schemesGrid.innerHTML = `
                <div class="empty-state col-span-full">
                    <i class="fa-solid fa-search"></i>
                    <h3>No schemes found</h3>
                    <p>Try adjusting your filters or search terms</p>
                    <button class="btn btn-outline" onclick="resetAllFilters()">Clear Filters</button>
                </div>
            `;
            return;
        }

        schemesGrid.innerHTML = schemesToRender.map(renderSchemeCard).join('');

        const cards = schemesGrid.querySelectorAll('.scheme-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }

    async function runQuery() {
        const myToken = ++requestToken;
        schemesGrid.innerHTML = `<div class="schemes-loading col-span-full"><div class="spinner"></div><p>Loading schemes...</p></div>`;

        try {
            const data = await API.get(buildQuery());
            if (myToken !== requestToken) return;

            loadedSchemes = data.results || (Array.isArray(data) ? data : []);
            nextPageUrl = toRelative(data.next);
            const total = data.count ?? loadedSchemes.length;

            renderSchemes(loadedSchemes);
            resultsCount.textContent = total;
            loadMore.style.display = nextPageUrl ? 'inline-flex' : 'none';
        } catch (err) {
            if (myToken !== requestToken) return;
            showToast('Could not load schemes', 'error');
            resultsCount.textContent = '0';
            renderSchemes([]);
            loadMore.style.display = 'none';
        }
    }

    async function loadNextPage() {
        if (!nextPageUrl) return;
        try {
            const data = await API.get(nextPageUrl);
            const more = data.results || [];
            loadedSchemes = loadedSchemes.concat(more);
            nextPageUrl = toRelative(data.next);

            renderSchemes(loadedSchemes);
            loadMore.style.display = nextPageUrl ? 'inline-flex' : 'none';
        } catch (err) {
            showToast('Could not load more schemes', 'error');
        }
    }

    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            filterTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentFilter = tab.dataset.filter;
            runQuery();
        });
    });

    searchInput.addEventListener('input', debounce(runQuery, 400));

    stateFilter.addEventListener('change', runQuery);
    benefitFilter.addEventListener('change', runQuery);

    resetFilters.addEventListener('click', () => {
        searchInput.value = '';
        stateFilter.value = '';
        benefitFilter.value = '';
        filterTabs.forEach(t => t.classList.remove('active'));
        filterTabs[0].classList.add('active');
        currentFilter = 'all';
        nextPageUrl = null;
        loadedSchemes = [];
        renderIdleState();
    });

    viewBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            viewBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentView = btn.dataset.view;

            if (currentView === 'list') {
                schemesGrid.classList.add('list-view');
            } else {
                schemesGrid.classList.remove('list-view');
            }
            renderSchemes(loadedSchemes);
        });
    });

    loadMore.addEventListener('click', loadNextPage);

    window.toggleBookmark = function (id) {
        const scheme = loadedSchemes.find(s => String(s.id) === String(id));
        if (scheme) {
            scheme.bookmarked = !scheme.bookmarked;
            renderSchemes(loadedSchemes);

            if (scheme.bookmarked) {
                showToast('Scheme bookmarked', 'success');
            } else {
                showToast('Bookmark removed', 'info');
            }
        }
    };

    window.listenToScheme = function (name) {
        if (SpeechService.speak(name)) {
            showToast('Playing scheme details', 'info');
        } else {
            showToast('Text-to-speech not supported', 'error');
        }
    };

    window.resetAllFilters = function () {
        resetFilters.click();
    };

    const voiceSearchBtn = document.querySelector('.voice-search-btn');
    if (voiceSearchBtn) {
        if (SpeechService.isSupported()) {
            const recognition = SpeechService.createRecognition({
                onResult: (transcript, isFinal) => {
                    if (isFinal) {
                        searchInput.value = transcript;
                        voiceSearchBtn.classList.remove('listening');
                        runQuery();
                        showToast(`Searching for: "${transcript}"`, 'success');
                    }
                },
                onError: (message) => {
                    voiceSearchBtn.classList.remove('listening');
                    showToast(message, 'error');
                },
                onEnd: () => {
                    voiceSearchBtn.classList.remove('listening');
                }
            }, { interimResults: false });

            voiceSearchBtn.addEventListener('click', () => {
                try {
                    recognition.start();
                    voiceSearchBtn.classList.add('listening');
                    showToast('Listening...', 'info');
                } catch (error) {
                    console.error('Speech recognition error:', error);
                }
            });

            document.addEventListener('languagechange', () => {
                SpeechService.syncLang(recognition);
            });
        } else {
            voiceSearchBtn.style.display = 'none';
        }
    }

// Idle state shown before the user has done anything — nothing is
    // fetched from the API until they search, pick a category, or pick a
    // state/benefit filter.
    function renderIdleState() {
        schemesGrid.innerHTML = `
            <div class="empty-state col-span-full">
                <i class="fa-solid fa-magnifying-glass"></i>
                <h3>Search for a scheme</h3>
                <p>Type a keyword above, or choose a category / state to see matching schemes</p>
            </div>
        `;
        resultsCount.textContent = '0';
        loadMore.style.display = 'none';
    }

    runQuery();
});