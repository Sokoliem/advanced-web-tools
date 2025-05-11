"""Configuration manager for computer interaction settings."""

import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ComputerConfigManager:
    """Manage configuration for computer interaction tools."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        if config_path is None:
            # Default to computer_config.json in the same directory
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "computer_config.json"
            )
        
        self.config_path = config_path
        self.config = self._load_config()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded computer config from {self.config_path}")
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
            "screen": {
                "screenshot_quality": 90,
                "highlight_color": "red",
                "highlight_thickness": 3,
                "monitor_poll_interval": 0.1,
                "wait_timeout": 5.0
            },
            "mouse": {
                "movement_duration": 0.5,
                "click_interval": 0.1,
                "drag_duration": 1.0,
                "failsafe": True,
                "pause_between_actions": 0.1
            },
            "keyboard": {
                "typing_interval": 0.05,
                "hotkey_pause": 0.1,
                "key_wait_timeout": 5.0
            },
            "window": {
                "activation_wait": 0.5,
                "operation_timeout": 10.0,
                "arrangement_animation_time": 0.3
            },
            "system": {
                "command_timeout": 30.0,
                "process_list_sort": "memory",
                "clipboard_retry_attempts": 3
            },
            "vision": {
                "ocr_language": "eng",
                "template_match_threshold": 0.8,
                "edge_detection_threshold_low": 50,
                "edge_detection_threshold_high": 150,
                "button_min_width": 30,
                "button_min_height": 20,
                "textbox_min_width": 50,
                "textbox_min_height": 15,
                "grayscale_matching": False
            },
            "safety": {
                "enable_failsafe": True,
                "max_operation_time": 300.0,
                "require_confirmation_for_commands": False,
                "blocked_commands": ["rm -rf /", "format c:", "del /s /q"]
            },
            "performance": {
                "enable_caching": True,
                "cache_timeout": 60.0,
                "max_concurrent_operations": 5,
                "operation_queue_size": 100
            }
        }
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        # Screen settings
        if val := os.getenv("COMPUTER_SCREENSHOT_QUALITY"):
            self.config["screen"]["screenshot_quality"] = int(val)
        if val := os.getenv("COMPUTER_HIGHLIGHT_COLOR"):
            self.config["screen"]["highlight_color"] = val
        if val := os.getenv("COMPUTER_MONITOR_POLL_INTERVAL"):
            self.config["screen"]["monitor_poll_interval"] = float(val)
        
        # Mouse settings
        if val := os.getenv("COMPUTER_MOUSE_DURATION"):
            self.config["mouse"]["movement_duration"] = float(val)
        if val := os.getenv("COMPUTER_MOUSE_FAILSAFE"):
            self.config["mouse"]["failsafe"] = val.lower() == "true"
        
        # Keyboard settings
        if val := os.getenv("COMPUTER_TYPING_INTERVAL"):
            self.config["keyboard"]["typing_interval"] = float(val)
        
        # Window settings
        if val := os.getenv("COMPUTER_WINDOW_TIMEOUT"):
            self.config["window"]["operation_timeout"] = float(val)
        
        # System settings
        if val := os.getenv("COMPUTER_COMMAND_TIMEOUT"):
            self.config["system"]["command_timeout"] = float(val)
        
        # Vision settings
        if val := os.getenv("COMPUTER_OCR_LANGUAGE"):
            self.config["vision"]["ocr_language"] = val
        if val := os.getenv("COMPUTER_TEMPLATE_THRESHOLD"):
            self.config["vision"]["template_match_threshold"] = float(val)
        
        # Safety settings
        if val := os.getenv("COMPUTER_ENABLE_FAILSAFE"):
            self.config["safety"]["enable_failsafe"] = val.lower() == "true"
        if val := os.getenv("COMPUTER_MAX_OPERATION_TIME"):
            self.config["safety"]["max_operation_time"] = float(val)
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
        
        Returns:
            Configuration value
        """
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
                json.dump(self.config, f, indent=4)
            logger.info(f"Saved computer config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        self._apply_env_overrides()
    
    @property
    def screen_config(self) -> Dict[str, Any]:
        """Get screen configuration."""
        return self.config.get("screen", {})
    
    @property
    def mouse_config(self) -> Dict[str, Any]:
        """Get mouse configuration."""
        return self.config.get("mouse", {})
    
    @property
    def keyboard_config(self) -> Dict[str, Any]:
        """Get keyboard configuration."""
        return self.config.get("keyboard", {})
    
    @property
    def window_config(self) -> Dict[str, Any]:
        """Get window configuration."""
        return self.config.get("window", {})
    
    @property
    def system_config(self) -> Dict[str, Any]:
        """Get system configuration."""
        return self.config.get("system", {})
    
    @property
    def vision_config(self) -> Dict[str, Any]:
        """Get vision configuration."""
        return self.config.get("vision", {})
    
    @property
    def safety_config(self) -> Dict[str, Any]:
        """Get safety configuration."""
        return self.config.get("safety", {})
    
    @property
    def performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.config.get("performance", {})


# Global config instance
computer_config = ComputerConfigManager()
