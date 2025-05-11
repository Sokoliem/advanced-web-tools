"""Error Handling and Recovery for Web Interaction.

This module provides error handling, recovery mechanisms, and diagnostics
for web interaction operations to improve reliability and debugging.
"""

import asyncio
import logging
import os
import traceback
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class ErrorCategory:
    """Error categories for classification."""
    NETWORK = "network"
    TIMEOUT = "timeout"
    NAVIGATION = "navigation"
    ELEMENT = "element"
    JAVASCRIPT = "javascript"
    BROWSER = "browser"
    PERMISSION = "permission"
    INPUT = "input"
    UNKNOWN = "unknown"

class WebErrorHandler:
    """Handles web interaction errors with recovery mechanisms."""
    
    def __init__(self, error_log_dir=None):
        """Initialize the error handler with optional error log directory."""
        # Set error log directory
        self.error_log_dir = error_log_dir
        if self.error_log_dir:
            os.makedirs(self.error_log_dir, exist_ok=True)
        
        # Error statistics
        self.error_stats = {
            category: {
                "count": 0,
                "last_occurred": None,
                "recent_errors": []
            }
            for category in vars(ErrorCategory).keys()
            if not category.startswith("__")
        }
        
        # Define error patterns for classification
        self.error_patterns = {
            ErrorCategory.NETWORK: [
                "net::ERR_",
                "network error",
                "failed to fetch",
                "connection refused",
                "cannot connect to host"
            ],
            ErrorCategory.TIMEOUT: [
                "timeout",
                "timed out",
                "deadline exceeded"
            ],
            ErrorCategory.NAVIGATION: [
                "navigation failed",
                "navigation timeout",
                "page crashed",
                "target closed"
            ],
            ErrorCategory.ELEMENT: [
                "element not found",
                "could not find element",
                "no element found",
                "failed to find element",
                "element is not attached"
            ],
            ErrorCategory.JAVASCRIPT: [
                "javascript error",
                "execution context was destroyed",
                "script error",
                "undefined is not a function",
                "cannot read property"
            ],
            ErrorCategory.BROWSER: [
                "browser disconnected",
                "browser closed",
                "target closed",
                "cdp session closed"
            ],
            ErrorCategory.PERMISSION: [
                "permission denied",
                "access denied",
                "not allowed",
                "blocked by"
            ],
            ErrorCategory.INPUT: [
                "invalid input",
                "invalid argument",
                "parameter",
                "expected",
                "required"
            ]
        }
        
        # Recovery strategies by category
        self.recovery_strategies = {
            ErrorCategory.NETWORK: [
                self._retry_with_delay,
                self._retry_with_new_page,
                self._refresh_page
            ],
            ErrorCategory.TIMEOUT: [
                self._retry_with_delay,
                self._retry_with_increased_timeout,
                self._refresh_page,
                self._retry_with_new_page
            ],
            ErrorCategory.NAVIGATION: [
                self._retry_with_delay,
                self._refresh_page,
                self._retry_with_new_page,
                self._restart_browser
            ],
            ErrorCategory.ELEMENT: [
                self._retry_after_wait,
                self._refresh_page,
                self._try_alternate_selector
            ],
            ErrorCategory.JAVASCRIPT: [
                self._retry_with_delay,
                self._refresh_page,
                self._retry_with_new_page
            ],
            ErrorCategory.BROWSER: [
                self._retry_with_new_page,
                self._restart_browser
            ],
            ErrorCategory.PERMISSION: [
                self._retry_with_modified_headers,
                self._retry_with_new_context
            ],
            ErrorCategory.INPUT: [
                self._apply_input_corrections
            ],
            ErrorCategory.UNKNOWN: [
                self._retry_with_delay,
                self._refresh_page,
                self._retry_with_new_page
            ]
        }
    
    def classify_error(self, error: Exception) -> str:
        """Classify an error into a category based on error patterns."""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Check each category's patterns
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern.lower() in error_str:
                    return category
        
        # Special error type classification
        if "timeout" in error_type.lower():
            return ErrorCategory.TIMEOUT
        
        if "navigation" in error_type.lower():
            return ErrorCategory.NAVIGATION
        
        if "element" in error_type.lower():
            return ErrorCategory.ELEMENT
        
        # Default to unknown if no pattern matches
        return ErrorCategory.UNKNOWN
    
    def log_error(self, operation: str, category: str, error: Exception, context: Dict[str, Any]) -> None:
        """Log error details to file and update error statistics."""
        # Update error statistics
        if category in self.error_stats:
            self.error_stats[category]["count"] += 1
            self.error_stats[category]["last_occurred"] = datetime.now().isoformat()
            
            # Add to recent errors (keep last 10)
            error_info = {
                "operation": operation,
                "error": str(error),
                "timestamp": datetime.now().isoformat(),
                "traceback": traceback.format_exc()
            }
            self.error_stats[category]["recent_errors"].append(error_info)
            if len(self.error_stats[category]["recent_errors"]) > 10:
                self.error_stats[category]["recent_errors"].pop(0)
        
        # Log to file if directory is set
        if self.error_log_dir:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"error_{category}_{timestamp}.json"
            file_path = os.path.join(self.error_log_dir, filename)
            
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "category": category,
                "error": str(error),
                "error_type": type(error).__name__,
                "traceback": traceback.format_exc(),
                "context": context
            }
            
            try:
                with open(file_path, 'w') as f:
                    json.dump(error_data, f, indent=2)
                logger.info(f"Error details logged to {file_path}")
            except Exception as log_error:
                logger.error(f"Failed to write error log: {str(log_error)}")
    
    async def attempt_recovery(self, page, browser_manager, operation: str, error: Exception, 
                               operation_params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Attempt to recover from an error using appropriate strategies.
        
        Args:
            page: The page where the error occurred
            browser_manager: Browser manager instance for browser operations
            operation: The operation that failed
            error: The exception that occurred
            operation_params: Parameters of the failed operation
            
        Returns:
            Tuple of (success, result_or_error)
        """
        # Classify the error
        category = self.classify_error(error)
        
        # Log the error
        context = {
            "page_url": page.url if page else "No page",
            "page_id": next((k for k, v in browser_manager.active_pages.items() if v == page), "Unknown"),
            "operation": operation,
            "operation_params": operation_params
        }
        self.log_error(operation, category, error, context)
        
        # Get recovery strategies for this category
        strategies = self.recovery_strategies.get(category, self.recovery_strategies[ErrorCategory.UNKNOWN])
        
        # Try each strategy in order until one succeeds
        for strategy in strategies:
            try:
                logger.info(f"Attempting recovery for {operation} with strategy {strategy.__name__}")
                success, result = await strategy(page, browser_manager, operation, operation_params)
                if success:
                    logger.info(f"Recovery successful with strategy {strategy.__name__}")
                    return True, result
            except Exception as recovery_error:
                logger.error(f"Recovery attempt failed with strategy {strategy.__name__}: {str(recovery_error)}")
        
        # All recovery strategies failed
        logger.warning(f"All recovery strategies failed for {operation}")
        return False, {
            "success": False,
            "error": f"Failed to recover from {category} error: {str(error)}",
            "original_error": str(error)
        }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "total_errors": sum(cat["count"] for cat in self.error_stats.values()),
            "by_category": {k: v["count"] for k, v in self.error_stats.items()},
            "details": self.error_stats
        }
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on error patterns."""
        recommendations = []
        
        # Network recommendations
        if self.error_stats[ErrorCategory.NETWORK]["count"] > 3:
            recommendations.append("Consider checking network connectivity or proxy settings")
        
        # Timeout recommendations
        if self.error_stats[ErrorCategory.TIMEOUT]["count"] > 3:
            recommendations.append("Consider increasing timeout values for operations")
        
        # Element recommendations
        if self.error_stats[ErrorCategory.ELEMENT]["count"] > 5:
            recommendations.append("Consider using more robust element selectors or adding wait conditions")
        
        # Browser recommendations
        if self.error_stats[ErrorCategory.BROWSER]["count"] > 2:
            recommendations.append("Consider checking browser stability or memory usage")
        
        return recommendations
    
    # Recovery strategies
    async def _retry_with_delay(self, page, browser_manager, operation, params, delay=2.0):
        """Retry the operation after a delay."""
        await asyncio.sleep(delay)
        try:
            # Get the operation function based on the operation name
            operation_func = getattr(page, operation, None)
            if operation_func and callable(operation_func):
                result = await operation_func(**params)
                return True, {"success": True, "result": result}
            return False, {"success": False, "error": f"Operation {operation} not found"}
        except Exception as e:
            return False, {"success": False, "error": str(e)}
    
    async def _retry_with_increased_timeout(self, page, browser_manager, operation, params):
        """Retry with an increased timeout value."""
        # Increase timeout parameter if present
        new_params = params.copy()
        if "timeout" in new_params:
            new_params["timeout"] = new_params["timeout"] * 2
        elif "options" in new_params and isinstance(new_params["options"], dict) and "timeout" in new_params["options"]:
            new_params["options"]["timeout"] = new_params["options"]["timeout"] * 2
        else:
            # Add a timeout parameter if there isn't one
            new_params["timeout"] = 60000  # 60 seconds
        
        try:
            # Get the operation function based on the operation name
            operation_func = getattr(page, operation, None)
            if operation_func and callable(operation_func):
                result = await operation_func(**new_params)
                return True, {"success": True, "result": result}
            return False, {"success": False, "error": f"Operation {operation} not found"}
        except Exception as e:
            return False, {"success": False, "error": str(e)}
    
    async def _refresh_page(self, page, browser_manager, operation, params):
        """Refresh the page and retry the operation."""
        try:
            await page.reload()
            # Wait for network idle after reload
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Get the operation function based on the operation name
            operation_func = getattr(page, operation, None)
            if operation_func and callable(operation_func):
                result = await operation_func(**params)
                return True, {"success": True, "result": result}
            return False, {"success": False, "error": f"Operation {operation} not found"}
        except Exception as e:
            return False, {"success": False, "error": str(e)}
    
    async def _retry_with_new_page(self, page, browser_manager, operation, params):
        """Create a new page, navigate to the same URL, and retry."""
        try:
            # Get current URL
            current_url = page.url
            
            # Get page ID
            page_id = next((k for k, v in browser_manager.active_pages.items() if v == page), None)
            
            # Create new page
            new_page, new_id = await browser_manager.get_page()
            
            # Navigate to the same URL
            if current_url and current_url != "about:blank":
                await new_page.goto(current_url, wait_until="networkidle")
            
            # Get the operation function based on the operation name
            operation_func = getattr(new_page, operation, None)
            if operation_func and callable(operation_func):
                result = await operation_func(**params)
                
                # If old page exists, close it
                if page_id and page_id in browser_manager.active_pages:
                    await browser_manager.close_page(page_id)
                
                return True, {
                    "success": True, 
                    "result": result,
                    "new_page_id": new_id
                }
            return False, {"success": False, "error": f"Operation {operation} not found"}
        except Exception as e:
            return False, {"success": False, "error": str(e)}
    
    async def _restart_browser(self, page, browser_manager, operation, params):
        """Restart the browser and retry the operation."""
        try:
            # Get current URL
            current_url = page.url
            
            # Get page ID
            page_id = next((k for k, v in browser_manager.active_pages.items() if v == page), None)
            
            # Close and reinitialize browser
            await browser_manager.close()
            await browser_manager.initialize()
            
            # Create new page
            new_page, new_id = await browser_manager.get_page()
            
            # Navigate to the same URL
            if current_url and current_url != "about:blank":
                await new_page.goto(current_url, wait_until="networkidle")
            
            # Get the operation function based on the operation name
            operation_func = getattr(new_page, operation, None)
            if operation_func and callable(operation_func):
                result = await operation_func(**params)
                return True, {
                    "success": True, 
                    "result": result,
                    "new_page_id": new_id
                }
            return False, {"success": False, "error": f"Operation {operation} not found"}
        except Exception as e:
            return False, {"success": False, "error": str(e)}
    
    async def _retry_after_wait(self, page, browser_manager, operation, params):
        """Wait for content to load and retry."""
        try:
            # Wait for network idle
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Then wait a bit longer for any dynamic content
            await asyncio.sleep(2.0)
            
            # Get the operation function based on the operation name
            operation_func = getattr(page, operation, None)
            if operation_func and callable(operation_func):
                result = await operation_func(**params)
                return True, {"success": True, "result": result}
            return False, {"success": False, "error": f"Operation {operation} not found"}
        except Exception as e:
            return False, {"success": False, "error": str(e)}
    
    async def _try_alternate_selector(self, page, browser_manager, operation, params):
        """Try alternate selectors for element operations."""
        # Only applicable for element operations
        if "selector" not in params:
            return False, {"success": False, "error": "Operation does not use selectors"}
        
        original_selector = params["selector"]
        alternate_selectors = generate_alternate_selectors(original_selector)
        
        for selector in alternate_selectors:
            try:
                new_params = params.copy()
                new_params["selector"] = selector
                
                # Get the operation function based on the operation name
                operation_func = getattr(page, operation, None)
                if operation_func and callable(operation_func):
                    result = await operation_func(**new_params)
                    return True, {
                        "success": True, 
                        "result": result,
                        "alternate_selector": selector
                    }
            except Exception:
                # Try next selector
                continue
        
        return False, {"success": False, "error": "All alternate selectors failed"}
    
    async def _retry_with_modified_headers(self, page, browser_manager, operation, params):
        """Retry with modified headers to avoid detection."""
        try:
            # Set a more standard user agent
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            })
            
            # Get the operation function based on the operation name
            operation_func = getattr(page, operation, None)
            if operation_func and callable(operation_func):
                result = await operation_func(**params)
                return True, {"success": True, "result": result}
            return False, {"success": False, "error": f"Operation {operation} not found"}
        except Exception as e:
            return False, {"success": False, "error": str(e)}
    
    async def _retry_with_new_context(self, page, browser_manager, operation, params):
        """Create a new browser context with different settings and retry."""
        try:
            # Get current URL
            current_url = page.url
            
            # Create a new context with different settings
            browser = list(browser_manager.browsers.values())[0]
            new_context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                locale="en-US"
            )
            
            # Create new page in the new context
            new_page = await new_context.new_page()
            
            # Navigate to the same URL
            if current_url and current_url != "about:blank":
                await new_page.goto(current_url, wait_until="networkidle")
            
            # Get the operation function based on the operation name
            operation_func = getattr(new_page, operation, None)
            if operation_func and callable(operation_func):
                result = await operation_func(**params)
                return True, {"success": True, "result": result}
            
            # Clean up
            await new_context.close()
            return False, {"success": False, "error": f"Operation {operation} not found"}
        except Exception as e:
            return False, {"success": False, "error": str(e)}
    
    async def _apply_input_corrections(self, page, browser_manager, operation, params):
        """Apply corrections to input parameters and retry."""
        # Only applicable for certain operations
        input_corrections = {
            "fill": self._correct_fill_params,
            "type": self._correct_type_params,
            "click": self._correct_click_params,
            "select_option": self._correct_select_params,
            "goto": self._correct_goto_params
        }
        
        correction_func = input_corrections.get(operation)
        if not correction_func:
            return False, {"success": False, "error": f"No corrections available for {operation}"}
        
        try:
            new_params = correction_func(params)
            
            # Get the operation function based on the operation name
            operation_func = getattr(page, operation, None)
            if operation_func and callable(operation_func):
                result = await operation_func(**new_params)
                return True, {
                    "success": True, 
                    "result": result,
                    "corrected_params": new_params
                }
            return False, {"success": False, "error": f"Operation {operation} not found"}
        except Exception as e:
            return False, {"success": False, "error": str(e)}
    
    # Helper functions for parameter corrections
    def _correct_fill_params(self, params):
        """Correct parameters for fill operation."""
        new_params = params.copy()
        
        # Ensure text is a string
        if "value" in new_params and not isinstance(new_params["value"], str):
            new_params["value"] = str(new_params["value"])
        
        return new_params
    
    def _correct_type_params(self, params):
        """Correct parameters for type operation."""
        new_params = params.copy()
        
        # Ensure text is a string
        if "text" in new_params and not isinstance(new_params["text"], str):
            new_params["text"] = str(new_params["text"])
        
        return new_params
    
    def _correct_click_params(self, params):
        """Correct parameters for click operation."""
        new_params = params.copy()
        
        # Add force option if it's not already there
        if "force" not in new_params:
            new_params["force"] = True
        
        return new_params
    
    def _correct_select_params(self, params):
        """Correct parameters for select_option operation."""
        new_params = params.copy()
        
        # Convert values to strings if they're not
        if "values" in new_params and isinstance(new_params["values"], list):
            new_params["values"] = [str(val) if not isinstance(val, str) else val for val in new_params["values"]]
        
        return new_params
    
    def _correct_goto_params(self, params):
        """Correct parameters for goto operation."""
        new_params = params.copy()
        
        # Ensure URL is properly formatted
        if "url" in new_params and not new_params["url"].startswith(("http://", "https://")):
            new_params["url"] = "https://" + new_params["url"]
        
        return new_params

