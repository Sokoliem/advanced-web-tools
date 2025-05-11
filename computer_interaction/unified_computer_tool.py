"""Unified computer interaction tool for MCP."""

import logging
from typing import Any, Dict, List, Optional

from .screen_control import ScreenController
from .keyboard_mouse import KeyboardMouseController
from .window_manager import WindowManager
from .system_operations import SystemOperations
from .computer_vision import ComputerVisionTools

logger = logging.getLogger(__name__)


class UnifiedComputerTool:
    """Unified interface for all computer interaction operations."""
    
    def __init__(self):
        self.screen = ScreenController()
        self.keyboard_mouse = KeyboardMouseController()
        self.window_manager = WindowManager()
        self.system_ops = SystemOperations()
        self.computer_vision = ComputerVisionTools()
    
    async def execute_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a sequence of computer operations.
        
        Args:
            operations: List of operations to execute
        
        Returns:
            Dict with results from all operations
        """
        results = []
        
        for i, operation in enumerate(operations):
            try:
                op_type = operation.get("type")
                params = operation.get("params", {})
                
                result = await self._execute_single_operation(op_type, params)
                results.append({
                    "operation_index": i,
                    "type": op_type,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Error in operation {i}: {str(e)}")
                results.append({
                    "operation_index": i,
                    "type": op_type,
                    "error": str(e)
                })
        
        return {
            "results": results,
            "total_operations": len(operations),
            "successful_operations": sum(1 for r in results if "error" not in r)
        }
    
    async def _execute_single_operation(self, op_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single operation."""
        
        # Screen operations
        if op_type == "capture_screen":
            return await self.screen.capture_screen(**params)
        elif op_type == "find_on_screen":
            return await self.screen.find_on_screen(**params)
        elif op_type == "get_pixel_color":
            return await self.screen.get_pixel_color(**params)
        elif op_type == "wait_for_screen_change":
            return await self.screen.wait_for_screen_change(**params)
        
        # Mouse operations
        elif op_type == "move_mouse":
            return await self.keyboard_mouse.move_mouse(**params)
        elif op_type == "click":
            return await self.keyboard_mouse.click(**params)
        elif op_type == "drag":
            return await self.keyboard_mouse.drag(**params)
        elif op_type == "scroll":
            return await self.keyboard_mouse.scroll(**params)
        elif op_type == "get_mouse_position":
            return await self.keyboard_mouse.get_mouse_position()
        
        # Keyboard operations
        elif op_type == "type_text":
            return await self.keyboard_mouse.type_text(**params)
        elif op_type == "press_key":
            return await self.keyboard_mouse.press_key(**params)
        elif op_type == "hot_key":
            return await self.keyboard_mouse.hot_key(**params)
        elif op_type == "wait_for_key":
            return await self.keyboard_mouse.wait_for_key(**params)
        
        # Window operations
        elif op_type == "get_all_windows":
            return await self.window_manager.get_all_windows()
        elif op_type == "find_window":
            return await self.window_manager.find_window(**params)
        elif op_type == "activate_window":
            return await self.window_manager.activate_window(**params)
        elif op_type == "minimize_window":
            return await self.window_manager.minimize_window(**params)
        elif op_type == "maximize_window":
            return await self.window_manager.maximize_window(**params)
        elif op_type == "resize_window":
            return await self.window_manager.resize_window(**params)
        elif op_type == "move_window":
            return await self.window_manager.move_window(**params)
        elif op_type == "close_window":
            return await self.window_manager.close_window(**params)
        elif op_type == "get_active_window":
            return await self.window_manager.get_active_window()
        elif op_type == "arrange_windows":
            return await self.window_manager.arrange_windows(**params)
        
        # System operations
        elif op_type == "get_system_info":
            return await self.system_ops.get_system_info()
        elif op_type == "list_processes":
            return await self.system_ops.list_processes(**params)
        elif op_type == "start_application":
            return await self.system_ops.start_application(**params)
        elif op_type == "kill_process":
            return await self.system_ops.kill_process(**params)
        elif op_type == "execute_command":
            return await self.system_ops.execute_command(**params)
        elif op_type == "get_environment_variables":
            return await self.system_ops.get_environment_variables()
        elif op_type == "set_environment_variable":
            return await self.system_ops.set_environment_variable(**params)
        elif op_type == "get_clipboard_content":
            return await self.system_ops.get_clipboard_content()
        elif op_type == "set_clipboard_content":
            return await self.system_ops.set_clipboard_content(**params)
        
        # Computer vision operations
        elif op_type == "find_text_on_screen":
            return await self.computer_vision.find_text_on_screen(**params)
        elif op_type == "detect_elements":
            return await self.computer_vision.detect_elements(**params)
        elif op_type == "compare_screenshots":
            return await self.computer_vision.compare_screenshots(**params)
        elif op_type == "find_template":
            return await self.computer_vision.find_template(**params)
        
        else:
            return {"error": f"Unknown operation type: {op_type}"}


# Global instance
unified_computer_tool = UnifiedComputerTool()


def register_unified_computer_tool(mcp, tool_instance=None):
    """Register the unified computer interaction tool with the MCP server."""
    
    if tool_instance is None:
        tool_instance = unified_computer_tool
    
    @mcp.tool()
    async def computer_use(operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform computer use operations.
        
        Args:
            operations: List of operations to perform
            
        Operation format:
            {
                "type": "operation_type",
                "params": {
                    # Operation-specific parameters
                }
            }
            
        Supported operation types:
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
        
        Computer vision operations:
        - find_text_on_screen: Find text using OCR
        - detect_elements: Detect UI elements
        - compare_screenshots: Compare two screenshots
        - find_template: Find template image in screenshot
        
        Returns:
            Dict with operation results
        """
        return await tool_instance.execute_operations(operations)
