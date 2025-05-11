"""Register all computer interaction tools."""

import logging
from typing import Dict, Any

from .unified_computer_tool import register_unified_computer_tool
from .screen_control import ScreenController
from .keyboard_mouse import KeyboardMouseController
from .window_manager import WindowManager
from .system_operations import SystemOperations
from .computer_vision import ComputerVisionTools

logger = logging.getLogger(__name__)


def register_all_computer_tools(mcp) -> Dict[str, Any]:
    """
    Register all computer interaction tools with the MCP server.
    
    Args:
        mcp: The MCP server instance
    
    Returns:
        Dict containing all registered tools and components
    """
    logger.info("Registering computer interaction tools...")
    
    # Create instances
    screen_controller = ScreenController()
    keyboard_mouse = KeyboardMouseController()
    window_manager = WindowManager()
    system_ops = SystemOperations()
    computer_vision = ComputerVisionTools()
    
    # Register the unified tool
    register_unified_computer_tool(mcp)
    
    # Also register individual tools for more granular control
    @mcp.tool()
    async def capture_screenshot(
        region: Dict[str, int] = None,
        highlight_areas: list = None
    ) -> Dict[str, Any]:
        """
        Capture a screenshot of the screen or a specific region.
        
        Args:
            region: Optional dict with x, y, width, height for specific region
            highlight_areas: Optional list of areas to highlight
        
        Returns:
            Dict containing the screenshot as base64
        """
        region_tuple = None
        if region:
            region_tuple = (region['x'], region['y'], region['width'], region['height'])
        return await screen_controller.capture_screen(region_tuple, highlight_areas)
    
    @mcp.tool()
    async def find_text_on_screen(
        screenshot_base64: str,
        text: str,
        language: str = 'eng'
    ) -> Dict[str, Any]:
        """
        Find text on screen using OCR.
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            text: Text to find
            language: OCR language
        
        Returns:
            Dict with found text locations
        """
        return await computer_vision.find_text_on_screen(screenshot_base64, text, language)
    
    @mcp.tool()
    async def click_at(
        x: int,
        y: int,
        button: str = 'left',
        clicks: int = 1
    ) -> Dict[str, Any]:
        """
        Click at specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button (left, right, middle)
            clicks: Number of clicks
        
        Returns:
            Dict with result
        """
        return await keyboard_mouse.click(x, y, button, clicks)
    
    @mcp.tool()
    async def type_text(
        text: str,
        interval: float = 0.05,
        press_enter: bool = False
    ) -> Dict[str, Any]:
        """
        Type text using the keyboard.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
            press_enter: Whether to press Enter after typing
        
        Returns:
            Dict with result
        """
        return await keyboard_mouse.type_text(text, interval, press_enter)
    
    @mcp.tool()
    async def get_active_window() -> Dict[str, Any]:
        """
        Get information about the currently active window.
        
        Returns:
            Dict with active window information
        """
        return await window_manager.get_active_window()
    
    @mcp.tool()
    async def list_windows() -> Dict[str, Any]:
        """
        Get information about all open windows.
        
        Returns:
            Dict containing window information
        """
        return await window_manager.get_all_windows()
    
    @mcp.tool()
    async def system_info() -> Dict[str, Any]:
        """
        Get system information.
        
        Returns:
            Dict containing system information
        """
        return await system_ops.get_system_info()
    
    @mcp.tool()
    async def execute_system_command(
        command: str,
        shell: bool = True,
        timeout: float = None
    ) -> Dict[str, Any]:
        """
        Execute a system command.
        
        Args:
            command: Command to execute
            shell: Whether to use shell
            timeout: Optional timeout
        
        Returns:
            Dict with command result
        """
        return await system_ops.execute_command(command, shell, timeout)
    
    @mcp.tool()
    async def get_clipboard() -> Dict[str, Any]:
        """
        Get clipboard content.
        
        Returns:
            Dict with clipboard content
        """
        return await system_ops.get_clipboard_content()
    
    @mcp.tool()
    async def set_clipboard(content: str) -> Dict[str, Any]:
        """
        Set clipboard content.
        
        Args:
            content: Content to set
        
        Returns:
            Dict with result
        """
        return await system_ops.set_clipboard_content(content)
    
    logger.info("Successfully registered computer interaction tools")
    
    return {
        'screen_controller': screen_controller,
        'keyboard_mouse': keyboard_mouse,
        'window_manager': window_manager,
        'system_ops': system_ops,
        'computer_vision': computer_vision
    }