def generate_alternate_selectors(selector):
    """Generate alternate selectors when the primary selector fails."""
    alternates = []
    
    # ID-based selector
    if selector.startswith("#"):
        # Try with a tag
        alternates.append(f"*{selector}")
        
        # Try by name
        name = selector[1:]
        alternates.append(f"[name='{name}']")
        
        # Try approximate match
        alternates.append(f"[id*='{name}']")
    
    # Class-based selector
    elif selector.startswith("."):
        # Try with a tag
        alternates.append(f"*{selector}")
        
        # Try approximate match
        class_name = selector[1:]
        alternates.append(f"[class*='{class_name}']")
    
    # Attribute selector
    elif selector.startswith("[") and "]" in selector:
        # Extract attribute name and value
        attr_part = selector.split("]")[0][1:]
        if "=" in attr_part:
            attr_name, attr_value = attr_part.split("=", 1)
            attr_value = attr_value.strip("'\"")
            
            # Try contains instead of equals
            alternates.append(f"[{attr_name}*={attr_value}]")
            
            # Try case-insensitive
            alternates.append(f"[{attr_name}*={attr_value} i]")
            
            # Try with tag
            alternates.append(f"*[{attr_name}*={attr_value}]")
    
    # Tag selector
    elif not selector.startswith((".", "#", "[")):
        # Try by role
        alternates.append(f"[role='{selector}']")
        
        # Try by content
        alternates.append(f"text={selector}")
        
        # Try by containing text
        alternates.append(f"text='{selector}'")
        
        # Try by approximate text
        alternates.append(f"text='{selector}' i")
    
    # Try removing :nth-child pseudo-selectors
    if ":nth-child" in selector:
        base_selector = selector.split(":nth-child")[0]
        alternates.append(base_selector)
    
    # Try XPath equivalent for simple selectors
    if selector.startswith(("#", ".")):
        if selector.startswith("#"):
            xpath = f"//[id='{selector[1:]}']"
        else:
            xpath = f"//[contains(@class, '{selector[1:]}')]"
        alternates.append(xpath)
    
    return alternates


