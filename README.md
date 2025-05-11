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

Browser behavior can be configured through environment variables or the `browser_config.json` file:

```json
{
  "headless": false,
  "slow_mo": 50,
  "width": 1280,
  "height": 800,
  "debug_screenshots": true,
  "timeout": 30000
}
```

### Environment Variables

- `MCP_BROWSER_HEADLESS`: Set to "true" for headless mode (default: "false")
- `MCP_BROWSER_SLOW_MO`: Slow down operations by specified milliseconds (default: 0)
- `MCP_BROWSER_WIDTH`: Browser viewport width (default: 1280)
- `MCP_BROWSER_HEIGHT`: Browser viewport height (default: 800)
- `MCP_BROWSER_DEBUG_SCREENSHOTS`: Set to "true" to save screenshots (default: "false")
- `MCP_BROWSER_TIMEOUT`: Default navigation timeout in milliseconds (default: 30000)
- `MCP_CAPTURE_NETWORK`: Set to "true" to capture network requests (default: "false")
- `PLAYWRIGHT_FORCE_VISIBLE`: Set to "true" to force visible browser regardless of other settings

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to improve this scaffold.

## License

[Your license here]