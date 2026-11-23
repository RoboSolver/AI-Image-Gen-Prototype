const API_BASE = '';

class SettingsPage {
    constructor() {
        this.initElements();
        this.bindEvents();
        this.loadTheme();
        this.loadSettings();
        this.loadStorageInfo();
        this.loadProviderStatus();
    }

    initElements() {
        this.pollinationsKey = document.getElementById('pollinationsKey');
        this.stabilityKey = document.getElementById('stabilityKey');
        this.defProvider = document.getElementById('defProvider');
        this.defAspect = document.getElementById('defAspect');
        this.defStyle = document.getElementById('defStyle');
        this.defResolution = document.getElementById('defResolution');
        this.defNumImages = document.getElementById('defNumImages');
        this.autoProvider = document.getElementById('autoProvider');
        this.theme = document.getElementById('theme');
        this.storageInfo = document.getElementById('storageInfo');
        this.cleanupBtn = document.getElementById('cleanupBtn');
        this.saveSettings = document.getElementById('saveSettings');
        this.testProvider = document.getElementById('testProvider');
        this.themeToggle = document.getElementById('themeToggle');
    }

    bindEvents() {
        document.querySelectorAll('.toggle-visibility').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetId = e.target.dataset.target;
                const input = document.getElementById(targetId);
                if (input.type === 'password') {
                    input.type = 'text';
                    e.target.textContent = '🙈';
                } else {
                    input.type = 'password';
                    e.target.textContent = '👁️';
                }
            });
        });

        this.saveSettings.addEventListener('click', () => this.save());
        this.testProvider.addEventListener('click', () => this.testProviderFn());
        this.cleanupBtn.addEventListener('click', () => this.cleanup());
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
    }

    async loadSettings() {
        try {
            const res = await fetch(`${API_BASE}/api/settings`);
            const settings = await res.json();
            
            if (settings.default_provider) this.defProvider.value = settings.default_provider;
            if (settings.default_aspect_ratio) this.defAspect.value = settings.default_aspect_ratio;
            if (settings.default_style) this.defStyle.value = settings.default_style;
            if (settings.default_resolution) this.defResolution.value = settings.default_resolution;
            if (settings.default_num_images) this.defNumImages.value = settings.default_num_images;
            if (settings.auto_provider !== undefined) this.autoProvider.checked = settings.auto_provider;
            if (settings.theme) this.theme.value = settings.theme;
            if (settings.pollinations_api_key) this.pollinationsKey.value = settings.pollinations_api_key;
            if (settings.stability_api_key) this.stabilityKey.value = settings.stability_api_key;
        } catch (err) {
            console.warn('Failed to load settings:', err);
        }
    }

    async save() {
        const settings = {
            default_provider: this.defProvider.value,
            default_aspect_ratio: this.defAspect.value,
            default_style: this.defStyle.value,
            default_resolution: this.defResolution.value,
            default_num_images: parseInt(this.defNumImages.value) || 1,
            auto_provider: this.autoProvider.checked,
            theme: this.theme.value,
            pollinations_api_key: this.pollinationsKey.value,
            stability_api_key: this.stabilityKey.value,
        };

        try {
            const res = await fetch(`${API_BASE}/api/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            const result = await res.json();
            if (result.success) {
                alert('Settings saved successfully!');
                document.body.dataset.theme = settings.theme;
                localStorage.setItem('theme', settings.theme);
            } else {
                alert('Failed to save settings');
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    }

    async testProviderFn() {
        this.testProvider.disabled = true;
        this.testProvider.textContent = 'Testing...';
        
        try {
            const res = await fetch(`${API_BASE}/api/providers`);
            const providers = await res.json();
            
            let msg = 'Provider Status:\n\n';
            providers.forEach(p => {
                msg += `${p.display_name}: ${p.available ? '✅ Available' : '❌ Unavailable'}`;
                if (p.requires_key) msg += ` (Key: ${p.has_key ? 'Set' : 'Not set'})`;
                msg += '\n';
            });
            alert(msg);
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            this.testProvider.disabled = false;
            this.testProvider.textContent = 'Test Provider';
        }
    }

    async loadStorageInfo() {
        try {
            const res = await fetch(`${API_BASE}/api/storage`);
            const info = await res.json();
            this.storageInfo.innerHTML = `
                <strong>Total Images:</strong> ${info.file_count}<br>
                <strong>Total Size:</strong> ${info.total_size_mb} MB<br>
                <strong>Location:</strong> ${info.base_path}
            `;
        } catch (err) {
            this.storageInfo.textContent = 'Failed to load storage info';
        }
    }

    async cleanup() {
        if (!confirm('Delete images older than 30 days?')) return;
        
        this.cleanupBtn.disabled = true;
        this.cleanupBtn.textContent = 'Cleaning up...';
        
        try {
            const res = await fetch(`${API_BASE}/api/cleanup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ days: 30 })
            });
            const result = await res.json();
            if (result.success) {
                alert(`Cleaned up ${result.deleted} old images`);
                this.loadStorageInfo();
            }
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            this.cleanupBtn.disabled = false;
            this.cleanupBtn.textContent = 'Cleanup Old Images (30+ days)';
        }
    }

    async loadProviderStatus() {
        // Could add a status indicator here
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
    window.settingsPage = new SettingsPage();
});