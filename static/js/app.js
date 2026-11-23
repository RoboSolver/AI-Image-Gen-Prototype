const API_BASE = '';

// Random prompt templates - categorized for variety
const RANDOM_PROMPTS = [
    // Photorealistic / Cinematic
    "A majestic lion in a cyberpunk city, neon lights, rain, photorealistic, 8k",
    "An elderly watchmaker in his workshop, dramatic lighting, hyperrealistic, 8k",
    "A lighthouse during a storm, massive waves crashing, cinematic, photorealistic",
    "A vintage car on Route 66 at golden hour, dust particles, cinematic lighting",
    "A portrait of a cyberpunk hacker, neon reflections in glasses, rain, 8k",
    
    // Fantasy / Magical
    "A magical forest with bioluminescent plants, fantasy art, ethereal, glowing",
    "An ancient tree with a door built into its trunk, fairy tale, magical, detailed",
    "A floating island with a waterfall pouring into clouds, fantasy landscape, epic",
    "A celestial dragon made of stars and galaxies, cosmic, majestic, vibrant colors",
    "A wizard's tower reaching into the clouds, magical aura, fantasy illustration",
    "A library where books float in the air, magical realism, soft lighting, cozy",
    "A phoenix rising from ashes, fire and embers, mythological, dynamic pose",
    "An enchanted garden with glowing mushrooms and fairy lights, whimsical, detailed",
    
    // Sci-Fi / Cyberpunk
    "A futuristic cityscape with flying cars, blade runner style, neon glow, rain",
    "A cyberpunk samurai with neon katana, rain-slicked streets, dramatic lighting",
    "An astronaut riding a horse on Mars, digital art, vibrant colors, retro-futurism",
    "A robotic owl with glowing eyes, mechanical details, sci-fi aesthetic, 8k",
    "An underwater city with glass domes, marine life, rays of light, futuristic",
    "A steampunk airship floating above Victorian London, detailed, cinematic, brass",
    "A Dyson sphere under construction, massive scale, sci-fi megastructure, epic",
    "A post-apocalyptic library overtaken by nature, moss and vines, atmospheric",
    
    // Artistic Styles
    "A Japanese cherry blossom garden with a traditional tea house, serene, ukiyo-e style",
    "A cozy cabin in the woods at sunset, warm lighting, peaceful atmosphere, oil painting",
    "A vintage travel poster for a fictional planet, retro style, bold colors, art deco",
    "A ghost town in the desert at golden hour, atmospheric, haunting, watercolor",
    "A mechanical heart with gears and cogs, steampunk, intricate details, metallic",
    "A tiny mouse knight in shining armor, whimsical, storybook illustration, detailed",
    "A polar bear wearing sunglasses on a tropical beach, humorous, vibrant, pop art",
    "A still life with fruit and flowers, classical oil painting, dramatic chiaroscuro",
    
    // Nature / Landscapes
    "Aurora borealis over an Icelandic glacier, night sky, stars, photorealistic",
    "A crystal cave with glowing crystals, underground, magical lighting, fantasy",
    "A bamboo forest with sunlight filtering through, peaceful, zen, photographic",
    "A volcanic eruption at night, lava flows, lightning, dramatic, nature photography",
    "A hidden waterfall in a tropical jungle, mist, lush greenery, serene",
    
    // Character / Portrait
    "A steampunk inventor with goggles and tools, Victorian era, detailed portrait",
    "An elf archer in an ancient forest, fantasy character design, intricate armor",
    "A cyberpunk street vendor selling neon noodles, night market, atmospheric",
    "A medieval alchemist in a candlelit laboratory, mysterious, detailed, fantasy",
];

class App {
    constructor() {
        this.generating = false;
        this.initElements();
        this.bindEvents();
        this.loadTheme();
        this.loadSettings();
    }

    initElements() {
        this.prompt = document.getElementById('prompt');
        this.numImages = document.getElementById('numImages');
        this.aspectRatio = document.getElementById('aspectRatio');
        this.style = document.getElementById('style');
        this.resolution = document.getElementById('resolution');
        this.provider = document.getElementById('provider');
        this.generateBtn = document.getElementById('generateBtn');
        this.randomPromptBtn = document.getElementById('randomPromptBtn');
        this.status = document.getElementById('status');
        this.gallery = document.getElementById('gallery');
        this.emptyState = document.getElementById('emptyState');
        this.clearGallery = document.getElementById('clearGallery');
        this.themeToggle = document.getElementById('themeToggle');
    }

