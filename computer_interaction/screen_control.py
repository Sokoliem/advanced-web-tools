"""Screen capture and control functionality."""

import asyncio
import base64
import io
import logging
from typing import Dict, Any, Optional, Tuple, List

try:
    import pyautogui
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
except ImportError:
    pyautogui = None
    Image = None
    np = None

logger = logging.getLogger(__name__)


class ScreenController:
    """Handles screen capture and visual operations."""
    
    def __init__(self):
        self.initialized = pyautogui is not None and Image is not None
        if not self.initialized:
            logger.warning("pyautogui or PIL not available. Screen control features disabled.")
        else:
            # Set up pyautogui safety settings
            pyautogui.PAUSE = 0.1  # Small pause between actions
            pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    
    async def capture_screen(self, 
                           region: Optional[Tuple[int, int, int, int]] = None,
                           highlight_areas: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Capture a screenshot of the screen or a specific region.
        
        Args:
            region: Optional (x, y, width, height) tuple for specific region
            highlight_areas: Optional list of areas to highlight on the screenshot
        
        Returns:
            Dict containing the screenshot as base64 and metadata
        """
        if not self.initialized:
            return {"error": "Screen control not available"}
        
        try:
            # Capture screenshot
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Convert to PIL Image if needed
            if not isinstance(screenshot, Image.Image):
                screenshot = Image.fromarray(np.array(screenshot))
            
            # Add highlights if specified
            if highlight_areas:
                draw = ImageDraw.Draw(screenshot)
                for area in highlight_areas:
                    x, y, w, h = area.get('bounds', (0, 0, 100, 100))
                    color = area.get('color', 'red')
                    thickness = area.get('thickness', 3)
                    draw.rectangle([x, y, x + w, y + h], outline=color, width=thickness)
                    
                    # Add label if provided
                    if 'label' in area:
                        try:
                            font = ImageFont.load_default()
                            draw.text((x, y - 20), area['label'], fill=color, font=font)
                        except:
                            # Fallback if font loading fails
                            draw.text((x, y - 20), area['label'], fill=color)
            
            # Convert to base64
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return {
                "screenshot": img_base64,
                "width": screenshot.width,
                "height": screenshot.height,
                "format": "PNG"
            }
            
        except Exception as e:
            logger.error(f"Error capturing screen: {str(e)}")
            return {"error": f"Failed to capture screen: {str(e)}"}
    
    async def find_on_screen(self, 
                           image_path: Optional[str] = None,
                           image_base64: Optional[str] = None,
                           confidence: float = 0.8,
                           grayscale: bool = False) -> Dict[str, Any]:
        """
        Find an image on screen using template matching.
        
        Args:
            image_path: Path to the template image
            image_base64: Base64 encoded template image
            confidence: Matching confidence threshold (0-1)
            grayscale: Whether to use grayscale matching
        
        Returns:
            Dict containing the location if found
        """
        if not self.initialized:
            return {"error": "Screen control not available"}
        
        try:
            # Load template image
            if image_path:
                template = Image.open(image_path)
            elif image_base64:
                image_data = base64.b64decode(image_base64)
                template = Image.open(io.BytesIO(image_data))
            else:
                return {"error": "No template image provided"}
            
            # Find on screen
            location = pyautogui.locateOnScreen(
                template,
                confidence=confidence,
                grayscale=grayscale
            )
            
            if location:
                center = pyautogui.center(location)
                return {
                    "found": True,
                    "location": {
                        "x": location.left,
                        "y": location.top,
                        "width": location.width,
                        "height": location.height
                    },
                    "center": {
                        "x": center.x,
                        "y": center.y
                    }
                }
            else:
                return {"found": False}
                
        except Exception as e:
            logger.error(f"Error finding on screen: {str(e)}")
            return {"error": f"Failed to find on screen: {str(e)}"}
    
    async def get_pixel_color(self, x: int, y: int) -> Dict[str, Any]:
        """
        Get the color of a pixel at specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
        
        Returns:
            Dict containing the RGB color values
        """
        if not self.initialized:
            return {"error": "Screen control not available"}
        
        try:
            # Get pixel color
            screenshot = pyautogui.screenshot()
            pixel_color = screenshot.getpixel((x, y))
            
            return {
                "color": {
                    "r": pixel_color[0],
                    "g": pixel_color[1],
                    "b": pixel_color[2]
                },
                "hex": f"#{pixel_color[0]:02x}{pixel_color[1]:02x}{pixel_color[2]:02x}"
            }
            
        except Exception as e:
            logger.error(f"Error getting pixel color: {str(e)}")
            return {"error": f"Failed to get pixel color: {str(e)}"}
    
    async def wait_for_screen_change(self, 
                                   region: Optional[Tuple[int, int, int, int]] = None,
                                   timeout: float = 5.0,
                                   poll_interval: float = 0.1) -> Dict[str, Any]:
        """
        Wait for a change in the screen content.
        
        Args:
            region: Optional specific region to monitor
            timeout: Maximum time to wait
            poll_interval: How often to check for changes
        
        Returns:
            Dict indicating if a change was detected
        """
        if not self.initialized:
            return {"error": "Screen control not available"}
        
        try:
            # Capture initial state
            initial_screenshot = await self.capture_screen(region=region)
            initial_data = initial_screenshot.get('screenshot', '')
            
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                await asyncio.sleep(poll_interval)
                
                # Check for change
                current_screenshot = await self.capture_screen(region=region)
                current_data = current_screenshot.get('screenshot', '')
                
                if current_data != initial_data:
                    return {
                        "changed": True,
                        "elapsed_time": asyncio.get_event_loop().time() - start_time
                    }
            
            return {
                "changed": False,
                "timeout": True,
                "elapsed_time": timeout
            }
            
        except Exception as e:
            logger.error(f"Error waiting for screen change: {str(e)}")
            return {"error": f"Failed to wait for screen change: {str(e)}"}
