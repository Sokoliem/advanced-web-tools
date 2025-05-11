"""MCP server implementation."""

import asyncio
import json
import logging
import os
import sys
import atexit
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP, Context

# Import and initialize configuration before logging
from .config import server_config, get_config

# Configure logging based on config
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP(server_config.get("server", "name", "Claude MCP Scaffold"))


@mcp.tool()
async def echo(message: str) -> Dict[str, Any]:
    """
    A simple echo tool that returns the input message.

    Args:
        message: The message to echo back.

    Returns:
        Dict: The echoed message.
    """
    # Check if feature is enabled
    if not server_config.is_feature_enabled("echo"):
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Echo feature is disabled in configuration"
                }
            ]
        }
    
    # Check max message length from config
    max_length = server_config.get("features", {}).get("echo", {}).get("max_message_length", 1000)
    if len(message) > max_length:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Message too long. Maximum length is {max_length} characters"
                }
            ]
        }
    
    logger.info(f"Echo tool called with message: {message}")
    return {
        "content": [
            {
                "type": "text",
                "text": f"Echo: {message}"
            }
        ]
    }


@mcp.tool()
async def calculator(operation: str, a: float, b: float, format: str = "standard") -> Dict[str, Any]:
    """
    An enhanced calculator tool with advanced operations.

    Args:
        operation: The operation to perform (add, subtract, multiply, divide, power, root, log, modulo).
        a: The first number.
        b: The second number.
        format: Output format ("standard" or "scientific").

    Returns:
        Dict: The result of the calculation.
    """
    import math
    
    # Check if feature is enabled
    if not server_config.is_feature_enabled("calculator"):
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Calculator feature is disabled in configuration"
                }
            ]
        }
    
    logger.info(f"Calculator tool called with operation: {operation}, a: {a}, b: {b}, format: {format}")
    result = None
    
    # Basic operations
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return {"content": [{"type": "text", "text": "Error: Cannot divide by zero"}]}
        result = a / b
    # Advanced operations
    elif operation == "power":
        result = math.pow(a, b)
    elif operation == "root":
        if a < 0 and b % 2 == 0:
            return {"content": [{"type": "text", "text": "Error: Cannot calculate even roots of negative numbers"}]}
        result = math.pow(a, 1/b)
    elif operation == "log":
        if a <= 0 or a == 1 or b <= 0:
            return {"content": [{"type": "text", "text": "Error: Invalid logarithm parameters"}]}
        result = math.log(b, a)  # logarithm of b with base a
    elif operation == "modulo":
        if b == 0:
            return {"content": [{"type": "text", "text": "Error: Cannot divide by zero"}]}
        result = a % b
    else:
        return {"content": [{"type": "text", "text": f"Error: Unknown operation '{operation}'. Supported operations: add, subtract, multiply, divide, power, root, log, modulo"}]}
    
    # Format the result with configurable precision
    precision = server_config.get("features", {}).get("calculator", {}).get("precision", 6)
    
    if format.lower() == "scientific":
        formatted_result = f"{result:.{precision}e}"
    else:
        # For standard format, round to precision decimal places
        formatted_result = f"{result:.{precision}f}".rstrip('0').rstrip('.')
    
    return {"content": [{"type": "text", "text": f"Result: {formatted_result}"}]}

