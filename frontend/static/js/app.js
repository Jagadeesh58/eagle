/* ============================================================
   EAGL — Shared JavaScript Utilities
   Session, API calls, Notifications, Modals, Navigation
   ============================================================ */

const API = 'http://localhost:8000';  // backend server URL

// ============================================================
// COOKIE MANAGEMENT
// ============================================================
function setCookie(name, value, days = 7) {
    const d = new Date();
    d.setTime(d.getTime() + days * 86400000);
    document.cookie = `${name}=${encodeURIComponent(value)};expires=${d.toUTCString()};path=/;SameSite=Lax`;
}

function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
}

function deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
}

// ============================================================
// SESSION MANAGEMENT
// ============================================================
function getSession() {
    const id     = getCookie('user_id');
    const name   = getCookie('user_name');
    const role   = getCookie('user_role');
    const email  = getCookie('user_email');
    const mobile = getCookie('user_mobile');
    if (id && role) return { id: parseInt(id), name, role, email, mobile };
    return null;
}

function setSession(user) {
    setCookie('user_id',         user.id);
    setCookie('user_name',       user.name);
    setCookie('user_role',       user.role);
    setCookie('user_email',      user.email);
    setCookie('user_mobile',     user.mobile || '');
    setCookie('is_first_login',  String(user.is_first_login ?? 0));
}

function clearSession() {
    ['user_id', 'user_name', 'user_role', 'user_email', 'user_mobile', 'is_first_login'].forEach(deleteCookie);
}

function logout() {
    clearSession();
    window.location.href = '/';
}

function requireAuth(allowedRoles) {
    const s = getSession();
    if (!s) { window.location.href = '/'; return null; }
    if (allowedRoles && !allowedRoles.includes(s.role)) {
        window.location.href = '/';
        return null;
    }
    return s;
}

// ============================================================
// API HELPER
// ============================================================
async function api(method, endpoint, body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);

    const res = await fetch(API + endpoint, opts);

    if (!res.ok) {
        let msg = `Error ${res.status}`;
        try { const j = await res.json(); msg = j.detail || msg; } catch(e) {}
        throw new Error(msg);
    }

    const text = await res.text();
    return text ? JSON.parse(text) : null;
}

// ============================================================
// NOTIFICATION / TOAST SYSTEM
// ============================================================
function showNotification(message, type = 'success') {
    let container = document.getElementById('notif-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notif-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }

    const el = document.createElement('div');
    el.className = `notification ${type}`;
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    el.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    container.appendChild(el);

    setTimeout(() => {
        el.classList.add('hiding');
        setTimeout(() => el.remove(), 300);
    }, 3500);
}

// ============================================================
// MODAL MANAGEMENT
// ============================================================
function openModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) {
        m.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) {
        m.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function closeAllModals() {
    document.querySelectorAll('.modal-overlay.active').forEach(m => {
        m.classList.remove('active');
    });
    document.body.style.overflow = '';
}

// Close modal on backdrop click
document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeAllModals();
});

// ============================================================
// FORMATTERS
// ============================================================
function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatCurrency(amount) {
    if (amount == null) return '—';
    return '₹' + Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ============================================================
// BADGE RENDERERS
// ============================================================
function roleBadge(role) {
    const cls = {
        admin: 'badge-admin',
        manager: 'badge-manager',
        field_coordinator: 'badge-coordinator1',
        delivery_coordinator: 'badge-coordinator2',
    };
    const label = {
        admin: 'Admin',
        manager: 'Manager',
        field_coordinator: 'Field Coordinator',
        delivery_coordinator: 'Delivery Coordinator',
    };
    return `<span class="badge ${cls[role] || 'badge-secondary'}">${label[role] || role}</span>`;
}

function statusBadge(status) {
    const cls = {
        pending: 'badge-pending',
        delivered: 'badge-delivered',
        completed: 'badge-completed',
    };
    return `<span class="badge ${cls[status] || 'badge-secondary'}">${status || '—'}</span>`;
}

function boolBadge(val, trueText = 'Yes', falseText = 'No') {
    return val
        ? `<span class="badge badge-success">${trueText}</span>`
        : `<span class="badge badge-danger">${falseText}</span>`;
}

// ============================================================
// TABLE SEARCH FILTER
// ============================================================
function setupTableSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener('input', () => {
        const q = input.value.toLowerCase();
        const rows = document.querySelectorAll(`#${tableId} tbody tr`);
        rows.forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    });
}

// ============================================================
// CONFIRM DIALOG
// ============================================================
function confirmAction(message) {
    return new Promise(resolve => {
        // Use simple confirm for now
        resolve(window.confirm(message));
    });
}

// ============================================================
// SIDEBAR NAVIGATION SETUP
// ============================================================
function setupNavigation() {
    const session = getSession();
    if (!session) return;

    // Set user info in sidebar footer
    const avatarEl = document.querySelector('.sidebar-footer .user-avatar');
    const nameEl   = document.querySelector('.sidebar-footer .user-meta .name');
    const roleEl   = document.querySelector('.sidebar-footer .user-meta .role-text');
    if (avatarEl) avatarEl.textContent = (session.name || 'U')[0].toUpperCase();
    if (nameEl)   nameEl.textContent = session.name;
    if (roleEl)   roleEl.textContent = session.role.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

    // Set topbar info
    const topName = document.getElementById('topUserName');
    const topRole = document.getElementById('topUserRole');
    if (topName) topName.textContent = session.name;
    if (topRole) {
        topRole.textContent = session.role.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }

    // Highlight active nav item
    const path = window.location.pathname;
    document.querySelectorAll('.nav-menu a').forEach(a => {
        if (a.getAttribute('href') === path) {
            a.classList.add('active');
        }
    });
}

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    const session = getSession();
    if (session) {
        setupNavigation();
    }
});
