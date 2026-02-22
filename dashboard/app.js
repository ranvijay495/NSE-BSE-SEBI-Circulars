const API_BASE = '';
let currentSource = 'ALL';
let allCirculars = [];
let bookmarkedIds = new Set();
let categories = [];

// === Data Loading ===

async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const stats = await res.json();
        document.getElementById('totalCount').textContent = stats.total || 0;
        document.getElementById('sebiCount').textContent = stats.SEBI || 0;
        document.getElementById('bseCount').textContent = stats.BSE || 0;
        document.getElementById('nseCount').textContent = stats.NSE || 0;
        document.getElementById('lastUpdated').textContent =
            `Updated: ${new Date(stats.last_updated).toLocaleString()}`;
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

async function loadCategories() {
    try {
        const res = await fetch(`${API_BASE}/api/categories`);
        const data = await res.json();
        categories = data.categories || [];
        const select = document.getElementById('categoryFilter');
        select.innerHTML = '<option value="">All Categories</option>';
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Failed to load categories:', err);
    }
}

async function loadCirculars(source) {
    const list = document.getElementById('circularList');
    const emptyState = document.getElementById('emptyState');
    const emptyText = document.getElementById('emptyText');

    list.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading circulars...</p></div>';
    emptyState.style.display = 'none';

    try {
        // Handle bookmarks tab
        if (source === 'BOOKMARKS') {
            const res = await fetch(`${API_BASE}/api/bookmarks`);
            const data = await res.json();
            allCirculars = data.bookmarks || [];
            bookmarkedIds = new Set(allCirculars.map(c => c.id));

            if (allCirculars.length === 0) {
                list.innerHTML = '';
                emptyText.textContent = 'No bookmarked circulars yet.';
                emptyState.style.display = 'block';
                return;
            }
            list.innerHTML = renderTable(allCirculars);
            return;
        }

        // Build query params
        const params = new URLSearchParams();
        const fromDate = document.getElementById('fromDate').value;
        const toDate = document.getElementById('toDate').value;
        const category = document.getElementById('categoryFilter').value;

        if (fromDate && toDate) {
            params.set('from_date', fromDate);
            params.set('to_date', toDate);
        } else {
            params.set('days', '14');
        }

        if (source && source !== 'ALL') {
            params.set('source', source);
        }

        if (category) {
            params.set('category', category);
        }

        const res = await fetch(`${API_BASE}/api/circulars?${params.toString()}`);
        const data = await res.json();
        allCirculars = data.circulars || [];

        // Track bookmarked IDs
        bookmarkedIds = new Set(
            allCirculars.filter(c => c.is_bookmarked).map(c => c.id)
        );

        if (allCirculars.length === 0) {
            list.innerHTML = '';
            emptyText.textContent = 'No circulars found for the selected filters.';
            emptyState.style.display = 'block';
            return;
        }

        list.innerHTML = renderTable(allCirculars);
    } catch (err) {
        list.innerHTML = `<div class="loading-state"><p>Error loading circulars: ${err.message}</p></div>`;
    }
}

// === Rendering ===

function renderTable(circulars) {
    const rows = circulars.map(c => {
        const date = formatDate(c.published_date);
        const sourceBadge = getSourceBadge(c.source);
        const newBadge = isNew(c.published_date) ? '<span class="new-badge">NEW</span>' : '';
        const isBookmarked = bookmarkedIds.has(c.id);

        const bookmarkBtn = `
            <button class="btn-bookmark ${isBookmarked ? 'bookmarked' : ''}" onclick="toggleBookmark('${c.id}')" title="${isBookmarked ? 'Remove bookmark' : 'Bookmark'}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="${isBookmarked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/>
                </svg>
            </button>
        `;

        // Attachments: View (inline, PDF only) + Download
        let attachments = '';
        const isZip = c.pdf_url && c.pdf_url.endsWith('.zip');
        if (c.pdf_url) {
            const viewBtn = isZip ? '' :
                `<a href="/api/circulars/${c.id}/pdf?mode=view" class="btn btn-sm btn-outline" target="_blank">View</a>`;
            const label = isZip ? 'Download ZIP' : 'Download';
            attachments = `
                ${viewBtn}
                <a href="/api/circulars/${c.id}/pdf?mode=download" class="btn btn-sm btn-download">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                    </svg>
                    ${label}
                </a>
            `;
        } else if (c.detail_url) {
            attachments = `<a href="${escapeAttr(c.detail_url)}" class="btn btn-sm btn-outline" target="_blank">Source</a>`;
        } else {
            attachments = '<span class="no-attachment">—</span>';
        }

        return `
            <tr>
                <td class="col-bookmark">${bookmarkBtn}</td>
                <td class="col-date">${date} ${newBadge}</td>
                <td class="col-source">${sourceBadge}</td>
                <td class="col-title">
                    <div class="circular-title">${escapeHtml(c.title)}</div>
                    ${c.circular_number ? `<div class="circular-ref">${escapeHtml(c.circular_number)}</div>` : ''}
                </td>
                <td class="col-category">${escapeHtml(c.category || '')}</td>
                <td class="col-attachments">${attachments}</td>
            </tr>
        `;
    }).join('');

    return `
        <table class="circular-table">
            <thead>
                <tr>
                    <th class="th-bookmark"></th>
                    <th>Date</th>
                    <th>Source</th>
                    <th>Title</th>
                    <th>Category</th>
                    <th>Attachments</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function getSourceBadge(source) {
    const cls = {
        'SEBI': 'badge-sebi',
        'BSE': 'badge-bse',
        'NSE': 'badge-nse',
    };
    return `<span class="source-badge ${cls[source] || ''}">${source}</span>`;
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function isNew(publishedDate) {
    if (!publishedDate) return false;
    const pub = new Date(publishedDate + 'T00:00:00');
    const now = new Date();
    const diffHours = (now - pub) / (1000 * 60 * 60);
    return diffHours <= 48;
}

// === Filters ===

function switchTab(source) {
    currentSource = source;
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.source === source);
    });
    loadCirculars(source);
}

function applyFilters() {
    loadCirculars(currentSource);
}

function clearFilters() {
    document.getElementById('fromDate').value = '';
    document.getElementById('toDate').value = '';
    document.getElementById('categoryFilter').value = '';
    loadCirculars(currentSource);
}

function refreshData() {
    loadStats();
    loadCategories();
    loadCirculars(currentSource);
}

// === Bookmarks ===

async function toggleBookmark(circularId) {
    const isCurrently = bookmarkedIds.has(circularId);

    try {
        if (isCurrently) {
            await fetch(`${API_BASE}/api/bookmarks/${circularId}`, { method: 'DELETE' });
            bookmarkedIds.delete(circularId);
        } else {
            await fetch(`${API_BASE}/api/bookmarks/${circularId}`, { method: 'POST' });
            bookmarkedIds.add(circularId);
        }

        // Update local state
        const circular = allCirculars.find(c => c.id === circularId);
        if (circular) {
            circular.is_bookmarked = !isCurrently;
        }

        // Re-render
        if (currentSource === 'BOOKMARKS') {
            loadCirculars('BOOKMARKS');
        } else {
            document.getElementById('circularList').innerHTML = renderTable(allCirculars);
        }
    } catch (err) {
        console.error('Bookmark toggle failed:', err);
    }
}

// === Utilities ===

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// === Init ===
loadStats();
loadCategories();
loadCirculars('ALL');
