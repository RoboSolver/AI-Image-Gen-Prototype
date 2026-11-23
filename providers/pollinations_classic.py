import requests
import time
import random
from typing import List, Dict, Any
from providers.base_provider import BaseProvider, GenerationResult

class PollinationsClassicProvider(BaseProvider):
    """Anonymous Pollinations API (no key required, separate rate limits)"""
    name = "pollinations-classic"
    display_name = "Pollinations (Classic/Anonymous)"
    requires_key = False
    free_models = ["flux"]
    
    BASE_URL = "https://image.pollinations.ai/prompt/"
    
    # HTTP status codes that warrant a retry
    RETRY_STATUS_CODES = {400, 402, 408, 429, 500, 502, 503, 504}
    MAX_RETRIES = 5
    BASE_RETRY_DELAY = 10.0  # seconds (classic API: 1 per 45s)
    
    STYLE_MAP = {
        'realistic': 'photorealistic, 8k, highly detailed, professional photography',
        'cartoon': 'cartoon style, vibrant colors, cel shaded, animated',
        'anime': 'anime style, manga, japanese animation, detailed',
        'pixel': 'pixel art, 16-bit, retro gaming, crisp pixels',
        'oil': 'oil painting, classical art, textured brushstrokes',
        'watercolor': 'watercolor painting, soft edges, artistic',
        'sketch': 'pencil sketch, hand drawn, artistic drawing',
        '3d': '3d render, octane render, unreal engine 5, volumetric lighting',
    }
    
    ASPECT_RATIOS = {
        '1:1': (768, 768),
        '16:9': (768, 432),
        '9:16': (432, 768),
        '4:3': (768, 576),
        '3:4': (576, 768),
        '21:9': (768, 330),
        '9:21': (330, 768),
    }
    
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-Image-Generator/1.0'
        })
    
    def is_available(self) -> bool:
        try:
            resp = self.session.head(self.BASE_URL, timeout=5)
            return resp.status_code < 500
        except requests.RequestException:
            return False
    
    def _build_prompt(self, prompt: str, style: str) -> str:
        style_suffix = self.STYLE_MAP.get(style, '')
        if style_suffix:
            return f"{prompt}, {style_suffix}"
        return prompt
    
    def _parse_resolution(self, resolution: str) -> tuple:
        try:
            w, h = resolution.lower().split('x')
            return int(w), int(h)
        except (ValueError, AttributeError):
            return 768, 768
    
    def _generate_single_image(self, url: str, params: Dict, attempt: int, base_seed: int = None) -> tuple:
        """Generate a single image with retry logic. Returns (success, content_or_error)."""
        if attempt > 0 and base_seed is not None:
            params = params.copy()
            new_seed = (base_seed + attempt * 1000 + random.randint(1, 1000)) % 2147483647
            if new_seed == 0:
                new_seed = 1
            params['seed'] = new_seed
        
        try:
            resp = self.session.get(url, params=params, timeout=90)
            
            if resp.status_code == 200:
                return True, resp.content
            
            # Check for rate limit in 402 response
            is_rate_limit = False
            if resp.status_code == 402:
                try:
                    error_data = resp.json()
                    error_msg = error_data.get('error', {}).get('message', '').lower()
                    error_code = error_data.get('error', {}).get('code', '').lower()
                    if 'free_limit' in error_code or 'rate limit' in error_msg or 'every 45' in error_msg:
                        is_rate_limit = True
                except:
                    pass
            
            # Non-retryable errors
            if resp.status_code == 402 and not is_rate_limit:
                return False, "Payment required. Add credits at enter.pollinations.ai"
            elif resp.status_code == 403:
                return False, "Access forbidden"
            
            # Retryable errors (including rate limits)
            if (resp.status_code in self.RETRY_STATUS_CODES or is_rate_limit) and attempt < self.MAX_RETRIES:
                delay = self.BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 5.0)
                time.sleep(delay)
                return self._generate_single_image(url, params, attempt + 1, base_seed)
            
            if is_rate_limit:
                return False, "Rate limited (anonymous). Wait 45s between requests."
            
            return False, f"HTTP {resp.status_code}"
            
        except requests.Timeout:
            if attempt < self.MAX_RETRIES:
                delay = self.BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 5.0)
                time.sleep(delay)
                return self._generate_single_image(url, params, attempt + 1, base_seed)
            return False, "Timeout"
        except requests.RequestException as e:
            if attempt < self.MAX_RETRIES:
                delay = self.BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 5.0)
                time.sleep(delay)
                return self._generate_single_image(url, params, attempt + 1, base_seed)
            return False, str(e)
    
    def generate(self, prompt: str, options: Dict[str, Any]) -> GenerationResult:
        num_images = min(max(options.get('num_images', 1), 1), 4)  # Classic API: max 4
        aspect_ratio = options.get('aspect_ratio', '1:1')
        style = options.get('style', 'realistic')
        resolution = options.get('resolution', '768x768')
        
        width, height = self.ASPECT_RATIOS.get(aspect_ratio, self._parse_resolution(resolution))
        full_prompt = self._build_prompt(prompt, style)
        
        images = []
        errors = []
        
        base_seed = options.get('seed')
        if base_seed is None:
            base_seed = random.randint(1, 2147483647)
        
        for i in range(num_images):
            seed = base_seed + i
            
            params = {
                'width': width,
                'height': height,
                'seed': seed,
                'nologo': 'false',  # Classic API always has logo
                'safe': 'false',
            }
            
            url = f"{self.BASE_URL}{requests.utils.quote(full_prompt)}"
            
            success, result = self._generate_single_image(url, params, 0, seed)
            
            if success:
                images.append(result)
            else:
                errors.append(f"Image {i+1}: {result}")
                if "Rate limited" in result:
                    break
        
        if images:
            return GenerationResult(
                success=True,
                images=images,
                provider=self.name,
                metadata={
                    'prompt': full_prompt,
                    'model': 'flux',
                    'width': width,
                    'height': height,
                    'count': len(images)
                }
            )
        else:
            return GenerationResult(
                success=False,
                images=[],
                error="; ".join(errors) if errors else "Generation failed",
                provider=self.name
            )