# Import and register web interaction tools if enabled
if server_config.is_web_enabled():
    try:
        # Import browser manager and all tools from web_interaction
        try:
            # Import and get browser_manager instance from web_interaction
            from .web_interaction import browser_manager
            logger.info("Using browser manager from web_interaction")
            
            # Import the register_all_tools function to register all tools at once
            from .web_interaction import register_all_tools
            
            # Register all web interaction tools including the new enhanced capabilities
            logger.info("Registering all web interaction tools...")
            all_tools = register_all_tools(mcp, browser_manager)
            logger.info(f"Successfully registered {len(all_tools)} web interaction tools")
        
        # Store references to specific tool categories for status reporting
        visual_tools = all_tools.get('visual_tools', {})
        console_tools = all_tools.get('console_tools', {})
        persistence_tools = all_tools.get('persistence_tools', {})
        export_tools = all_tools.get('export_tools', {})
        error_tools = all_tools.get('error_tools', {})
        advanced_tools = all_tools.get('advanced_tools', {})
        
        logger.info("Enhanced capabilities integrated successfully")
    except ImportError as e:
        # Fall back to legacy tool registration if register_all_tools is not available
        logger.warning(f"Unable to use register_all_tools. Falling back to individual registrations. Error: {str(e)}")
        
        # First, use the enhanced browser manager instead of the regular one
        try:
            from .web_interaction.enhanced_browser_manager import EnhancedBrowserManager
            logger.info("Using enhanced browser manager")
            browser_manager = EnhancedBrowserManager()
        except ImportError:
            # Fall back to regular browser manager
            from .web_interaction.browser_manager import BrowserManager
            logger.info("Using standard browser manager")
            browser_manager = BrowserManager()
        
        # Register error handling tools
        try:
            from .web_interaction.error_handler import register_error_handling_tool
            logger.info("Registering error handling tools...")
            error_tools = register_error_handling_tool(mcp, browser_manager)
            logger.info("Error handling tools registered successfully")
        except ImportError as e:
            logger.warning(f"Error handling tools not registered. Error: {str(e)}")
        
        # Register advanced unified tool
        try:
            from .web_interaction.advanced_unified_tool import register_advanced_unified_tool
            logger.info("Registering advanced unified web interaction tool...")
            advanced_tools = register_advanced_unified_tool(mcp, browser_manager)
            logger.info("Advanced unified web interaction tool registered successfully")
        except ImportError as e:
            logger.warning(f"Advanced unified tools not registered. Error: {str(e)}")
        
        # Still register the original unified tool for backward compatibility
        from .web_interaction import register_unified_tool
        logger.info("Registering unified web interaction tool...")
        register_unified_tool(mcp, browser_manager)
        logger.info("Unified web interaction tool registered successfully")
        
        # For backward compatibility, also register the old tools
        from .web_interaction import (
            register_core_tools,
            register_advanced_tools,
            register_data_extraction_tools,
            register_workflow_tools
        )
        
        # Register all the old web interaction tools for backward compatibility
        logger.info("Registering legacy web interaction tools for backward compatibility...")
        register_core_tools(mcp, browser_manager)
        register_advanced_tools(mcp, browser_manager)
        register_data_extraction_tools(mcp, browser_manager)
        register_workflow_tools(mcp, browser_manager)
        logger.info("Legacy web interaction tools registered successfully")
    
    # We'll clean up browser resources when the process ends
    async def cleanup_browser():
        """Clean up browser resources when shutting down."""
        logger.info("Shutting down browser resources...")
        await browser_manager.close()
        logger.info("Browser resources shut down")
    
    # Register an exit handler to clean up resources
    atexit.register(lambda: asyncio.run(cleanup_browser()))

except ImportError as e:
    logger.warning(f"Web interaction tools not loaded. Error: {str(e)}")
    logger.warning("Make sure to install required dependencies with install_dependencies.py")
else:
    logger.info("Web interaction tools disabled in configuration")

# Import and register computer interaction tools if enabled
if server_config.is_computer_enabled():
    try:
        from .computer_interaction import register_all_computer_tools
        
        logger.info("Registering computer interaction tools...")
        computer_tools = register_all_computer_tools(mcp)
        logger.info("Successfully registered computer interaction tools")
        
        # Store references for status reporting
        screen_controller = computer_tools.get('screen_controller')
        keyboard_mouse = computer_tools.get('keyboard_mouse')
        window_manager = computer_tools.get('window_manager')
        system_ops = computer_tools.get('system_ops')
        computer_vision = computer_tools.get('computer_vision')
        
    except ImportError as e:
        logger.warning(f"Computer interaction tools not loaded. Error: {str(e)}")
        logger.warning("Make sure to install required dependencies: pyautogui, pygetwindow, etc.")
        computer_tools = None
else:
    logger.info("Computer interaction tools disabled in configuration")
    computer_tools = None


@mcp.tool()
async def get_config() -> Dict[str, Any]:
    """
    Get the current server configuration.

    Returns:
        Dict: Current configuration settings.
    """
    return {
        "content": [
            {
                "type": "text",
                "text": "Configuration retrieved successfully"
            }
        ],
        "config": server_config.config
    }


