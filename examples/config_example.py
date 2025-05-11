"""Example of using the configuration system."""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import server_config

# Print current configuration
print("Current Configuration:")
print(f"Server Name: {server_config.get('server', 'name')}")
print(f"Log Level: {server_config.get('server', 'log_level')}")
print(f"Web Interaction Enabled: {server_config.is_web_enabled()}")
print(f"Computer Interaction Enabled: {server_config.is_computer_enabled()}")

# Update a configuration value
print("\nUpdating log level to DEBUG...")
server_config.set('server', 'log_level', 'DEBUG')

# Check if calculator is enabled
if server_config.is_feature_enabled('calculator'):
    print("\nCalculator is enabled")
    precision = server_config.get('features', {}).get('calculator', {}).get('precision', 6)
    print(f"Calculator precision: {precision}")

# Get web browser config
web_config = server_config.web_config
if web_config.get('enabled'):
    browser_config = web_config.get('browser', {})
    print(f"\nBrowser headless mode: {browser_config.get('headless', False)}")
    print(f"Browser width: {browser_config.get('width', 1280)}")
    print(f"Browser height: {browser_config.get('height', 800)}")

# Example of environment variable override
os.environ['MCP_BROWSER_HEADLESS'] = 'true'
server_config.reload()  # Reload to pick up env var
print(f"\nAfter env var override - Browser headless: {server_config.get('web_interaction', {}).get('browser', {}).get('headless')}")

# Save configuration
print("\nSaving configuration...")
server_config.save()

print("\nConfiguration example complete!")
