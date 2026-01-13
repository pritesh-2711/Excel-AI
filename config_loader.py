import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self, config_path: str = None):
        # Load environment variables from .env file
        load_dotenv()
        
        if config_path is None:
            # Get directory where this script is located
            script_dir = Path(__file__).parent
            config_path = script_dir / "config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.config['llm_providers'].keys())
    
    def get_provider_display_name(self, provider: str) -> str:
        """Get display name for provider"""
        return self.config['llm_providers'][provider].get('display_name', provider)
    
    def get_models(self, provider: str) -> List[str]:
        """Get available models for a provider"""
        return self.config['llm_providers'][provider]['models']
    
    def get_base_url(self, provider: str) -> Optional[str]:
        """Get base URL for provider if applicable"""
        return self.config['llm_providers'][provider].get('base_url')
    
    def requires_api_key(self, provider: str) -> bool:
        """Check if provider requires API key"""
        return self.config['llm_providers'][provider].get('requires_api_key', False)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key from environment variable"""
        env_var = self.config['llm_providers'][provider].get('env_var')
        if env_var:
            return os.getenv(env_var)
        return None
    
    def get_api_version(self, provider: str) -> Optional[str]:
        """Get API version for provider (Azure)"""
        return self.config['llm_providers'][provider].get('api_version')
    
    def get_endpoint(self, provider: str) -> Optional[str]:
        """Get endpoint from environment variable (Azure)"""
        env_var = self.config['llm_providers'][provider].get('endpoint_env_var')
        if env_var:
            return os.getenv(env_var)
        return None