@mcp.tool()
async def update_config(section: str, key: str, value: Any) -> Dict[str, Any]:
    """
    Update a configuration value.

    Args:
        section: Configuration section to update
        key: Configuration key to update
        value: New value to set

    Returns:
        Dict: Update result.
    """
    try:
        old_value = server_config.get(section, key)
        server_config.set(section, key, value)
        
        # Save configuration if it's a persistent change
        server_config.save()
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Configuration updated: [{section}]{key} = {value}"
                }
            ],
            "old_value": old_value,
            "new_value": value
        }
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error updating configuration: {str(e)}"
                }
            ]
        }


@mcp.tool()
async def reload_config() -> Dict[str, Any]:
    """
    Reload configuration from file.

    Returns:
        Dict: Reload result.
    """
    try:
        server_config.reload()
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Configuration reloaded successfully"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error reloading configuration: {str(e)}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error reloading configuration: {str(e)}"
                }
            ]
        }


@mcp.tool()
async def server_status() -> Dict[str, Any]:
    """
    Get the current status of the MCP server including enhanced capabilities.

    Returns:
        Dict: Server status information.
    """
    try:
        # Gather basic server info
        status_info = {
            "version": server_config.get("server", "version", "0.3.0"),
            "name": server_config.get("server", "name", "Claude MCP Scaffold"),
            "log_level": server_config.get("server", "log_level", "INFO"),
            "uptime": "Unknown",  # Would need to track server start time
            "tools_count": len(mcp.tools),
            "config_path": server_config.config_path
        }
        
        # Add browser info if available
        if 'browser_manager' in globals():
            if hasattr(browser_manager, 'initialized'):
                status_info["browser_initialized"] = browser_manager.initialized
            
            if hasattr(browser_manager, 'active_pages'):
                status_info["active_pages_count"] = len(browser_manager.active_pages)
            
            if hasattr(browser_manager, 'page_metadata'):
                status_info["total_pages_count"] = len(browser_manager.page_metadata)
            
            # Add enhanced browser features if available
            if hasattr(browser_manager, 'get_browser_status'):
                status_info["browser_status"] = await browser_manager.get_browser_status()
        
        # Add enhanced capabilities status
        status_info["enhanced_capabilities"] = {
            "visual_debugging": 'visual_tools' in globals(),
            "console_integration": 'console_tools' in globals(),
            "data_persistence": 'persistence_tools' in globals(),
            "data_export": 'export_tools' in globals(),
            "computer_interaction": 'computer_tools' in globals()
        }
        
        # Add computer interaction status
        if 'computer_tools' in globals() and computer_tools:
            status_info["computer_capabilities"] = {
                "screen_control": 'screen_controller' in globals() and screen_controller.initialized,
                "keyboard_mouse": 'keyboard_mouse' in globals() and keyboard_mouse.initialized,
                "window_management": 'window_manager' in globals() and window_manager.initialized,
                "system_operations": 'system_ops' in globals(),
                "computer_vision": 'computer_vision' in globals() and computer_vision.initialized
            }
        
        # Add error stats if available
        if 'error_tools' in globals() and 'error_handler' in error_tools:
            error_handler = error_tools['error_handler']
            status_info["error_stats"] = error_handler.get_error_stats()
        
        # Add console monitor stats if available
        if 'console_tools' in globals() and 'console_monitor' in console_tools:
            console_monitor = console_tools['console_monitor']
            status_info["console_stats"] = console_monitor.get_stats()
        
        # Add data persistence stats if available
        if 'persistence_tools' in globals() and 'persistence_manager' in persistence_tools:
            persistence_manager = persistence_tools['persistence_manager']
            status_info["persistence_stats"] = persistence_manager.get_stats()
        
        # Add visual debugger stats if available
        if 'visual_tools' in globals() and 'visual_debugger' in visual_tools:
            visual_debugger = visual_tools['visual_debugger']
            status_info["visual_debugger_stats"] = visual_debugger.get_stats()
        
        # Add data export stats if available
        if 'export_tools' in globals() and 'export_manager' in export_tools:
            export_manager = export_tools['export_manager']
            status_info["export_stats"] = export_manager.get_stats()
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Server status retrieved successfully"
                }
            ],
            "status": status_info
        }
    except Exception as e:
        logger.error(f"Error getting server status: {str(e)}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error getting server status: {str(e)}"
                }
            ]
        }


