from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class GenerationResult:
    success: bool
    images: List[bytes]
    error: Optional[str] = None
    provider: Optional[str] = None
    metadata: Optional[Dict] = None

class BaseProvider(ABC):
    name: str = "base"
    display_name: str = "Base Provider"
    requires_key: bool = False
    free_models: List[str] = []
    
    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def generate(self, prompt: str, options: Dict[str, Any]) -> GenerationResult:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    def get_models(self) -> List[str]:
        return self.free_models
    
    def validate_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        return options