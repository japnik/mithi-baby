// Logger Utility
const Logger = {
    logs: [],

    log(message, data = null) {
        const entry = {
            timestamp: new Date().toISOString(),
            type: 'INFO',
            message,
            data
        };
        this.save(entry);
        console.log(`[MyLori] ${message}`, data || '');
    },

    error(message, error) {
        const entry = {
            timestamp: new Date().toISOString(),
            type: 'ERROR',
            message,
            data: error ? { message: error.message, stack: error.stack } : null
        };
        this.save(entry);
        console.error(`[MyLori] ❌ ${message}`, error || '');
    },

    save(entry) {
        this.logs.push(entry);
        // Keep last 100 logs
        if (this.logs.length > 100) this.logs.shift();
        localStorage.setItem('mylori_debug_logs', JSON.stringify(this.logs));

        // Send to Backend
        fetch('/api/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry)
        }).catch(err => console.error('Failed to send log to backend', err));
    },

    getLogs() {
        return JSON.parse(localStorage.getItem('mylori_debug_logs') || '[]');
    },

    clear() {
        this.logs = [];
        localStorage.removeItem('mylori_debug_logs');
    }
};

// Lyrics History Manager
const LyricsHistory = {
    save(lyrics, babyName, occasion) {
        const history = this.getAll();
        const entry = {
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
            babyName,
            occasion,
            title: lyrics.title,
            text: lyrics.text,
            prompt: lyrics.prompt
        };
        history.unshift(entry); // Add to top
        localStorage.setItem('mylori_lyrics_history', JSON.stringify(history));
        Logger.log('Lyrics saved to history', { title: lyrics.title });
        return entry;
    },

    getAll() {
        return JSON.parse(localStorage.getItem('mylori_lyrics_history') || '[]');
    }
};

// Make globally available
window.Logger = Logger;
window.LyricsHistory = LyricsHistory;
