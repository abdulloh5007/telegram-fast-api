const $ = (id) => document.getElementById(id);

const el = {
    dropZone: $('drop-zone'),
    fileInput: $('file-input'),
    fileInfo: $('file-info'),
    fileName: $('file-name'),
    btnRemoveFile: $('btn-remove-file'),
    passwordSection: $('password-section'),
    password: $('decrypt-password'),
    btnDecrypt: $('btn-decrypt'),
    errorMessage: $('error-message'),
    uploadSection: $('upload-section'),
    viewerSection: $('viewer-section'),
    viewerUser: $('viewer-user'),
    viewerDialogs: $('viewer-dialogs'),
    viewerChatHeader: $('viewer-chat-header'),
    viewerMessages: $('viewer-messages'),
    chatTitle: $('chat-title'),
    btnSearch: $('btn-search'),
    searchContainer: $('search-container'),
    searchInput: $('search-input'),
    searchCount: $('search-count'),
    searchPrev: $('search-prev'),
    searchNext: $('search-next'),
    searchClose: $('search-close')
};

let fileContent = null;
let decryptedData = null;
let currentDialogIndex = -1;
let searchMatches = [];
let currentSearchIndex = 0;

async function deriveKey(password, salt) {
    const enc = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        enc.encode(password),
        'PBKDF2',
        false,
        ['deriveKey']
    );
    return crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['decrypt']
    );
}

async function decrypt(base64Content, password) {
    const raw = Uint8Array.from(atob(base64Content), c => c.charCodeAt(0));

    const salt = raw.slice(0, 16);
    const nonce = raw.slice(16, 28);
    const encrypted = raw.slice(28);

    const key = await deriveKey(password, salt);

    const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: nonce },
        key,
        encrypted
    );

    return JSON.parse(new TextDecoder().decode(decrypted));
}

function showError(msg) {
    el.errorMessage.textContent = msg;
    el.errorMessage.style.display = 'block';
}

function hideError() {
    el.errorMessage.style.display = 'none';
}

function handleFile(file) {
    if (!file.name.endsWith('.enc')) {
        showError('Пожалуйста, выберите файл с расширением .enc');
        return;
    }

    hideError();

    const reader = new FileReader();
    reader.onload = () => {
        fileContent = reader.result;
        el.fileName.textContent = file.name;
        el.fileInfo.style.display = 'flex';
        el.dropZone.style.display = 'none';
        el.passwordSection.style.display = 'flex';
    };
    reader.readAsText(file);
}

function removeFile() {
    fileContent = null;
    el.fileInfo.style.display = 'none';
    el.dropZone.style.display = 'block';
    el.passwordSection.style.display = 'none';
    el.password.value = '';
    el.fileInput.value = '';
    hideError();
}

el.btnRemoveFile?.addEventListener('click', removeFile);

el.dropZone?.addEventListener('dragover', (e) => {
    e.preventDefault();
    el.dropZone.classList.add('dragover');
});

el.dropZone?.addEventListener('dragleave', () => {
    el.dropZone.classList.remove('dragover');
});

el.dropZone?.addEventListener('drop', (e) => {
    e.preventDefault();
    el.dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
});

el.fileInput?.addEventListener('change', () => {
    const file = el.fileInput.files[0];
    if (file) handleFile(file);
});

el.btnDecrypt?.addEventListener('click', async () => {
    const password = el.password?.value;
    if (!password) {
        showError('Введите пароль');
        return;
    }

    if (!fileContent) {
        showError('Сначала выберите файл');
        return;
    }

    el.btnDecrypt.disabled = true;
    el.btnDecrypt.textContent = 'Расшифровка...';
    hideError();

    try {
        decryptedData = await decrypt(fileContent, password);
        showViewer();
    } catch (e) {
        showError('Неверный пароль или повреждённый файл');
    }

    el.btnDecrypt.disabled = false;
    el.btnDecrypt.textContent = 'Расшифровать';
});

function escape(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
}

function formatTime(date) {
    if (!date) return '';
    return new Date(date).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' });
}

// Text formatting (bold, italic, code, links)
function formatText(text) {
    if (!text) return '';

    let formatted = escape(text);

    // Bold **text**
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic __text__
    formatted = formatted.replace(/__(.+?)__/g, '<em>$1</em>');

    // Code `text`
    formatted = formatted.replace(/`(.+?)`/g, '<code>$1</code>');

    // URLs
    formatted = formatted.replace(
        /(https?:\/\/[^\s<]+)/g,
        '<a href="$1" target="_blank" rel="noopener">$1</a>'
    );

    // Newlines
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
}