@mcp.prompt()
def help_prompt() -> str:
    """A helpful prompt explaining how to use this MCP server."""
    try:
        # Check if web interaction tools are available
        from .web_interaction import browser_manager
        has_web_tools = True
    except ImportError:
        has_web_tools = False
    
    # Check for enhanced capabilities
    has_advanced_tools = 'advanced_tools' in globals()
    has_error_tools = 'error_tools' in globals()
    has_visual_tools = 'visual_tools' in globals()
    has_console_tools = 'console_tools' in globals()
    has_persistence_tools = 'persistence_tools' in globals()
    has_export_tools = 'export_tools' in globals()
    has_computer_tools = 'computer_tools' in globals()
    
    base_prompt = """
    This is the Claude MCP Scaffold Server. You can use the following tools:

    - echo: Echo back a message
    - calculator: Perform enhanced arithmetic operations (add, subtract, multiply, divide, power, root, log, modulo)
    - server_status: Get information about the server's current state
    - get_config: Get the current server configuration
    - update_config: Update a configuration value
    - reload_config: Reload configuration from file
    """
    
    web_tools_prompt = """
    Advanced Web Interaction tools:
    
    - web_interact: Unified tool for web interactions
      This tool can perform multiple operations in a single call:
      - navigate: Navigate to a URL in a browser
      - extract_content: Extract content from a web page
      - find_element: Find elements on a page using natural language
      - interact: Interact with elements (click, type, etc.)
      - extract_structured: Extract structured data from a page
      
    Legacy web interaction tools (for backward compatibility):
    - navigate: Navigate to a URL in a browser
    - extract_page_content: Extract content from a web page
    - semantic_find: Find elements on a page using natural language
    - interact_with_element: Interact with elements (click, type, etc.)
    - extract_structured_data: Extract structured data from a page
    - run_web_workflow: Run multi-step web workflows
    """
    
    advanced_tools_prompt = """
    Enhanced Web Interaction tools:
    
    - web_interact_advanced: Advanced unified tool with improved capabilities
      This tool offers enhanced features such as:
      - Session management for organizing related pages
      - Multi-browser support (Chromium, Firefox, WebKit)
      - More robust element finding and interaction
      - Advanced error handling and recovery
      - Screenshot functionality
      - JavaScript execution
      - Tab management to prevent browser overload
      
    - get_browser_info: Get information about current browser state
    - take_browser_screenshot: Take screenshot of a page or element
    - get_browser_tabs: Get detailed information about all open browser tabs
    - clean_browser_tabs: Clean up browser tabs by closing inactive or least used tabs
    - clear_browser_state: Clear all saved browser state and close all tabs (complete reset)
    """
    
    error_tools_prompt = """
    Error Handling & Diagnostics tools:
    
    - diagnostics_report: Generate a comprehensive diagnostic report
    - fix_common_issues: Automatically attempt to fix common browser issues
    
    Comprehensive Web Diagnostic Toolkit:
    - create_diagnostic_session: Create a new diagnostic session for testing and debugging
    - collect_web_diagnostics: Collect comprehensive diagnostics from a web page
    - start_performance_monitoring: Start monitoring performance metrics for a web page
    - stop_performance_monitoring: Stop performance monitoring for a page or all pages
    - get_performance_report: Generate a performance report for a page or session
    - create_web_diagnostic_report: Create a comprehensive diagnostic report
    - list_diagnostic_sessions: List all diagnostic sessions
    """
    
    visual_debugging_prompt = """
    Visual Debugging tools:
    
    - take_element_debug_screenshot: Take a detailed screenshot of a specific element with debug overlays
    - create_element_visualization: Generate a visual representation of an element's state and properties
    - create_page_structure_visualization: Visualize the DOM structure of a page
    - create_debug_timeline: Create a timeline visualization of page/element interactions
    - highlight_element: Highlight an element on the page for debugging
    - compare_element_states: Compare the visual state of an element before and after an action
    - create_interactive_dom_explorer: Generate an interactive DOM explorer for debugging
    """
    
    console_integration_prompt = """
    Console Integration tools:
    
    - get_console_logs: Retrieve console logs from the browser
    - get_filtered_console_logs: Get console logs filtered by level or content
    - execute_console_command: Execute JavaScript in the console and capture results
    - monitor_network_requests: Monitor and analyze network requests made by the page
    - get_performance_metrics: Get browser performance metrics
    - monitor_page_errors: Monitor and capture JavaScript errors on the page
    - monitor_resource_usage: Monitor resource usage of the browser
    - analyze_console_patterns: Analyze patterns in console logs
    - get_browser_tabs: Get detailed information about all open browser tabs
    - clean_browser_tabs: Clean up browser tabs by closing inactive or least used tabs
    - clear_browser_state: Clear all saved browser state and close all tabs (complete reset)
    """
    
    data_persistence_prompt = """
    Data Persistence tools:
    
    - create_data_session: Create a new session for storing related data
    - persist_page_content: Store page content in the persistence layer
    - persist_element_data: Store element data in the persistence layer
    - create_data_entry: Create a new data entry with custom fields
    - query_persisted_data: Query stored data by various criteria
    - list_data_sessions: List all available data sessions
    - get_session_data: Get all data for a specific session
    - update_persisted_data: Update previously stored data
    - delete_persisted_data: Delete data from persistence
    """
    
    data_export_prompt = """
    Data Export tools:
    
    - export_page_to_format: Export a page to various formats (HTML, PDF, etc.)
    - export_table_data_to_csv: Export table data to CSV format
    - export_form_data_to_json: Export form data to JSON format
    - export_session_data: Export all data from a session to a specified format
    - generate_data_report: Generate a comprehensive report from session data
    - export_visualization: Export a visualization to an image format
    - export_multiple_pages: Export multiple pages in batch
    - create_data_archive: Create a compressed archive of exported data
    """
    
    computer_tools_prompt = """
    Computer Interaction tools:
    
    - computer_use: Unified tool for computer interactions
      This tool can perform multiple operations in a single call:
      
      Screen operations:
      - capture_screen: Capture a screenshot
      - find_on_screen: Find an image on screen
      - get_pixel_color: Get color at specific coordinates
      - wait_for_screen_change: Wait for screen content to change
      
      Mouse operations:
      - move_mouse: Move mouse to coordinates
      - click: Click at position
      - drag: Drag from one point to another
      - scroll: Scroll mouse wheel
      - get_mouse_position: Get current mouse position
      
      Keyboard operations:
      - type_text: Type text
      - press_key: Press a key or key combination
      - hot_key: Press a hotkey combination
      - wait_for_key: Wait for a specific key press
      
      Window operations:
      - get_all_windows: List all windows
      - find_window: Find windows by title
      - activate_window: Bring window to front
      - minimize_window: Minimize a window
      - maximize_window: Maximize a window
      - resize_window: Resize a window
      - move_window: Move a window
      - close_window: Close a window
      - get_active_window: Get active window info
      - arrange_windows: Arrange windows in a layout
      
      System operations:
      - get_system_info: Get system information
      - list_processes: List running processes
      - start_application: Start an application
      - kill_process: Kill a process
      - execute_command: Execute a shell command
      - get_environment_variables: Get environment variables
      - set_environment_variable: Set an environment variable
      - get_clipboard_content: Get clipboard content
      - set_clipboard_content: Set clipboard content
    
    Individual computer interaction tools:
    - capture_screenshot: Capture a screenshot
    - find_text_on_screen: Find text using OCR
    - click_at: Click at specific coordinates
    - type_text: Type text
    - get_active_window: Get active window info
    - list_windows: List all windows
    - system_info: Get system information
    - execute_system_command: Execute a system command
    - get_clipboard: Get clipboard content
    - set_clipboard: Set clipboard content
    """
    
    full_prompt = base_prompt
    
    if has_web_tools:
        full_prompt += web_tools_prompt
    
    if has_advanced_tools:
        full_prompt += advanced_tools_prompt
    
    if has_error_tools:
        full_prompt += error_tools_prompt
    
    # Add new enhanced capabilities prompts
    if has_visual_tools:
        full_prompt += visual_debugging_prompt
    
    if has_console_tools:
        full_prompt += console_integration_prompt
    
    if has_persistence_tools:
        full_prompt += data_persistence_prompt
    
    if has_export_tools:
        full_prompt += data_export_prompt
    
    if has_computer_tools:
        full_prompt += computer_tools_prompt
    
    return full_prompt
