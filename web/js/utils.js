const initial = (name) => name ? name.charAt(0).toUpperCase() : '?';

const escape = (text) => {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
};

const formatTime = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    const today = new Date().toDateString() === d.toDateString();
    return today
        ? d.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
        : d.toLocaleDateString('ru', { day: 'numeric', month: 'short' });
};

const formatMsg = (iso) => {
    if (!iso) return '';
    return new Date(iso).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' });
};

const formatTelegramText = (text, entities) => {
    if (!text) return '';
    if (!entities || !entities.length) return escape(text);

    const chars = [...text];
    const tags = [];

    entities.sort((a, b) => a.offset - b.offset);

    for (const e of entities) {
        let open = '', close = '';

        switch (e.type) {
            case 'bold':
                open = '<b>'; close = '</b>'; break;
            case 'italic':
                open = '<i>'; close = '</i>'; break;
            case 'code':
                open = '<code>'; close = '</code>'; break;
            case 'pre':
                open = '<pre>'; close = '</pre>'; break;
            case 'strike':
                open = '<s>'; close = '</s>'; break;
            case 'underline':
                open = '<u>'; close = '</u>'; break;
            case 'text_url':
                open = `<a href="${escape(e.url)}" target="_blank" rel="noopener">`;
                close = '</a>'; break;
            case 'url':
                const url = text.slice(e.offset, e.offset + e.length);
                open = `<a href="${escape(url)}" target="_blank" rel="noopener">`;
                close = '</a>'; break;
            case 'mention':
                open = '<span class="mention">'; close = '</span>'; break;
            case 'hashtag':
                open = '<span class="hashtag">'; close = '</span>'; break;
        }

        if (open) {
            tags.push({ pos: e.offset, tag: open, isOpen: true });
            tags.push({ pos: e.offset + e.length, tag: close, isOpen: false });
        }
    }

    tags.sort((a, b) => {
        if (a.pos !== b.pos) return b.pos - a.pos;
        return a.isOpen ? 1 : -1;
    });

    let result = chars.map(c => escape(c)).join('');

    const charOffsets = [];
    let htmlPos = 0;
    for (let i = 0; i < chars.length; i++) {
        charOffsets[i] = htmlPos;
        htmlPos += escape(chars[i]).length;
    }
    charOffsets[chars.length] = htmlPos;

    for (const t of tags) {
        const insertPos = charOffsets[t.pos] || result.length;
        result = result.slice(0, insertPos) + t.tag + result.slice(insertPos);

        for (let i = t.pos; i <= chars.length; i++) {
            if (charOffsets[i] !== undefined) {
                charOffsets[i] += t.tag.length;
            }
        }
    }

    return result;
};

export { initial, escape, formatTime, formatMsg, formatTelegramText };