    bindEvents() {
        this.prompt.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.generate();
            }
        });
        this.prompt.addEventListener('input', () => this.updateGenerateBtn());
        this.generateBtn.addEventListener('click', () => this.generate());
        this.randomPromptBtn.addEventListener('click', () => this.setRandomPrompt());
        this.clearGallery.addEventListener('click', () => this.clearGalleryFn());
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
    }

    updateGenerateBtn() {
        const hasPrompt = this.prompt.value.trim().length > 0;
        this.generateBtn.disabled = !hasPrompt || this.generating;
    }

    setRandomPrompt() {
        const randomPrompt = RANDOM_PROMPTS[Math.floor(Math.random() * RANDOM_PROMPTS.length)];
        this.prompt.value = randomPrompt;
        this.updateGenerateBtn();
        this.prompt.focus();
    }

    async generate() {
        if (this.generating) return;
        const prompt = this.prompt.value.trim();
        if (!prompt) return;

        this.setGenerating(true);
        this.setStatus('Preparing generation...', 'info');

        const options = {
            num_images: parseInt(this.numImages.value) || 1,
            aspect_ratio: this.aspectRatio.value,
            style: this.style.value,
            resolution: this.resolution.value,
            provider: this.provider.value,
        };

        try {
            const response = await fetch(`${API_BASE}/api/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, ...options })
            });

            const result = await response.json();

            if (result.success) {
                this.setStatus(`Generated ${result.images.length} image(s) via ${result.provider}`, 'success');
                this.addImagesToGallery(result.images, prompt);
                this.prompt.value = '';
                this.updateGenerateBtn();
            } else {
                this.setStatus(result.error || 'Generation failed', 'error');
                if (result.fallback) {
                    this.setStatus(`Fallback used: ${result.provider}`, 'info');
                }
            }
        } catch (err) {
            this.setStatus(`Network error: ${err.message}`, 'error');
        } finally {
            this.setGenerating(false);
        }
    }

    setGenerating(generating) {
        this.generating = generating;
        this.generateBtn.disabled = generating || !this.prompt.value.trim();
        const btnText = this.generateBtn.querySelector('.btn-text');
        const btnLoading = this.generateBtn.querySelector('.btn-loading');
        if (generating) {
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline-flex';
        } else {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
        }
    }

    setStatus(message, type = 'info') {
        this.status.textContent = message;
        this.status.className = `status ${type}`;
    }

    addImagesToGallery(images, prompt) {
        this.emptyState.style.display = 'none';
        
        images.forEach((img, index) => {
            const item = document.createElement('div');
            item.className = 'gallery-item';
            item.innerHTML = `
                <img src="${img.url}" alt="${prompt} - Image ${index + 1}" loading="lazy">
                <div class="gallery-item-actions">
                    <button class="btn btn-small" onclick="app.downloadImage('${img.url}', '${img.filename}')">⬇️ Download</button>
                    <button class="btn btn-small" onclick="app.openFullImage('${img.url}')">🔍 View</button>
                </div>
            `;
            this.gallery.insertBefore(item, this.gallery.firstChild);
        });
    }

    downloadImage(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    openFullImage(url) {
        window.open(url, '_blank');
    }

    clearGalleryFn() {
        if (confirm('Clear all images from gallery?')) {
            this.gallery.innerHTML = '';
            this.emptyState.style.display = 'block';
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

    async loadSettings() {
        try {
            const res = await fetch(`${API_BASE}/api/settings`);
            const settings = await res.json();
            if (settings.default_num_images) this.numImages.value = settings.default_num_images;
            if (settings.default_aspect_ratio) this.aspectRatio.value = settings.default_aspect_ratio;
            if (settings.default_style) this.style.value = settings.default_style;
            if (settings.default_resolution) this.resolution.value = settings.default_resolution;
            if (settings.default_provider) this.provider.value = settings.default_provider;
        } catch (err) {
            console.warn('Failed to load settings:', err);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});