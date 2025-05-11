# Configuration System

This document describes the configuration system for the Claude MCP Scaffold server.

## Overview

The server uses a hierarchical JSON configuration system that allows for flexible configuration of all components. Configuration can be set via JSON files or overridden with environment variables.

## Configuration Files

### Main Configuration
- **Location**: `config/server_config.json`
- **Purpose**: Global server settings and feature configuration

### Module-Specific Configuration
- **Web Interaction**: `web_interaction/browser_config.json`
- **Computer Interaction**: `computer_interaction/computer_config.json`

## Configuration Structure

```json
{
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
    "enabled": true,
    "config_file": "./web_interaction/browser_config.json",
    "browser": {
      "headless": false,
      "slow_mo": 100,
      "width": 1280,
      "height": 800,
      "debug_screenshots": true,
      "timeout": 30000,
      "max_tabs": 8,
      "tab_idle_timeout": 300
    }
  },
  "computer_interaction": {
    "enabled": true,
    "config_file": "./computer_interaction/computer_config.json",
    "default_settings": {
      "screenshot_quality": 90,
      "mouse_duration": 0.5,
      "typing_interval": 0.05,
      "command_timeout": 30.0,
      "enable_failsafe": true
    }
  },
  "features": {
    "calculator": {
      "enabled": true,
      "precision": 6,
      "max_calculation_time": 5.0
    },
    "echo": {
      "enabled": true,
      "max_message_length": 1000
    },
    "server_status": {
      "enabled": true,
      "include_system_info": true,
      "include_performance_metrics": true
    }
  },
  "environment": {
    "override_from_env": true,
    "env_prefix": "MCP_",
    "allowed_env_vars": [
      "MCP_LOG_LEVEL",
      "MCP_BROWSER_HEADLESS",
      "MCP_COMPUTER_ENABLED",
      "MCP_DEBUG_MODE"
    ]
  }
}
```

## Environment Variables

Environment variables can override configuration values. By default, variables must start with `MCP_`.

### Common Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MCP_LOG_LEVEL` | Set logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `MCP_WEB_ENABLED` | Enable/disable web interaction | `true`, `false` |
| `MCP_COMPUTER_ENABLED` | Enable/disable computer interaction | `true`, `false` |
| `MCP_BROWSER_HEADLESS` | Run browser in headless mode | `true`, `false` |
| `MCP_DEBUG_MODE` | Enable debug mode | `true`, `false` |

### Computer Interaction Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `COMPUTER_SCREENSHOT_QUALITY` | Screenshot quality (0-100) | `90` |
| `COMPUTER_MOUSE_DURATION` | Mouse movement duration | `0.5` |
| `COMPUTER_TYPING_INTERVAL` | Typing speed interval | `0.05` |
| `COMPUTER_ENABLE_FAILSAFE` | Enable safety failsafe | `true` |

## Configuration Tools

The server provides tools to manage configuration:

### get_config
Retrieve the current configuration.

```python
config = await get_config()
```

### update_config
Update a configuration value.

```python
result = await update_config("server", "log_level", "DEBUG")
```

### reload_config
Reload configuration from file.

```python
result = await reload_config()
```

## Usage Examples

### Enable Debug Mode
```bash
export MCP_DEBUG_MODE=true
```

### Run Browser in Headless Mode
```bash
export MCP_BROWSER_HEADLESS=true
```

### Disable Computer Interaction
```bash
export MCP_COMPUTER_ENABLED=false
```

### Programmatic Configuration

```python
from config import server_config

# Get a value
log_level = server_config.get("server", "log_level")

# Set a value
server_config.set("server", "log_level", "DEBUG")

# Save configuration
server_config.save()

# Reload from file
server_config.reload()
```

## Custom Configuration

You can create custom configuration files by:

1. Creating a new JSON file with your settings
2. Passing the path when starting the server:

```python
from config import ServerConfigManager

custom_config = ServerConfigManager("/path/to/custom_config.json")
```

## Best Practices

1. **Use Environment Variables for Deployment**: Override sensitive or environment-specific settings with environment variables
2. **Keep Defaults Reasonable**: Ensure default values work out of the box
3. **Document Configuration Changes**: Update this README when adding new configuration options
4. **Validate Configuration**: Consider adding validation for critical settings
5. **Version Your Configuration**: Include version information for compatibility

## Extending Configuration

To add new configuration options:

1. Update the default configuration in `config_manager.py`
2. Add environment variable support if needed
3. Update existing code to use the new configuration
4. Update the configuration file template
5. Document the new options in this README

## Troubleshooting

### Configuration Not Loading
- Check file path and permissions
- Verify JSON syntax is valid
- Check log output for error messages

### Environment Variables Not Working
- Ensure `override_from_env` is set to `true`
- Check that variable names use the correct prefix
- Verify environment variables are exported correctly

### Changes Not Taking Effect
- Remember to save configuration after changes
- Reload configuration if changed externally
- Some settings may require server restart
