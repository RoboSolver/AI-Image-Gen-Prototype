const API_BASE = '';

class HistoryPage {
    constructor() {
        this.initElements();
        this.bindEvents();
        this.loadTheme();
        this.loadHistory();
    }

    initElements() {
        this.historyList = document.getElementById('historyList');
        this.historyEmpty = document.getElementById('historyEmpty');
        this.historyLoading = document.getElementById('historyLoading');
        this.clearHistory = document.getElementById('clearHistory');
        this.themeToggle = document.getElementById('themeToggle');
    }

    bindEvents() {
        this.clearHistory.addEventListener('click', () => this.clearAllHistory());
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
    }

    async loadHistory() {
        try {
            const res = await fetch(`${API_BASE}/api/history?limit=100`);
            const generations = await res.json();
            
            this.historyLoading.style.display = 'none';
            
            if (generations.length === 0) {
                this.historyEmpty.style.display = 'block';
                return;
            }
            
            this.historyList.innerHTML = generations.map(gen => this.renderGeneration(gen)).join('');
        } catch (err) {
            this.historyLoading.textContent = `Error loading history: ${err.message}`;
        }
    }

    renderGeneration(gen) {
        let images = [];
        try {
            images = JSON.parse(gen.images_json || '[]');
        } catch (e) {
            images = [];
        }
        
        const date = new Date(gen.created_at).toLocaleString();
        const meta = [
            gen.provider,
            gen.style,
            gen.aspect_ratio,
            gen.resolution,
            `${gen.num_images} img`
        ].filter(Boolean).join(' • ');
        
        const imagesHtml = images.map(url => `
            <img src="${url}" alt="Generated image" loading="lazy" onclick="window.open('${url}', '_blank')">
        `).join('');
        
        return `
            <div class="history-item">
                <div class="history-item-header">
                    <div class="history-item-prompt">${this.escapeHtml(gen.prompt)}</div>
                    <div class="history-item-meta">${meta}</div>
                </div>
                <div class="history-item-images">${imagesHtml}</div>
                <div class="history-item-actions">
                    <span style="flex:1; color: var(--fg-secondary); font-size: 0.8rem;">${date}</span>
                    <button class="btn btn-danger btn-small" onclick="historyPage.deleteGeneration(${gen.id})">Delete</button>
                </div>
            </div>
        `;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async deleteGeneration(id) {
        if (!confirm('Delete this generation from history?')) return;
        
        try {
            const res = await fetch(`${API_BASE}/api/history/${id}`, { method: 'DELETE' });
            const result = await res.json();
            if (result.success) {
                this.loadHistory();
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    }

    async clearAllHistory() {
        if (!confirm('Delete ALL generation history? This cannot be undone.')) return;
        
        try {
            const res = await fetch(`${API_BASE}/api/history/clear`, { method: 'POST' });
            const result = await res.json();
            if (result.success) {
                this.loadHistory();
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    }

    toggleTheme() {
        const current = document.body.dataset.theme;
        const themes = ['dark', 'light'];
        const next = themes[(themes.indexOf(current) + 1) % themes.length];
        document.body.dataset.theme = next;
        localStorage.setItem('theme', next);
    }

    loadTheme() {
        const saved = localStorage.getItem('theme');
        if (saved) {
            document.body.dataset.theme = saved;
        } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.dataset.theme = 'dark';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.historyPage = new HistoryPage();
});