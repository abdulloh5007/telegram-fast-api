import api from './api.js';
import state from './state.js';
import { initial, escape, formatTime, formatMsg, formatTelegramText } from './utils.js';

const $ = (id) => document.getElementById(id);

const el = {
    sessionScreen: $('session-screen'),
    chatScreen: $('chat-screen'),
    sessionsList: $('sessions-list'),
    userAvatar: $('user-avatar'),
    userName: $('user-name'),
    userUsername: $('user-username'),
    btnLogout: $('btn-logout'),
    btnBack: $('btn-back'),
    btnSettings: $('btn-settings'),
    sidebar: document.querySelector('.sidebar'),
    searchInput: $('search-input'),
    dialogsList: $('dialogs-list'),
    chatHeader: $('chat-header'),
    chatAvatar: $('chat-avatar'),
    chatName: $('chat-name'),
    chatStatus: $('chat-status'),
    messagesContainer: $('messages-container'),
    messagesList: $('messages-list'),
    searchToggle: $('search-toggle'),
    searchBar: $('search-bar'),
    searchInputChat: $('search-input-chat'),
    searchResults: $('search-results'),
    searchPrev: $('search-prev'),
    searchNext: $('search-next'),
    searchClose: $('search-close'),
    settingsModal: $('settings-modal'),
    modalClose: $('modal-close'),
    btnBackup: $('btn-backup'),
    backupStatus: $('backup-status'),
    backupLog: $('backup-log'),
    sessionExpiredModal: $('session-expired-modal'),
    btnViewSaved: $('btn-view-saved'),
    btnNewLogin: $('btn-new-login')
};

function renderSessions(sessions) {
    if (!sessions.length) {
        el.sessionsList.innerHTML = '<div class="loading">Нет сессий</div>';
        return;
    }

    el.sessionsList.innerHTML = sessions.map(s => `
        <div class="session-item" data-id="${s.id}">
            <div class="session-icon">${initial(s.name)}</div>
            <div class="session-info">
                <span class="session-name">${escape(s.name)}</span>
                <span class="session-id">${s.id}</span>
            </div>
        </div>
    `).join('');

    el.sessionsList.querySelectorAll('.session-item').forEach(item => {
        item.onclick = () => selectSession(item.dataset.id);
    });
}

function renderUser(user) {
    state.user = user;
    el.userName.textContent = [user.first_name, user.last_name].filter(Boolean).join(' ');
    el.userUsername.textContent = user.username ? `@${user.username}` : user.phone || '';

    if (user.has_photo) {
        const img = new Image();
        img.src = api.userPhoto(state.session, user.id);
        img.onload = () => { el.userAvatar.innerHTML = ''; el.userAvatar.appendChild(img); };
    }
}

