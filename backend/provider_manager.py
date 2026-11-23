import os
from typing import Dict, List, Optional
from providers.base_provider import BaseProvider
from providers.pollinations import PollinationsProvider
from providers.pollinations_classic import PollinationsClassicProvider
from providers.stability import StabilityAIProvider

class ProviderManager:
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self._providers: Dict[str, BaseProvider] = {}
        self._init_providers()
    
    def _get_pollinations_key(self) -> str:
        key = self.settings.get('pollinations_api_key', '').strip()
        if key:
            return key
        return os.getenv('POLLINATIONS_API_KEY', '').strip()
    
    def _get_stability_key(self) -> str:
        key = self.settings.get('stability_api_key', '').strip()
        if key:
            return key
        return os.getenv('STABILITY_API_KEY', '').strip()
    
    def _init_providers(self):
        pollinations_key = self._get_pollinations_key()
        self._providers['pollinations'] = PollinationsProvider(api_key=pollinations_key if pollinations_key else None)
        self._providers['pollinations-classic'] = PollinationsClassicProvider()
        
        stability_key = self._get_stability_key()
        self._providers['stability'] = StabilityAIProvider(api_key=stability_key if stability_key else None)
    
    def reload_providers(self):
        """Reload providers with current settings (e.g., after API key change)"""
        self._init_providers()
    
    def get_provider(self, name: str) -> Optional[BaseProvider]:
        return self._providers.get(name)
    
    def get_all_providers(self) -> Dict[str, BaseProvider]:
        return self._providers.copy()
    
    def get_available_providers(self) -> List[BaseProvider]:
        # Order: Stability (fast, has key) -> Pollinations Classic (free but slow) -> Pollinations (no credits)
        priority = {'stability': 0, 'pollinations-classic': 1, 'pollinations': 2}
        available = [p for p in self._providers.values() if p.is_available()]
        return sorted(available, key=lambda p: priority.get(p.name, 99))
    
    def get_provider_status(self) -> List[Dict]:
        status = []
        for name, provider in self._providers.items():
            available = provider.is_available()
            status.append({
                'name': name,
                'display_name': provider.display_name,
                'available': available,
                'requires_key': provider.requires_key,
                'has_key': bool(provider.api_key),
                'free_models': provider.free_models,
            })
        return status
    
    def get_default_provider(self) -> Optional[BaseProvider]:
        default_name = self.settings.get('default_provider', 'pollinations')
        provider = self.get_provider(default_name)
        if provider and provider.is_available():
            return provider
        return self.get_available_providers()[0] if self.get_available_providers() else None
    
    def get_fallback_provider(self, failed_provider: str) -> Optional[BaseProvider]:
        if not self.settings.get('auto_provider', True):
            return None
        for name, provider in self._providers.items():
            if name != failed_provider and provider.is_available():
                return provider
        return None