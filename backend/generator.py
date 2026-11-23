from typing import Dict, Any, List, Optional
from backend.provider_manager import ProviderManager
from backend.database import Database
from backend.image_manager import ImageManager
from providers.base_provider import GenerationResult

class GenerationManager:
    def __init__(self, database: Database, settings_manager, image_manager: ImageManager):
        self.db = database
        self.settings = settings_manager
        self.image_mgr = image_manager
        self.provider_mgr = ProviderManager(settings_manager)
    
    def refresh_providers(self):
        """Refresh providers after settings change (e.g., API key update)"""
        self.provider_mgr.reload_providers()
    
    def _get_provider_chain(self, provider_name: str) -> List:
        """Get ordered list of providers to try"""
        chain = []
        
        if provider_name == 'auto':
            # Auto mode: try all available providers in order
            chain = self.provider_mgr.get_available_providers()
        else:
            # Specific provider: start with it
            provider = self.provider_mgr.get_provider(provider_name)
            if provider and provider.is_available():
                chain.append(provider)
            
            # Add fallbacks if auto_provider is enabled
            if self.settings.get('auto_provider', True):
                fallbacks = [p for p in self.provider_mgr.get_available_providers() if p != provider]
                chain.extend(fallbacks)
        
        return chain
    
    def _try_generate(self, provider, prompt: str, options: Dict[str, Any]):
        """Try generation with a provider, return result or None"""
        try:
            result: GenerationResult = provider.generate(prompt, options)
            return result
        except Exception as e:
            return GenerationResult(
                success=False,
                images=[],
                error=f'{provider.display_name}: {str(e)}',
                provider=provider.name
            )
    
    def _save_result(self, prompt: str, result: GenerationResult, options: Dict[str, Any], fallback_used: bool = False):
        """Save successful generation result"""
        saved_images = self.image_mgr.save_images(prompt, result.images)
        
        gen_id = self.db.add_generation(
            prompt=prompt,
            provider=result.provider or provider.name,
            style=options.get('style'),
            aspect_ratio=options.get('aspect_ratio'),
            resolution=options.get('resolution'),
            num_images=len(result.images),
            images=[img['url'] for img in saved_images]
        )
        
        return {
            'success': True,
            'generation_id': gen_id,
            'images': saved_images,
            'provider': result.provider,
            'metadata': result.metadata,
            'fallback': fallback_used
        }
    
    def generate(self, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        provider_name = options.get('provider', self.settings.get('default_provider', 'pollinations'))
        
        provider_chain = self._get_provider_chain(provider_name)
        
        if not provider_chain:
            return {'success': False, 'error': 'No available providers'}
        
        last_error = None
        for i, provider in enumerate(provider_chain):
            result = self._try_generate(provider, prompt, options)
            
            if result.success and result.images:
                return self._save_result(prompt, result, options, fallback_used=(i > 0))
            
            last_error = result.error
            # Continue to next provider in chain
        
        return {
            'success': False,
            'error': last_error or 'All providers failed',
            'provider': provider_name
        }
    
    def get_provider_status(self) -> List[Dict]:
        return self.provider_mgr.get_provider_status()