function renderDialogs(dialogs) {
    state.dialogs = dialogs;

    if (!dialogs.length) {
        el.dialogsList.innerHTML = '<div class="loading">Нет чатов</div>';
        return;
    }

    el.dialogsList.innerHTML = dialogs.map(d => `
        <div class="dialog-item" data-id="${d.id}">
            <div class="dialog-avatar ${d.type}">
                ${d.has_photo ? `<img src="${api.dialogPhoto(state.session, d.id)}" onerror="this.parentElement.innerHTML='${initial(d.name)}'">` : initial(d.name)}
            </div>
            <div class="dialog-content">
                <div class="dialog-header">
                    <span class="dialog-name">${escape(d.name)}</span>
                    <span class="dialog-time">${formatTime(d.last_date)}</span>
                </div>
                <div class="dialog-preview">
                    ${escape(d.last_message) || ''}
                    ${d.unread_count > 0 ? `<span class="dialog-unread">${d.unread_count}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');

    el.dialogsList.querySelectorAll('.dialog-item').forEach(item => {
        item.onclick = () => selectDialog(parseInt(item.dataset.id));
    });
}

function renderMessages(messages) {
    if (!messages.length) {
        el.messagesList.innerHTML = '<div class="loading">Нет сообщений</div>';
        return;
    }

    el.messagesList.innerHTML = messages.map(m => {
        let mediaHtml = '';
        if (m.has_media && m.media_type === 'photo') {
            mediaHtml = `<img class="message-photo" src="${api.messageMedia(state.session, state.dialog, m.id)}" loading="lazy" onclick="window.open(this.src)">`;
        } else if (m.has_media) {
            mediaHtml = `<div class="message-media">📎 ${m.media_type || 'Media'}</div>`;
        }

        return `
            <div class="message ${m.is_outgoing ? 'outgoing' : 'incoming'}">
                <div class="message-bubble">
                    ${!m.is_outgoing && m.sender_name ? `<div class="message-sender">${escape(m.sender_name)}</div>` : ''}
                    ${mediaHtml}
                    ${m.text ? `<div class="message-text">${formatTelegramText(m.text, m.entities)}</div>` : ''}
                    <div class="message-meta"><span>${formatMsg(m.date)}</span></div>
                </div>
            </div>
        `;
    }).join('');

    el.messagesContainer.scrollTop = el.messagesContainer.scrollHeight;
}

function appendMessage(m) {
    let mediaHtml = '';
    if (m.has_media && m.media_type === 'photo') {
        mediaHtml = `<img class="message-photo" src="${api.messageMedia(state.session, state.dialog, m.id)}" loading="lazy" onclick="window.open(this.src)">`;
    } else if (m.has_media) {
        mediaHtml = `<div class="message-media">📎 ${m.media_type || 'Media'}</div>`;
    }

    const html = `
        <div class="message ${m.is_outgoing ? 'outgoing' : 'incoming'}">
            <div class="message-bubble">
                ${!m.is_outgoing && m.sender_name ? `<div class="message-sender">${escape(m.sender_name)}</div>` : ''}
                ${mediaHtml}
                ${m.text ? `<div class="message-text">${formatTelegramText(m.text, m.entities)}</div>` : ''}
                <div class="message-meta"><span>${formatMsg(m.date)}</span></div>
            </div>
        </div>
    `;
    el.messagesList.insertAdjacentHTML('beforeend', html);
    el.messagesContainer.scrollTop = el.messagesContainer.scrollHeight;
}

function connectWebSocket(sessionId, dialogId) {
    if (state.ws) {
        state.ws.close();
        state.ws = null;
    }

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${location.host}/ws/${sessionId}/${dialogId}`;

    console.log('[WS] Connecting to:', url);

    state.ws = new WebSocket(url);

    state.ws.onopen = () => {
        console.log('[WS] Connected');
    };

    state.ws.onmessage = (e) => {
        console.log('[WS] Message:', e.data);
        const data = JSON.parse(e.data);
        if (data.type === 'new_message' && state.dialog === dialogId) {
            appendMessage(data.message);
        }
    };

    state.ws.onerror = (e) => {
        console.error('[WS] Error:', e);
    };

    state.ws.onclose = (e) => {
        console.log('[WS] Closed:', e.code, e.reason);
        if (state.dialog === dialogId) {
            setTimeout(() => connectWebSocket(sessionId, dialogId), 3000);
        }
    };
}

async function selectSession(sid) {
    state.session = sid;
    el.sessionScreen.classList.remove('active');
    el.chatScreen.classList.add('active');
    el.dialogsList.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        const [user, dialogs] = await Promise.all([api.getUser(sid), api.getDialogs(sid)]);
        renderUser(user);
        renderDialogs(dialogs);
    } catch (e) {
        el.dialogsList.innerHTML = `<div class="loading">Ошибка: ${e.message}</div>`;
    }
}

async function selectDialog(did) {
    state.dialog = did;

    el.dialogsList.querySelectorAll('.dialog-item').forEach(item => {
        item.classList.toggle('active', parseInt(item.dataset.id) === did);
    });

    const dialog = state.dialogs.find(d => d.id === did);
    if (!dialog) return;

    el.chatHeader.style.display = 'flex';
    el.messagesContainer.style.display = 'flex';
    document.querySelector('.chat-placeholder')?.remove();

    el.sidebar?.classList.add('hidden');

    el.chatName.textContent = dialog.name;
    el.chatStatus.textContent = dialog.type;

    if (dialog.has_photo) {
        const img = new Image();
        img.src = api.dialogPhoto(state.session, did);
        img.onload = () => { el.chatAvatar.innerHTML = ''; el.chatAvatar.appendChild(img); };
    } else {
        el.chatAvatar.innerHTML = initial(dialog.name);
    }

    el.messagesList.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        const messages = await api.getMessages(state.session, did);
        renderMessages(messages);
        connectWebSocket(state.session, did);
    } catch (e) {
        el.messagesList.innerHTML = `<div class="loading">Ошибка: ${e.message}</div>`;
    }
}

function logout() {
    if (state.ws) { state.ws.close(); state.ws = null; }
    state.session = null;
    state.dialog = null;
    state.dialogs = [];
    state.user = null;

    el.chatScreen.classList.remove('active');
    el.sessionScreen.classList.add('active');
    el.chatHeader.style.display = 'none';
    el.messagesContainer.style.display = 'none';
    el.messagesList.innerHTML = '';

    loadSessions();
}

async function loadSessions() {
    el.sessionsList.innerHTML = '<div class="loading">Загрузка...</div>';
    try {
        renderSessions(await api.getSessions());
    } catch (e) {
        el.sessionsList.innerHTML = `<div class="loading">Ошибка: ${e.message}</div>`;
    }
}

el.searchInput?.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    el.dialogsList.querySelectorAll('.dialog-item').forEach(item => {
        const name = item.querySelector('.dialog-name').textContent.toLowerCase();
        item.style.display = name.includes(q) ? 'flex' : 'none';
    });
});

el.btnLogout?.addEventListener('click', logout);

function goBack() {
    el.sidebar?.classList.remove('hidden');
    el.chatHeader.style.display = 'none';
    el.messagesContainer.style.display = 'none';
    state.dialog = null;
    el.dialogsList.querySelectorAll('.dialog-item').forEach(i => i.classList.remove('active'));
}

el.btnBack?.addEventListener('click', goBack);

el.btnSettings?.addEventListener('click', () => {
    el.settingsModal?.classList.add('active');
});

el.modalClose?.addEventListener('click', () => {
    el.settingsModal?.classList.remove('active');
});

el.settingsModal?.addEventListener('click', (e) => {
    if (e.target === el.settingsModal) {
        el.settingsModal.classList.remove('active');
    }
});

const backupEl = {
    modeLocal: $('mode-local'),
    modeCloud: $('mode-cloud'),
    passwordGroup: $('password-group'),
    password: $('backup-password'),
    msgLimit: $('msg-limit'),
    msgLimitValue: $('msg-limit-value'),
    chatSelector: $('chat-selector'),
    selectAll: $('select-all'),
    deselectAll: $('deselect-all'),
    backupWarning: $('backup-warning'),
    btnDeleteOld: $('btn-delete-old')
};

let backupMode = 'local';
let hasExistingBackup = false;
let telegramId = null;

backupEl.modeLocal?.addEventListener('click', () => {
    backupMode = 'local';
    backupEl.modeLocal.classList.add('active');
    backupEl.modeCloud?.classList.remove('active');
    backupEl.passwordGroup.style.display = 'block';
    backupEl.backupWarning.style.display = 'none';
});

backupEl.modeCloud?.addEventListener('click', async () => {
    backupMode = 'cloud';
    backupEl.modeCloud.classList.add('active');
    backupEl.modeLocal?.classList.remove('active');
    backupEl.passwordGroup.style.display = 'none';
    if (hasExistingBackup) {
        backupEl.backupWarning.style.display = 'flex';
    }
});

backupEl.msgLimit?.addEventListener('input', () => {
    backupEl.msgLimitValue.textContent = backupEl.msgLimit.value;
});

backupEl.selectAll?.addEventListener('click', () => {
    backupEl.chatSelector?.querySelectorAll('input').forEach(cb => cb.checked = true);
});

backupEl.deselectAll?.addEventListener('click', () => {
    backupEl.chatSelector?.querySelectorAll('input').forEach(cb => cb.checked = false);
});

backupEl.btnDeleteOld?.addEventListener('click', async () => {
    if (!telegramId) return;
    backupEl.btnDeleteOld.disabled = true;
    backupEl.btnDeleteOld.textContent = 'Удаляю...';
    try {
        await api.deleteBackup(telegramId);
        hasExistingBackup = false;
        backupEl.backupWarning.style.display = 'none';
        addLogItem('Старые данные удалены', 'success');
    } catch (e) {
        addLogItem('Ошибка удаления: ' + e.message, 'error');
    }
    backupEl.btnDeleteOld.disabled = false;
    backupEl.btnDeleteOld.textContent = 'Удалить старые';
});

function addLogItem(text, type = '') {
    const log = el.backupLog;
    if (!log) return;
    log.style.display = 'block';
    const item = document.createElement('div');
    item.className = `backup-log-item ${type}`;
    item.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
}

async function loadChatSelector() {
    if (!state.dialogs?.length) return;
    backupEl.chatSelector.innerHTML = state.dialogs.map(d => `
        <label class="chat-checkbox">
            <input type="checkbox" value="${d.id}" checked>
            <span>${escape(d.name)}</span>
        </label>
    `).join('');
}

async function checkBackupStatus() {
    if (!state.session) return;
    try {
        const status = await api.backupStatus(state.session);
        hasExistingBackup = status.has_backup;
        telegramId = status.telegram_id;
    } catch { }
}

el.btnSettings?.addEventListener('click', async () => {
    el.settingsModal?.classList.add('active');
    loadChatSelector();
    await checkBackupStatus();
    if (hasExistingBackup && backupMode === 'cloud') {
        backupEl.backupWarning.style.display = 'flex';
    }
});

el.btnBackup?.addEventListener('click', async () => {
    if (!state.session) return;

    const selectedDialogs = Array.from(backupEl.chatSelector?.querySelectorAll('input:checked') || [])
        .map(cb => parseInt(cb.value));

    if (selectedDialogs.length === 0) {
        el.backupStatus.className = 'backup-status show error';
        el.backupStatus.textContent = 'Выберите хотя бы один чат';
        return;
    }

    const msgLimit = parseInt(backupEl.msgLimit?.value || 50);

    if (backupMode === 'local') {
        const password = backupEl.password?.value;
        if (!password || password.length < 4) {
            el.backupStatus.className = 'backup-status show error';
            el.backupStatus.textContent = 'Пароль должен быть минимум 4 символа';
            return;
        }

        el.btnBackup.disabled = true;
        el.btnBackup.textContent = 'Скачиваю...';
        el.backupStatus.className = 'backup-status show loading';
        el.backupStatus.textContent = 'Создание зашифрованного файла...';
        if (el.backupLog) el.backupLog.innerHTML = '';
        addLogItem('Начало экспорта...');

        try {
            const blob = await api.exportLocal(state.session, selectedDialogs, msgLimit, password);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `telegram_backup_${telegramId || 'data'}.enc`;
            a.click();
            URL.revokeObjectURL(url);
            addLogItem('Файл скачан!', 'success');
            el.backupStatus.className = 'backup-status show success';
            el.backupStatus.textContent = '✓ Файл сохранён на компьютер';
        } catch (e) {
            addLogItem('Ошибка: ' + e.message, 'error');
            el.backupStatus.className = 'backup-status show error';
            el.backupStatus.textContent = '✗ ' + e.message;
        }
    } else {
        if (hasExistingBackup) {
            el.backupStatus.className = 'backup-status show error';
            el.backupStatus.textContent = 'Сначала удалите старые данные';
            return;
        }

        el.btnBackup.disabled = true;
        el.btnBackup.textContent = 'Сохраняю...';
        el.backupStatus.className = 'backup-status show loading';
        el.backupStatus.textContent = 'Сохранение в Supabase...';
        if (el.backupLog) el.backupLog.innerHTML = '';
        addLogItem('Начало backup в Supabase...');

        try {
            const result = await api.backup(state.session, selectedDialogs, msgLimit);
            addLogItem(`Сохранено чатов: ${result.dialogs}`, 'success');
            addLogItem(`Сохранено сообщений: ${result.messages}`, 'success');
            el.backupStatus.className = 'backup-status show success';
            el.backupStatus.textContent = `✓ Сохранено ${result.dialogs} чатов, ${result.messages} сообщений`;
            hasExistingBackup = true;
        } catch (e) {
            addLogItem('Ошибка: ' + e.message, 'error');
            el.backupStatus.className = 'backup-status show error';
            el.backupStatus.textContent = '✗ ' + e.message;
        }
    }

    el.btnBackup.disabled = false;
    el.btnBackup.textContent = 'Сохранить';
});

function showSessionExpired() {
    el.sessionExpiredModal?.classList.add('active');
}

el.btnNewLogin?.addEventListener('click', () => {
    el.sessionExpiredModal?.classList.remove('active');
    logout();
});

el.btnViewSaved?.addEventListener('click', async () => {
    if (!state.user) return;

    const saved = await api.getSavedData(state.user.id);
    if (saved) {
        el.sessionExpiredModal?.classList.remove('active');
        alert('Функция просмотра сохранённых данных будет доступна в следующей версии');
    } else {
        alert('Нет сохранённых данных');
    }
});

// Search functionality
let searchMatches = [];
let currentMatch = -1;

el.searchToggle?.addEventListener('click', () => {
    el.searchBar?.classList.toggle('active');
    if (el.searchBar?.classList.contains('active')) {
        el.searchInputChat?.focus();
    } else {
        clearSearch();
    }
});

el.searchClose?.addEventListener('click', () => {
    el.searchBar?.classList.remove('active');
    clearSearch();
});

function clearSearch() {
    el.searchInputChat.value = '';
    el.searchResults.textContent = '';
    searchMatches = [];
    currentMatch = -1;
    el.messagesList?.querySelectorAll('.message').forEach(m => {
        m.classList.remove('search-match');
    });
}

function performSearch() {
    const query = el.searchInputChat?.value.toLowerCase().trim();
    if (!query) {
        clearSearch();
        return;
    }

    searchMatches = [];
    const messages = el.messagesList?.querySelectorAll('.message');

    messages?.forEach((m, i) => {
        m.classList.remove('search-match');
        const text = m.querySelector('.message-text')?.textContent?.toLowerCase() || '';
        if (text.includes(query)) {
            searchMatches.push(m);
        }
    });

    el.searchResults.textContent = searchMatches.length > 0
        ? `${searchMatches.length} найдено`
        : 'Не найдено';

    if (searchMatches.length > 0) {
        currentMatch = 0;
        highlightMatch();
    }
}

function highlightMatch() {
    searchMatches.forEach((m, i) => {
        m.classList.toggle('search-match', i === currentMatch);
    });

    if (searchMatches[currentMatch]) {
        searchMatches[currentMatch].scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.searchResults.textContent = `${currentMatch + 1} / ${searchMatches.length}`;
    }
}

el.searchInputChat?.addEventListener('input', () => {
    performSearch();
});

el.searchInputChat?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        if (e.shiftKey) {
            goToPrevMatch();
        } else {
            goToNextMatch();
        }
    } else if (e.key === 'Escape') {
        el.searchBar?.classList.remove('active');
        clearSearch();
    }
});

function goToNextMatch() {
    if (searchMatches.length === 0) return;
    currentMatch = (currentMatch + 1) % searchMatches.length;
    highlightMatch();
}

function goToPrevMatch() {
    if (searchMatches.length === 0) return;
    currentMatch = (currentMatch - 1 + searchMatches.length) % searchMatches.length;
    highlightMatch();
}

el.searchNext?.addEventListener('click', goToNextMatch);
el.searchPrev?.addEventListener('click', goToPrevMatch);

async function init() {
    const sid = new URLSearchParams(location.search).get('session');
    if (sid) {
        try { await selectSession(sid); }
        catch { loadSessions(); }
    } else {
        loadSessions();
    }
}

init();


