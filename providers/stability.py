import requests
import time
import random
from typing import List, Dict, Any
from providers.base_provider import BaseProvider, GenerationResult

class StabilityAIProvider(BaseProvider):
    """Stability AI API provider"""
    name = "stability"
    display_name = "Stability AI (SD3)"
    requires_key = True
    free_models = ["sd3", "sd3-turbo", "core"]  # Available with free credits
    
    BASE_URL = "https://api.stability.ai"
    GENERATE_ENDPOINT = "/v2beta/stable-image/generate"
    
    # HTTP status codes that warrant a retry
    RETRY_STATUS_CODES = {400, 408, 429, 500, 502, 503, 504}
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 2.0
    
    MODEL_COSTS = {
        'ultra': 8,
        'sd3': 6.5,
        'sd3-turbo': 4,
        'sd3.5-large': 6.5,
        'sd3.5-large-turbo': 4,
        'sd3.5-medium': 3.5,
        'core': 3,
    }
    
    # Default to cheaper model that works with free credits
    DEFAULT_MODEL = 'core'
    
    ASPECT_RATIOS = {
        '1:1': '1:1',
        '16:9': '16:9',
        '9:16': '9:16',
        '4:3': '4:3',
        '3:4': '3:4',
        '21:9': '21:9',
        '9:21': '9:21',
    }
    
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
    
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-Image-Generator/1.0',
            'Accept': 'image/*',
        })
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
    
    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            resp = self.session.get(f"{self.BASE_URL}/v1/user/balance", timeout=10)
            return resp.status_code == 200
        except requests.RequestException:
            return False
    
    def get_balance(self) -> Dict:
        """Get account balance/credits"""
        try:
            resp = self.session.get(f"{self.BASE_URL}/v1/user/balance", timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {}
        except requests.RequestException:
            return {}
    
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
    
    def _generate_single_image(self, url: str, data: Dict, files: Dict, attempt: int) -> tuple:
        """Generate a single image with retry logic. Returns (success, content_or_error)."""
        try:
            resp = self.session.post(url, data=data, files=files, timeout=120)
            
            if resp.status_code == 200:
                return True, resp.content
            
            # Non-retryable errors
            if resp.status_code == 401:
                return False, "Invalid API key"
            elif resp.status_code == 402:
                try:
                    error_data = resp.json()
                    error_msg = error_data.get('error', {}).get('message', '').lower()
                    if 'insufficient' in error_msg or 'credits' in error_msg:
                        return False, "Insufficient credits. Add credits at platform.stability.ai"
                    return False, "Payment required"
                except:
                    return False, "Payment required"
            elif resp.status_code == 403:
                return False, "Access forbidden"
            elif resp.status_code == 404:
                return False, "Model not found"
            
            # Retryable errors
            if resp.status_code in self.RETRY_STATUS_CODES and attempt < self.MAX_RETRIES:
                delay = self.BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1.0)
                time.sleep(delay)
                return self._generate_single_image(url, data, files, attempt + 1)
            
            # Try to parse error
            try:
                error_data = resp.json()
                error_msg = error_data.get('error', {}).get('message', f'HTTP {resp.status_code}')
                return False, error_msg
            except:
                return False, f"HTTP {resp.status_code}"
                
        except requests.Timeout:
            if attempt < self.MAX_RETRIES:
                delay = self.BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1.0)
                time.sleep(delay)
                return self._generate_single_image(url, data, files, attempt + 1)
            return False, "Timeout"
        except requests.RequestException as e:
            if attempt < self.MAX_RETRIES:
                delay = self.BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1.0)
                time.sleep(delay)
                return self._generate_single_image(url, data, files, attempt + 1)
            return False, str(e)
    
    def generate(self, prompt: str, options: Dict[str, Any]) -> GenerationResult:
        num_images = min(max(options.get('num_images', 1), 1), 9)
        aspect_ratio = options.get('aspect_ratio', '1:1')
        style = options.get('style', 'realistic')
        resolution = options.get('resolution', '1024x1024')
        model = options.get('model', self.DEFAULT_MODEL)
        
        full_prompt = self._build_prompt(prompt, style)
        aspect_ratio_param = self.ASPECT_RATIOS.get(aspect_ratio, '1:1')
        
        images = []
        errors = []
        
        for i in range(num_images):
            seed = options.get('seed')
            if seed is None:
                seed = random.randint(1, 2**32 - 1)
            else:
                seed = seed + i
            
            url = f"{self.BASE_URL}{self.GENERATE_ENDPOINT}/{model}"
            
            data = {
                'prompt': full_prompt,
                'aspect_ratio': aspect_ratio_param,
                'seed': str(seed),
                'output_format': 'png',
                'mode': 'text-to-image',
            }
            
            # Stability AI requires multipart/form-data with "none" field
            files = {'none': ''}
            
            success, result = self._generate_single_image(url, data, files, 0)
            
            if success:
                images.append(result)
            else:
                errors.append(f"Image {i+1}: {result}")
                # Stop on non-retryable errors
                if any(x in result.lower() for x in ['invalid api key', 'insufficient credits', 'access forbidden']):
                    break
        
        if images:
            return GenerationResult(
                success=True,
                images=images,
                provider=self.name,
                metadata={
                    'prompt': full_prompt,
                    'model': model,
                    'aspect_ratio': aspect_ratio_param,
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