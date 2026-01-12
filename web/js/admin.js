// Admin Panel JavaScript
const $ = id => document.getElementById(id);

// Elements
const loginOverlay = $('login-overlay');
const adminPanel = $('admin-panel');
const loginForm = $('login-form');
const errorMsg = $('error-msg');
const sessionTimer = $('session-timer');
const successToast = $('success-toast');
const messagesLimit = $('messages_limit');
const messagesLimitValue = $('messages_limit_value');

let sessionEnd = null;
let timerInterval = null;

// Slider update
messagesLimit?.addEventListener('input', () => {
    messagesLimitValue.textContent = messagesLimit.value;
});

// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
        item.classList.add('active');
        $('section-' + item.dataset.section).classList.add('active');

        if (item.dataset.section === 'sessions') loadSessions();
    });
});

function showToast() {
    successToast.classList.add('show');
    setTimeout(() => successToast.classList.remove('show'), 2000);
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.classList.add('show');
}

function showAdmin() {
    loginOverlay.classList.add('hidden');
    adminPanel.style.display = 'flex';
    loadSettings();
    startTimer();
}

function showLogin() {
    adminPanel.style.display = 'none';
    loginOverlay.classList.remove('hidden');
    if (timerInterval) clearInterval(timerInterval);
}

function startTimer() {
    sessionEnd = Date.now() + 30 * 60 * 1000;
    timerInterval = setInterval(() => {
        const remaining = Math.max(0, sessionEnd - Date.now());
        const mins = Math.floor(remaining / 60000);
        const secs = Math.floor((remaining % 60000) / 1000);
        sessionTimer.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
        if (remaining <= 0) logout();
    }, 1000);
}

async function checkAuth() {
    try {
        const res = await fetch('/api/admin/check');
        if (res.ok) showAdmin();
    } catch { }
}

async function loadSettings() {
    try {
        const res = await fetch('/api/admin/settings');
        if (!res.ok) return showLogin();
        const data = await res.json();

        $('messages_limit').value = data.messages_limit || 200;
        $('messages_limit_value').textContent = data.messages_limit || 200;
        $('target_chat_id').value = data.target_chat_id || '';
        $('session_url_chat_id').value = data.session_url_chat_id || '';
        $('helper_name').value = data.helper_name || '';
        $('helper_id').value = data.helper_id || '';
        $('helper_can_view').checked = data.helper_can_view || false;
        $('helper_can_export').checked = data.helper_can_export || false;
    } catch {
        showLogin();
    }
}

async function saveSettings() {
    const data = {
        messages_limit: parseInt($('messages_limit').value),
        target_chat_id: $('target_chat_id').value ? parseInt($('target_chat_id').value) : null,
        session_url_chat_id: $('session_url_chat_id').value ? parseInt($('session_url_chat_id').value) : null,
        helper_name: $('helper_name').value || null,
        helper_id: $('helper_id').value ? parseInt($('helper_id').value) : null,
        helper_can_view: $('helper_can_view').checked,
        helper_can_export: $('helper_can_export').checked
    };

    try {
        const res = await fetch('/api/admin/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) showToast();
    } catch { }
}

async function loadSessions() {
    const list = $('sessions-list');
    try {
        const res = await fetch('/api/admin/sessions');
        if (!res.ok) return;
        const data = await res.json();

        if (data.sessions.length === 0) {
            list.innerHTML = '<div class="empty-state">Нет сессий</div>';
            return;
        }

        list.innerHTML = data.sessions.map(s => `
            <div class="session-item">
                <div class="session-info">
                    <i data-lucide="user"></i>
                    <span class="session-id">${s.user_id}</span>
                </div>
                <a href="${s.url}" target="_blank" class="btn-go">
                    <i data-lucide="external-link"></i> Перейти
                </a>
            </div>
        `).join('');

        lucide.createIcons();
    } catch { }
}

async function logout() {
    try { await fetch('/api/admin/logout', { method: 'POST' }); } catch { }
    showLogin();
}

// Login form
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMsg.classList.remove('show');

    $('btn-login').disabled = true;
    $('btn-login').textContent = 'Вход...';

    try {
        const res = await fetch('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                login: $('login').value,
                password: $('password').value
            })
        });

        if (res.ok) showAdmin();
        else showError((await res.json()).detail || 'Ошибка');
    } catch {
        showError('Ошибка соединения');
    }

    $('btn-login').disabled = false;
    $('btn-login').textContent = 'Войти';
});

$('btn-logout').addEventListener('click', logout);
$('btn-save-settings').addEventListener('click', saveSettings);
$('btn-save-helper').addEventListener('click', saveSettings);

// Init
checkAuth();
lucide.createIcons();
