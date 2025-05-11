"""Computer vision tools for advanced image analysis."""

import logging
import base64
import io
from typing import Dict, Any, List, Optional, Tuple

from .config_manager import computer_config

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
    import pytesseract
except ImportError:
    cv2 = None
    np = None
    Image = None
    pytesseract = None

logger = logging.getLogger(__name__)


class ComputerVisionTools:
    """Advanced computer vision operations."""
    
    def __init__(self):
        self.initialized = all([cv2, np, Image])
        self.ocr_available = pytesseract is not None
        
        if not self.initialized:
            logger.warning("OpenCV or PIL not available. Computer vision features disabled.")
        if not self.ocr_available:
            logger.warning("pytesseract not available. OCR features disabled.")
    
    async def find_text_on_screen(self, 
                                 screenshot_base64: str,
                                 text_to_find: str,
                                 language: str = None) -> Dict[str, Any]:
        """
        Find text on screen using OCR.
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            text_to_find: Text to search for
            language: OCR language
        
        Returns:
            Dict with found text locations
        """
        if not self.ocr_available:
            return {"error": "OCR not available"}
        
        # Use config language if not provided
        if language is None:
            language = computer_config.get('vision', 'ocr_language', 'eng')
        
        try:
            # Decode image
            image_data = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Perform OCR with location data
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            
            # Find matching text
            matches = []
            for i, word in enumerate(data['text']):
                if text_to_find.lower() in word.lower():
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    matches.append({
                        "text": word,
                        "confidence": data['conf'][i],
                        "bounds": {"x": x, "y": y, "width": w, "height": h},
                        "center": {"x": x + w//2, "y": y + h//2}
                    })
            
            return {
                "found": len(matches) > 0,
                "matches": matches,
                "count": len(matches)
            }
            
        except Exception as e:
            logger.error(f"Error finding text on screen: {str(e)}")
            return {"error": f"Failed to find text: {str(e)}"}
    
    async def detect_elements(self, 
                            screenshot_base64: str,
                            element_type: str = "button") -> Dict[str, Any]:
        """
        Detect UI elements in screenshot.
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            element_type: Type of element to detect (button, textbox, etc.)
        
        Returns:
            Dict with detected elements
        """
        if not self.initialized:
            return {"error": "Computer vision not available"}
        
        try:
            # Decode image
            image_data = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_data))
            img_array = np.array(image)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Different detection methods based on element type
            if element_type == "button":
                elements = self._detect_buttons(gray)
            elif element_type == "textbox":
                elements = self._detect_textboxes(gray)
            elif element_type == "edge":
                elements = self._detect_edges(gray)
            else:
                return {"error": f"Unknown element type: {element_type}"}
            
            return {
                "elements": elements,
                "count": len(elements),
                "type": element_type
            }
            
        except Exception as e:
            logger.error(f"Error detecting elements: {str(e)}")
            return {"error": f"Failed to detect elements: {str(e)}"}
    
    def _detect_buttons(self, gray_image) -> List[Dict[str, Any]]:
        """Detect button-like elements."""
        buttons = []
        
        # Use edge detection
        edges = cv2.Canny(gray_image, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio and size for button-like shapes
            aspect_ratio = w / float(h)
            if 0.5 < aspect_ratio < 5 and w > 30 and h > 20:
                buttons.append({
                    "bounds": {"x": x, "y": y, "width": w, "height": h},
                    "center": {"x": x + w//2, "y": y + h//2},
                    "area": w * h,
                    "aspect_ratio": aspect_ratio
                })
        
        return buttons
    
    def _detect_textboxes(self, gray_image) -> List[Dict[str, Any]]:
        """Detect textbox-like elements."""
        textboxes = []
        
        # Apply threshold
        _, thresh = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter for textbox-like shapes
            aspect_ratio = w / float(h)
            if aspect_ratio > 3 and w > 50 and h > 15:
                textboxes.append({
                    "bounds": {"x": x, "y": y, "width": w, "height": h},
                    "center": {"x": x + w//2, "y": y + h//2},
                    "area": w * h,
                    "aspect_ratio": aspect_ratio
                })
        
        return textboxes
    
    def _detect_edges(self, gray_image) -> List[Dict[str, Any]]:
        """Detect edges in the image."""
        edges = cv2.Canny(gray_image, 50, 150)
        
        # Find lines using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=50, maxLineGap=10)
        
        edge_list = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                edge_list.append({
                    "start": {"x": x1, "y": y1},
                    "end": {"x": x2, "y": y2},
                    "length": np.sqrt((x2-x1)**2 + (y2-y1)**2)
                })
        
        return edge_list
    
    async def compare_screenshots(self, 
                                screenshot1_base64: str,
                                screenshot2_base64: str,
                                method: str = "structural") -> Dict[str, Any]:
        """
        Compare two screenshots.
        
        Args:
            screenshot1_base64: First screenshot
            screenshot2_base64: Second screenshot
            method: Comparison method (structural, histogram, pixel)
        
        Returns:
            Dict with comparison results
        """
        if not self.initialized:
            return {"error": "Computer vision not available"}
        
        try:
            # Decode images
            img1_data = base64.b64decode(screenshot1_base64)
            img2_data = base64.b64decode(screenshot2_base64)
            
            img1 = cv2.imdecode(np.frombuffer(img1_data, np.uint8), cv2.IMREAD_COLOR)
            img2 = cv2.imdecode(np.frombuffer(img2_data, np.uint8), cv2.IMREAD_COLOR)
            
            if method == "structural":
                # Structural Similarity Index
                from skimage.metrics import structural_similarity as ssim
                gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
                
                score, diff = ssim(gray1, gray2, full=True)
                diff = (diff * 255).astype("uint8")
                
                return {
                    "similarity": score,
                    "identical": score > 0.95,
                    "method": "SSIM"
                }
            
            elif method == "histogram":
                # Histogram comparison
                hist1 = cv2.calcHist([img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                hist2 = cv2.calcHist([img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                
                score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                
                return {
                    "similarity": score,
                    "identical": score > 0.95,
                    "method": "Histogram"
                }
            
            elif method == "pixel":
                # Pixel-wise comparison
                if img1.shape != img2.shape:
                    return {
                        "error": "Images have different dimensions",
                        "shape1": img1.shape,
                        "shape2": img2.shape
                    }
                
                diff = cv2.absdiff(img1, img2)
                non_zero = np.count_nonzero(diff)
                total_pixels = img1.shape[0] * img1.shape[1] * img1.shape[2]
                similarity = 1 - (non_zero / total_pixels)
                
                return {
                    "similarity": similarity,
                    "identical": similarity > 0.99,
                    "different_pixels": non_zero,
                    "total_pixels": total_pixels,
                    "method": "Pixel"
                }
            
            else:
                return {"error": f"Unknown comparison method: {method}"}
            
        except Exception as e:
            logger.error(f"Error comparing screenshots: {str(e)}")
            return {"error": f"Failed to compare screenshots: {str(e)}"}
    
    async def find_template(self, 
                          screenshot_base64: str,
                          template_base64: str,
                          threshold: float = 0.8) -> Dict[str, Any]:
        """
        Find a template image within a screenshot.
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            template_base64: Base64 encoded template
            threshold: Matching threshold
        
        Returns:
            Dict with match locations
        """
        if not self.initialized:
            return {"error": "Computer vision not available"}
        
        try:
            # Decode images
            screen_data = base64.b64decode(screenshot_base64)
            template_data = base64.b64decode(template_base64)
            
            screen = cv2.imdecode(np.frombuffer(screen_data, np.uint8), cv2.IMREAD_COLOR)
            template = cv2.imdecode(np.frombuffer(template_data, np.uint8), cv2.IMREAD_COLOR)
            
            # Perform template matching
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            
            # Find locations where matching exceeds threshold
            locations = np.where(result >= threshold)
            
            matches = []
            for pt in zip(*locations[::-1]):
                matches.append({
                    "position": {"x": pt[0], "y": pt[1]},
                    "confidence": result[pt[1], pt[0]],
                    "bounds": {
                        "x": pt[0],
                        "y": pt[1],
                        "width": template.shape[1],
                        "height": template.shape[0]
                    }
                })
            
            return {
                "found": len(matches) > 0,
                "matches": matches,
                "count": len(matches)
            }
            
        except Exception as e:
            logger.error(f"Error finding template: {str(e)}")
            return {"error": f"Failed to find template: {str(e)}"}
