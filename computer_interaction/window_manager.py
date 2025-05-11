"""Window management functionality."""

import logging
from typing import Dict, Any, List, Optional, Tuple

try:
    import pygetwindow as gw
    import pyautogui
except ImportError:
    gw = None
    pyautogui = None

# Platform-specific imports
try:
    import win32gui
    import win32con
    PLATFORM = "windows"
except ImportError:
    win32gui = None
    win32con = None
    PLATFORM = "other"

logger = logging.getLogger(__name__)


class WindowManager:
    """Handles window management operations."""
    
    def __init__(self):
        self.initialized = gw is not None
        self.platform = PLATFORM
        if not self.initialized:
            logger.warning("pygetwindow not available. Window management features disabled.")
    
    async def get_all_windows(self) -> Dict[str, Any]:
        """
        Get information about all open windows.
        
        Returns:
            Dict containing window information
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            windows = gw.getAllWindows()
            window_list = []
            
            for window in windows:
                if window.title:  # Skip windows without titles
                    window_list.append({
                        "title": window.title,
                        "position": {"x": window.left, "y": window.top},
                        "size": {"width": window.width, "height": window.height},
                        "visible": window.visible,
                        "minimized": window.isMinimized,
                        "maximized": window.isMaximized,
                        "active": window.isActive
                    })
            
            return {
                "windows": window_list,
                "count": len(window_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting windows: {str(e)}")
            return {"error": f"Failed to get windows: {str(e)}"}
    
    async def find_window(self, title: str, exact_match: bool = False) -> Dict[str, Any]:
        """
        Find windows by title.
        
        Args:
            title: Window title to search for
            exact_match: Whether to match exactly or partially
        
        Returns:
            Dict containing found windows
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            if exact_match:
                windows = gw.getWindowsWithTitle(title)
            else:
                all_windows = gw.getAllWindows()
                windows = [w for w in all_windows if title.lower() in w.title.lower()]
            
            window_list = []
            for window in windows:
                window_list.append({
                    "title": window.title,
                    "position": {"x": window.left, "y": window.top},
                    "size": {"width": window.width, "height": window.height},
                    "visible": window.visible,
                    "minimized": window.isMinimized,
                    "maximized": window.isMaximized,
                    "active": window.isActive
                })
            
            return {
                "windows": window_list,
                "count": len(window_list),
                "found": len(window_list) > 0
            }
            
        except Exception as e:
            logger.error(f"Error finding window: {str(e)}")
            return {"error": f"Failed to find window: {str(e)}"}
    
    async def activate_window(self, title: str) -> Dict[str, Any]:
        """
        Activate (bring to front) a window by title.
        
        Args:
            title: Window title
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return {"error": f"Window '{title}' not found"}
            
            window = windows[0]
            
            # Restore if minimized
            if window.isMinimized:
                window.restore()
            
            # Activate the window
            window.activate()
            
            return {
                "success": True,
                "window": {
                    "title": window.title,
                    "active": window.isActive
                }
            }
            
        except Exception as e:
            logger.error(f"Error activating window: {str(e)}")
            return {"error": f"Failed to activate window: {str(e)}"}
    
    async def minimize_window(self, title: str) -> Dict[str, Any]:
        """
        Minimize a window by title.
        
        Args:
            title: Window title
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return {"error": f"Window '{title}' not found"}
            
            window = windows[0]
            window.minimize()
            
            return {
                "success": True,
                "window": {
                    "title": window.title,
                    "minimized": window.isMinimized
                }
            }
            
        except Exception as e:
            logger.error(f"Error minimizing window: {str(e)}")
            return {"error": f"Failed to minimize window: {str(e)}"}
    
    async def maximize_window(self, title: str) -> Dict[str, Any]:
        """
        Maximize a window by title.
        
        Args:
            title: Window title
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return {"error": f"Window '{title}' not found"}
            
            window = windows[0]
            window.maximize()
            
            return {
                "success": True,
                "window": {
                    "title": window.title,
                    "maximized": window.isMaximized
                }
            }
            
        except Exception as e:
            logger.error(f"Error maximizing window: {str(e)}")
            return {"error": f"Failed to maximize window: {str(e)}"}
    
    async def resize_window(self, 
                          title: str, 
                          width: int, 
                          height: int) -> Dict[str, Any]:
        """
        Resize a window.
        
        Args:
            title: Window title
            width: New width
            height: New height
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return {"error": f"Window '{title}' not found"}
            
            window = windows[0]
            window.resizeTo(width, height)
            
            return {
                "success": True,
                "window": {
                    "title": window.title,
                    "size": {"width": window.width, "height": window.height}
                }
            }
            
        except Exception as e:
            logger.error(f"Error resizing window: {str(e)}")
            return {"error": f"Failed to resize window: {str(e)}"}
    
    async def move_window(self, 
                         title: str, 
                         x: int, 
                         y: int) -> Dict[str, Any]:
        """
        Move a window to specific coordinates.
        
        Args:
            title: Window title
            x: X coordinate
            y: Y coordinate
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return {"error": f"Window '{title}' not found"}
            
            window = windows[0]
            window.moveTo(x, y)
            
            return {
                "success": True,
                "window": {
                    "title": window.title,
                    "position": {"x": window.left, "y": window.top}
                }
            }
            
        except Exception as e:
            logger.error(f"Error moving window: {str(e)}")
            return {"error": f"Failed to move window: {str(e)}"}
    
    async def close_window(self, title: str) -> Dict[str, Any]:
        """
        Close a window by title.
        
        Args:
            title: Window title
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                return {"error": f"Window '{title}' not found"}
            
            window = windows[0]
            window.close()
            
            return {
                "success": True,
                "closed": title
            }
            
        except Exception as e:
            logger.error(f"Error closing window: {str(e)}")
            return {"error": f"Failed to close window: {str(e)}"}
    
    async def get_active_window(self) -> Dict[str, Any]:
        """
        Get information about the currently active window.
        
        Returns:
            Dict with active window information
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            active_window = gw.getActiveWindow()
            
            if active_window:
                return {
                    "window": {
                        "title": active_window.title,
                        "position": {"x": active_window.left, "y": active_window.top},
                        "size": {"width": active_window.width, "height": active_window.height},
                        "visible": active_window.visible,
                        "minimized": active_window.isMinimized,
                        "maximized": active_window.isMaximized
                    }
                }
            else:
                return {"window": None}
                
        except Exception as e:
            logger.error(f"Error getting active window: {str(e)}")
            return {"error": f"Failed to get active window: {str(e)}"}
    
    async def arrange_windows(self, arrangement: str = "cascade") -> Dict[str, Any]:
        """
        Arrange windows in a specific layout.
        
        Args:
            arrangement: Layout type ("cascade", "tile_vertical", "tile_horizontal")
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Window management not available"}
        
        try:
            windows = gw.getAllWindows()
            visible_windows = [w for w in windows if w.visible and w.title]
            
            if not visible_windows:
                return {"error": "No visible windows to arrange"}
            
            screen_width, screen_height = pyautogui.size()
            
            if arrangement == "cascade":
                offset = 30
                for i, window in enumerate(visible_windows):
                    x = i * offset
                    y = i * offset
                    window.moveTo(x, y)
                    window.resizeTo(int(screen_width * 0.7), int(screen_height * 0.7))
            
            elif arrangement == "tile_vertical":
                width = screen_width // len(visible_windows)
                for i, window in enumerate(visible_windows):
                    x = i * width
                    window.moveTo(x, 0)
                    window.resizeTo(width, screen_height)
            
            elif arrangement == "tile_horizontal":
                height = screen_height // len(visible_windows)
                for i, window in enumerate(visible_windows):
                    y = i * height
                    window.moveTo(0, y)
                    window.resizeTo(screen_width, height)
            
            else:
                return {"error": f"Unknown arrangement type: {arrangement}"}
            
            return {
                "success": True,
                "arrangement": arrangement,
                "windows_arranged": len(visible_windows)
            }
            
        except Exception as e:
            logger.error(f"Error arranging windows: {str(e)}")
            return {"error": f"Failed to arrange windows: {str(e)}"}
