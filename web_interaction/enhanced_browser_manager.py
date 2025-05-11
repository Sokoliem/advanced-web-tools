"""Enhanced Browser Management for Web Interaction Extension.

This module provides an enhanced browser manager with additional capabilities
such as multi-browser support, session management, and advanced browser automation.
"""

import asyncio
import json
import logging
import os
import pathlib
import time
import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple, Any, Union, List, Set

# Configure logging
logger = logging.getLogger(__name__)

class SessionInfo:
    """Information about a browser session."""
    def __init__(self, id: str, name: str = None):
        self.id = id
        self.name = name or f"Session {id}"
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.pages = set()  # Set of page IDs in this session
        self.metadata = {}
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "pages": list(self.pages),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary after deserialization."""
        session = cls(data["id"], data["name"])
        session.created_at = data["created_at"]
        session.last_accessed = data["last_accessed"]
        session.pages = set(data["pages"])
        session.metadata = data["metadata"]
        return session

class EnhancedBrowserManager:
    """Enhanced browser manager with advanced capabilities."""
    
    def __init__(self, storage_dir=None):
        """Initialize the browser manager."""
        # Base browser resources
        self.browsers = {}  # Multiple browser instances
        self.contexts = {}  # Multiple browser contexts
        self.active_pages = {}  # All active pages
        self.initialized = False
        
        # Session management
        self.sessions = {}  # Session ID -> SessionInfo
        self.page_to_session = {}  # Page ID -> Session ID
        
        # Set storage directory for persistence
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".claude_web_interaction")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.state_file = os.path.join(self.storage_dir, "browser_state.json")
        self.sessions_file = os.path.join(self.storage_dir, "sessions.json")
        
        # Create lock file for thread safety
        self.lock_file = os.path.join(self.storage_dir, "browser_lock")
        
        # Load browser configuration
        self.config = self.load_config()
        
        # Browser configuration settings
        self.default_browser = self.config.get("default_browser", "chromium")
        self.headless = self.config.get("headless", False)
        self.slow_mo = self.config.get("slow_mo", 50)
        self.width = self.config.get("width", 1280)
        self.height = self.config.get("height", 800)
        self.debug_screenshots = self.config.get("debug_screenshots", False)
        self.timeout = self.config.get("timeout", 30000)
        self.proxy = self.config.get("proxy", None)
        self.geolocation = self.config.get("geolocation", None)
        self.locale = self.config.get("locale", "en-US")
        self.timezone_id = self.config.get("timezone_id", "America/Los_Angeles")
        
        # Override defaults if environment forces visible browser
        if os.environ.get('PLAYWRIGHT_FORCE_VISIBLE', 'false').lower() == 'true':
            self.headless = False
            logger.info("Browser visibility forced by PLAYWRIGHT_FORCE_VISIBLE")
            
        # Screenshot directory for debugging
        if self.debug_screenshots:
            self.screenshot_dir = pathlib.Path(self.storage_dir) / 'screenshots'
            self.screenshot_dir.mkdir(exist_ok=True)
            logger.info(f"Debug screenshots will be saved to {self.screenshot_dir}")
        
        # Import console monitoring
        try:
            from .console_monitor import ConsoleMonitor
            self.console_monitor = ConsoleMonitor(self.storage_dir)
        except ImportError:
            logger.warning("Console monitoring not available")
            self.console_monitor = None
        
        # Load state from persistent storage
        self._load_state()
        self._load_sessions()
    
    def load_config(self) -> Dict[str, Any]:
        """Load browser configuration from file or environment variables."""
        config = {
            'default_browser': 'chromium',  # chromium, firefox, or webkit
            'headless': False,              # Default is visible
            'slow_mo': 50,                  # Default delay
            'width': 1280,                  # Default width
            'height': 800,                  # Default height
            'debug_screenshots': False,     # Disabled by default
            'timeout': 30000,               # Default timeout (30 seconds)
            'proxy': None,                  # No proxy by default
            'geolocation': None,            # No geolocation override by default
            'locale': 'en-US',              # Default locale
            'timezone_id': 'America/Los_Angeles',  # Default timezone
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
            'default_browser': os.environ.get('MCP_BROWSER_TYPE'),
            'headless': os.environ.get('MCP_BROWSER_HEADLESS'),
            'slow_mo': os.environ.get('MCP_BROWSER_SLOW_MO'),
            'width': os.environ.get('MCP_BROWSER_WIDTH'),
            'height': os.environ.get('MCP_BROWSER_HEIGHT'),
            'debug_screenshots': os.environ.get('MCP_BROWSER_DEBUG_SCREENSHOTS'),
            'timeout': os.environ.get('MCP_BROWSER_TIMEOUT'),
            'proxy': os.environ.get('MCP_BROWSER_PROXY'),
            'locale': os.environ.get('MCP_BROWSER_LOCALE'),
            'timezone_id': os.environ.get('MCP_BROWSER_TIMEZONE'),
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
    
    def _load_sessions(self):
        """Load sessions from persistent storage."""
        try:
            self._acquire_lock()
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, "r") as f:
                    sessions_data = json.load(f)
                    
                for session_data in sessions_data:
                    session = SessionInfo.from_dict(session_data)
                    self.sessions[session.id] = session
                
                logger.info(f"Loaded {len(self.sessions)} sessions")
            else:
                logger.info("No saved sessions found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading sessions: {str(e)}")
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
    
    def _save_sessions(self):
        """Save sessions to persistent storage."""
        try:
            self._acquire_lock()
            
            # Convert sessions to serializable format
            sessions_data = [session.to_dict() for session in self.sessions.values()]
            
            with open(self.sessions_file, "w") as f:
                json.dump(sessions_data, f)
                
            logger.info(f"Saved {len(self.sessions)} sessions")
        except Exception as e:
            logger.error(f"Error saving sessions: {str(e)}")
        finally:
            self._release_lock()
    
    async def initialize(self, browser_type=None):
        """Initialize browsers if not already initialized."""
        if not self.initialized:
            try:
                # Import here to avoid import errors if playwright isn't installed
                import playwright.async_api as pw
                
                logger.info("Initializing Playwright browsers...")
                playwright = await pw.async_playwright().start()
                
                # Initialize default browser
                browser_type = browser_type or self.default_browser
                
                # Configure browser launch options
                browser_options = {
                    "headless": self.headless,
                    "slow_mo": self.slow_mo,
                }
                
                # Add proxy configuration if set
                if self.proxy:
                    browser_options["proxy"] = {
                        "server": self.proxy
                    }
                
                # Launch browsers
                if browser_type == "chromium" or browser_type == "all":
                    logger.info(f"Launching Chromium with headless={self.headless}, slow_mo={self.slow_mo}ms")
                    self.browsers["chromium"] = await playwright.chromium.launch(**browser_options)
                
                if browser_type == "firefox" or browser_type == "all":
                    logger.info(f"Launching Firefox with headless={self.headless}, slow_mo={self.slow_mo}ms")
                    self.browsers["firefox"] = await playwright.firefox.launch(**browser_options)
                
                if browser_type == "webkit" or browser_type == "all":
                    logger.info(f"Launching WebKit with headless={self.headless}, slow_mo={self.slow_mo}ms")
                    self.browsers["webkit"] = await playwright.webkit.launch(**browser_options)
                
                # Create default browser context
                for browser_name, browser in self.browsers.items():
                    # Context options
                    context_options = {
                        "viewport": {"width": self.width, "height": self.height},
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "locale": self.locale,
                        "timezone_id": self.timezone_id,
                    }
                    
                    # Add geolocation if configured
                    if self.geolocation:
                        context_options["geolocation"] = self.geolocation
                    
                    # Create context
                    self.contexts[browser_name] = await browser.new_context(**context_options)
                    logger.info(f"Created browser context for {browser_name}")
                
                self.initialized = True
                logger.info(f"Browsers initialized successfully with configuration: {self.config}")
                
                # Take screenshot if debug screenshots are enabled
                if self.debug_screenshots:
                    try:
                        # Create a debug page and take screenshot
                        main_browser = list(self.browsers.values())[0]
                        main_context = list(self.contexts.values())[0]
                        debug_page = await main_context.new_page()
                        await debug_page.goto('about:blank')
                        await debug_page.evaluate("""
                        () => {
                            document.body.style.backgroundColor = 'black';
                            document.body.innerHTML = `
                                <h1 style="color:lime; font-size:48px; text-align:center; margin-top:100px;">ENHANCED BROWSER INITIALIZED</h1>
                                <p style="color:white; text-align:center; font-size:24px;">Browser type: ${navigator.userAgent}</p>
                                <p style="color:white; text-align:center; font-size:18px;">Timestamp: ${new Date().toISOString()}</p>
                            `;
                        }
                        """)
                        timestamp = time.time()
                        screenshot_path = str(self.screenshot_dir / f"init_test_{timestamp:.0f}.png")
                        await debug_page.screenshot(path=screenshot_path)
                        logger.info(f"Saved initialization test screenshot to {screenshot_path}")
                        await debug_page.close()
                    except Exception as e:
                        logger.error(f"Error creating initialization test screenshot: {str(e)}")
                
                # Don't automatically restore old pages on startup
                # await self._restore_pages()
            except Exception as e:
                logger.error(f"Error initializing browsers: {str(e)}")
                raise
    
    async def _restore_pages(self):
        """Restore pages from metadata."""
        for page_id, metadata in list(self.page_metadata.items()):
            try:
                # Check if page already exists
                if page_id in self.active_pages:
                    continue
                
                # Get browser type from metadata or use default
                browser_type = metadata.get("browser_type", self.default_browser)
                if browser_type not in self.browsers:
                    browser_type = self.default_browser
                
                # Create new page in the appropriate context
                new_page = await self.contexts[browser_type].new_page()
                self.active_pages[page_id] = new_page
                
                # Set up console monitoring if available
                if self.console_monitor:
                    await self.console_monitor.setup_page_monitoring(new_page, page_id)
                
                # Get session ID from metadata
                session_id = metadata.get("session_id")
                if session_id and session_id in self.sessions:
                    self.sessions[session_id].pages.add(page_id)
                    self.page_to_session[page_id] = session_id
                
                # Navigate to last URL if available
                last_url = metadata.get("last_url")
                if last_url and last_url != "about:blank":
                    try:
                        await new_page.goto(last_url, wait_until="domcontentloaded", timeout=self.timeout)
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
        self._save_sessions()
    
    async def create_session(self, name=None):
        """Create a new browser session."""
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session info
        session = SessionInfo(session_id, name)
        self.sessions[session_id] = session
        
        # Save sessions
        self._save_sessions()
        
        return session_id
    
    async def get_session(self, session_id):
        """Get information about a session."""
        if session_id in self.sessions:
            # Update last accessed time
            self.sessions[session_id].last_accessed = time.time()
            self._save_sessions()
            return self.sessions[session_id]
        return None
    
    async def delete_session(self, session_id):
        """Delete a session and all its pages."""
        if session_id in self.sessions:
            # Get pages in this session
            pages = self.sessions[session_id].pages.copy()
            
            # Close all pages in this session
            for page_id in pages:
                await self.close_page(page_id)
            
            # Remove session
            del self.sessions[session_id]
            self._save_sessions()
            return True
        return False
    
    async def get_page(self, page_id=None, session_id=None, browser_type=None):
        """
        Get a page by ID or create a new one.
        
        Args:
            page_id: Optional ID of an existing page
            session_id: Optional ID of a session to add the page to
            browser_type: Optional browser type to use (chromium, firefox, webkit)
            
        Returns:
            Tuple of (page, page_id)
        """
        await self.initialize(browser_type)
        
        # Use specified browser type or default
        browser_type = browser_type or self.default_browser
        if browser_type not in self.browsers:
            logger.warning(f"Browser type {browser_type} not available, using {self.default_browser}")
            browser_type = self.default_browser
        
        # Handle string/int conversion for page_id
        if page_id is not None:
            # Convert to string if it's a number or other type
            page_id = str(page_id)
        
        # Check if page exists
        if page_id and page_id in self.active_pages:
            logger.info(f"Using existing page with ID {page_id}")
            
            # Update session if provided
            if session_id and session_id in self.sessions:
                # Remove from old session if exists
                old_session_id = self.page_to_session.get(page_id)
                if old_session_id and old_session_id in self.sessions:
                    self.sessions[old_session_id].pages.discard(page_id)
                
                # Add to new session
                self.sessions[session_id].pages.add(page_id)
                self.page_to_session[page_id] = session_id
                self._save_sessions()
            
            # Update metadata
            if page_id in self.page_metadata:
                self.page_metadata[page_id]["last_accessed"] = time.time()
                self._save_state()
            
            return self.active_pages[page_id], page_id
        
        # Try to restore page from metadata
        if page_id and page_id in self.page_metadata:
            try:
                # Get browser type from metadata
                stored_browser_type = self.page_metadata[page_id].get("browser_type", browser_type)
                if stored_browser_type not in self.browsers:
                    stored_browser_type = browser_type
                
                # Create new page
                logger.info(f"Recreating page with ID {page_id} from metadata")
                new_page = await self.contexts[stored_browser_type].new_page()
                self.active_pages[page_id] = new_page
                
                # Set up console monitoring if available
                if self.console_monitor:
                    await self.console_monitor.setup_page_monitoring(new_page, page_id)
                
                # Navigate to last URL if available
                last_url = self.page_metadata[page_id].get("last_url")
                if last_url and last_url != "about:blank":
                    try:
                        logger.info(f"Attempting to restore page {page_id} to {last_url}")
                        await new_page.goto(last_url, wait_until="domcontentloaded", timeout=self.timeout)
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
                self.page_metadata[page_id]["browser_type"] = stored_browser_type
                
                # Update session if provided
                if session_id and session_id in self.sessions:
                    # Get old session ID if exists
                    old_session_id = self.page_metadata[page_id].get("session_id")
                    if old_session_id and old_session_id in self.sessions:
                        self.sessions[old_session_id].pages.discard(page_id)
                    
                    # Update session
                    self.sessions[session_id].pages.add(page_id)
                    self.page_to_session[page_id] = session_id
                    self.page_metadata[page_id]["session_id"] = session_id
                
                self._save_state()
                self._save_sessions()
                
                return new_page, page_id
            except Exception as e:
                logger.error(f"Error recreating page {page_id}: {str(e)}")
        
        # Create new page
        logger.info(f"Creating new browser page with {browser_type}")
        new_page = await self.contexts[browser_type].new_page()
        
        # Generate new ID
        existing_ids = set(list(self.active_pages.keys()) + list(self.page_metadata.keys()))
        new_id = str(max([int(i) if i.isdigit() else 0 for i in existing_ids], default=0) + 1)
        
        # Add to active pages and metadata
        self.active_pages[new_id] = new_page
        self.page_metadata[new_id] = {
            "created_at": time.time(),
            "last_accessed": time.time(),
            "last_url": "about:blank",
            "browser_type": browser_type
        }
        
        # Set up console monitoring if available
        if self.console_monitor:
            await self.console_monitor.setup_page_monitoring(new_page, new_id)
        
        # Add to session if provided
        if session_id and session_id in self.sessions:
            self.sessions[session_id].pages.add(new_id)
            self.page_to_session[new_id] = session_id
            self.page_metadata[new_id]["session_id"] = session_id
        
        # Save state
        self._save_state()
        self._save_sessions()
        
        logger.info(f"Created new page with ID {new_id}, browser type: {browser_type}")
        return new_page, new_id
    
    async def update_page_metadata(self, page_id, url=None, title=None, extra_data=None):
        """Update page metadata."""
        if page_id in self.page_metadata:
            if url:
                self.page_metadata[page_id]["last_url"] = url
            
            if title:
                self.page_metadata[page_id]["title"] = title
            
            self.page_metadata[page_id]["last_updated"] = time.time()
            
            # Add any extra data
            if extra_data and isinstance(extra_data, dict):
                for key, value in extra_data.items():
                    self.page_metadata[page_id][key] = value
            
            # Save state
            self._save_state()
    
    async def take_screenshot(self, page_id, full_page=False, element_selector=None):
        """Take a screenshot of a page or element."""
        if page_id not in self.active_pages:
            logger.error(f"Page {page_id} not found for screenshot")
            return None
        
        try:
            page = self.active_pages[page_id]
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = pathlib.Path(self.storage_dir) / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = int(time.time())
            if element_selector:
                filename = f"element_{page_id}_{timestamp}.png"
                screenshot_path = str(screenshots_dir / filename)
                
                # Find element and take screenshot
                element = await page.query_selector(element_selector)
                if element:
                    await element.screenshot(path=screenshot_path)
                    logger.info(f"Took screenshot of element on page {page_id}, saved to {screenshot_path}")
                else:
                    logger.error(f"Element not found with selector: {element_selector}")
                    return None
            else:
                filename = f"page_{page_id}_{timestamp}.png"
                screenshot_path = str(screenshots_dir / filename)
                
                # Take page screenshot
                await page.screenshot(path=screenshot_path, full_page=full_page)
                logger.info(f"Took {'full page' if full_page else 'viewport'} screenshot of page {page_id}, saved to {screenshot_path}")
            
            return screenshot_path
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return None
    
    async def get_page_info(self, page_id=None):
        """Get information about pages."""
        result = {}
        
        # If page_id specified, get info for that page
        if page_id:
            if page_id in self.page_metadata:
                metadata = self.page_metadata[page_id].copy()
                metadata["active"] = page_id in self.active_pages
                
                # Get session info if available
                session_id = self.page_to_session.get(page_id)
                if session_id and session_id in self.sessions:
                    metadata["session"] = {
                        "id": session_id,
                        "name": self.sessions[session_id].name
                    }
                
                result = metadata
        else:
            # Get info for all pages
            pages_info = {}
            for page_id, metadata in self.page_metadata.items():
                page_info = metadata.copy()
                page_info["active"] = page_id in self.active_pages
                
                # Get session info if available
                session_id = self.page_to_session.get(page_id)
                if session_id and session_id in self.sessions:
                    page_info["session"] = {
                        "id": session_id,
                        "name": self.sessions[session_id].name
                    }
                
                pages_info[page_id] = page_info
            
            result = {
                "pages": pages_info,
                "active_count": len(self.active_pages),
                "total_count": len(self.page_metadata),
                "browser_types": list(self.browsers.keys())
            }
        
        return result
        
    async def get_tab_status(self):
        """
        Get detailed status of all tabs/pages.
        
        Returns:
            Dict with detailed tab status information
        """
        tab_status = {
            "active_tabs_count": len(self.active_pages),
            "max_tabs": 8,  # Default maximum tabs
            "tab_idle_timeout": 300,  # Default timeout in seconds
            "tabs": {}
        }
        
        current_time = time.time()
        
        # Add info for each active tab
        sorted_tabs = []
        for page_id, page in self.active_pages.items():
            try:
                metadata = self.page_metadata.get(page_id, {})
                
                # Calculate last activity time
                last_updated = metadata.get("last_updated", 0)
                last_accessed = metadata.get("last_accessed", 0)
                last_activity = max(last_updated, last_accessed)
                
                idle_time = current_time - last_activity if last_activity > 0 else 0
                
                # Get current URL and title
                try:
                    url = page.url
                    title = await page.title()
                except Exception as e:
                    url = metadata.get("last_url", "unknown")
                    title = metadata.get("title", "unknown")
                    logger.debug(f"Error getting page info for tab {page_id}: {str(e)}")
                
                # Add tab info with activity timestamp for sorting
                sorted_tabs.append((
                    page_id,
                    last_activity,
                    {
                        "page_id": page_id,
                        "url": url,
                        "title": title,
                        "created_at": metadata.get("created_at", 0),
                        "session_id": metadata.get("session_id", None),
                        "last_activity": last_activity,
                        "idle_time_seconds": idle_time,
                        "idle_percentage": (idle_time / 300) * 100  # Based on 5 minute idle timeout
                    }
                ))
            except Exception as e:
                logger.error(f"Error processing tab {page_id} for status: {str(e)}")
                sorted_tabs.append((
                    page_id,
                    0,  # Lowest priority for sorting
                    {
                        "page_id": page_id,
                        "error": str(e)
                    }
                ))
        
        # Sort tabs by last activity (most recent first)
        sorted_tabs.sort(key=lambda x: x[1], reverse=True)
        
        # Add tabs to status dictionary
        for page_id, _, tab_info in sorted_tabs:
            tab_status["tabs"][page_id] = tab_info
        
        # Add information about cleanup
        tab_status["cleanup_info"] = {
            "scheduled": False,  # No scheduled cleanup
            "next_tabs_to_close": [page_id for page_id, _, _ in sorted_tabs[-3:]] if len(sorted_tabs) > 3 else []
        }
        
        return tab_status
    
    async def get_session_info(self, session_id=None):
        """Get information about sessions."""
        result = {}
        
        # If session_id specified, get info for that session
        if session_id:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                result = session.to_dict()
                
                # Add page info
                pages_info = {}
                for page_id in session.pages:
                    if page_id in self.page_metadata:
                        page_info = self.page_metadata[page_id].copy()
                        page_info["active"] = page_id in self.active_pages
                        pages_info[page_id] = page_info
                
                result["pages_info"] = pages_info
        else:
            # Get info for all sessions
            sessions_info = {}
            for session_id, session in self.sessions.items():
                session_info = session.to_dict()
                session_info["active_pages"] = sum(1 for page_id in session.pages if page_id in self.active_pages)
                sessions_info[session_id] = session_info
            
            result = {
                "sessions": sessions_info,
                "count": len(self.sessions)
            }
        
        return result
    
    async def highlight_element(self, page, selector, duration=1000):
        """Highlight an element on the page for visibility."""
        try:
            # Add highlight effect
            await page.evaluate(f"""
            (selector, duration) => {{
                const element = document.querySelector(selector);
                if (!element) return false;
                
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
                    if (label.parentNode === element) {{
                        element.removeChild(label);
                    }}
                }}, duration);
                
                return true;
            }}
            """, selector, duration)
            
            # Wait for visual effect to be seen
            await asyncio.sleep(duration / 1000)
        except Exception as e:
            logger.error(f"Error highlighting element: {str(e)}")
    
    async def close_page(self, page_id):
        """Close a specific page."""
        if page_id in self.active_pages:
            try:
                # Update metadata before closing
                page = self.active_pages[page_id]
                current_url = page.url
                
                if page_id in self.page_metadata:
                    self.page_metadata[page_id]["last_url"] = current_url
                    self.page_metadata[page_id]["last_updated"] = time.time()
                
                # Close the page
                await page.close()
                del self.active_pages[page_id]
                logger.info(f"Closed page {page_id}")
                
                # Update session if needed
                session_id = self.page_to_session.get(page_id)
                if session_id and session_id in self.sessions:
                    # Keep page in session but mark as inactive
                    pass
                
                # Save state
                self._save_state()
                self._save_sessions()
                
                return True
            except Exception as e:
                logger.error(f"Error closing page {page_id}: {str(e)}")
                return False
        
        return False
        
    async def cleanup_tabs(self, force=False):
        """
        Manually trigger cleanup of browser tabs.
        
        Args:
            force: Whether to force cleanup even if under threshold
            
        Returns:
            Dict with cleanup results
        """
        logger.info(f"Manual tab cleanup triggered (force={force})")
        
        # Store original tab count
        original_count = len(self.active_pages)
        
        # Define inactive threshold (5 minutes)
        inactive_threshold = 300  # seconds
        current_time = time.time()
        
        # Find inactive tabs
        inactive_tabs = []
        for page_id in list(self.active_pages.keys()):
            if page_id in self.page_metadata:
                last_updated = self.page_metadata[page_id].get("last_updated", 0)
                last_accessed = self.page_metadata[page_id].get("last_accessed", 0)
                
                # Use the most recent timestamp
                last_activity = max(last_updated, last_accessed)
                
                # Check if tab is inactive
                if current_time - last_activity > inactive_threshold:
                    inactive_tabs.append(page_id)
        
        # Close inactive tabs
        inactive_closed = 0
        for page_id in inactive_tabs:
            if await self.close_page(page_id):
                inactive_closed += 1
                
        # Force close additional tabs if needed
        forced_closed = 0
        if force and len(self.active_pages) > 3:  # Leave at least 3 tabs open
            # Sort tabs by last activity
            sorted_tabs = []
            for page_id in self.active_pages:
                if page_id in self.page_metadata:
                    last_updated = self.page_metadata[page_id].get("last_updated", 0)
                    last_accessed = self.page_metadata[page_id].get("last_accessed", 0)
                    last_activity = max(last_updated, last_accessed)
                    sorted_tabs.append((page_id, last_activity))
            
            # Sort by activity time (oldest first)
            sorted_tabs.sort(key=lambda x: x[1])
            
            # Close oldest tabs, leaving at least 3
            tabs_to_close = sorted_tabs[:-3] if len(sorted_tabs) > 3 else []
            for page_id, _ in tabs_to_close:
                if await self.close_page(page_id):
                    forced_closed += 1
        
        return {
            "original_tab_count": original_count,
            "current_tab_count": len(self.active_pages),
            "inactive_tabs_closed": inactive_closed,
            "forced_tabs_closed": forced_closed,
            "total_closed": inactive_closed + forced_closed
        }
    
    async def clear_cookies(self, page_id=None, session_id=None):
        """Clear cookies for a page, session, or all pages."""
        try:
            if page_id:
                # Clear cookies for specific page
                if page_id in self.active_pages:
                    context = await self.active_pages[page_id].context
                    await context.clear_cookies()
                    logger.info(f"Cleared cookies for page {page_id}")
                    return True
                else:
                    logger.warning(f"Page {page_id} not found for clearing cookies")
                    return False
            elif session_id:
                # Clear cookies for all pages in a session
                if session_id in self.sessions:
                    for page_id in self.sessions[session_id].pages:
                        if page_id in self.active_pages:
                            context = await self.active_pages[page_id].context
                            await context.clear_cookies()
                    logger.info(f"Cleared cookies for all pages in session {session_id}")
                    return True
                else:
                    logger.warning(f"Session {session_id} not found for clearing cookies")
                    return False
            else:
                # Clear cookies for all contexts
                for context in self.contexts.values():
                    await context.clear_cookies()
                logger.info("Cleared cookies for all browser contexts")
                return True
        except Exception as e:
            logger.error(f"Error clearing cookies: {str(e)}")
            return False
    
    async def get_console_logs(self, page_id=None):
        """Get console logs for a page or all pages."""
        if self.console_monitor:
            return await self.console_monitor.get_console_logs(page_id)
        return {}
    
    async def get_page_errors(self, page_id=None):
        """Get page errors for a page or all pages."""
        if self.console_monitor:
            return await self.console_monitor.get_page_errors(page_id)
        return {}
    
    async def execute_console_command(self, page_id, command):
        """Execute a JavaScript command in the console of a page."""
        if page_id not in self.active_pages:
            return {
                'success': False,
                'error': f"Page {page_id} not found"
            }
        
        if self.console_monitor:
            return await self.console_monitor.execute_console_command(self.active_pages[page_id], command)
        else:
            try:
                result = await self.active_pages[page_id].evaluate(command)
                return {
                    'success': True,
                    'result': result
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
    
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
        self._save_sessions()
        
        # Close all pages and browsers
        for browser_type, browser in list(self.browsers.items()):
            if browser:
                for context_name, context in list(self.contexts.items()):
                    if context_name.startswith(browser_type) and context:
                        await context.close()
                        del self.contexts[context_name]
                
                await browser.close()
                del self.browsers[browser_type]
        
        # Clear active pages
        self.active_pages.clear()
        
        self.initialized = False
        logger.info("Browser resources closed")