"""
Configuration Loader

Loads and manages application configuration from YAML files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigLoader:
    """
    Configuration loader for the crawler system
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration loader
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._settings: Optional[Dict[str, Any]] = None
        self._portals: Optional[Dict[str, Any]] = None
        
        # Load environment variables
        env_file = self.config_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Load application settings from settings.yaml
        
        Returns:
            Dictionary containing settings
        """
        if self._settings is None:
            settings_file = self.config_dir / "settings.yaml"
            self._settings = self._load_yaml(settings_file)
        
        return self._settings
    
    def load_portals(self) -> Dict[str, Any]:
        """
        Load portal configurations from portals.yaml
        
        Returns:
            Dictionary containing portal configurations
        """
        if self._portals is None:
            portals_file = self.config_dir / "portals.yaml"
            self._portals = self._load_yaml(portals_file)
        
        return self._portals
    
    def get_enabled_portals(self) -> list:
        """
        Get list of enabled portals
        
        Returns:
            List of enabled portal configurations
        """
        portals_config = self.load_portals()
        portals = portals_config.get('portals', [])
        return [p for p in portals if p.get('enabled', False)]
    
    def get_portal_config(self, portal_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific portal
        
        Args:
            portal_name: Name of the portal
        
        Returns:
            Portal configuration dictionary or None if not found
        """
        portals = self.load_portals().get('portals', [])
        for portal in portals:
            if portal.get('name') == portal_name:
                return portal
        return None
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get a specific setting using dot notation
        
        Args:
            key_path: Dot-separated path to setting (e.g., 'crawler.timeout_seconds')
            default: Default value if setting not found
        
        Returns:
            Setting value or default
        """
        settings = self.load_settings()
        keys = key_path.split('.')
        
        value = settings
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_env(self, key: str, default: str = "") -> str:
        """
        Get environment variable
        
        Args:
            key: Environment variable name
            default: Default value if not found
        
        Returns:
            Environment variable value
        """
        return os.getenv(key, default)
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """
        Load YAML file
        
        Args:
            file_path: Path to YAML file
        
        Returns:
            Dictionary containing YAML data
        
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file {file_path}: {e}")
    
    def reload(self) -> None:
        """Reload all configuration files"""
        self._settings = None
        self._portals = None
        self.load_settings()
        self.load_portals()


# Global config instance
_config_instance: Optional[ConfigLoader] = None


def get_config(config_dir: str = "config") -> ConfigLoader:
    """
    Get global configuration instance
    
    Args:
        config_dir: Configuration directory path
    
    Returns:
        ConfigLoader instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader(config_dir)
    return _config_instance
