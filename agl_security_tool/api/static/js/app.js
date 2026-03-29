/**
 * AGL Security — Client-side utilities
 * Alpine.js plugins + Chart.js configurations + helpers
 */

// ── Alpine.js x-collapse plugin (simple) ──────────────
document.addEventListener('alpine:init', () => {
    Alpine.directive('collapse', (el) => {
        // Simple show/hide with height transition
        const originalTransition = el.style.transition;
        el.style.overflow = 'hidden';

        // Watch x-show changes
        const observer = new MutationObserver(() => {
            if (el.style.display === 'none') {
                el.style.height = '0px';
            } else {
                el.style.height = el.scrollHeight + 'px';
                setTimeout(() => {
                    el.style.height = 'auto';
                }, 300);
            }
        });

        observer.observe(el, { attributes: true, attributeFilter: ['style'] });
    });
});


// ── Notification toast ──────────────────────────────────
function showToast(message, type = 'info') {
    const colors = {
        info: 'bg-blue-500/90',
        success: 'bg-green-500/90',
        error: 'bg-red-500/90',
        warning: 'bg-yellow-500/90',
    };

    const toast = document.createElement('div');
    toast.className = `fixed top-20 right-4 z-[100] px-6 py-3 rounded-xl ${colors[type] || colors.info} text-white text-sm font-medium shadow-2xl transition-all transform translate-x-full`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
    });

    // Animate out
    setTimeout(() => {
        toast.style.transform = 'translateX(120%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}


// ── Chart.js dark theme defaults ────────────────────────
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = '#1e1e3a';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
}


// ── Helper: Format large numbers ────────────────────────
function formatUSD(n) {
    if (!n || n === 0) return '$0';
    if (n >= 1e9) return '$' + (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return '$' + (n / 1e3).toFixed(1) + 'K';
    return '$' + n.toFixed(0);
}


// ── Helper: Time ago ────────────────────────────────────
function timeAgo(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    if (seconds < 172800) return 'yesterday';
    return date.toLocaleDateString();
}


// ── Console branding ────────────────────────────────────
console.log(
    '%c🛡️ AGL Security %cv1.1.0',
    'color: #6366f1; font-size: 20px; font-weight: bold;',
    'color: #8b5cf6; font-size: 14px;'
);
console.log(
    '%cSmart Contract Security Analysis Tool',
    'color: #94a3b8; font-size: 12px;'
);
