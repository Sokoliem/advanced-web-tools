"""Persistent Browser Manager for Web Interaction.

This module provides a browser manager that maintains state between function calls
by using a simple file-based persistence mechanism.
"""

import asyncio
import json
import logging
import os
import time
import pickle
from typing import Dict, Optional, Tuple, Any, Union, List
from pathlib import Path
from datetime import datetime

# Import console monitoring
from .console_monitor import ConsoleMonitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PersistentBrowserManager:
    """Manages browser instances with persistent state."""
    
    def __init__(self, storage_dir=None):
        """Initialize the browser manager."""
        self.browser = None
        self.context = None
        self.active_pages = {}
        self.initialized = False
        
        # Set storage directory for persistence
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".claude_web_interaction")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.state_file = os.path.join(self.storage_dir, "browser_state.json")
        
        # Create lock file for thread safety
        self.lock_file = os.path.join(self.storage_dir, "browser_lock")
        
        # Browser configuration settings
        self.headless = os.environ.get('MCP_BROWSER_HEADLESS', 'false').lower() == 'true'
        self.slow_mo = int(os.environ.get('MCP_BROWSER_SLOW_MO', '50'))
        self.debug_screenshots = os.environ.get('MCP_BROWSER_DEBUG_SCREENSHOTS', 'false').lower() == 'true'
        
        # Console monitoring
        self.console_monitor = ConsoleMonitor(self.storage_dir)
        
        # Override defaults if environment forces visible browser
        if os.environ.get('PLAYWRIGHT_FORCE_VISIBLE', 'false').lower() == 'true':
            self.headless = False
            logger.info("Browser visibility forced by PLAYWRIGHT_FORCE_VISIBLE")
            
        # Screenshot directory for debugging
        if self.debug_screenshots:
            self.screenshot_dir = Path(self.storage_dir) / 'screenshots'
            self.screenshot_dir.mkdir(exist_ok=True)
            logger.info(f"Debug screenshots will be saved to {self.screenshot_dir}")
        
        # Load state from persistent storage
        self._load_state()
        
    def _acquire_lock(self):
        """Acquire lock for thread-safe operations."""
        lock_count = 0
        while os.path.exists(self.lock_file) and lock_count < 10:
            # Wait for lock to be released
            time.sleep(0.1)
            lock_count += 1
            
        if lock_count >= 10:
            logger.warning("Lock acquisition timeout")
            # Force release lock
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                
        # Create lock file
        with open(self.lock_file, "w") as f:
            f.write(str(time.time()))
            
    def _release_lock(self):
        """Release lock after operation."""
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)
            
    def _load_state(self):
        """Load state from persistent storage."""
        try:
            self._acquire_lock()
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    
                # Only load metadata, not actual page objects
                self.page_metadata = state.get("page_metadata", {})
                logger.info(f"Loaded state with {len(self.page_metadata)} pages")
            else:
                self.page_metadata = {}
                logger.info("No saved state found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading state: {str(e)}")
            self.page_metadata = {}
        finally:
            self._release_lock()
            
    def _save_state(self):
        """Save state to persistent storage."""
        try:
            self._acquire_lock()
            
            # Store only metadata, not actual page objects
            state = {
                "page_metadata": self.page_metadata
            }
            
            with open(self.state_file, "w") as f:
                json.dump(state, f)
                
            logger.info(f"Saved state with {len(self.page_metadata)} pages")
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
        finally:
            self._release_lock()
            
    async def initialize(self):
        """Initialize the browser if not already initialized."""
        if not self.initialized:
            try:
                # Import here to avoid import errors if playwright isn't installed
                import playwright.async_api as pw
                
                logger.info("Initializing Playwright browser...")
                playwright = await pw.async_playwright().start()
                
                # Configure browser launch options
                logger.info(f"Launching browser with headless={self.headless}, slow_mo={self.slow_mo}ms")
                browser_options = {
                    "headless": False,  # Force visible browser
                    "slow_mo": self.slow_mo,
                    "devtools": True    # Open dev tools for better visibility
                }
                
                self.browser = await playwright.chromium.launch(**browser_options)
                self.context = await self.browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                self.initialized = True
                logger.info(f"Browser initialized with visible mode enabled")
                
                # Take screenshot if debug screenshots are enabled
                if hasattr(self, 'debug_screenshots') and self.debug_screenshots:
                    try:
                        # Create a debug page and take screenshot
                        debug_page = await self.context.new_page()
                        await debug_page.goto('about:blank')
                        await debug_page.evaluate("""
                        () => {
                            document.body.style.backgroundColor = 'black';
                            document.body.innerHTML = '<h1 style="color:lime; font-size:48px; text-align:center; margin-top:100px;">VISIBILITY TEST</h1><p style="color:white; text-align:center; font-size:24px;">If you can see this, the browser is visible!</p>';
                        }
                        """)
                        timestamp = time.time()
                        screenshot_path = str(self.screenshot_dir / f"init_test_{timestamp:.0f}.png")
                        await debug_page.screenshot(path=screenshot_path)
                        logger.info(f"Saved initialization test screenshot to {screenshot_path}")
                        await debug_page.close()
                    except Exception as e:
                        logger.error(f"Error creating visibility test: {str(e)}")
                
                # Don't automatically restore old pages on startup
                # await self._restore_pages()
            except Exception as e:
                logger.error(f"Error initializing browser: {str(e)}")
                raise
                
    async def _restore_pages(self):
        """Restore pages from metadata."""
        for page_id, metadata in list(self.page_metadata.items()):
            try:
                # Check if page already exists
                if page_id in self.active_pages:
                    continue
                    
                # Create new page
                new_page = await self.context.new_page()
                self.active_pages[page_id] = new_page
                
                # Set up console monitoring
                await self.console_monitor.setup_page_monitoring(new_page, page_id)
                
                # Navigate to last URL if available
                last_url = metadata.get("last_url")
                if last_url:
                    try:
                        await new_page.goto(last_url, wait_until="domcontentloaded")
                        logger.info(f"Restored page {page_id} to {last_url}")
                    except Exception as e:
                        logger.error(f"Error restoring page {page_id} to {last_url}: {str(e)}")
                        # If navigation fails, navigate to about:blank
                        await new_page.goto("about:blank")
            except Exception as e:
                logger.error(f"Error restoring page {page_id}: {str(e)}")
                # Remove failed page from metadata
                if page_id in self.page_metadata:
                    del self.page_metadata[page_id]
                    
        # Save updated state
        self._save_state()
            
    async def get_page(self, page_id=None):
        """
        Get a page by ID or create a new one.
        
        Args:
            page_id: Optional ID of an existing page
            
        Returns:
            Tuple of (page, page_id)
        """
        await self.initialize()
        
        # Handle string/int conversion for page_id
        if page_id is not None:
            # Handle different input types (string with quotes, integer, etc.)
            if isinstance(page_id, str):
                # Remove quotes if present
                page_id = page_id.strip('"\'')
            # Convert to string
            page_id = str(page_id)
            logger.info(f"Looking for page with ID {page_id}")
        
        # Check if page exists and is valid
        if page_id:
            # First check active pages
            if page_id in self.active_pages:
                logger.info(f"Using existing active page with ID {page_id}")
                # Update timestamp to indicate page is still in use
                if page_id in self.page_metadata:
                    self.page_metadata[page_id]["last_accessed"] = time.time()
                    self._save_state()
                return self.active_pages[page_id], page_id
                
            # Then check if page is in metadata but not active
            if page_id in self.page_metadata:
                try:
                    # Create new page
                    logger.info(f"Recreating page with ID {page_id} from metadata")
                    new_page = await self.context.new_page()
                    self.active_pages[page_id] = new_page
                    
                    # Set up console monitoring
                    await self.console_monitor.setup_page_monitoring(new_page, page_id)
                    
                    # Navigate to last URL if available
                    last_url = self.page_metadata[page_id].get("last_url")
                    if last_url and last_url != "about:blank":
                        try:
                            logger.info(f"Attempting to restore page {page_id} to {last_url}")
                            await new_page.goto(last_url, wait_until="domcontentloaded", timeout=30000)
                            logger.info(f"Successfully restored page {page_id} to {last_url}")
                        except Exception as e:
                            logger.error(f"Error restoring page {page_id} to {last_url}: {str(e)}")
                            # If navigation fails, navigate to about:blank
                            await new_page.goto("about:blank")
                    else:
                        logger.info(f"No valid URL to restore for page {page_id}, using about:blank")
                        await new_page.goto("about:blank")
                    
                    # Update metadata
                    self.page_metadata[page_id]["last_accessed"] = time.time()
                    self._save_state()
                    
                    return new_page, page_id
                except Exception as e:
                    logger.error(f"Error recreating page {page_id}: {str(e)}")
        
        # Create new page
        logger.info("Creating new browser page")
        new_page = await self.context.new_page()
        
        # Generate new ID
        existing_ids = set(list(self.active_pages.keys()) + list(self.page_metadata.keys()))
        new_id = str(max([int(i) if i.isdigit() else 0 for i in existing_ids], default=0) + 1)
        
        # Add to active pages and metadata
        self.active_pages[new_id] = new_page
        self.page_metadata[new_id] = {
            "created_at": time.time(),
            "last_url": "about:blank"
        }
        
        # Set up console monitoring
        await self.console_monitor.setup_page_monitoring(new_page, new_id)
        
        # Save state
        self._save_state()
        
        logger.info(f"Created new page with ID {new_id}, active pages: {list(self.active_pages.keys())}")
        return new_page, new_id
        
    async def update_page_metadata(self, page_id, url):
        """Update page metadata with current URL."""
        if page_id in self.page_metadata:
            self.page_metadata[page_id]["last_url"] = url
            self.page_metadata[page_id]["last_updated"] = time.time()
            # Save state
            self._save_state()
            
    async def highlight_element(self, page, selector, duration=1000):
        """Highlight an element on the page for visibility."""
        try:
            # Add highlight effect
            await page.evaluate(f"""
            (selector, duration) => {{
                const element = document.querySelector(selector);
                if (!element) return;
                
                // Store original styles
                const originalOutline = element.style.outline;
                const originalBoxShadow = element.style.boxShadow;
                const originalPosition = element.style.position;
                const originalZIndex = element.style.zIndex;
                
                // Apply highlight effect
                element.style.outline = '3px solid red';
                element.style.boxShadow = '0 0 10px rgba(255, 0, 0, 0.7)';
                element.style.position = 'relative';
                element.style.zIndex = '9999';
                
                // Create label to show the action
                const label = document.createElement('div');
                label.textContent = 'MCP ACTION';
                label.style.position = 'absolute';
                label.style.top = '-30px';
                label.style.left = '50%';
                label.style.transform = 'translateX(-50%)';
                label.style.backgroundColor = 'red';
                label.style.color = 'white';
                label.style.padding = '5px 10px';
                label.style.borderRadius = '3px';
                label.style.fontWeight = 'bold';
                label.style.fontSize = '14px';
                label.style.zIndex = '10000';
                element.appendChild(label);
                
                // Reset after duration
                setTimeout(() => {{
                    element.style.outline = originalOutline;
                    element.style.boxShadow = originalBoxShadow;
                    element.style.position = originalPosition;
                    element.style.zIndex = originalZIndex;
                    element.removeChild(label);
                }}, duration);
            }}
            """, selector, duration)
            
            # Wait for visual effect to be seen
            await asyncio.sleep(duration / 1000)
        except Exception as e:
            logger.error(f"Error highlighting element: {str(e)}")
    
    async def get_console_logs(self, page_id=None):
        """Get console logs for a page or all pages."""
        return await self.console_monitor.get_console_logs(page_id)
    
    async def get_page_errors(self, page_id=None):
        """Get page errors for a page or all pages."""
        return await self.console_monitor.get_page_errors(page_id)
    
    async def get_network_requests(self, page_id=None):
        """Get network requests for a page or all pages."""
        return await self.console_monitor.get_network_requests(page_id)
    
    async def execute_console_command(self, page_id, command):
        """Execute a JavaScript command in the console of a page."""
        if page_id not in self.active_pages:
            return {
                'success': False,
                'error': f"Page {page_id} not found"
            }
            
        return await self.console_monitor.execute_console_command(self.active_pages[page_id], command)
    
    async def close_page(self, page_id):
        """Close a specific page."""
        if page_id in self.active_pages:
            # Close the page
            await self.active_pages[page_id].close()
            del self.active_pages[page_id]
            logger.info(f"Closed page {page_id}")
            
            # Keep metadata for future reference
            self._save_state()
            
    async def close(self):
        """Close all browser resources."""
        logger.info("Closing browser resources...")
        
        # Update metadata for all active pages
        for page_id, page in list(self.active_pages.items()):
            try:
                url = page.url
                if page_id in self.page_metadata:
                    self.page_metadata[page_id]["last_url"] = url
                    self.page_metadata[page_id]["last_updated"] = time.time()
            except:
                pass
                
        # Save state before closing
        self._save_state()
        
        # Close all pages and browser
        if self.browser:
            for page_id in list(self.active_pages.keys()):
                if self.active_pages[page_id]:
                    await self.active_pages[page_id].close()
                    del self.active_pages[page_id]
            
            await self.context.close()
            await self.browser.close()
            self.initialized = False
            logger.info("Browser resources closed")
