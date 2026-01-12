const api = {
    async getSessions() {
        return (await fetch('/api/sessions')).json();
    },

    async getUser(sid) {
        return (await fetch(`/api/user/${sid}`)).json();
    },

    async getDialogs(sid, limit = 50) {
        return (await fetch(`/api/dialogs/${sid}?limit=${limit}`)).json();
    },

    async getMessages(sid, did, limit = 50) {
        return (await fetch(`/api/messages/${sid}/${did}?limit=${limit}`)).json();
    },

    async backupStatus(sid) {
        const res = await fetch(`/api/backup/status/${sid}`);
        if (!res.ok) return { configured: false, has_backup: false };
        return res.json();
    },

    async backup(sid, dialogIds = null, messagesLimit = 50) {
        const res = await fetch(`/api/backup/${sid}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dialog_ids: dialogIds, messages_limit: messagesLimit })
        });
        if (!res.ok) throw new Error((await res.json()).detail || 'Backup failed');
        return res.json();
    },

    async deleteBackup(telegramId) {
        const res = await fetch(`/api/backup/${telegramId}`, { method: 'DELETE' });
        return res.json();
    },

    async exportLocal(sid, dialogIds, messagesLimit, password) {
        const res = await fetch(`/api/export/${sid}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dialog_ids: dialogIds, messages_limit: messagesLimit, password })
        });
        if (!res.ok) throw new Error((await res.json()).detail || 'Export failed');
        return res.blob();
    },

    async getSavedData(telegramId) {
        const res = await fetch(`/api/saved/${telegramId}`);
        if (!res.ok) return null;
        return res.json();
    },

    async getSavedMessages(telegramId, dialogId) {
        return (await fetch(`/api/saved/${telegramId}/messages/${dialogId}`)).json();
    },

    userPhoto: (sid, uid) => `/api/photo/${sid}/user/${uid}`,
    dialogPhoto: (sid, did) => `/api/photo/${sid}/dialog/${did}`,
    messageMedia: (sid, did, mid) => `/api/media/${sid}/${did}/${mid}`
};

export default api;
