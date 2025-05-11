"""Keyboard and mouse control functionality."""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    import pyautogui
    import keyboard
    import mouse
except ImportError:
    pyautogui = None
    keyboard = None
    mouse = None

logger = logging.getLogger(__name__)


class KeyboardMouseController:
    """Handles keyboard and mouse operations."""
    
    def __init__(self):
        self.initialized = pyautogui is not None
        if not self.initialized:
            logger.warning("pyautogui not available. Keyboard/mouse control features disabled.")
        
        # Use keyboard/mouse libraries if available for more advanced features
        self.keyboard_available = keyboard is not None
        self.mouse_available = mouse is not None
    
    async def move_mouse(self, 
                        x: int, 
                        y: int, 
                        duration: float = 0.5,
                        relative: bool = False) -> Dict[str, Any]:
        """
        Move the mouse to specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Duration of the movement
            relative: Whether the movement is relative to current position
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Mouse control not available"}
        
        try:
            if relative:
                pyautogui.moveRel(x, y, duration=duration)
            else:
                pyautogui.moveTo(x, y, duration=duration)
            
            current_x, current_y = pyautogui.position()
            return {
                "success": True,
                "position": {"x": current_x, "y": current_y}
            }
        except Exception as e:
            logger.error(f"Error moving mouse: {str(e)}")
            return {"error": f"Failed to move mouse: {str(e)}"}
    
    async def click(self, 
                   x: Optional[int] = None, 
                   y: Optional[int] = None,
                   button: str = 'left',
                   clicks: int = 1,
                   interval: float = 0.1) -> Dict[str, Any]:
        """
        Click the mouse.
        
        Args:
            x: Optional X coordinate (clicks at current position if not provided)
            y: Optional Y coordinate
            button: 'left', 'right', or 'middle'
            clicks: Number of clicks
            interval: Interval between clicks
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Mouse control not available"}
        
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
            else:
                pyautogui.click(clicks=clicks, interval=interval, button=button)
            
            current_x, current_y = pyautogui.position()
            return {
                "success": True,
                "position": {"x": current_x, "y": current_y},
                "button": button,
                "clicks": clicks
            }
        except Exception as e:
            logger.error(f"Error clicking mouse: {str(e)}")
            return {"error": f"Failed to click mouse: {str(e)}"}
    
    async def drag(self,
                  start_x: int,
                  start_y: int,
                  end_x: int,
                  end_y: int,
                  duration: float = 1.0,
                  button: str = 'left') -> Dict[str, Any]:
        """
        Drag the mouse from one point to another.
        
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Duration of the drag
            button: Mouse button to use
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Mouse control not available"}
        
        try:
            pyautogui.moveTo(start_x, start_y)
            pyautogui.dragTo(end_x, end_y, duration=duration, button=button)
            
            return {
                "success": True,
                "start": {"x": start_x, "y": start_y},
                "end": {"x": end_x, "y": end_y}
            }
        except Exception as e:
            logger.error(f"Error dragging mouse: {str(e)}")
            return {"error": f"Failed to drag mouse: {str(e)}"}
    
    async def scroll(self, 
                    clicks: int, 
                    x: Optional[int] = None,
                    y: Optional[int] = None) -> Dict[str, Any]:
        """
        Scroll the mouse wheel.
        
        Args:
            clicks: Number of scroll clicks (positive=up, negative=down)
            x: Optional X coordinate
            y: Optional Y coordinate
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Mouse control not available"}
        
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            
            pyautogui.scroll(clicks)
            
            return {
                "success": True,
                "scrolled": clicks,
                "direction": "up" if clicks > 0 else "down"
            }
        except Exception as e:
            logger.error(f"Error scrolling: {str(e)}")
            return {"error": f"Failed to scroll: {str(e)}"}
    
    async def type_text(self, 
                       text: str, 
                       interval: float = 0.05,
                       press_enter: bool = False) -> Dict[str, Any]:
        """
        Type text using the keyboard.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
            press_enter: Whether to press Enter after typing
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Keyboard control not available"}
        
        try:
            pyautogui.typewrite(text, interval=interval)
            
            if press_enter:
                pyautogui.press('enter')
            
            return {
                "success": True,
                "typed": text,
                "length": len(text)
            }
        except Exception as e:
            logger.error(f"Error typing text: {str(e)}")
            return {"error": f"Failed to type text: {str(e)}"}
    
    async def press_key(self, 
                       key: Union[str, List[str]], 
                       modifiers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Press a key or key combination.
        
        Args:
            key: Key to press (or list for combo)
            modifiers: Optional modifier keys (ctrl, alt, shift, cmd)
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Keyboard control not available"}
        
        try:
            if modifiers:
                # Press with modifiers
                with pyautogui.hold(modifiers):
                    if isinstance(key, list):
                        pyautogui.hotkey(*key)
                    else:
                        pyautogui.press(key)
            else:
                if isinstance(key, list):
                    pyautogui.hotkey(*key)
                else:
                    pyautogui.press(key)
            
            return {
                "success": True,
                "key": key,
                "modifiers": modifiers
            }
        except Exception as e:
            logger.error(f"Error pressing key: {str(e)}")
            return {"error": f"Failed to press key: {str(e)}"}
    
    async def hot_key(self, *keys: str) -> Dict[str, Any]:
        """
        Press a hotkey combination.
        
        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c')
        
        Returns:
            Dict with the result
        """
        if not self.initialized:
            return {"error": "Keyboard control not available"}
        
        try:
            pyautogui.hotkey(*keys)
            
            return {
                "success": True,
                "keys": list(keys)
            }
        except Exception as e:
            logger.error(f"Error pressing hotkey: {str(e)}")
            return {"error": f"Failed to press hotkey: {str(e)}"}
    
    async def get_mouse_position(self) -> Dict[str, Any]:
        """
        Get the current mouse position.
        
        Returns:
            Dict with the mouse position
        """
        if not self.initialized:
            return {"error": "Mouse control not available"}
        
        try:
            x, y = pyautogui.position()
            return {
                "position": {"x": x, "y": y}
            }
        except Exception as e:
            logger.error(f"Error getting mouse position: {str(e)}")
            return {"error": f"Failed to get mouse position: {str(e)}"}
    
    async def wait_for_key(self, 
                          key: str, 
                          timeout: float = 5.0) -> Dict[str, Any]:
        """
        Wait for a specific key press.
        
        Args:
            key: Key to wait for
            timeout: Maximum time to wait
        
        Returns:
            Dict indicating if the key was pressed
        """
        if not self.keyboard_available:
            return {"error": "Advanced keyboard control not available"}
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Set up a flag to track key press
            key_pressed = False
            
            def on_key_press(event):
                nonlocal key_pressed
                if event.name == key:
                    key_pressed = True
            
            # Register the callback
            keyboard.on_press_key(key, on_key_press)
            
            # Wait for key press or timeout
            while not key_pressed and (asyncio.get_event_loop().time() - start_time) < timeout:
                await asyncio.sleep(0.1)
            
            # Unregister the callback
            keyboard.unhook_key(key)
            
            return {
                "pressed": key_pressed,
                "elapsed_time": asyncio.get_event_loop().time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error waiting for key: {str(e)}")
            return {"error": f"Failed to wait for key: {str(e)}"}
