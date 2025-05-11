"""Global configuration manager for the MCP server."""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ServerConfigManager:
    """Manage global server configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        if config_path is None:
            # Default to server_config.json in the config directory
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "server_config.json"
            )
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Set up logging based on config
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded server config from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file not found at {self.config_path}, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "server": {
                "name": "Claude MCP Scaffold",
                "version": "0.3.0",
                "log_level": "INFO",
                "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "max_concurrent_requests": 10,
                "startup_timeout": 30,
                "shutdown_timeout": 10
            },
            "web_interaction": {
                "enabled": True,
                "config_file": "./web_interaction/browser_config.json"
            },
            "computer_interaction": {
                "enabled": True,
                "config_file": "./computer_interaction/computer_config.json"
            },
            "features": {
                "calculator": {"enabled": True},
                "echo": {"enabled": True},
                "server_status": {"enabled": True}
            }
        }
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        env_prefix = self.config.get("environment", {}).get("env_prefix", "MCP_")
        override_from_env = self.config.get("environment", {}).get("override_from_env", True)
        
        if not override_from_env:
            return
        
        # Server settings
        if val := os.getenv(f"{env_prefix}LOG_LEVEL"):
            self.config["server"]["log_level"] = val
        
        if val := os.getenv(f"{env_prefix}MAX_CONCURRENT_REQUESTS"):
            self.config["server"]["max_concurrent_requests"] = int(val)
        
        # Web interaction settings
        if val := os.getenv(f"{env_prefix}WEB_ENABLED"):
            self.config["web_interaction"]["enabled"] = val.lower() == "true"
        
        if val := os.getenv(f"{env_prefix}BROWSER_HEADLESS"):
            if "browser" not in self.config["web_interaction"]:
                self.config["web_interaction"]["browser"] = {}
            self.config["web_interaction"]["browser"]["headless"] = val.lower() == "true"
        
        # Computer interaction settings
        if val := os.getenv(f"{env_prefix}COMPUTER_ENABLED"):
            self.config["computer_interaction"]["enabled"] = val.lower() == "true"
        
        # Debug mode
        if val := os.getenv(f"{env_prefix}DEBUG_MODE"):
            debug_mode = val.lower() == "true"
            if debug_mode:
                self.config["server"]["log_level"] = "DEBUG"
                if "web_interaction" in self.config and "browser" in self.config["web_interaction"]:
                    self.config["web_interaction"]["browser"]["debug_screenshots"] = True
    
    def _setup_logging(self):
        """Set up logging based on configuration."""
        log_level = self.config.get("server", {}).get("log_level", "INFO")
        log_format = self.config.get("server", {}).get("log_format", 
                                                       "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # Convert string log level to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=numeric_level,
            format=log_format,
            force=True  # Force reconfiguration
        )
        
        # Update our logger level specifically
        logger.setLevel(numeric_level)
        logger.info(f"Logging configured with level: {log_level}")
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key (if None, returns entire section)
            default: Default value if not found
        
        Returns:
            Configuration value
        """
        if key is None:
            return self.config.get(section, default)
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def save(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved server config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        self._apply_env_overrides()
        self._setup_logging()
        logger.info("Configuration reloaded")
    
    @property
    def server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return self.config.get("server", {})
    
    @property
    def web_config(self) -> Dict[str, Any]:
        """Get web interaction configuration."""
        return self.config.get("web_interaction", {})
    
    @property
    def computer_config(self) -> Dict[str, Any]:
        """Get computer interaction configuration."""
        return self.config.get("computer_interaction", {})
    
    @property
    def features_config(self) -> Dict[str, Any]:
        """Get features configuration."""
        return self.config.get("features", {})
    
    def is_web_enabled(self) -> bool:
        """Check if web interaction is enabled."""
        return self.get("web_interaction", "enabled", True)
    
    def is_computer_enabled(self) -> bool:
        """Check if computer interaction is enabled."""
        return self.get("computer_interaction", "enabled", True)
    
    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a specific feature is enabled.
        
        Args:
            feature: Feature name
        
        Returns:
            True if enabled, False otherwise
        """
        return self.get("features", {}).get(feature, {}).get("enabled", True)
    
    def get_web_config_path(self) -> str:
        """Get the path to web interaction config file."""
        config_file = self.get("web_interaction", "config_file", "./web_interaction/browser_config.json")
        
        # Convert relative path to absolute path
        if not os.path.isabs(config_file):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_file = os.path.join(base_dir, config_file)
        
        return config_file
    
    def get_computer_config_path(self) -> str:
        """Get the path to computer interaction config file."""
        config_file = self.get("computer_interaction", "config_file", "./computer_interaction/computer_config.json")
        
        # Convert relative path to absolute path
        if not os.path.isabs(config_file):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_file = os.path.join(base_dir, config_file)
        
        return config_file
    
    def get_data_directory(self, subdir: str = "") -> str:
        """
        Get path to data directory, creating it if needed.
        
        Args:
            subdir: Subdirectory within data directory
        
        Returns:
            Path to data directory
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data", subdir)
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        return data_dir


# Global config instance
server_config = ServerConfigManager()


# Convenience functions
def get_config() -> ServerConfigManager:
    """Get the global config manager instance."""
    return server_config


def reload_config():
    """Reload configuration from file."""
    server_config.reload()


def save_config():
    """Save current configuration to file."""
    server_config.save()
