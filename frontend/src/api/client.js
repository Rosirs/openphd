const BASE = '';
export const api = {
    async listTools(userId) {
        const r = await fetch(`${BASE}/tools/catalog?user_id=${encodeURIComponent(userId)}`);
        if (!r.ok)
            throw new Error(`catalog failed: ${r.status}`);
        const body = await r.json();
        return body.tools;
    },
    async createConversation(userId, title = 'New chat') {
        const r = await fetch(`${BASE}/chat/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, title }),
        });
        if (!r.ok)
            throw new Error(`create conv failed: ${r.status}`);
        const body = await r.json();
        return body.session;
    },
    async listConversations(userId) {
        const r = await fetch(`${BASE}/chat/conversations?user_id=${encodeURIComponent(userId)}`);
        if (!r.ok)
            throw new Error(`list conv failed: ${r.status}`);
        const body = await r.json();
        return body.conversations;
    },
    async previewPrompt(name, systemPrompt, subTools) {
        const r = await fetch(`${BASE}/canvas/preview-prompt`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, system_prompt: systemPrompt, sub_tools: subTools }),
        });
        if (!r.ok)
            throw new Error(`preview failed: ${r.status}`);
        const body = await r.json();
        return body.augmented_system_prompt;
    },
    async saveComposite(userId, def) {
        const r = await fetch(`${BASE}/canvas/composite?user_id=${encodeURIComponent(userId)}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(def),
        });
        if (!r.ok)
            throw new Error(`save composite failed: ${r.status}`);
        const body = await r.json();
        return body.tool;
    },
    /**
     * Subscribe to chat messages via SSE.
     * Yields each parsed event. Closes the connection when the
     * stream reports a 'message_completed' or 'error' event.
     */
    subscribeMessages(userId, conversationId, content) {
        const ctrl = new AbortController();
        const stream = async function* () {
            const r = await fetch(`${BASE}/chat/conversations/${conversationId}/messages?user_id=${encodeURIComponent(userId)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }), signal: ctrl.signal });
            if (!r.ok || !r.body)
                throw new Error(`message failed: ${r.status}`);
            const reader = r.body.getReader();
            const dec = new TextDecoder();
            let buf = '';
            while (true) {
                const { value, done } = await reader.read();
                if (done)
                    break;
                buf += dec.decode(value, { stream: true });
                const parts = buf.split('\n\n');
                buf = parts.pop() || '';
                for (const part of parts) {
                    let type = '';
                    let data = {};
                    for (const line of part.split('\n')) {
                        if (line.startsWith('event: '))
                            type = line.slice(7).trim();
                        else if (line.startsWith('data: ')) {
                            try {
                                data = JSON.parse(line.slice(6));
                            }
                            catch { /* ignore */ }
                        }
                    }
                    if (type)
                        yield { type, ...data };
                }
            }
        };
        return { stream: stream(), close: () => ctrl.abort() };
    },
};
export const onboardApi = {
    async getStatus() {
        const r = await fetch(`${BASE}/onboard/status`);
        if (!r.ok)
            throw new Error(`status failed: ${r.status}`);
        return r.json();
    },
    async save(body) {
        const r = await fetch(`${BASE}/onboard/save`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!r.ok)
            throw new Error(`save failed: ${r.status}`);
        return r.json();
    },
    async test(body) {
        const r = await fetch(`${BASE}/onboard/test`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!r.ok)
            throw new Error(`test failed: ${r.status}`);
        return r.json();
    },
    async skip() {
        const r = await fetch(`${BASE}/onboard/skip`, { method: 'POST' });
        if (!r.ok)
            throw new Error(`skip failed: ${r.status}`);
        return r.json();
    },
};
