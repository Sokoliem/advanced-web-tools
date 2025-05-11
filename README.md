# Advanced Web Tools

An MCP server that provides advanced web interaction and browser automation capabilities for Claude and other AI assistants, now with full computer control capabilities.

## Overview

This project provides a comprehensive MCP server that enables Claude and other AI agents to interact with web browsers and control computer systems. It allows AI models to perform a wide range of operations:

**Web Interaction:**
- Web navigation
- Content extraction
- Element interaction (click, type, etc.)
- Structured data extraction
- Console command execution

**Computer Control:**
- Screenshot capture and analysis
- Mouse and keyboard control
- Window management
- System operations
- Computer vision and OCR

## Quick Start

### Prerequisites

- Python 3.9+
- [Playwright](https://playwright.dev/python/docs/intro) for browser automation
- Beautiful Soup for HTML parsing
- PyAutoGUI for computer control (optional)
- Additional dependencies for computer interaction (see COMPUTER_TOOLS_README.md)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/your-username/claude-mcp-scaffold.git
cd claude-mcp-scaffold
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install browser drivers:
```bash
playwright install chromium
```

### Running the Server

```bash
python -m claude_mcp_scaffold
```

## Features

### Web Interaction

**Unified Web Interaction Tool**

The main tool, `web_interact`, allows for multiple operations in a single call:

```json
{
  "operations": [
    {
      "type": "navigate",
      "params": {
        "url": "https://example.com"
      }
    },
    {
      "type": "extract_content",
      "params": {
        "include_html": false
      }
    }
  ]
}
```

### Computer Interaction

**Unified Computer Use Tool**

The `computer_use` tool provides full computer control:

```json
{
  "operations": [
    {
      "type": "capture_screen",
      "params": {}
    },
    {
      "type": "click",
      "params": {
        "x": 100,
        "y": 200
      }
    },
    {
      "type": "type_text",
      "params": {
        "text": "Hello, World!"
      }
    }
  ]
}
```

Capabilities include:
- Screen capture and analysis
- Mouse and keyboard control
- Window management
- System operations
- Computer vision and OCR

For detailed documentation on computer interaction tools, see [COMPUTER_TOOLS_README.md](COMPUTER_TOOLS_README.md).

### Persistent Browser State

The scaffold maintains browser state between calls, allowing for multi-step interactions.

### Console Access

Provides direct access to browser console for executing JavaScript commands and viewing logs.

### Structured Data Extraction

Automatically extracts and parses:
- Products
- Articles
- Tables
- Lists
- JSON-LD data

## Configuration

The server uses a comprehensive configuration system that allows customization through JSON files and environment variables. See [CONFIG_README.md](CONFIG_README.md) for detailed documentation.

### Configuration Files

- **Global Configuration**: `config/server_config.json` - Main server settings
- **Web Interaction**: `web_interaction/browser_config.json` - Browser-specific settings
- **Computer Interaction**: `computer_interaction/computer_config.json` - Computer control settings

### Quick Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` to customize settings:
```bash
# Enable/disable features
MCP_WEB_ENABLED=true
MCP_COMPUTER_ENABLED=true

# Set log level
MCP_LOG_LEVEL=INFO

# Browser settings
MCP_BROWSER_HEADLESS=false
MCP_BROWSER_WIDTH=1280
MCP_BROWSER_HEIGHT=800
```

### Configuration Tools

The server provides tools to manage configuration at runtime:

- `get_config`: Retrieve current configuration
- `update_config`: Update configuration values
- `reload_config`: Reload configuration from file

Example:
```python
# Update log level
await update_config("server", "log_level", "DEBUG")

# Check if a feature is enabled
config = await get_config()
web_enabled = config["config"]["web_interaction"]["enabled"]
```

### Environment Variables

Common environment variables:

- `MCP_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `MCP_WEB_ENABLED`: Enable/disable web interaction (true/false)
- `MCP_COMPUTER_ENABLED`: Enable/disable computer interaction (true/false)
- `MCP_BROWSER_HEADLESS`: Run browser in headless mode (true/false)
- `MCP_DEBUG_MODE`: Enable debug mode (true/false)

For a complete list, see `.env.example` and [CONFIG_README.md](CONFIG_README.md).

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to improve this scaffold.

## License

[Your license here]