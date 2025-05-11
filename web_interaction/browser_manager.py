"""Browser Management for Web Interaction Extension."""

import asyncio
import json
import logging
import os
import pathlib
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, Union, List

# Configure logging
logger = logging.getLogger(__name__)

class BrowserManager:
    """Manages browser instances for web interaction."""
    
    def __init__(self):
        """Initialize the browser manager."""
        self.browser = None
        self.context = None
        self.active_pages = {}
        self.initialized = False
        self.page_metadata = {}
        
        # Load browser configuration from config file or environment variables
        self.config = self.load_config()
        self.headless = self.config.get('headless', False)
        self.slow_mo = self.config.get('slow_mo', 0)
        self.width = self.config.get('width', 1280)
        self.height = self.config.get('height', 800)
        self.debug_screenshots = self.config.get('debug_screenshots', False)
        self.timeout = self.config.get('timeout', 30000)
        
        # Tab management settings
        self.max_tabs = self.config.get('max_tabs', 8)  # Maximum number of open tabs
        self.tab_idle_timeout = self.config.get('tab_idle_timeout', 300)  # Time in seconds before a tab is considered idle
        self.last_activity = {}  # Track last activity time for each tab
        
        # Set up storage directory for screenshots and other data
        self.storage_dir = Path(__file__).parent.parent / 'storage'
        self.storage_dir.mkdir(exist_ok=True)
        
        # Screenshot directory for debugging
        self.screenshot_dir = self.storage_dir / 'screenshots'
        self.screenshot_dir.mkdir(exist_ok=True)
        logger.info(f"Screenshots will be saved to {self.screenshot_dir}")
        
        # Set up auto-cleanup for tabs
        self._cleanup_scheduled = False
        
    async def initialize(self):
        """Initialize the browser if not already initialized."""
        if not self.initialized:
            try:
                # Import here to avoid import errors if playwright isn't installed
                import playwright.async_api as pw
                
                logger.info("Initializing Playwright browser...")
                playwright = await pw.async_playwright().start()
                # Use visible browser (headless=False) for better debugging and visualization
                logger.info(f"Launching browser with headless={self.headless}, slow_mo={self.slow_mo}ms")
                self.browser = await playwright.chromium.launch(
                    headless=False,  # Force headless to be False regardless of config
                    slow_mo=100,     # Add a slight delay to make operations more visible
                    devtools=True,   # Open developer tools for better visibility
                )
                self.context = await self.browser.new_context(
                    viewport={"width": self.width, "height": self.height},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                self.initialized = True
                logger.info(f"Browser initialized successfully with configuration: {self.config}")
                
                # Take a screenshot when browser is initialized if debug screenshots are enabled
                if self.debug_screenshots:
                    # Create a debug page and take screenshot
                    debug_page = await self.context.new_page()
                    await debug_page.goto('about:blank')
                    await debug_page.evaluate("document.body.innerHTML = '<h1>Browser Initialized Successfully</h1><p>If you can see this, headless mode is disabled.</p>'")
                    timestamp = asyncio.get_event_loop().time()
                    screenshot_path = str(self.screenshot_dir / f"browser_init_{timestamp:.0f}.png")
                    await debug_page.screenshot(path=screenshot_path)
                    logger.info(f"Saved initialization screenshot to {screenshot_path}")
                    await debug_page.close()
            except Exception as e:
                logger.error(f"Error initializing browser: {str(e)}")
                raise
            
    async def get_page(self, page_id=None, session_id=None, browser_type=None):
        """
        Get a page by ID or create a new one.
        
        Args:
            page_id: Optional ID of an existing page
            session_id: Optional session ID to associate with the page
            browser_type: Optional browser type to use
            
        Returns:
            Tuple of (page, page_id)
        """
        await self.initialize()
        
        # Handle string/int conversion for page_id
        if page_id is not None:
            # Convert to string if it's an integer or other type
            page_id = str(page_id)
            logger.info(f"Converted page_id to string: {page_id}")
        
        # Check if page exists
        if page_id and page_id in self.active_pages:
            logger.info(f"Using existing page with ID {page_id}")
            # Update last activity time for this page
            self.last_activity[page_id] = time.time()
            return self.active_pages[page_id], page_id
            
        # Check if we need to clean up tabs before creating a new one
        if len(self.active_pages) >= self.max_tabs:
            logger.warning(f"Reached maximum number of tabs ({self.max_tabs}), cleaning up inactive tabs")
            await self._cleanup_inactive_tabs()
            
            # If we're still at maximum tabs, close the least recently used tab
            if len(self.active_pages) >= self.max_tabs:
                await self._close_least_used_tab()
        
        # Create new page
        logger.info("Creating new browser page")
        new_page = await self.context.new_page()
        new_id = str(len(self.active_pages) + 1)
        self.active_pages[new_id] = new_page
        logger.info(f"Created new page with ID {new_id}, active pages: {list(self.active_pages.keys())}")
        
        # Set up page metadata
        self.page_metadata = getattr(self, 'page_metadata', {})
        self.page_metadata[new_id] = {
            'created_at': time.time(),
            'session_id': session_id,
            'browser_type': browser_type,
            'url': 'about:blank',
            'title': ''
        }
        
        # Initialize last activity time for this page
        self.last_activity[new_id] = time.time()
        
        # Schedule tab cleanup if not already scheduled
        if not self._cleanup_scheduled:
            self._schedule_tab_cleanup()
        
        return new_page, new_id
        
    async def _cleanup_inactive_tabs(self):
        """Close tabs that have been inactive for too long."""
        current_time = time.time()
        inactive_tabs = []
        
        # Find tabs that have been inactive for longer than the timeout
        for page_id, last_time in list(self.last_activity.items()):
            if current_time - last_time > self.tab_idle_timeout and page_id in self.active_pages:
                inactive_tabs.append(page_id)
        
        # Close inactive tabs
        for page_id in inactive_tabs:
            logger.info(f"Closing inactive tab with ID {page_id} (inactive for {current_time - self.last_activity.get(page_id, 0):.1f} seconds)")
            await self.close_page(page_id)
            
        return len(inactive_tabs)
    
    async def _close_least_used_tab(self):
        """Close the least recently used tab."""
        if not self.active_pages:
            return False
            
        # Find the least recently used page
        least_used_id = min(self.last_activity.items(), key=lambda x: x[1])[0]
        
        # Only close if it's actually in active_pages
        if least_used_id in self.active_pages:
            logger.info(f"Closing least recently used tab with ID {least_used_id}")
            await self.close_page(least_used_id)
            return True
            
        return False
    
    def _schedule_tab_cleanup(self):
        """Schedule regular tab cleanup."""
        self._cleanup_scheduled = True
        
        # Define the cleanup function
        async def cleanup_task():
            while True:
                try:
                    await asyncio.sleep(60)  # Check every minute
                    if len(self.active_pages) > self.max_tabs // 2:  # Only clean if we have a significant number of tabs
                        await self._cleanup_inactive_tabs()
                except Exception as e:
                    logger.error(f"Error in tab cleanup task: {str(e)}")
                    
        # Start the cleanup task
        asyncio.create_task(cleanup_task())
        logger.info("Tab cleanup task scheduled")
        
    async def update_page_metadata(self, page_id, **kwargs):
        """
        Update metadata for a page.
        
        Args:
            page_id: ID of the page to update
            **kwargs: Metadata key-value pairs to update
        """
        if page_id is not None:
            page_id = str(page_id)
        
        # Initialize metadata dict if it doesn't exist
        if not hasattr(self, 'page_metadata'):
            self.page_metadata = {}
        
        # Initialize page metadata if it doesn't exist
        if page_id not in self.page_metadata:
            self.page_metadata[page_id] = {
                'created_at': time.time(),
                'url': 'about:blank',
                'title': ''
            }
        
        # Update metadata
        for key, value in kwargs.items():
            self.page_metadata[page_id][key] = value
            
        # Track activity on this page
        self.last_activity[page_id] = time.time()
            
        logger.debug(f"Updated metadata for page {page_id}: {kwargs}")
        
    async def close_page(self, page_id):
        """
        Close a page and clean up associated resources.
        
        Args:
            page_id: ID of the page to close
            
        Returns:
            Success flag
        """
        if page_id is not None:
            page_id = str(page_id)
            
        # Check if page exists
        if page_id in self.active_pages:
            try:
                # Close the page
                logger.info(f"Closing page with ID {page_id}")
                await self.active_pages[page_id].close()
                
                # Remove from active pages
                del self.active_pages[page_id]
                
                # Clean up last activity record
                if page_id in self.last_activity:
                    del self.last_activity[page_id]
                
                # Keep metadata for history
                if page_id in self.page_metadata:
                    self.page_metadata[page_id]['closed_at'] = time.time()
                    self.page_metadata[page_id]['active'] = False
                
                logger.info(f"Page {page_id} closed successfully, remaining pages: {list(self.active_pages.keys())}")
                return True
            except Exception as e:
                logger.error(f"Error closing page {page_id}: {str(e)}")
                
                # Force cleanup even if there was an error
                if page_id in self.active_pages:
                    del self.active_pages[page_id]
                if page_id in self.last_activity:
                    del self.last_activity[page_id]
                
                return False
        else:
            logger.warning(f"Page {page_id} not found for closing")
            return False
        
    async def take_screenshot(self, page_id, full_page=False, element_selector=None):
        """
        Take a screenshot of a page or element.
        
        Args:
            page_id: ID of the page to screenshot
            full_page: Whether to capture the full page or just the viewport
            element_selector: Optional CSS selector of an element to screenshot
            
        Returns:
            Path to the screenshot file
        """
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
                logger.info(f"Ensuring screenshot page_id is string: {page_id}")
            
            # Check if page exists
            if page_id not in self.active_pages:
                logger.warning(f"Page {page_id} not found for screenshot")
                
                # Try a fallback page if there are any active pages
                if self.active_pages:
                    fallback_page_id = next(iter(self.active_pages.keys()))
                    logger.info(f"Using fallback page: {fallback_page_id}")
                    page_id = fallback_page_id
                else:
                    # Create a new page as a last resort
                    try:
                        logger.info("No active pages available, creating a new page")
                        page, page_id = await self.get_page()
                        await page.goto("about:blank")
                        logger.info(f"Created new page with ID {page_id} for screenshot")
                    except Exception as create_error:
                        logger.error(f"Error creating new page for screenshot: {str(create_error)}")
                        return None
            
            # Ensure the screenshot directory exists
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Get the page
            page = self.active_pages[page_id]
            
            # Create a unique filename with timestamp
            timestamp = int(time.time())
            logger.info(f"Using screenshot directory: {self.screenshot_dir}")
            
            # Take screenshot
            if element_selector:
                # Element screenshot
                try:
                    # Find the element
                    element = await page.query_selector(element_selector)
                    if not element:
                        logger.warning(f"Element not found with selector: {element_selector}, falling back to full page screenshot")
                        # Fall back to full page screenshot
                        filename = f"page_{page_id}_{timestamp}.png"
                        screenshot_path = str(self.screenshot_dir / filename)
                        await page.screenshot(path=screenshot_path, full_page=full_page)
                        logger.info(f"Fallback page screenshot saved to {screenshot_path}")
                        return screenshot_path
                        
                    # Take screenshot of the element
                    filename = f"element_{page_id}_{timestamp}.png"
                    screenshot_path = str(self.screenshot_dir / filename)
                    await element.screenshot(path=screenshot_path)
                    logger.info(f"Element screenshot saved to {screenshot_path}")
                    return screenshot_path
                except Exception as e:
                    logger.error(f"Error taking element screenshot: {str(e)}")
                    # Try falling back to full page screenshot
                    try:
                        filename = f"fallback_page_{page_id}_{timestamp}.png"
                        screenshot_path = str(self.screenshot_dir / filename)
                        await page.screenshot(path=screenshot_path, full_page=False)
                        logger.info(f"Fallback page screenshot saved to {screenshot_path}")
                        return screenshot_path
                    except Exception as fallback_error:
                        logger.error(f"Fallback screenshot also failed: {str(fallback_error)}")
                        return None
            else:
                # Page screenshot
                try:
                    filename = f"page_{page_id}_{timestamp}.png"
                    screenshot_path = str(self.screenshot_dir / filename)
                    
                    # Try with full page first if requested
                    if full_page:
                        try:
                            await page.screenshot(path=screenshot_path, full_page=True)
                        except Exception as full_page_error:
                            logger.warning(f"Full page screenshot failed: {str(full_page_error)}, falling back to viewport screenshot")
                            await page.screenshot(path=screenshot_path, full_page=False)
                    else:
                        await page.screenshot(path=screenshot_path, full_page=False)
                        
                    logger.info(f"Page screenshot saved to {screenshot_path}")
                    return screenshot_path
                except Exception as e:
                    logger.error(f"Error taking page screenshot: {str(e)}")
                    return None
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return None
    
    async def highlight_element(self, page, selector, color='red', duration=1):
        """
        Highlight an element on the page for debugging.
        
        Args:
            page: Page containing the element
            selector: CSS selector for the element
            color: Color for the highlight (e.g., 'red', 'blue', 'green')
            duration: How long to highlight (in seconds)
        """
        try:
            # CSS colors for the highlight
            color_map = {
                'red': '#ff0000',
                'blue': '#0000ff', 
                'green': '#00ff00',
                'yellow': '#ffff00',
                'purple': '#800080',
                'orange': '#ffa500'
            }
            
            # Use color from map or use provided color
            highlight_color = color_map.get(color, color)
            
            # Inject highlight script
            await page.evaluate(f"""
            (selector) => {{
                const element = document.querySelector(selector);
                if (!element) return false;
                
                // Store original styles
                const original = {{
                    outline: element.style.outline,
                    boxShadow: element.style.boxShadow
                }};
                
                // Apply highlight
                element.style.outline = '2px solid {highlight_color}';
                element.style.boxShadow = '0 0 10px {highlight_color}';
                
                // Scroll into view if needed
                element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                
                // Store original styles on element for later restoration
                element._originalStyles = original;
                
                return true;
            }}
            """, selector)
            
            # Wait for duration
            await asyncio.sleep(duration)
            
            # Remove highlight
            await page.evaluate("""
            (selector) => {
                const element = document.querySelector(selector);
                if (!element || !element._originalStyles) return false;
                
                // Restore original styles
                element.style.outline = element._originalStyles.outline || '';
                element.style.boxShadow = element._originalStyles.boxShadow || '';
                
                // Clean up
                delete element._originalStyles;
                
                return true;
            }
            """, selector)
            
            return True
        except Exception as e:
            logger.error(f"Error highlighting element: {str(e)}")
            # Try to remove highlight if an error occurs
            try:
                await page.evaluate("""
                (selector) => {
                    const element = document.querySelector(selector);
                    if (!element) return;
                    element.style.outline = '';
                    element.style.boxShadow = '';
                }
                """, selector)
            except:
                pass
            return False
        
    def load_config(self) -> Dict[str, Any]:
        """Load browser configuration from file or environment variables."""
        config = {
            'headless': False,  # Default is visible
            'slow_mo': 0,      # No delay by default
            'width': 1280,     # Default width
            'height': 800,     # Default height
            'debug_screenshots': False,  # Disabled by default
            'timeout': 30000   # Default timeout (30 seconds)
        }
        
        # Check for config file
        config_path = pathlib.Path(__file__).parent / 'browser_config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    logger.info(f"Loaded browser configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading browser config from {config_path}: {str(e)}")
        else:
            logger.info(f"No config file found at {config_path}, using defaults and environment variables")
        
        # Environment variables override file config
        env_overrides = {
            'headless': os.environ.get('MCP_BROWSER_HEADLESS'),
            'slow_mo': os.environ.get('MCP_BROWSER_SLOW_MO'),
            'width': os.environ.get('MCP_BROWSER_WIDTH'),
            'height': os.environ.get('MCP_BROWSER_HEIGHT'),
            'debug_screenshots': os.environ.get('MCP_BROWSER_DEBUG_SCREENSHOTS'),
            'timeout': os.environ.get('MCP_BROWSER_TIMEOUT')
        }
        
        # Apply environment variable overrides if set
        for key, value in env_overrides.items():
            if value is not None:
                if isinstance(config[key], bool):
                    config[key] = value.lower() == 'true'
                elif isinstance(config[key], int):
                    config[key] = int(value)
                else:
                    config[key] = value
                    
        return config
    
    async def get_page_info(self):
        """
        Get information about all active pages.
        
        Returns:
            Dict with page information
        """
        page_info = {}
        
        for page_id, page in self.active_pages.items():
            try:
                # Get page metadata
                metadata = self.page_metadata.get(page_id, {}) if hasattr(self, 'page_metadata') else {}
                
                # Get current URL and title
                try:
                    url = page.url
                    title = await page.title()
                except Exception as e:
                    url = metadata.get('url', 'unknown')
                    title = metadata.get('title', 'unknown')
                    logger.error(f"Error getting page info for page {page_id}: {str(e)}")
                
                # Create page info entry
                page_info[page_id] = {
                    'page_id': page_id,
                    'url': url,
                    'title': title,
                    'created_at': metadata.get('created_at', None),
                    'session_id': metadata.get('session_id', None),
                    'browser_type': metadata.get('browser_type', None)
                }
            except Exception as e:
                logger.error(f"Error processing page {page_id}: {str(e)}")
                page_info[page_id] = {
                    'page_id': page_id,
                    'error': str(e)
                }
        
        return page_info
        
    async def execute_console_command(self, page_id, command):
        """
        Execute a JavaScript command in the console of a page.
        
        Args:
            page_id: ID of the page to execute the command on
            command: JavaScript code to execute
            
        Returns:
            Dict with execution result or error
        """
        logger.info(f"Executing console command on page {page_id}: {command}")
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
                logger.info(f"Ensuring page_id is string: {page_id}")
                
            # Check if the page exists
            if page_id not in self.active_pages:
                logger.error(f"Page {page_id} not found for console command execution")
                return {
                    "success": False,
                    "error": f"Page {page_id} not found"
                }
                
            # Get the page and execute the command
            page = self.active_pages[page_id]
            
            # Execute JavaScript on the page
            try:
                # Handle different types of JavaScript code
                if command.strip().startswith('return'):
                    # Wrap the return statement in a function
                    wrapped_command = f"() => {{ {command} }}"
                    result = await page.evaluate(wrapped_command)
                elif not command.strip().startswith('(') and not command.strip().startswith('function'):
                    # Wrap code in a function if it's not already wrapped
                    wrapped_command = f"""
                    () => {{
                        try {{
                            {command}
                        }} catch (e) {{
                            return {{ error: e.toString() }};
                        }}
                    }}
                    """
                    result = await page.evaluate(wrapped_command)
                else:
                    # Execute as-is
                    result = await page.evaluate(command)
                
                # Check if result is an error object (from our try/catch)
                if isinstance(result, dict) and 'error' in result:
                    return {
                        "success": False,
                        "error": result['error']
                    }
                
                return {
                    "success": True,
                    "result": result
                }
            except Exception as e:
                # Try as evaluateHandle if evaluate fails
                try:
                    logger.info("Trying evaluateHandle as fallback")
                    handle = await page.evaluateHandle(command)
                    json_value = await handle.jsonValue()
                    await handle.dispose()
                    return {
                        "success": True,
                        "result": json_value
                    }
                except Exception as fallback_error:
                    logger.error(f"Both evaluate methods failed: {str(e)} and {str(fallback_error)}")
                    return {
                        "success": False,
                        "error": f"JavaScript execution failed: {str(e)}"
                    }
        except Exception as e:
            logger.error(f"Error executing console command: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_tab_status(self):
        """
        Get detailed status of all tabs/pages.
        
        Returns:
            Dict with detailed tab status information
        """
        tab_status = {
            "active_tabs_count": len(self.active_pages),
            "max_tabs": self.max_tabs,
            "tab_idle_timeout": self.tab_idle_timeout,
            "tabs": {}
        }
        
        current_time = time.time()
        
        # Add info for each active tab
        for page_id, page in self.active_pages.items():
            try:
                metadata = self.page_metadata.get(page_id, {})
                last_activity = self.last_activity.get(page_id, 0)
                idle_time = current_time - last_activity if last_activity > 0 else 0
                
                # Get current URL and title
                try:
                    url = page.url
                    title = await page.title()
                except Exception as e:
                    url = metadata.get('url', 'unknown')
                    title = metadata.get('title', 'unknown')
                    logger.debug(f"Error getting page info for tab {page_id}: {str(e)}")
                
                tab_status["tabs"][page_id] = {
                    "page_id": page_id,
                    "url": url,
                    "title": title,
                    "created_at": metadata.get('created_at', 0),
                    "session_id": metadata.get('session_id', None),
                    "last_activity": last_activity,
                    "idle_time_seconds": idle_time,
                    "idle_percentage": (idle_time / self.tab_idle_timeout) * 100 if self.tab_idle_timeout > 0 else 0
                }
            except Exception as e:
                logger.error(f"Error processing tab {page_id} for status: {str(e)}")
                tab_status["tabs"][page_id] = {
                    "page_id": page_id,
                    "error": str(e)
                }
        
        # Sort tabs by last activity (most recent first)
        sorted_tabs = sorted(tab_status["tabs"].items(), 
                            key=lambda x: x[1].get("last_activity", 0), 
                            reverse=True)
        
        # Rebuild the tabs dictionary in sorted order
        tab_status["tabs"] = {k: v for k, v in sorted_tabs}
        
        # Add information about tab cleanup
        tab_status["cleanup_info"] = {
            "scheduled": self._cleanup_scheduled,
            "next_tabs_to_close": [
                page_id for page_id, _ in sorted(
                    self.last_activity.items(), 
                    key=lambda x: x[1]
                )[:3] if page_id in self.active_pages
            ] if self.active_pages else []
        }
        
        return tab_status
    
    async def cleanup_tabs(self, force=False):
        """
        Manually trigger tab cleanup.
        
        Args:
            force: Whether to force cleanup even if under the threshold
            
        Returns:
            Dict with cleanup results
        """
        logger.info(f"Manual tab cleanup triggered (force={force})")
        
        # Store original tab count
        original_count = len(self.active_pages)
        
        # Clean up inactive tabs first
        inactive_closed = await self._cleanup_inactive_tabs()
        
        # Force close additional tabs if needed
        forced_closed = 0
        if force and len(self.active_pages) > self.max_tabs // 2:
            # Close tabs until we're at half max
            target_count = max(1, self.max_tabs // 2)
            while len(self.active_pages) > target_count:
                if await self._close_least_used_tab():
                    forced_closed += 1
                else:
                    break
        
        return {
            "original_tab_count": original_count,
            "current_tab_count": len(self.active_pages),
            "inactive_tabs_closed": inactive_closed,
            "forced_tabs_closed": forced_closed,
            "total_closed": inactive_closed + forced_closed
        }
    
    async def clear_browser_state(self):
        """Clear all saved browser state and close all pages."""
        logger.info("Clearing all browser state...")
        
        # Close all active pages
        if self.browser:
            for page_id in list(self.active_pages.keys()):
                if self.active_pages[page_id]:
                    await self.active_pages[page_id].close()
                    del self.active_pages[page_id]
        
        # Clear page metadata
        self.page_metadata = {}
        
        # Clear activity tracking
        self.last_activity = {}
        
        # Save empty state if the browser manager has a save_state method
        if hasattr(self, '_save_state'):
            self._save_state()
            
        logger.info("Browser state cleared")
        return True
        
    async def close(self):
        """Close all browser resources."""
        logger.info("Closing browser resources...")
        if self.browser:
            for page_id in list(self.active_pages.keys()):
                if self.active_pages[page_id]:
                    await self.active_pages[page_id].close()
                    del self.active_pages[page_id]
            
            await self.context.close()
            await self.browser.close()
            self.initialized = False
            logger.info("Browser resources closed")
