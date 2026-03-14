// ── Sample seed data ──
const seedReports = [
    { item: 'Dried longan (commercially packaged)', checkerSaid: 'allowed', actualOutcome: 'confiscated', accurate: 'no', details: 'Officer said dried fruit still requires declaration regardless of packaging.', country: 'Vietnam', date: '2 days ago' },
    { item: 'Instant pho noodle pack (sealed)', checkerSaid: 'allowed', actualOutcome: 'allowed', accurate: 'yes', details: 'No issues at all, just waved through.', country: 'Vietnam', date: '3 days ago' },
    { item: 'Salted egg crisps', checkerSaid: 'declare', actualOutcome: 'declared', accurate: 'yes', details: 'Declared it, officer inspected and let me keep it.', country: 'Singapore', date: '5 days ago' },
    { item: 'Homemade chili sauce (jar)', checkerSaid: 'allowed', actualOutcome: 'confiscated', accurate: 'no', details: 'The checker said it was fine but homemade sauces seem to be a grey area.', country: 'Philippines', date: '1 week ago' },
    { item: 'Japanese KitKat (matcha flavour)', checkerSaid: 'allowed', actualOutcome: 'allowed', accurate: 'yes', details: '', country: 'Japan', date: '1 week ago' },
    { item: 'Dried shrimp (vacuum sealed)', checkerSaid: 'declare', actualOutcome: 'confiscated', accurate: 'no', details: 'Even vacuum sealed, dried seafood was taken. Officer said it needed an import permit.', country: 'China', date: '2 weeks ago' },
    { item: 'Coconut candy (wrapped)', checkerSaid: 'allowed', actualOutcome: 'allowed', accurate: 'yes', details: 'Commercially wrapped sweets, no problem at all.', country: 'Thailand', date: '2 weeks ago' },
];

let allReports = [...seedReports];
let accuracyValue = '';

// ── Render feed ──
function renderFeed(filter = 'all') {
    const feed = document.getElementById('reportsFeed');
    let filtered = allReports;
    if (filter === 'wrong')       filtered = allReports.filter(r => r.accurate === 'no');
    if (filter === 'confiscated') filtered = allReports.filter(r => r.actualOutcome === 'confiscated');

    if (filtered.length === 0) {
        feed.innerHTML = `<div class="empty-feed">No reports match this filter yet.</div>`;
        return;
    }

    feed.innerHTML = filtered.map((r, i) => {
        const outcomeClass = { allowed: 'badge-green', declared: 'badge-amber', confiscated: 'badge-red', not_travelled: 'badge-muted' }[r.actualOutcome] || 'badge-muted';
        const outcomeLabel = { allowed: 'Let through', declared: 'Declared & passed', confiscated: 'Confiscated', not_travelled: 'Not travelled' }[r.actualOutcome] || r.actualOutcome;
        const accuracyBadge = r.accurate === 'yes'
            ? `<span class="accuracy-badge correct">✓ Checker was correct</span>`
            : r.accurate === 'no'
            ? `<span class="accuracy-badge wrong">✗ Checker was wrong</span>`
            : '';

        return `
        <div class="report-card" data-outcome="${r.actualOutcome}" data-accurate="${r.accurate}">
            <div class="report-card-top">
                <div class="report-item-name">${r.item}</div>
                <span class="outcome-badge ${outcomeClass}">${outcomeLabel}</span>
            </div>
            ${r.details ? `<p class="report-detail">"${r.details}"</p>` : ''}
            <div class="report-meta">
                ${r.country ? `<span>✈ from ${r.country}</span>` : ''}
                <span>${r.date}</span>
                ${accuracyBadge}
            </div>
        </div>`;
    }).join('');
}

function filterReports(filter, btn) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderFeed(filter);
}

// ── Accuracy toggle ──
function setAccuracy(val) {
    accuracyValue = val;
    document.getElementById('accuracyValue').value = val;
    document.querySelectorAll('.toggle-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.value === val);
    });
}

// ── Char counter ──
document.getElementById('itemName').addEventListener('input', function() {
    const len = this.value.length;
    document.getElementById('charCount').textContent = len;
    if (len > 120) this.value = this.value.substring(0, 120);
});

// ── Submit ──
function submitReport() {
    const item         = document.getElementById('itemName').value.trim();
    const checkerSaid  = document.querySelector('input[name="checkerSaid"]:checked')?.value;
    const actualOutcome = document.querySelector('input[name="actualOutcome"]:checked')?.value;
    const details      = document.getElementById('details').value.trim();
    const country      = document.getElementById('originCountry').value;

    if (!item) { highlight('itemName'); return; }
    if (!checkerSaid) { highlight('checkerSaidGroup'); return; }
    if (!actualOutcome) { highlight('actualOutcomeGroup'); return; }

    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Submitting…`;

    setTimeout(() => {
        // Prepend new report
        allReports.unshift({
            item, checkerSaid, actualOutcome,
            accurate: accuracyValue || 'unsure',
            details, country, date: 'Just now'
        });

        // Update stats
        document.getElementById('totalCount').textContent = allReports.length + 240;
        document.getElementById('recentCount').textContent = parseInt(document.getElementById('recentCount').textContent) + 1;

        renderFeed('all');
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('[data-filter="all"]').classList.add('active');

        // Show success
        btn.style.display = 'none';
        document.getElementById('successMsg').style.display = 'flex';

        // Reset form after delay
        setTimeout(resetForm, 4000);
    }, 900);
}

function highlight(id) {
    const el = document.getElementById(id);
    el.classList.add('shake');
    el.style.borderColor = '#dc2626';
    setTimeout(() => { el.classList.remove('shake'); el.style.borderColor = ''; }, 600);
}

function resetForm() {
    document.getElementById('itemName').value = '';
    document.getElementById('charCount').textContent = '0';
    document.getElementById('details').value = '';
    document.getElementById('originCountry').value = '';
    document.querySelectorAll('input[type="radio"]').forEach(r => r.checked = false);
    document.querySelectorAll('.radio-card').forEach(c => c.classList.remove('selected'));
    document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
    accuracyValue = '';
    const btn = document.getElementById('submitBtn');
    btn.style.display = 'flex';
    btn.disabled = false;
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg> Submit Report`;
    document.getElementById('successMsg').style.display = 'none';
}

// ── Radio card visual selection ──
document.querySelectorAll('.radio-card input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const group = this.closest('.radio-group');
        group.querySelectorAll('.radio-card').forEach(c => c.classList.remove('selected'));
        this.closest('.radio-card').classList.add('selected');
    });
});

// ── Init ──
renderFeed();
