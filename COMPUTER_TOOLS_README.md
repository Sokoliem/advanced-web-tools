# Computer Interaction Tools - Advanced Web Tools MCP Server

This document describes the computer interaction capabilities added to the Advanced Web Tools MCP server.

## Overview

The computer interaction tools extend the MCP server beyond web browsing to provide full computer control capabilities. These tools allow Claude and other AI assistants to:

- Capture and analyze screenshots
- Control the mouse and keyboard
- Manage windows and applications
- Execute system commands
- Perform computer vision tasks

## Installation

### Prerequisites

- Python 3.9+
- Windows, macOS, or Linux
- Administrator/sudo access may be required for some operations

### Basic Installation

```bash
# Install core dependencies
pip install pyautogui pygetwindow psutil pyperclip keyboard mouse numpy Pillow

# On Windows, also install:
pip install pywin32
```

### Advanced Installation (Optional)

For advanced computer vision and OCR capabilities:

```bash
# Install computer vision dependencies
pip install opencv-python pytesseract scikit-image

# For OCR, also install Tesseract separately:
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr
```

### Automated Installation

Use the provided installation script:

```bash
python install_computer_tools.py
```

## Available Tools

### 1. Unified Computer Use Tool

The main tool `computer_use` accepts a list of operations to perform:

```python
operations = [
    {
        "type": "capture_screen",
        "params": {}
    },
    {
        "type": "find_on_screen",
        "params": {
            "image_base64": "...",
            "confidence": 0.8
        }
    }
]
```

### 2. Screen Operations

- **capture_screen**: Capture a screenshot
  - Parameters: `region` (optional), `highlight_areas` (optional)
  - Returns: Base64 encoded image

- **find_on_screen**: Find an image on screen
  - Parameters: `image_path` or `image_base64`, `confidence` (0-1)
  - Returns: Location coordinates if found

- **get_pixel_color**: Get color at specific coordinates
  - Parameters: `x`, `y`
  - Returns: RGB color values

- **wait_for_screen_change**: Wait for screen content to change
  - Parameters: `region` (optional), `timeout`, `poll_interval`
  - Returns: Whether change was detected

### 3. Mouse Operations

- **move_mouse**: Move mouse to coordinates
  - Parameters: `x`, `y`, `duration`, `relative` (bool)

- **click**: Click at position
  - Parameters: `x`, `y`, `button` (left/right/middle), `clicks`

- **drag**: Drag from one point to another
  - Parameters: `start_x`, `start_y`, `end_x`, `end_y`, `duration`

- **scroll**: Scroll mouse wheel
  - Parameters: `clicks` (positive=up, negative=down), `x`, `y`

### 4. Keyboard Operations

- **type_text**: Type text
  - Parameters: `text`, `interval`, `press_enter` (bool)

- **press_key**: Press a key or combination
  - Parameters: `key`, `modifiers` (list)

- **hot_key**: Press a hotkey combination
  - Parameters: `*keys` (e.g., 'ctrl', 'c')

- **wait_for_key**: Wait for a specific key press
  - Parameters: `key`, `timeout`

### 5. Window Management

- **get_all_windows**: List all windows
  - Returns: Window information (title, position, size, state)

- **find_window**: Find windows by title
  - Parameters: `title`, `exact_match` (bool)

- **activate_window**: Bring window to front
  - Parameters: `title`

- **minimize_window/maximize_window**: Change window state
  - Parameters: `title`

- **resize_window**: Resize a window
  - Parameters: `title`, `width`, `height`

- **move_window**: Move a window
  - Parameters: `title`, `x`, `y`

- **arrange_windows**: Arrange windows in a layout
  - Parameters: `arrangement` (cascade/tile_vertical/tile_horizontal)

### 6. System Operations

- **get_system_info**: Get system information
  - Returns: Platform, CPU, memory, disk info

- **list_processes**: List running processes
  - Parameters: `filter_name`, `sort_by`

- **start_application**: Start an application
  - Parameters: `application_path`, `arguments`, `wait` (bool)

- **kill_process**: Kill a process
  - Parameters: `pid` or `name`

- **execute_command**: Execute shell command
  - Parameters: `command`, `shell` (bool), `timeout`

- **get/set_clipboard_content**: Manage clipboard
  - Parameters: `content` (for setting)

### 7. Computer Vision (Optional)

- **find_text_on_screen**: Find text using OCR
  - Parameters: `screenshot_base64`, `text_to_find`, `language`

- **detect_elements**: Detect UI elements
  - Parameters: `screenshot_base64`, `element_type` (button/textbox/edge)

- **compare_screenshots**: Compare two screenshots
  - Parameters: `screenshot1_base64`, `screenshot2_base64`, `method`

- **find_template**: Find template image in screenshot
  - Parameters: `screenshot_base64`, `template_base64`, `threshold`

## Usage Examples

### Example 1: Take a Screenshot

```python
result = await computer_use([
    {
        "type": "capture_screen",
        "params": {}
    }
])
```

### Example 2: Open Application and Type

```python
result = await computer_use([
    {
        "type": "start_application",
        "params": {
            "application_path": "notepad.exe"
        }
    },
    {
        "type": "wait_for_screen_change",
        "params": {
            "timeout": 5
        }
    },
    {
        "type": "type_text",
        "params": {
            "text": "Hello, World!",
            "press_enter": True
        }
    }
])
```

### Example 3: Window Management

```python
result = await computer_use([
    {
        "type": "get_all_windows",
        "params": {}
    },
    {
        "type": "arrange_windows",
        "params": {
            "arrangement": "tile_vertical"
        }
    }
])
```

## Security Considerations

1. **Permissions**: Some operations require elevated privileges
2. **Safety**: PyAutoGUI has built-in failsafes (move mouse to corner to abort)
3. **Privacy**: Be cautious with screenshots and OCR of sensitive information
4. **System Access**: The execute_command operation can run arbitrary commands

## Platform-Specific Notes

### Windows
- Full functionality available
- Some operations may require running as administrator
- pywin32 required for advanced features

### macOS
- May require accessibility permissions
- Some window management features limited by macOS security

### Linux
- Requires X11 or Wayland support
- Some features may vary by desktop environment

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path and virtual environment

2. **Permission Denied**
   - Run with appropriate privileges
   - Check system security settings

3. **OCR Not Working**
   - Install Tesseract separately
   - Add Tesseract to system PATH
   - Verify language data files are installed

4. **Screen Capture Issues**
   - Check display scaling settings
   - Ensure screen is not locked
   - Verify multiple monitor setup

## Limitations

1. Cannot interact with privileged system dialogs
2. Some applications may block automation
3. Performance depends on system resources
4. OCR accuracy varies with image quality

## Best Practices

1. Always verify operations completed successfully
2. Use appropriate timeouts for operations
3. Handle errors gracefully
4. Consider system load when performing intensive operations
5. Test thoroughly on target platform

## Contributing

To extend the computer interaction capabilities:

1. Add new operations to the relevant module
2. Update the unified tool to support new operations
3. Add appropriate error handling
4. Document new features
5. Add tests for new functionality