def register_error_handling_tool(mcp, browser_manager):
    """Register error handling tools with the MCP server."""
    # Create error handler instance
    error_handler = WebErrorHandler(
        error_log_dir=os.path.join(os.path.expanduser("~"), ".claude_web_interaction", "error_logs")
    )
    
    @mcp.tool()
    async def diagnostics_report() -> Dict[str, Any]:
        """
        Generate a diagnostic report for web interaction.
        
        Returns:
            Dict with diagnostic information
        """
        try:
            # Safely gather browser information with error handling for each property
            browser_info = {
                "initialized": getattr(browser_manager, 'initialized', False)
            }
            
            # Safely add active_pages_count with fallback
            try:
                browser_info["active_pages_count"] = len(browser_manager.active_pages) if hasattr(browser_manager, 'active_pages') else 0
            except Exception as e:
                logger.warning(f"Error getting active_pages_count: {str(e)}")
                browser_info["active_pages_count"] = 0
                
            # Safely add total_pages_count with fallback
            try:
                if hasattr(browser_manager, 'page_metadata') and browser_manager.page_metadata is not None:
                    browser_info["total_pages_count"] = len(browser_manager.page_metadata)
                else:
                    browser_info["total_pages_count"] = 0
            except Exception as e:
                logger.warning(f"Error getting total_pages_count: {str(e)}")
                browser_info["total_pages_count"] = 0
            
            # Get browser contexts if available
            if hasattr(browser_manager, 'contexts'):
                try:
                    browser_info["contexts_count"] = len(browser_manager.contexts)
                except Exception as e:
                    logger.warning(f"Error getting contexts_count: {str(e)}")
                    browser_info["contexts_count"] = 0
            
            # Get browser types if available
            if hasattr(browser_manager, 'browsers'):
                try:
                    browser_info["browser_types"] = list(browser_manager.browsers.keys())
                except Exception as e:
                    logger.warning(f"Error getting browser_types: {str(e)}")
                    browser_info["browser_types"] = []
            
            # Include storage directories in the report
            try:
                if hasattr(browser_manager, 'storage_dir'):
                    browser_info["storage_dir"] = str(browser_manager.storage_dir)
                if hasattr(browser_manager, 'screenshot_dir'):
                    browser_info["screenshot_dir"] = str(browser_manager.screenshot_dir)
            except Exception as storage_error:
                logger.warning(f"Error getting storage directories: {str(storage_error)}")
                
            # Get active page details
            try:
                active_pages = {}
                if hasattr(browser_manager, 'active_pages'):
                    for page_id, page in browser_manager.active_pages.items():
                        try:
                            active_pages[page_id] = {
                                "url": page.url if hasattr(page, 'url') else "unknown",
                                "title": "unknown"  # We'll get title asynchronously later
                            }
                        except Exception as page_error:
                            logger.warning(f"Error getting details for page {page_id}: {str(page_error)}")
                            active_pages[page_id] = {"error": str(page_error)}
                    
                    browser_info["active_pages"] = active_pages
            except Exception as pages_error:
                logger.warning(f"Error getting active page details: {str(pages_error)}")
                browser_info["active_pages"] = {}
            
            # Get page metadata
            try:
                if hasattr(browser_manager, 'page_metadata') and browser_manager.page_metadata is not None:
                    # Convert to dict if it's another type
                    metadata_dict = dict(browser_manager.page_metadata)
                    # Convert any non-serializable values
                    sanitized_metadata = {}
                    for k, v in metadata_dict.items():
                        try:
                            # Ensure keys are strings
                            str_key = str(k)
                            if isinstance(v, dict):
                                sanitized_metadata[str_key] = v
                            else:
                                sanitized_metadata[str_key] = str(v)
                        except Exception:
                            # Skip any entry that can't be serialized
                            continue
                    
                    browser_info["page_metadata"] = sanitized_metadata
            except Exception as metadata_error:
                logger.warning(f"Error getting page metadata: {str(metadata_error)}")
                browser_info["page_metadata"] = {}
            
            # Get error statistics
            try:
                error_stats = error_handler.get_error_stats()
            except Exception as stats_error:
                logger.warning(f"Error getting error statistics: {str(stats_error)}")
                error_stats = {"error": str(stats_error)}
            
            # Get recommendations
            try:
                recommendations = error_handler.get_recommendations()
            except Exception as rec_error:
                logger.warning(f"Error getting recommendations: {str(rec_error)}")
                recommendations = ["Error retrieving recommendations: " + str(rec_error)]
            
            # Add system diagnostics
            try:
                import platform
                import psutil
                system_info = {
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "machine": platform.machine(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent
                }
            except ImportError:
                system_info = {"note": "psutil not available for system diagnostics"}
            except Exception as sys_error:
                system_info = {"error": str(sys_error)}
            
            # Create diagnostic report
            report = {
                "timestamp": datetime.now().isoformat(),
                "browser_info": browser_info,
                "error_stats": error_stats,
                "recommendations": recommendations,
                "system_info": system_info
            }
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Diagnostic report generated successfully"
                    }
                ],
                "success": True,
                "report": report
            }
        except Exception as e:
            logger.error(f"Error generating diagnostic report: {str(e)}")
            # Return a minimal diagnostic with the error
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error generating complete diagnostic report: {str(e)}. Returning partial report."
                    }
                ],
                "success": False,
                "error": str(e),
                "partial_report": {
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            }
    
    @mcp.tool()
    async def fix_common_issues() -> Dict[str, Any]:
        """
        Attempt to fix common browser issues.
        
        Returns:
            Dict with results of fix attempts
        """
        try:
            fix_results = {}
            
            # Fix: Clear browser cookies
            try:
                await browser_manager.clear_cookies()
                fix_results["clear_cookies"] = "success"
            except Exception as e:
                fix_results["clear_cookies"] = f"failed: {str(e)}"
            
            # Fix: Restart problematic pages
            problematic_pages = []
            for page_id, page in list(browser_manager.active_pages.items()):
                try:
                    url = page.url
                    if url == "about:blank" or not url.startswith(("http://", "https://")):
                        continue
                    
                    # Check if page has errors
                    has_errors = False
                    if hasattr(browser_manager, 'console_monitor'):
                        page_errors = await browser_manager.get_page_errors(page_id)
                        if page_errors and len(page_errors) > 0:
                            has_errors = True
                    
                    if has_errors:
                        problematic_pages.append(page_id)
                except:
                    problematic_pages.append(page_id)
            
            # Restart problematic pages
            for page_id in problematic_pages:
                try:
                    url = browser_manager.page_metadata.get(page_id, {}).get("last_url", "about:blank")
                    await browser_manager.close_page(page_id)
                    new_page, new_id = await browser_manager.get_page()
                    if url != "about:blank":
                        await new_page.goto(url)
                    fix_results[f"restart_page_{page_id}"] = f"success: recreated as {new_id}"
                except Exception as e:
                    fix_results[f"restart_page_{page_id}"] = f"failed: {str(e)}"
            
            # Fix: Reset error statistics
            error_handler.error_stats = {
                category: {
                    "count": 0,
                    "last_occurred": None,
                    "recent_errors": []
                }
                for category in vars(ErrorCategory).keys()
                if not category.startswith("__")
            }
            fix_results["reset_error_stats"] = "success"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Common issues fixing completed"
                    }
                ],
                "fix_results": fix_results
            }
        except Exception as e:
            logger.error(f"Error fixing common issues: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error fixing common issues: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    logger.info("Error handling tools registered")
    
    # Return the error handler for use in other modules
    return {
        "diagnostics_report": diagnostics_report,
        "fix_common_issues": fix_common_issues,
        "error_handler": error_handler
    }