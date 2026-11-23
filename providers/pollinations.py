import requests
import time
import random
from typing import List, Dict, Any
from providers.base_provider import BaseProvider, GenerationResult

class PollinationsProvider(BaseProvider):
    name = "pollinations"
    display_name = "Pollinations (FLUX)"
    requires_key = False
    free_models = ["flux", "turbo", "kontext", "gptimage"]
    
    BASE_URL = "https://image.pollinations.ai/prompt/"
    API_URL = "https://gen.pollinations.ai/image/"
    
    # HTTP status codes that warrant a retry
    RETRY_STATUS_CODES = {400, 408, 429, 500, 502, 503, 504}
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 1.0  # seconds
    
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
        '1:1': (1024, 1024),
        '16:9': (1024, 576),
        '9:16': (576, 1024),
        '4:3': (1024, 768),
        '3:4': (768, 1024),
        '21:9': (1024, 440),
        '9:21': (440, 1024),
    }
    
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-Image-Generator/1.0'
        })
        # Don't set Authorization header - use key query param instead
    
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
            return 1024, 1024
    
    def _generate_single_image(self, url: str, params: Dict, attempt: int, base_seed: int = None) -> tuple:
        """Generate a single image with retry logic. Returns (success, content_or_error)."""
        # Use different seed on each retry to avoid stuck 400 errors
        if attempt > 0 and base_seed is not None:
            params = params.copy()
            # Keep seed within API limits (max 2147483647)
            new_seed = (base_seed + attempt * 1000 + random.randint(1, 1000)) % 2147483647
            if new_seed == 0:
                new_seed = 1
            params['seed'] = new_seed
        
        try:
            resp = self.session.get(url, params=params, timeout=60)
            
            if resp.status_code == 200:
                return True, resp.content
            
            # Non-retryable errors
            if resp.status_code == 401:
                return False, "Invalid API key"
            elif resp.status_code == 402:
                # Check response body to distinguish rate limit vs insufficient balance
                try:
                    error_data = resp.json()
                    error_msg = error_data.get('error', {}).get('message', '').lower()
                    if 'insufficient balance' in error_msg or 'balance is $0' in error_msg:
                        return False, "Insufficient credits. Add credits at enter.pollinations.ai or use anonymous mode."
                    else:
                        return False, "Rate limited (free tier). Wait 45s or add API key."
                except:
                    return False, "Rate limited (free tier). Wait 45s or add API key."
            elif resp.status_code == 403:
                return False, "Access forbidden"
            elif resp.status_code == 404:
                return False, "Model not found"
            
            # Retryable errors
            if resp.status_code in self.RETRY_STATUS_CODES and attempt < self.MAX_RETRIES:
                delay = self.BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(delay)
                return self._generate_single_image(url, params, attempt + 1, base_seed)
            
            return False, f"HTTP {resp.status_code}"
            
        except requests.Timeout:
            if attempt < self.MAX_RETRIES:
                delay = self.BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(delay)
                return self._generate_single_image(url, params, attempt + 1, base_seed)
            return False, "Timeout"
        except requests.RequestException as e:
            if attempt < self.MAX_RETRIES:
                delay = self.BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(delay)
                return self._generate_single_image(url, params, attempt + 1, base_seed)
            return False, str(e)
    
    def generate(self, prompt: str, options: Dict[str, Any]) -> GenerationResult:
        num_images = min(max(options.get('num_images', 1), 1), 9)
        aspect_ratio = options.get('aspect_ratio', '1:1')
        style = options.get('style', 'realistic')
        resolution = options.get('resolution', '1024x1024')
        model = options.get('model', 'flux')
        
        # Use resolution for actual pixel dimensions, aspect ratio for reference
        width, height = self._parse_resolution(resolution)
        
        full_prompt = self._build_prompt(prompt, style)
        
        images = []
        errors = []
        
        base_seed = options.get('seed')
        if base_seed is None:
            base_seed = random.randint(1, 2147483647)  # Max 32-bit signed int for API
        
        for i in range(num_images):
            seed = base_seed + i
            
            params = {
                'width': width,
                'height': height,
                'seed': seed,
                'model': model,
                'nologo': 'true' if self.api_key else 'false',
                'safe': 'false',
            }
            if self.api_key:
                params['key'] = self.api_key
            
            url = f"{self.API_URL}{requests.utils.quote(full_prompt)}"
            
            success, result = self._generate_single_image(url, params, 0, seed)
            
            if success:
                images.append(result)
            else:
                errors.append(f"Image {i+1}: {result}")
                # If it's a non-retryable error (like 401, 402), stop trying
                if "Invalid API key" in result or "Rate limited" in result or "Access forbidden" in result:
                    break
        
        if images:
            return GenerationResult(
                success=True,
                images=images,
                provider=self.name,
                metadata={
                    'prompt': full_prompt,
                    'model': model,
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