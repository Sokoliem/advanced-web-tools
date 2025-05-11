#!/usr/bin/env python3
"""
Installation script for Claude MCP Scaffold.

This script automates the installation of all required dependencies for the Claude MCP Scaffold,
including Python packages and browser drivers.
"""

import subprocess
import sys
import os
import platform

def main():
    """Run the installation process."""
    print("Starting Claude MCP Scaffold installation...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print("Error: Python 3.9 or higher is required")
        sys.exit(1)
    
    print(f"Python version {python_version.major}.{python_version.minor}.{python_version.micro} detected")
    
    # Install Python dependencies
    print("\nInstalling Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("✅ Python dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Python dependencies: {e}")
        sys.exit(1)
    
    # Install development dependencies
    print("\nInstalling development dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], check=True)
        print("✅ Development dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing development dependencies: {e}")
        print("Continuing with installation...")
    
    # Install Playwright browser drivers
    print("\nInstalling Playwright browser drivers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("✅ Playwright browser drivers installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Playwright browser drivers: {e}")
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    print("\nSetting up environment configuration...")
    env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_file_path):
        with open(env_file_path, "w") as f:
            f.write("""# Claude MCP Scaffold Configuration
# Browser visibility (true/false)
MCP_BROWSER_HEADLESS=false

# Slow down operations by specified milliseconds
MCP_BROWSER_SLOW_MO=50

# Browser viewport dimensions
MCP_BROWSER_WIDTH=1280
MCP_BROWSER_HEIGHT=800

# Enable debug screenshots
MCP_BROWSER_DEBUG_SCREENSHOTS=false

# Default navigation timeout (milliseconds)
MCP_BROWSER_TIMEOUT=30000

# Network request capturing
MCP_CAPTURE_NETWORK=false

# Force browser visibility regardless of headless setting
PLAYWRIGHT_FORCE_VISIBLE=true
""")
        print("✅ Created default .env configuration file")
    else:
        print("ℹ️ .env configuration file already exists")
    
    # Create browser_config.json if it doesn't exist
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_interaction")
    config_file_path = os.path.join(config_dir, "browser_config.json")
    if not os.path.exists(config_file_path):
        with open(config_file_path, "w") as f:
            f.write("""{
    "headless": false,
    "slow_mo": 50,
    "width": 1280,
    "height": 800,
    "debug_screenshots": false,
    "timeout": 30000
}""")
        print("✅ Created default browser configuration file")
    else:
        print("ℹ️ Browser configuration file already exists")
    
    print("\n✅ Claude MCP Scaffold installation completed successfully!")
    print("\nTo run the server:")
    print("    python -m claude_mcp_scaffold")
    print("or if you installed in development mode:")
    print("    claude-mcp")
    
    # Ask about computer interaction tools
    print("\n" + "="*50)
    print("Computer Interaction Tools")
    print("="*50)
    print("\nThe advanced-web-tools MCP server now supports computer interaction capabilities.")
    print("These tools allow control of the mouse, keyboard, windows, and more.")
    print("\nWould you like to install computer interaction dependencies?")
    response = input("Install computer tools? (y/n): ").lower()
    
    if response == 'y':
        print("\nInstalling computer interaction tools...")
        try:
            subprocess.run([sys.executable, "install_computer_tools.py"], check=True)
            print("✅ Computer interaction tools installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing computer tools: {e}")
            print("You can try running 'python install_computer_tools.py' manually later.")
    else:
        print("\nSkipping computer tools installation.")
        print("You can install them later by running: python install_computer_tools.py")

if __name__ == "__main__":
    main()