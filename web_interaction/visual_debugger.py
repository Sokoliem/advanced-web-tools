"""Visual Debugging Tools for Web Interaction.

This module provides advanced visualization and debugging tools for web interactions,
allowing developers to better understand page states, element interactions, 
and browser behavior.
"""

import asyncio
import json
import logging
import time
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class VisualDebugger:
    """Provides visual debugging capabilities for web interactions."""
    
    def __init__(self, browser_manager, storage_dir=None):
        """Initialize the visual debugger."""
        self.browser_manager = browser_manager
        
        # Set storage directory
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".claude_web_interaction")
        
        # Set up debug directories
        self.debug_dir = Path(self.storage_dir) / 'debug'
        self.debug_dir.mkdir(exist_ok=True)
        
        self.screenshots_dir = self.debug_dir / 'screenshots'
        self.screenshots_dir.mkdir(exist_ok=True)
        
        self.visualizations_dir = self.debug_dir / 'visualizations'
        self.visualizations_dir.mkdir(exist_ok=True)
        
        self.dom_snapshots_dir = self.debug_dir / 'dom_snapshots'
        self.dom_snapshots_dir.mkdir(exist_ok=True)
        
        self.timeline_dir = self.debug_dir / 'timeline'
        self.timeline_dir.mkdir(exist_ok=True)
        
        # Store debug history
        self.debug_history = {}
        self.session_start_time = time.time()
        
        # Load any existing debug history
        self._load_debug_history()
    
    def _load_debug_history(self):
        """Load debug history from storage if available."""
        history_file = self.debug_dir / 'debug_history.json'
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    self.debug_history = history
                    logger.info(f"Loaded debug history with {len(history)} entries")
            except Exception as e:
                logger.error(f"Error loading debug history: {str(e)}")
    
    def _save_debug_history(self):
        """Save debug history to storage."""
        history_file = self.debug_dir / 'debug_history.json'
        try:
            with open(history_file, 'w') as f:
                json.dump(self.debug_history, f, indent=2)
                logger.info(f"Saved debug history with {len(self.debug_history)} entries")
        except Exception as e:
            logger.error(f"Error saving debug history: {str(e)}")
    
    async def take_element_screenshot(self, page, selector, highlight=True, annotation=None):
        """
        Take a screenshot of a specific element with optional highlighting and annotation.
        
        Args:
            page: The page containing the element
            selector: CSS selector for the element
            highlight: Whether to highlight the element
            annotation: Optional text annotation to add to the screenshot
            
        Returns:
            Path to the screenshot file
        """
        try:
            # Find the element
            element = await page.query_selector(selector)
            if not element:
                logger.error(f"Element not found with selector: {selector}")
                return None
            
            # Create a unique filename
            timestamp = int(time.time() * 1000)
            filename = f"element_{timestamp}.png"
            screenshot_path = str(self.screenshots_dir / filename)
            
            # Apply highlight if requested
            if highlight:
                # Add highlight effect to element
                await page.evaluate("""
                (selector) => {
                    const element = document.querySelector(selector);
                    if (!element) return false;
                    
                    // Store original styles
                    element.__originalStyles = {
                        outline: element.style.outline,
                        boxShadow: element.style.boxShadow,
                        position: element.style.position,
                        zIndex: element.style.zIndex
                    };
                    
                    // Apply highlight effect
                    element.style.outline = '3px solid red';
                    element.style.boxShadow = '0 0 10px rgba(255, 0, 0, 0.7)';
                    element.style.position = 'relative';
                    element.style.zIndex = '9999';
                    
                    return true;
                }
                """, selector)
            
            # Take the screenshot
            await element.screenshot(path=screenshot_path)
            
            # If annotation is provided, add it to the image
            if annotation:
                # We'll use browser to add annotation via HTML/CSS
                # Create a temporary page for annotation
                temp_page = await self.browser_manager.context.new_page()
                
                # Read the screenshot as base64
                with open(screenshot_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # Create HTML with annotation
                html = f"""
                <html>
                <head>
                    <style>
                        body {{ margin: 0; padding: 0; }}
                        .container {{ position: relative; display: inline-block; }}
                        .annotation {{ 
                            position: absolute; 
                            bottom: 0; 
                            left: 0; 
                            background-color: rgba(0, 0, 0, 0.7); 
                            color: white; 
                            padding: 5px 10px; 
                            font-family: Arial, sans-serif; 
                            font-size: 14px; 
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <img src="data:image/png;base64,{img_data}" />
                        <div class="annotation">{annotation}</div>
                    </div>
                </body>
                </html>
                """
                
                # Set content and take screenshot
                await temp_page.set_content(html)
                
                # Wait for image to load
                await temp_page.wait_for_selector('img')
                
                # Take screenshot of the container
                container = await temp_page.query_selector('.container')
                await container.screenshot(path=screenshot_path)
                
                # Close the temporary page
                await temp_page.close()
            
            # Remove highlight if it was applied
            if highlight:
                await page.evaluate("""
                (selector) => {
                    const element = document.querySelector(selector);
                    if (!element || !element.__originalStyles) return false;
                    
                    // Restore original styles
                    element.style.outline = element.__originalStyles.outline || '';
                    element.style.boxShadow = element.__originalStyles.boxShadow || '';
                    element.style.position = element.__originalStyles.position || '';
                    element.style.zIndex = element.__originalStyles.zIndex || '';
                    
                    // Clean up
                    delete element.__originalStyles;
                    
                    return true;
                }
                """, selector)
            
            # Add to debug history
            page_id = next((k for k, v in self.browser_manager.active_pages.items() if v == page), "unknown")
            history_entry = {
                "type": "element_screenshot",
                "timestamp": timestamp,
                "page_id": page_id,
                "selector": selector,
                "path": screenshot_path,
                "annotation": annotation
            }
            
            if page_id not in self.debug_history:
                self.debug_history[page_id] = []
            
            self.debug_history[page_id].append(history_entry)
            self._save_debug_history()
            
            logger.info(f"Element screenshot saved to {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error taking element screenshot: {str(e)}")
            return None
    
    async def take_full_page_screenshot(self, page, annotations=None):
        """
        Take a screenshot of the full page with optional annotations.
        
        Args:
            page: The page to screenshot
            annotations: Optional list of annotations, each containing:
                {
                    "selector": CSS selector for the element,
                    "label": Text label for the annotation,
                    "color": Color for the highlight (optional)
                }
            
        Returns:
            Path to the screenshot file
        """
        try:
            # Create a unique filename
            timestamp = int(time.time() * 1000)
            filename = f"page_{timestamp}.png"
            screenshot_path = str(self.screenshots_dir / filename)
            
            # If annotations provided, add them before taking screenshot
            if annotations:
                # Add highlight and annotations to the page
                annotation_script = """
                (annotations) => {
                    // Create a container for annotations
                    const container = document.createElement('div');
                    container.id = '__debug_annotations';
                    container.style.position = 'absolute';
                    container.style.top = '0';
                    container.style.left = '0';
                    container.style.width = '100%';
                    container.style.height = '100%';
                    container.style.pointerEvents = 'none';
                    container.style.zIndex = '9999';
                    document.body.appendChild(container);
                    
                    // Store original styles for cleanup
                    window.__originalElementStyles = {};
                    
                    // Process each annotation
                    annotations.forEach((annotation, index) => {
                        const element = document.querySelector(annotation.selector);
                        if (!element) return;
                        
                        // Store original styles
                        window.__originalElementStyles[index] = {
                            outline: element.style.outline,
                            boxShadow: element.style.boxShadow
                        };
                        
                        // Highlight element
                        const color = annotation.color || '#FF0000';
                        element.style.outline = `3px solid ${color}`;
                        element.style.boxShadow = `0 0 10px ${color}80`;
                        
                        // Add label
                        if (annotation.label) {
                            const rect = element.getBoundingClientRect();
                            const label = document.createElement('div');
                            label.textContent = annotation.label;
                            label.style.position = 'absolute';
                            label.style.left = rect.left + 'px';
                            label.style.top = (rect.top - 25) + 'px';
                            label.style.backgroundColor = color;
                            label.style.color = 'white';
                            label.style.padding = '2px 5px';
                            label.style.borderRadius = '3px';
                            label.style.fontSize = '12px';
                            label.style.fontFamily = 'Arial, sans-serif';
                            label.style.pointerEvents = 'none';
                            label.style.zIndex = '10000';
                            container.appendChild(label);
                        }
                    });
                    
                    return true;
                }
                """
                
                await page.evaluate(annotation_script, annotations)
            
            # Take the screenshot
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # Clean up annotations if they were added
            if annotations:
                cleanup_script = """
                () => {
                    // Remove annotation container
                    const container = document.getElementById('__debug_annotations');
                    if (container) {
                        container.remove();
                    }
                    
                    // Restore original element styles
                    if (window.__originalElementStyles) {
                        Object.keys(window.__originalElementStyles).forEach(index => {
                            const selector = annotations[index].selector;
                            const element = document.querySelector(selector);
                            const originalStyles = window.__originalElementStyles[index];
                            
                            if (element && originalStyles) {
                                element.style.outline = originalStyles.outline || '';
                                element.style.boxShadow = originalStyles.boxShadow || '';
                            }
                        });
                        
                        delete window.__originalElementStyles;
                    }
                    
                    return true;
                }
                """
                
                await page.evaluate(cleanup_script)
            
            # Add to debug history
            page_id = next((k for k, v in self.browser_manager.active_pages.items() if v == page), "unknown")
            history_entry = {
                "type": "page_screenshot",
                "timestamp": timestamp,
                "page_id": page_id,
                "path": screenshot_path,
                "annotations": annotations
            }
            
            if page_id not in self.debug_history:
                self.debug_history[page_id] = []
            
            self.debug_history[page_id].append(history_entry)
            self._save_debug_history()
            
            logger.info(f"Full page screenshot saved to {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error taking full page screenshot: {str(e)}")
            return None
    
    async def capture_dom_snapshot(self, page, include_styles=True):
        """
        Capture a snapshot of the DOM with optional styles.
        
        Args:
            page: The page to capture
            include_styles: Whether to include computed styles for elements
            
        Returns:
            Path to the DOM snapshot file
        """
        try:
            # Create a unique filename
            timestamp = int(time.time() * 1000)
            filename = f"dom_{timestamp}.json"
            snapshot_path = str(self.dom_snapshots_dir / filename)
            
            # DOM capture script
            dom_script = """
            (includeStyles) => {
                function processElement(element, includeStyles) {
                    // Skip script, style, and hidden elements
                    if (
                        element.tagName === 'SCRIPT' || 
                        element.tagName === 'STYLE' || 
                        element.style.display === 'none' || 
                        element.style.visibility === 'hidden'
                    ) {
                        return null;
                    }
                    
                    // Basic element info
                    const result = {
                        tagName: element.tagName,
                        id: element.id || null,
                        className: element.className || null,
                        textContent: element.textContent ? element.textContent.trim().substring(0, 100) : null,
                        attributes: {},
                        children: []
                    };
                    
                    // Add position info
                    const rect = element.getBoundingClientRect();
                    result.position = {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        visible: rect.width > 0 && rect.height > 0
                    };
                    
                    // Add element attributes
                    for (const attr of element.attributes) {
                        result.attributes[attr.name] = attr.value;
                    }
                    
                    // Add computed styles if requested
                    if (includeStyles) {
                        const styles = window.getComputedStyle(element);
                        result.styles = {};
                        
                        // Include most important styles
                        const importantStyles = [
                            'display', 'position', 'z-index', 'visibility',
                            'backgroundColor', 'color', 'fontSize', 'fontWeight',
                            'margin', 'padding', 'border',
                            'overflow', 'opacity'
                        ];
                        
                        importantStyles.forEach(style => {
                            result.styles[style] = styles[style];
                        });
                    }
                    
                    // Process children
                    for (const child of element.children) {
                        const childResult = processElement(child, includeStyles);
                        if (childResult) {
                            result.children.push(childResult);
                        }
                    }
                    
                    return result;
                }
                
                return processElement(document.documentElement, includeStyles);
            }
            """
            
            # Execute DOM capture
            dom_data = await page.evaluate(dom_script, include_styles)
            
            # Add page metadata
            page_id = next((k for k, v in self.browser_manager.active_pages.items() if v == page), "unknown")
            metadata = {
                "timestamp": timestamp,
                "page_id": page_id,
                "url": page.url,
                "title": await page.title(),
                "viewport": await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })"),
                "include_styles": include_styles
            }
            
            # Combine data
            snapshot_data = {
                "metadata": metadata,
                "dom": dom_data
            }
            
            # Save to file
            with open(snapshot_path, 'w') as f:
                json.dump(snapshot_data, f, indent=2)
            
            # Add to debug history
            history_entry = {
                "type": "dom_snapshot",
                "timestamp": timestamp,
                "page_id": page_id,
                "path": snapshot_path,
                "url": page.url
            }
            
            if page_id not in self.debug_history:
                self.debug_history[page_id] = []
            
            self.debug_history[page_id].append(history_entry)
            self._save_debug_history()
            
            logger.info(f"DOM snapshot saved to {snapshot_path}")
            return snapshot_path
            
        except Exception as e:
            logger.error(f"Error capturing DOM snapshot: {str(e)}")
            return None
    
    async def visualize_element_state(self, page, selector, include_styles=True, include_events=True, include_ancestors=True):
        """
        Create a detailed visualization of an element's state.
        
        Args:
            page: The page containing the element
            selector: CSS selector for the element
            include_styles: Whether to include computed styles
            include_events: Whether to include event listeners
            include_ancestors: Whether to include ancestor elements
            
        Returns:
            Path to the visualization file
        """
        try:
            # Create a unique filename
            timestamp = int(time.time() * 1000)
            filename = f"element_state_{timestamp}.html"
            visualization_path = str(self.visualizations_dir / filename)
            
            # Take a screenshot of the element
            element = await page.query_selector(selector)
            if not element:
                logger.error(f"Element not found with selector: {selector}")
                return None
                
            screenshot_path = str(self.screenshots_dir / f"element_vis_{timestamp}.png")
            await element.screenshot(path=screenshot_path)
            
            # Element state capture script
            state_script = """
            (selector, includeStyles, includeEvents, includeAncestors) => {
                const element = document.querySelector(selector);
                if (!element) return null;
                
                // Basic element info
                const result = {
                    tagName: element.tagName,
                    id: element.id || null,
                    className: element.className || null,
                    textContent: element.textContent ? element.textContent.trim() : null,
                    attributes: {},
                    children: []
                };
                
                // Add attributes
                for (const attr of element.attributes) {
                    result.attributes[attr.name] = attr.value;
                }
                
                // Add position info
                const rect = element.getBoundingClientRect();
                result.position = {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    visible: rect.width > 0 && rect.height > 0
                };
                
                // Add computed styles if requested
                if (includeStyles) {
                    const styles = window.getComputedStyle(element);
                    result.styles = {};
                    
                    // Get all styles
                    for (const style of styles) {
                        result.styles[style] = styles[style];
                    }
                }
                
                // Add event listeners if requested
                if (includeEvents) {
                    // Get event listeners is not possible directly in the browser
                    // We can only check for inline event handlers
                    result.events = {};
                    
                    const eventAttributes = [
                        'onclick', 'onmouseover', 'onmouseout', 'onkeydown', 'onkeyup',
                        'onsubmit', 'onchange', 'onfocus', 'onblur', 'oninput'
                    ];
                    
                    eventAttributes.forEach(attr => {
                        if (element[attr]) {
                            result.events[attr] = true;
                        }
                    });
                }
                
                // Add ancestors if requested
                if (includeAncestors) {
                    result.ancestors = [];
                    let parent = element.parentElement;
                    
                    while (parent) {
                        const parentInfo = {
                            tagName: parent.tagName,
                            id: parent.id || null,
                            className: parent.className || null,
                            selector: getSelector(parent)
                        };
                        
                        result.ancestors.unshift(parentInfo);
                        parent = parent.parentElement;
                    }
                }
                
                // Helper function to get a unique selector for an element
                function getSelector(el) {
                    if (el.id) {
                        return '#' + el.id;
                    }
                    
                    let selector = el.tagName.toLowerCase();
                    
                    if (el.className) {
                        selector += '.' + el.className.split(' ').join('.');
                    }
                    
                    // Add position among siblings if needed
                    if (!el.id) {
                        const siblings = Array.from(el.parentElement.children).filter(s => s.tagName === el.tagName);
                        if (siblings.length > 1) {
                            const index = siblings.indexOf(el);
                            selector += `:nth-child(${index + 1})`;
                        }
                    }
                    
                    return selector;
                }
                
                return result;
            }
            """
            
            # Execute state capture
            element_state = await page.evaluate(state_script, selector, include_styles, include_events, include_ancestors)
            
            # Add page metadata
            page_id = next((k for k, v in self.browser_manager.active_pages.items() if v == page), "unknown")
            metadata = {
                "timestamp": timestamp,
                "page_id": page_id,
                "url": page.url,
                "title": await page.title(),
                "selector": selector
            }
            
            # Create HTML visualization
            with open(screenshot_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Element State Visualization</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    .container {{ display: flex; flex-wrap: wrap; gap: 20px; }}
                    .screenshot {{ border: 1px solid #ccc; padding: 10px; }}
                    .info {{ flex: 1; min-width: 400px; }}
                    .section {{ 
                        margin-bottom: 20px; 
                        border: 1px solid #eee; 
                        border-radius: 5px; 
                        padding: 10px; 
                    }}
                    .section h2 {{ margin-top: 0; color: #444; font-size: 18px; }}
                    .properties {{ 
                        display: grid; 
                        grid-template-columns: 150px 1fr; 
                        gap: 5px; 
                    }}
                    .key {{ font-weight: bold; }}
                    .ancestor {{ 
                        padding: 5px; 
                        border-bottom: 1px solid #eee; 
                    }}
                    .ancestor:last-child {{ border-bottom: none; }}
                    .selected {{ background-color: #f8f8f8; }}
                    pre {{ 
                        background-color: #f5f5f5; 
                        padding: 10px; 
                        overflow: auto; 
                        border-radius: 5px; 
                    }}
                </style>
            </head>
            <body>
                <h1>Element State Visualization</h1>
                <p>
                    <strong>Page:</strong> {metadata['title']}<br>
                    <strong>URL:</strong> {metadata['url']}<br>
                    <strong>Selector:</strong> {metadata['selector']}<br>
                    <strong>Timestamp:</strong> {datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')}
                </p>
                
                <div class="container">
                    <div class="screenshot">
                        <h2>Element Screenshot</h2>
                        <img src="data:image/png;base64,{img_data}" />
                    </div>
                    
                    <div class="info">
                        <div class="section">
                            <h2>Basic Information</h2>
                            <div class="properties">
                                <div class="key">Tag Name:</div>
                                <div>{element_state['tagName']}</div>
                                
                                <div class="key">ID:</div>
                                <div>{element_state['id'] or 'None'}</div>
                                
                                <div class="key">Class Name:</div>
                                <div>{element_state['className'] or 'None'}</div>
                                
                                <div class="key">Position:</div>
                                <div>
                                    x: {element_state['position']['x']}, 
                                    y: {element_state['position']['y']}, 
                                    width: {element_state['position']['width']}, 
                                    height: {element_state['position']['height']}
                                </div>
                                
                                <div class="key">Visible:</div>
                                <div>{element_state['position']['visible']}</div>
                                
                                <div class="key">Text Content:</div>
                                <div>{element_state['textContent'] or 'None'}</div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>Attributes</h2>
                            <div class="properties">
            """
            
            # Add attributes
            if element_state['attributes']:
                for key, value in element_state['attributes'].items():
                    html += f"""
                                <div class="key">{key}:</div>
                                <div>{value}</div>
                    """
            else:
                html += """
                                <div>No attributes found</div>
                """
            
            html += """
                            </div>
                        </div>
            """
            
            # Add ancestors if available
            if include_ancestors and 'ancestors' in element_state and element_state['ancestors']:
                html += """
                        <div class="section">
                            <h2>Ancestor Elements</h2>
                            <div>
                """
                
                for i, ancestor in enumerate(element_state['ancestors']):
                    html += f"""
                                <div class="ancestor" style="padding-left: {i*10}px;">
                                    {ancestor['tagName'].lower()}
                                    {f"#" + ancestor['id'] if ancestor['id'] else ""}
                                    {f"." + ancestor['className'].replace(' ', '.') if ancestor['className'] else ""}
                                </div>
                    """
                
                html += """
                            </div>
                        </div>
                """
            
            # Add styles if available
            if include_styles and 'styles' in element_state:
                html += """
                        <div class="section">
                            <h2>Computed Styles</h2>
                            <pre>
                """
                
                # Format styles nicely
                styles_json = json.dumps(element_state['styles'], indent=2)
                html += styles_json
                
                html += """
                            </pre>
                        </div>
                """
            
            # Add events if available
            if include_events and 'events' in element_state and element_state['events']:
                html += """
                        <div class="section">
                            <h2>Event Handlers</h2>
                            <ul>
                """
                
                for event in element_state['events']:
                    html += f"""
                                <li>{event}</li>
                    """
                
                html += """
                            </ul>
                        </div>
                """
            
            # Close HTML
            html += """
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Write HTML to file
            with open(visualization_path, 'w') as f:
                f.write(html)
            
            # Add to debug history
            history_entry = {
                "type": "element_visualization",
                "timestamp": timestamp,
                "page_id": page_id,
                "path": visualization_path,
                "selector": selector,
                "screenshot_path": screenshot_path
            }
            
            if page_id not in self.debug_history:
                self.debug_history[page_id] = []
            
            self.debug_history[page_id].append(history_entry)
            self._save_debug_history()
            
            logger.info(f"Element state visualization saved to {visualization_path}")
            return visualization_path
            
        except Exception as e:
            logger.error(f"Error visualizing element state: {str(e)}")
            return None
    
    async def capture_dom_state(self, page_id, include_styles=True, include_events=True):
        """
        Capture a snapshot of the DOM structure with optional styles and event information.
        
        Args:
            page_id: ID of the page to capture DOM from
            include_styles: Whether to include computed styles
            include_events: Whether to include event listeners
            
        Returns:
            Path to the DOM state file
        """
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
                logger.info(f"Converted page_id to string: {page_id}")
            
            # Check if page exists
            if page_id not in self.browser_manager.active_pages:
                logger.error(f"Page {page_id} not found for DOM state capture")
                
                # Try a fallback page if there are any active pages
                if self.browser_manager.active_pages:
                    fallback_page_id = next(iter(self.browser_manager.active_pages.keys()))
                    logger.info(f"Using fallback page: {fallback_page_id}")
                    page_id = fallback_page_id
                else:
                    logger.error("No active pages available for DOM state capture")
                    return None
            
            # Get the page
            page = self.browser_manager.active_pages[page_id]
            
            # Create a unique filename
            timestamp = int(time.time() * 1000)
            filename = f"dom_state_{timestamp}.json"
            dom_state_path = str(self.storage_dir / filename)
            
            # DOM capture script
            dom_capture_script = """
            (includeStyles, includeEvents) => {
                // Helper function to process elements recursively
                function processElement(element, depth = 0) {
                    if (!element) return null;
                    
                    // Skip non-element nodes
                    if (element.nodeType !== 1) return null;
                    
                    // Basic element info
                    const result = {
                        tagName: element.tagName,
                        id: element.id || null,
                        className: element.className || null,
                        attributes: {},
                        childCount: element.children.length,
                        depth: depth
                    };
                    
                    // Add text content if it's a text node or has direct text
                    const textContent = Array.from(element.childNodes)
                        .filter(node => node.nodeType === 3) // Text nodes
                        .map(node => node.textContent.trim())
                        .filter(text => text.length > 0)
                        .join(' ');
                    
                    if (textContent) {
                        result.textContent = textContent.length > 100 ? 
                            textContent.substring(0, 100) + '...' : textContent;
                    }
                    
                    // Add attributes
                    for (const attr of element.attributes) {
                        result.attributes[attr.name] = attr.value;
                    }
                    
                    // Add position info if the element is visible
                    const rect = element.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        result.position = {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            visible: true
                        };
                    } else {
                        result.position = {
                            visible: false
                        };
                    }
                    
                    // Add computed styles if requested and element is visible
                    if (includeStyles && rect.width > 0 && rect.height > 0) {
                        const styles = window.getComputedStyle(element);
                        result.styles = {};
                        
                        // Get important styles only to avoid huge output
                        const importantStyles = [
                            'display', 'position', 'visibility', 'opacity', 
                            'z-index', 'overflow', 'background-color', 'color', 
                            'font-size', 'font-weight', 'width', 'height', 
                            'margin', 'padding', 'border'
                        ];
                        
                        importantStyles.forEach(style => {
                            result.styles[style] = styles[style];
                        });
                    }
                    
                    // Add event listeners if requested
                    if (includeEvents) {
                        // Get event attributes (can't get all listeners in plain JavaScript)
                        result.events = {};
                        
                        const eventAttributes = [
                            'onclick', 'onmouseover', 'onmouseout', 'onkeydown', 
                            'onkeyup', 'onsubmit', 'onchange', 'onfocus', 
                            'onblur', 'oninput'
                        ];
                        
                        eventAttributes.forEach(attr => {
                            if (element[attr]) {
                                result.events[attr] = true;
                            }
                        });
                    }
                    
                    // Process children recursively (limit depth and number for large DOMs)
                    if (depth < 20) {  // Maximum depth
                        result.children = [];
                        
                        // Limit number of children to process
                        const maxChildren = 50;
                        const childElements = Array.from(element.children).slice(0, maxChildren);
                        
                        childElements.forEach(child => {
                            const childResult = processElement(child, depth + 1);
                            if (childResult) {
                                result.children.push(childResult);
                            }
                        });
                        
                        if (element.children.length > maxChildren) {
                            result.children.push({
                                tagName: "TRUNCATED",
                                textContent: `...${element.children.length - maxChildren} more elements truncated...`
                            });
                        }
                    } else {
                        result.children = [{
                            tagName: "MAX_DEPTH",
                            textContent: "Maximum recursion depth reached"
                        }];
                    }
                    
                    return result;
                }
                
                // Process the document body
                const domState = {
                    title: document.title,
                    url: window.location.href,
                    timestamp: Date.now(),
                    rootElement: processElement(document.documentElement, 0)
                };
                
                return domState;
            }
            """
            
            # Execute DOM capture
            dom_state = await page.evaluate(dom_capture_script, include_styles, include_events)
            
            # Add metadata
            dom_state["page_id"] = page_id
            dom_state["capture_timestamp"] = timestamp
            
            # Save DOM state to file
            with open(dom_state_path, 'w') as f:
                json.dump(dom_state, f, indent=2)
            
            # Create a more readable HTML version
            html_filename = f"dom_state_{timestamp}.html"
            html_path = str(self.visualizations_dir / html_filename)
            
            # Generate HTML representation
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>DOM State Snapshot - {dom_state['title']}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #333; }}
                    .metadata {{ margin-bottom: 20px; }}
                    .tree-view {{ 
                        font-family: monospace; 
                        margin-top: 20px;
                        border: 1px solid #ccc;
                        padding: 10px;
                        border-radius: 4px;
                    }}
                    .tree-item {{ 
                        padding: 2px 0;
                        white-space: nowrap;
                    }}
                    .expanded {{ display: block; }}
                    .collapsed {{ display: none; }}
                    .toggle {{ 
                        cursor: pointer;
                        display: inline-block;
                        width: 20px;
                        text-align: center;
                    }}
                    .element-tag {{ color: #0000cc; }}
                    .element-id {{ color: #e91e63; }}
                    .element-class {{ color: #4caf50; }}
                    .element-text {{ color: #555; font-style: italic; }}
                    .element-pos {{ color: #795548; }}
                </style>
                <script>
                    function toggleNode(id) {{
                        const childrenDiv = document.getElementById(id);
                        const toggle = document.getElementById('toggle-' + id);
                        if (childrenDiv.className === 'collapsed') {{
                            childrenDiv.className = 'expanded';
                            toggle.textContent = '-';
                        }} else {{
                            childrenDiv.className = 'collapsed';
                            toggle.textContent = '+';
                        }}
                    }}
                </script>
            </head>
            <body>
                <h1>DOM State Snapshot</h1>
                <div class="metadata">
                    <strong>Page Title:</strong> {dom_state['title']}<br>
                    <strong>URL:</strong> {dom_state['url']}<br>
                    <strong>Page ID:</strong> {page_id}<br>
                    <strong>Timestamp:</strong> {datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')}<br>
                    <strong>Styles Included:</strong> {include_styles}<br>
                    <strong>Events Included:</strong> {include_events}
                </div>
                
                <h2>DOM Tree</h2>
                <div class="tree-view">
            """
            
            # Recursive function to generate HTML tree view
            def generate_tree_html(element, element_id, depth=0):
                if not element:
                    return ""
                
                # Generate unique ID for this element in the tree
                node_id = f"node-{element_id}"
                
                # Basic element info
                tag_name = element.get('tagName', 'UNKNOWN')
                element_id_attr = element.get('id', '')
                class_name = element.get('className', '')
                text_content = element.get('textContent', '')
                
                # Position info
                position = element.get('position', {})
                pos_str = ""
                if position.get('visible', False):
                    w = position.get('width', 0)
                    h = position.get('height', 0)
                    pos_str = f"[{w}x{h}]"
                
                # Create tree item HTML
                html = f"<div class='tree-item' style='padding-left: {depth * 20}px;'>"
                
                # Add toggle button if has children
                children = element.get('children', [])
                if children:
                    html += f"<span class='toggle' id='toggle-{node_id}' onclick='toggleNode(\"{node_id}\")'>-</span> "
                else:
                    html += "<span class='toggle'>&nbsp;</span> "
                
                # Add element info
                html += f"<span class='element-tag'>{tag_name.lower()}</span>"
                if element_id_attr:
                    html += f"<span class='element-id'> #{element_id_attr}</span>"
                if class_name:
                    classes = class_name.split()
                    html += f"<span class='element-class'> .{'.'.join(classes)}</span>"
                if pos_str:
                    html += f"<span class='element-pos'> {pos_str}</span>"
                if text_content:
                    # Truncate long text
                    if len(text_content) > 50:
                        text_content = text_content[:50] + "..."
                    html += f"<span class='element-text'> \"{text_content}\"</span>"
                
                html += "</div>"
                
                # Add children
                if children:
                    html += f"<div id='{node_id}' class='expanded'>"
                    for i, child in enumerate(children):
                        html += generate_tree_html(child, f"{element_id}-{i}", depth + 1)
                    html += "</div>"
                
                return html
            
            # Generate tree HTML for root element
            html += generate_tree_html(dom_state["rootElement"], "root")
            
            # Close HTML
            html += """
                </div>
            </body>
            </html>
            """
            
            # Write HTML to file
            with open(html_path, 'w') as f:
                f.write(html)
            
            # Add to debug history
            history_entry = {
                "type": "dom_state",
                "timestamp": timestamp,
                "page_id": page_id,
                "json_path": dom_state_path,
                "html_path": html_path
            }
            
            if page_id not in self.debug_history:
                self.debug_history[page_id] = []
            
            self.debug_history[page_id].append(history_entry)
            self._save_debug_history()
            
            logger.info(f"DOM state captured and saved to {dom_state_path} and {html_path}")
            return {
                "json_path": dom_state_path,
                "html_path": html_path
            }
        
        except Exception as e:
            logger.error(f"Error capturing DOM state: {str(e)}")
            return None
    
    async def create_interaction_timeline(self, page_id=None, include_operations=True, include_screenshots=True):
        """
        Create a timeline visualization of interactions with the page.
        
        Args:
            page_id: Optional ID of the page to create timeline for
            include_operations: Whether to include operation history
            include_screenshots: Whether to include screenshots
            
        Returns:
            Path to the timeline file
        """
        try:
            # Create a unique filename
            timestamp = int(time.time() * 1000)
            filename = f"timeline_{timestamp}.html"
            timeline_path = str(self.timeline_dir / filename)
            
            # Get page history
            if page_id:
                page_history = self.debug_history.get(page_id, [])
                page_ids = [page_id]
            else:
                # Combine history from all pages
                page_history = []
                page_ids = list(self.debug_history.keys())
                for p_id, history in self.debug_history.items():
                    for entry in history:
                        entry['page_id'] = p_id
                        page_history.append(entry)
            
            # Sort history by timestamp
            page_history.sort(key=lambda x: x['timestamp'])
            
            # Create HTML visualization
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Interaction Timeline</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #333; }
                    .timeline {
                        position: relative;
                        margin: 40px 0;
                        padding-left: 50px;
                    }
                    .timeline::before {
                        content: '';
                        position: absolute;
                        left: 20px;
                        top: 0;
                        bottom: 0;
                        width: 4px;
                        background: #ccc;
                    }
                    .event {
                        position: relative;
                        margin-bottom: 30px;
                        padding: 15px;
                        background: #f9f9f9;
                        border-radius: 5px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }
                    .event::before {
                        content: '';
                        position: absolute;
                        left: -35px;
                        top: 20px;
                        width: 16px;
                        height: 16px;
                        border-radius: 50%;
                        background: #6c757d;
                        border: 3px solid #f9f9f9;
                    }
                    .event-time {
                        font-size: 12px;
                        color: #6c757d;
                        margin-bottom: 10px;
                    }
                    .event-title {
                        font-weight: bold;
                        color: #495057;
                        margin-bottom: 5px;
                    }
                    .event-details {
                        color: #6c757d;
                        margin-bottom: 10px;
                    }
                    .event-page {
                        font-style: italic;
                        color: #6c757d;
                        margin-bottom: 10px;
                    }
                    .event-image {
                        margin-top: 10px;
                        border: 1px solid #dee2e6;
                        max-width: 100%;
                    }
                    .pages {
                        margin-bottom: 20px;
                    }
                    .page-filter {
                        margin-right: 10px;
                        cursor: pointer;
                        padding: 5px 10px;
                        background: #f1f1f1;
                        border-radius: 3px;
                        display: inline-block;
                    }
                    .page-filter.active {
                        background: #007bff;
                        color: white;
                    }
                </style>
            </head>
            <body>
                <h1>Interaction Timeline</h1>
                <p>
                    <strong>Generated:</strong> """ + datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S') + """<br>
                    <strong>Pages:</strong> """ + str(len(page_ids)) + """<br>
                    <strong>Events:</strong> """ + str(len(page_history)) + """
                </p>
                
                <div class="pages">
                    <strong>Filter by Page:</strong>
                    <span class="page-filter active" data-page="all">All Pages</span>
            """
            
            # Add page filters
            for p_id in page_ids:
                html += f"""
                    <span class="page-filter" data-page="{p_id}">Page {p_id}</span>
                """
            
            html += """
                </div>
                
                <div class="timeline">
            """
            
            # Add events to timeline
            for entry in page_history:
                entry_type = entry['type']
                entry_time = datetime.fromtimestamp(entry['timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S')
                p_id = entry['page_id']
                
                # Create event HTML based on type
                event_title = ""
                event_details = ""
                event_image = ""
                
                if entry_type == "element_screenshot":
                    event_title = "Element Screenshot"
                    event_details = f"Selector: {entry['selector']}"
                    if include_screenshots and 'path' in entry:
                        with open(entry['path'], 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                            event_image = f'<img src="data:image/png;base64,{img_data}" class="event-image" />'
                
                elif entry_type == "page_screenshot":
                    event_title = "Page Screenshot"
                    if include_screenshots and 'path' in entry:
                        # Resize large screenshots
                        with open(entry['path'], 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                            event_image = f'<img src="data:image/png;base64,{img_data}" class="event-image" style="max-height: 300px;" />'
                
                elif entry_type == "dom_snapshot":
                    event_title = "DOM Snapshot"
                    event_details = f"URL: {entry.get('url', 'Unknown')}"
                
                elif entry_type == "element_visualization":
                    event_title = "Element Visualization"
                    event_details = f"Selector: {entry['selector']}"
                    if include_screenshots and 'screenshot_path' in entry:
                        with open(entry['screenshot_path'], 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                            event_image = f'<img src="data:image/png;base64,{img_data}" class="event-image" />'
                
                # Add event to timeline
                html += f"""
                    <div class="event" data-page="{p_id}">
                        <div class="event-time">{entry_time}</div>
                        <div class="event-title">{event_title}</div>
                        <div class="event-page">Page ID: {p_id}</div>
                        <div class="event-details">{event_details}</div>
                        {event_image}
                    </div>
                """
            
            # Close HTML
            html += """
                </div>
                
                <script>
                    // Simple filtering functionality
                    document.addEventListener('DOMContentLoaded', function() {
                        // Filter buttons
                        const filterButtons = document.querySelectorAll('.page-filter');
                        const events = document.querySelectorAll('.event');
                        
                        filterButtons.forEach(button => {
                            button.addEventListener('click', function() {
                                // Remove active class from all buttons
                                filterButtons.forEach(btn => btn.classList.remove('active'));
                                // Add active class to clicked button
                                this.classList.add('active');
                                
                                const pageId = this.getAttribute('data-page');
                                
                                // Filter events
                                events.forEach(event => {
                                    if (pageId === 'all' || event.getAttribute('data-page') === pageId) {
                                        event.style.display = 'block';
                                    } else {
                                        event.style.display = 'none';
                                    }
                                });
                            });
                        });
                    });
                </script>
            </body>
            </html>
            """
            
            # Write HTML to file
            with open(timeline_path, 'w') as f:
                f.write(html)
            
            logger.info(f"Interaction timeline saved to {timeline_path}")
            return timeline_path
            
        except Exception as e:
            logger.error(f"Error creating interaction timeline: {str(e)}")
            return None
    
    async def get_debug_history(self, page_id=None):
        """
        Get debug history for a page or all pages.
        
        Args:
            page_id: Optional ID of the page to get history for
            
        Returns:
            List of debug history entries
        """
        if page_id:
            return self.debug_history.get(page_id, [])
        else:
            # Flatten history from all pages
            flattened_history = []
            for p_id, history in self.debug_history.items():
                for entry in history:
                    entry_copy = entry.copy()
                    entry_copy['page_id'] = p_id
                    flattened_history.append(entry_copy)
            
            # Sort by timestamp
            flattened_history.sort(key=lambda x: x['timestamp'])
            return flattened_history
    
    async def clear_debug_history(self, page_id=None):
        """
        Clear debug history for a page or all pages.
        
        Args:
            page_id: Optional ID of the page to clear history for
            
        Returns:
            Success flag
        """
        try:
            if page_id:
                if page_id in self.debug_history:
                    del self.debug_history[page_id]
            else:
                self.debug_history = {}
            
            self._save_debug_history()
            logger.info(f"Debug history cleared for {'page ' + page_id if page_id else 'all pages'}")
            return True
        except Exception as e:
            logger.error(f"Error clearing debug history: {str(e)}")
            return False

def register_visual_debugging_tools(mcp, browser_manager):
    """Register visual debugging tools with the MCP server."""
    # Create visual debugger instance
    visual_debugger = VisualDebugger(browser_manager)
    
    @mcp.tool()
    async def take_element_debug_screenshot(page_id: str, selector: str, highlight: bool = True, annotation: Optional[str] = None) -> Dict[str, Any]:
        """
        Take a screenshot of a specific element with optional highlighting and annotation.
        
        Args:
            page_id: ID of the page containing the element
            selector: CSS selector for the element
            highlight: Whether to highlight the element
            annotation: Optional text annotation to add
            
        Returns:
            Dict with screenshot information
        """
        logger.info(f"Taking element debug screenshot for selector '{selector}' on page {page_id}")
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
            
            # Get the page
            page = browser_manager.active_pages.get(page_id)
            if not page:
                logger.error(f"Page {page_id} not found")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Page {page_id} not found"
                        }
                    ],
                    "success": False,
                    "error": f"Page {page_id} not found"
                }
            
            # Take the screenshot
            screenshot_path = await visual_debugger.take_element_screenshot(page, selector, highlight, annotation)
            
            if screenshot_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Element screenshot taken successfully"
                        }
                    ],
                    "success": True,
                    "screenshot_path": screenshot_path,
                    "selector": selector
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to take element screenshot"
                        }
                    ],
                    "success": False,
                    "error": "Failed to take element screenshot"
                }
        except Exception as e:
            logger.error(f"Error taking element debug screenshot: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error taking element debug screenshot: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def take_annotated_page_screenshot(page_id: str, annotations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Take a screenshot of the full page with optional element annotations.
        
        Args:
            page_id: ID of the page to screenshot
            annotations: Optional list of annotations, each containing:
                {
                    "selector": CSS selector for the element,
                    "label": Text label for the annotation,
                    "color": Color for the highlight (optional)
                }
            
        Returns:
            Dict with screenshot information
        """
        logger.info(f"Taking annotated page screenshot for page {page_id}")
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
                logger.info(f"Converted page_id to string: {page_id}")
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: page_id must be provided"
                        }
                    ],
                    "success": False,
                    "error": "page_id must be provided"
                }
            
            # Verify annotations format
            if annotations is not None:
                logger.info(f"Verifying annotations format: {annotations}")
                
                # Handle string representation of JSON
                if isinstance(annotations, str):
                    try:
                        annotations = json.loads(annotations)
                        logger.info(f"Converted annotations from string to JSON: {annotations}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid annotations JSON format: {str(e)}")
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error: Invalid annotations format. {str(e)}"
                                }
                            ],
                            "success": False,
                            "error": f"Invalid annotations format: {str(e)}"
                        }
                
                # Ensure annotations is a list
                if not isinstance(annotations, list):
                    logger.error(f"Annotations must be a list, got {type(annotations)}")
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Annotations must be a list, got {type(annotations)}"
                            }
                        ],
                        "success": False,
                        "error": f"Annotations must be a list, got {type(annotations)}"
                    }
                
                # Validate each annotation
                valid_annotations = []
                for i, annotation in enumerate(annotations):
                    if not isinstance(annotation, dict):
                        logger.warning(f"Skipping annotation {i}: Not a dictionary")
                        continue
                        
                    if "selector" not in annotation:
                        logger.warning(f"Skipping annotation {i}: Missing required 'selector' field")
                        continue
                    
                    # Create a valid annotation
                    valid_annotation = {
                        "selector": annotation["selector"],
                        "label": annotation.get("label", f"Element {i+1}"),
                        "color": annotation.get("color", "#FF0000")  # Default to red
                    }
                    valid_annotations.append(valid_annotation)
                
                # Use validated annotations
                annotations = valid_annotations
                logger.info(f"Using validated annotations: {annotations}")
            
            # Check if page exists
            if page_id not in browser_manager.active_pages:
                logger.error(f"Page {page_id} not found")
                
                # Try a fallback page if there are any active pages
                if browser_manager.active_pages:
                    fallback_page_id = next(iter(browser_manager.active_pages.keys()))
                    logger.info(f"Using fallback page: {fallback_page_id}")
                    page_id = fallback_page_id
                else:
                    # Create a new page as a last resort
                    try:
                        logger.info("No active pages available, creating a new page")
                        page, page_id = await browser_manager.get_page()
                        await page.goto("about:blank")
                        logger.info(f"Created new page with ID {page_id} for screenshot")
                    except Exception as create_error:
                        logger.error(f"Error creating new page for screenshot: {str(create_error)}")
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error: Failed to create a new page. {str(create_error)}"
                                }
                            ],
                            "success": False,
                            "error": f"Failed to create a new page. {str(create_error)}"
                        }
            
            # Get the page
            page = browser_manager.active_pages.get(page_id)
            
            # Take the screenshot with retry mechanism
            max_retries = 3
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    screenshot_path = await visual_debugger.take_full_page_screenshot(page, annotations)
                    
                    if screenshot_path:
                        logger.info(f"Annotated screenshot saved to {screenshot_path}")
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Annotated page screenshot taken successfully"
                                }
                            ],
                            "success": True,
                            "screenshot_path": screenshot_path,
                            "annotations_count": len(annotations) if annotations else 0,
                            "page_id": page_id
                        }
                    
                    retry_count += 1
                    await asyncio.sleep(1)  # Wait before retrying
                except Exception as e:
                    logger.error(f"Error on attempt {retry_count+1}: {str(e)}")
                    last_error = e
                    retry_count += 1
                    await asyncio.sleep(1)  # Wait before retrying
            
            # If we get here, all retries failed
            error_message = "Failed to take annotated page screenshot"
            if last_error:
                error_message += f": {str(last_error)}"
                
            logger.error(error_message)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": error_message
                    }
                ],
                "success": False,
                "error": error_message
            }
        except Exception as e:
            logger.error(f"Error taking annotated page screenshot: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error taking annotated page screenshot: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def create_element_visualization(page_id: str, selector: str, include_styles: bool = True, include_events: bool = True, include_ancestors: bool = True) -> Dict[str, Any]:
        """
        Create a detailed visualization of an element's state.
        
        Args:
            page_id: ID of the page containing the element
            selector: CSS selector for the element
            include_styles: Whether to include computed styles
            include_events: Whether to include event listeners
            include_ancestors: Whether to include ancestor elements
            
        Returns:
            Dict with visualization information
        """
        logger.info(f"Creating element visualization for selector '{selector}' on page {page_id}")
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
            
            # Get the page
            page = browser_manager.active_pages.get(page_id)
            if not page:
                logger.error(f"Page {page_id} not found")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Page {page_id} not found"
                        }
                    ],
                    "success": False,
                    "error": f"Page {page_id} not found"
                }
            
            # Create the visualization
            visualization_path = await visual_debugger.visualize_element_state(
                page, selector, include_styles, include_events, include_ancestors
            )
            
            if visualization_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Element visualization created successfully"
                        }
                    ],
                    "success": True,
                    "visualization_path": visualization_path,
                    "selector": selector
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to create element visualization"
                        }
                    ],
                    "success": False,
                    "error": "Failed to create element visualization"
                }
        except Exception as e:
            logger.error(f"Error creating element visualization: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error creating element visualization: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def capture_dom_state(page_id: str, include_styles: bool = True) -> Dict[str, Any]:
        """
        Capture a snapshot of the DOM with optional styles.
        
        Args:
            page_id: ID of the page to capture
            include_styles: Whether to include computed styles for elements
            
        Returns:
            Dict with DOM snapshot information
        """
        logger.info(f"Capturing DOM state for page {page_id}")
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
            
            # Get the page
            page = browser_manager.active_pages.get(page_id)
            if not page:
                logger.error(f"Page {page_id} not found")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Page {page_id} not found"
                        }
                    ],
                    "success": False,
                    "error": f"Page {page_id} not found"
                }
            
            # Capture the DOM
            snapshot_path = await visual_debugger.capture_dom_snapshot(page, include_styles)
            
            if snapshot_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"DOM snapshot captured successfully"
                        }
                    ],
                    "success": True,
                    "snapshot_path": snapshot_path,
                    "url": page.url
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to capture DOM snapshot"
                        }
                    ],
                    "success": False,
                    "error": "Failed to capture DOM snapshot"
                }
        except Exception as e:
            logger.error(f"Error capturing DOM state: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error capturing DOM state: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def create_debug_timeline(page_id: Optional[str] = None, include_operations: bool = True, include_screenshots: bool = True) -> Dict[str, Any]:
        """
        Create a timeline visualization of interactions with a page.
        
        Args:
            page_id: Optional ID of the page to create timeline for
            include_operations: Whether to include operation history
            include_screenshots: Whether to include screenshots
            
        Returns:
            Dict with timeline information
        """
        logger.info(f"Creating debug timeline for {'page ' + page_id if page_id else 'all pages'}")
        try:
            # Ensure page_id is a string if provided
            if page_id is not None:
                page_id = str(page_id)
                
                # Verify the page exists
                if page_id not in browser_manager.active_pages:
                    logger.warning(f"Page {page_id} not found, but will create timeline from history if available")
            
            # Create the timeline
            timeline_path = await visual_debugger.create_interaction_timeline(page_id, include_operations, include_screenshots)
            
            if timeline_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Debug timeline created successfully"
                        }
                    ],
                    "success": True,
                    "timeline_path": timeline_path,
                    "page_id": page_id
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to create debug timeline"
                        }
                    ],
                    "success": False,
                    "error": "Failed to create debug timeline"
                }
        except Exception as e:
            logger.error(f"Error creating debug timeline: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error creating debug timeline: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_debug_info(page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get debugging information for a page or all pages.
        
        Args:
            page_id: Optional ID of the page to get information for
            
        Returns:
            Dict with debug information
        """
        logger.info(f"Getting debug info for {'page ' + page_id if page_id else 'all pages'}")
        try:
            # Ensure page_id is a string if provided
            if page_id is not None:
                page_id = str(page_id)
            
            # Get the debug history
            debug_history = await visual_debugger.get_debug_history(page_id)
            
            # Group history by type
            history_by_type = {}
            for entry in debug_history:
                entry_type = entry['type']
                if entry_type not in history_by_type:
                    history_by_type[entry_type] = []
                history_by_type[entry_type].append(entry)
            
            # Count entries by type
            counts_by_type = {
                entry_type: len(entries)
                for entry_type, entries in history_by_type.items()
            }
            
            # Get session information
            session_info = {
                "session_start_time": datetime.fromtimestamp(visual_debugger.session_start_time).isoformat(),
                "session_duration_seconds": time.time() - visual_debugger.session_start_time
            }
            
            # Get storage information
            storage_info = {
                "debug_dir": str(visual_debugger.debug_dir),
                "screenshots_dir": str(visual_debugger.screenshots_dir),
                "visualizations_dir": str(visual_debugger.visualizations_dir),
                "dom_snapshots_dir": str(visual_debugger.dom_snapshots_dir),
                "timeline_dir": str(visual_debugger.timeline_dir)
            }
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Debug info retrieved successfully"
                    }
                ],
                "success": True,
                "page_id": page_id,
                "history_count": len(debug_history),
                "counts_by_type": counts_by_type,
                "session_info": session_info,
                "storage_info": storage_info
            }
        except Exception as e:
            logger.error(f"Error getting debug info: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting debug info: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def clear_debug_data(page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear debugging data for a page or all pages.
        
        Args:
            page_id: Optional ID of the page to clear data for
            
        Returns:
            Dict with result information
        """
        logger.info(f"Clearing debug data for {'page ' + page_id if page_id else 'all pages'}")
        try:
            # Ensure page_id is a string if provided
            if page_id is not None:
                page_id = str(page_id)
            
            # Clear the debug history
            result = await visual_debugger.clear_debug_history(page_id)
            
            if result:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Debug data cleared successfully for {'page ' + page_id if page_id else 'all pages'}"
                        }
                    ],
                    "success": True
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to clear debug data"
                        }
                    ],
                    "success": False,
                    "error": "Failed to clear debug data"
                }
        except Exception as e:
            logger.error(f"Error clearing debug data: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error clearing debug data: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    logger.info("Visual debugging tools registered")
    
    # Return the debugger instance and tools
    return {
        "visual_debugger": visual_debugger,
        "take_element_debug_screenshot": take_element_debug_screenshot,
        "take_annotated_page_screenshot": take_annotated_page_screenshot,
        "create_element_visualization": create_element_visualization,
        "capture_dom_state": capture_dom_state,
        "create_debug_timeline": create_debug_timeline,
        "get_debug_info": get_debug_info,
        "clear_debug_data": clear_debug_data
    }