function showViewer() {
    el.uploadSection.style.display = 'none';
    el.viewerSection.style.display = 'flex';

    const user = decryptedData.user;
    el.viewerUser.innerHTML = `
        <div>👤 ${escape(user.first_name)} ${escape(user.last_name || '')}</div>
        <div style="font-size: 12px; color: var(--text-muted)">@${user.username || user.phone || 'Unknown'}</div>
    `;

    el.viewerDialogs.innerHTML = decryptedData.dialogs.map((d, i) => `
        <div class="viewer-dialog" data-index="${i}">
            <div class="viewer-dialog-name">${escape(d.name)}</div>
            <div class="viewer-dialog-count">${d.messages.length} сообщений</div>
        </div>
    `).join('');

    el.viewerDialogs.querySelectorAll('.viewer-dialog').forEach(item => {
        item.onclick = () => {
            el.viewerDialogs.querySelectorAll('.viewer-dialog').forEach(d => d.classList.remove('active'));
            item.classList.add('active');
            showDialog(parseInt(item.dataset.index));
        };
    });
}

function showDialog(index) {
    currentDialogIndex = index;
    const dialog = decryptedData.dialogs[index];
    el.chatTitle.textContent = dialog.name;
    el.btnSearch.style.display = 'block';

    el.viewerMessages.innerHTML = dialog.messages.map((m, i) => `
        <div class="viewer-message ${m.is_outgoing ? 'outgoing' : 'incoming'}" data-index="${i}">
            ${m.sender_name ? `<div class="viewer-message-sender">${escape(m.sender_name)}</div>` : ''}
            <div class="viewer-message-text">${formatText(m.text) || (m.has_media ? `[${m.media_type || 'Media'}]` : '')}</div>
            <div class="viewer-message-time">${formatTime(m.date)}</div>
        </div>
    `).join('');

    el.viewerMessages.scrollTop = el.viewerMessages.scrollHeight;
    closeSearch();
}

// Search functionality
el.btnSearch?.addEventListener('click', openSearch);
el.searchClose?.addEventListener('click', closeSearch);
el.searchPrev?.addEventListener('click', () => navigateSearch(-1));
el.searchNext?.addEventListener('click', () => navigateSearch(1));
el.searchInput?.addEventListener('input', performSearch);

function openSearch() {
    el.searchContainer.style.display = 'flex';
    el.btnSearch.style.display = 'none';
    el.searchInput.focus();
}

function closeSearch() {
    el.searchContainer.style.display = 'none';
    if (currentDialogIndex >= 0) {
        el.btnSearch.style.display = 'block';
    }
    el.searchInput.value = '';
    el.searchCount.textContent = '';
    clearHighlights();
    searchMatches = [];
}

function performSearch() {
    clearHighlights();
    const query = el.searchInput.value.toLowerCase().trim();
    if (!query || currentDialogIndex < 0) {
        el.searchCount.textContent = '';
        searchMatches = [];
        return;
    }

    const dialog = decryptedData.dialogs[currentDialogIndex];
    searchMatches = [];

    dialog.messages.forEach((m, i) => {
        if (m.text && m.text.toLowerCase().includes(query)) {
            searchMatches.push(i);
        }
    });

    el.searchCount.textContent = searchMatches.length ? `${searchMatches.length} found` : '0';

    searchMatches.forEach(index => {
        const msgEl = el.viewerMessages.querySelector(`[data-index="${index}"]`);
        if (msgEl) msgEl.classList.add('search-highlight');
    });

    if (searchMatches.length > 0) {
        currentSearchIndex = 0;
        scrollToMatch(0);
    }
}

function navigateSearch(dir) {
    if (searchMatches.length === 0) return;
    currentSearchIndex = (currentSearchIndex + dir + searchMatches.length) % searchMatches.length;
    scrollToMatch(currentSearchIndex);
}

function scrollToMatch(index) {
    const msgIndex = searchMatches[index];
    const msgEl = el.viewerMessages.querySelector(`[data-index="${msgIndex}"]`);
    if (msgEl) {
        msgEl.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Flash effect
        msgEl.classList.add('search-current');
        setTimeout(() => msgEl.classList.remove('search-current'), 1000);
    }
    el.searchCount.textContent = `${index + 1}/${searchMatches.length}`;
}

function clearHighlights() {
    el.viewerMessages.querySelectorAll('.search-highlight').forEach(el => {
        el.classList.remove('search-highlight', 'search-current');
    });
}
