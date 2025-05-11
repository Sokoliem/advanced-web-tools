"""Enhanced Console Integration for Web Interaction.

This module provides advanced console monitoring, logging, and interaction
capabilities for web debugging and automation.
"""

import asyncio
import json
import logging
import time
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class ConsoleMessage:
    """Represents a console message with enhanced metadata."""
    
    def __init__(self, page_id, message_type, text, location=None, args=None, timestamp=None):
        """Initialize the console message."""
        self.page_id = page_id
        self.type = message_type
        self.text = text
        self.location = location
        self.args = args or []
        self.timestamp = timestamp or datetime.now().isoformat()
        self.context = {}  # Additional context for the message
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "page_id": self.page_id,
            "type": self.type,
            "text": self.text,
            "location": self.location,
            "args": self.args,
            "timestamp": self.timestamp,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary after deserialization."""
        message = cls(
            data["page_id"], 
            data["type"], 
            data["text"], 
            data.get("location"),
            data.get("args", []),
            data.get("timestamp")
        )
        message.context = data.get("context", {})
        return message

class NetworkRequest:
    """Represents a network request with enhanced metadata."""
    
    def __init__(self, page_id, url, method, resource_type, headers=None, timestamp=None):
        """Initialize the network request."""
        self.page_id = page_id
        self.url = url
        self.method = method
        self.resource_type = resource_type
        self.headers = headers or {}
        self.timestamp = timestamp or datetime.now().isoformat()
        self.response = None  # Will be set when response is received
        self.error = None  # Will be set if request fails
        self.duration = None  # Will be set when response is received
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "page_id": self.page_id,
            "url": self.url,
            "method": self.method,
            "resource_type": self.resource_type,
            "headers": self.headers,
            "timestamp": self.timestamp,
            "response": self.response,
            "error": self.error,
            "duration": self.duration
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary after deserialization."""
        request = cls(
            data["page_id"],
            data["url"],
            data["method"],
            data["resource_type"],
            data.get("headers", {}),
            data.get("timestamp")
        )
        request.response = data.get("response")
        request.error = data.get("error")
        request.duration = data.get("duration")
        return request

class ConsoleFilter:
    """Filter for console messages."""
    
    def __init__(self, types=None, patterns=None, exclude_patterns=None, limit=None, page_id=None):
        """Initialize the console filter."""
        self.types = types  # List of message types to include
        self.patterns = patterns  # List of regex patterns to match
        self.exclude_patterns = exclude_patterns  # List of regex patterns to exclude
        self.limit = limit  # Maximum number of messages to return
        self.page_id = page_id  # Filter by page ID
    
    def matches(self, message):
        """Check if a message matches the filter."""
        # Filter by page ID
        if self.page_id and message.page_id != self.page_id:
            return False
        
        # Filter by message type
        if self.types and message.type.lower() not in [t.lower() for t in self.types]:
            return False
        
        # Filter by patterns
        if self.patterns:
            match_found = False
            for pattern in self.patterns:
                if re.search(pattern, message.text, re.IGNORECASE):
                    match_found = True
                    break
            if not match_found:
                return False
        
        # Filter by exclude patterns
        if self.exclude_patterns:
            for pattern in self.exclude_patterns:
                if re.search(pattern, message.text, re.IGNORECASE):
                    return False
        
        return True

class EnhancedConsoleMonitor:
    """Enhanced console monitoring with advanced filtering and analysis."""
    
    def __init__(self, browser_manager, storage_dir=None):
        """Initialize the enhanced console monitor."""
        self.browser_manager = browser_manager
        
        # Set storage directory
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".claude_web_interaction")
        
        # Set up console directories
        self.console_dir = Path(self.storage_dir) / 'console_logs'
        self.console_dir.mkdir(exist_ok=True)
        
        self.network_dir = Path(self.storage_dir) / 'network_logs'
        self.network_dir.mkdir(exist_ok=True)
        
        # Storage for console logs, errors, and network requests
        self.console_logs = {}  # page_id -> List[ConsoleMessage]
        self.page_errors = {}  # page_id -> List[ConsoleMessage]
        self.network_requests = {}  # page_id -> List[NetworkRequest]
        
        # Request/response mapping
        self.request_map = {}  # request_id -> NetworkRequest
        
        # Configuration
        self.capture_console = True
        self.capture_network = True
        self.max_logs_per_page = 1000  # Prevent unbounded memory growth
        
        # Load existing logs
        self._load_console_logs()
    
    def _load_console_logs(self):
        """Load console logs from storage if available."""
        try:
            # Look for console log files
            for log_file in self.console_dir.glob('console_*.jsonl'):
                try:
                    # Extract page ID from filename
                    filename = log_file.name
                    page_id = filename.replace('console_', '').replace('.jsonl', '')
                    
                    # Initialize log container
                    if page_id not in self.console_logs:
                        self.console_logs[page_id] = []
                    
                    # Read log entries
                    with open(log_file, 'r') as f:
                        for line in f:
                            if line.strip():
                                entry = json.loads(line)
                                message = ConsoleMessage.from_dict(entry)
                                self.console_logs[page_id].append(message)
                except Exception as e:
                    logger.error(f"Error loading console log file {log_file}: {str(e)}")
            
            # Look for error log files
            for error_file in self.console_dir.glob('errors_*.jsonl'):
                try:
                    # Extract page ID from filename
                    filename = error_file.name
                    page_id = filename.replace('errors_', '').replace('.jsonl', '')
                    
                    # Initialize error container
                    if page_id not in self.page_errors:
                        self.page_errors[page_id] = []
                    
                    # Read error entries
                    with open(error_file, 'r') as f:
                        for line in f:
                            if line.strip():
                                entry = json.loads(line)
                                message = ConsoleMessage.from_dict(entry)
                                self.page_errors[page_id].append(message)
                except Exception as e:
                    logger.error(f"Error loading error log file {error_file}: {str(e)}")
            
            # Look for network log files
            for network_file in self.network_dir.glob('network_*.jsonl'):
                try:
                    # Extract page ID from filename
                    filename = network_file.name
                    page_id = filename.replace('network_', '').replace('.jsonl', '')
                    
                    # Initialize network container
                    if page_id not in self.network_requests:
                        self.network_requests[page_id] = []
                    
                    # Read network entries
                    with open(network_file, 'r') as f:
                        for line in f:
                            if line.strip():
                                entry = json.loads(line)
                                request = NetworkRequest.from_dict(entry)
                                self.network_requests[page_id].append(request)
                except Exception as e:
                    logger.error(f"Error loading network log file {network_file}: {str(e)}")
            
            logger.info(f"Loaded console logs for {len(self.console_logs)} pages")
        except Exception as e:
            logger.error(f"Error loading console logs: {str(e)}")
    
    def _save_console_log(self, message):
        """Save console log to file."""
        try:
            # Create log file for this page
            log_file = self.console_dir / f"console_{message.page_id}.jsonl"
            
            # Append the log entry
            with open(log_file, 'a') as f:
                f.write(json.dumps(message.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Error saving console log: {str(e)}")
    
    def _save_page_error(self, error):
        """Save page error to file."""
        try:
            # Create error file for this page
            error_file = self.console_dir / f"errors_{error.page_id}.jsonl"
            
            # Append the error entry
            with open(error_file, 'a') as f:
                f.write(json.dumps(error.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Error saving page error: {str(e)}")
    
    def _save_network_request(self, request):
        """Save network request to file."""
        try:
            # Create network file for this page
            network_file = self.network_dir / f"network_{request.page_id}.jsonl"
            
            # Append the network entry
            with open(network_file, 'a') as f:
                f.write(json.dumps(request.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Error saving network request: {str(e)}")
    
    async def setup_page_monitoring(self, page, page_id):
        """Set up console monitoring for a page."""
        if not self.capture_console:
            return
        
        # Initialize containers for this page
        if page_id not in self.console_logs:
            self.console_logs[page_id] = []
        
        if page_id not in self.page_errors:
            self.page_errors[page_id] = []
        
        if page_id not in self.network_requests:
            self.network_requests[page_id] = []
        
        # Console log listener
        async def console_handler(msg):
            # Create console message
            log_entry = ConsoleMessage(
                page_id=page_id,
                message_type=msg.type,
                text=msg.text,
                location=str(msg.location) if hasattr(msg, 'location') else None,
                args=[str(arg) for arg in msg.args] if hasattr(msg, 'args') else []
            )
            
            # Add context about current page state
            try:
                log_entry.context["url"] = page.url
                log_entry.context["title"] = await page.title()
            except:
                pass
            
            # Add to memory storage (with limit)
            if len(self.console_logs[page_id]) >= self.max_logs_per_page:
                self.console_logs[page_id].pop(0)  # Remove oldest entry
            
            self.console_logs[page_id].append(log_entry)
            
            # Log to console
            log_level = getattr(logging, msg.type.upper(), logging.INFO)
            logger.log(log_level, f"[Console:{page_id}] {msg.type}: {msg.text}")
            
            # Save to file
            self._save_console_log(log_entry)
            
            # Check for special patterns in console logs
            await self._analyze_console_message(page, log_entry)
        
        # Page error listener
        async def error_handler(error):
            # Create error message
            error_entry = ConsoleMessage(
                page_id=page_id,
                message_type="error",
                text=str(error),
                location="page",
                args=[getattr(error, 'stack', 'No stack trace')]
            )
            
            # Add context about current page state
            try:
                error_entry.context["url"] = page.url
                error_entry.context["title"] = await page.title()
            except:
                pass
            
            # Add to memory storage (with limit)
            if len(self.page_errors[page_id]) >= self.max_logs_per_page:
                self.page_errors[page_id].pop(0)  # Remove oldest entry
            
            self.page_errors[page_id].append(error_entry)
            
            # Log to console
            logger.error(f"[PageError:{page_id}] {error}")
            
            # Save to file
            self._save_page_error(error_entry)
        
        # Network request listener
        async def request_handler(request):
            if not self.capture_network:
                return
            
            # Create network request
            request_entry = NetworkRequest(
                page_id=page_id,
                url=request.url,
                method=request.method,
                resource_type=request.resource_type,
                headers=dict(request.headers) if hasattr(request, 'headers') else {}
            )
            
            # Store in request map for later correlation with response
            if hasattr(request, 'id'):
                self.request_map[request.id] = request_entry
            
            # Add to memory storage (with limit)
            if len(self.network_requests[page_id]) >= self.max_logs_per_page:
                self.network_requests[page_id].pop(0)  # Remove oldest entry
            
            self.network_requests[page_id].append(request_entry)
            
            # Log certain request types to avoid noise
            if request.resource_type in ['document', 'xhr', 'fetch']:
                logger.info(f"[Network:{page_id}] {request.method} {request.url}")
            
            # Save to file
            self._save_network_request(request_entry)
        
        # Network response listener
        async def response_handler(response):
            if not self.capture_network:
                return
            
            # Find the corresponding request
            request_id = response.request.id if hasattr(response.request, 'id') else None
            if request_id and request_id in self.request_map:
                request_entry = self.request_map[request_id]
                
                # Update request with response info
                try:
                    status = response.status
                    status_text = response.status_text if hasattr(response, 'status_text') else ""
                    headers = dict(response.headers) if hasattr(response, 'headers') else {}
                    
                    request_entry.response = {
                        "status": status,
                        "status_text": status_text,
                        "headers": headers
                    }
                    
                    # Calculate duration if possible
                    request_time = datetime.fromisoformat(request_entry.timestamp)
                    current_time = datetime.now()
                    duration_ms = (current_time - request_time).total_seconds() * 1000
                    request_entry.duration = duration_ms
                    
                    # Save updated request
                    self._save_network_request(request_entry)
                    
                    # Log important responses
                    if status >= 400:
                        logger.warning(f"[Network:{page_id}] {response.request.method} {response.url} - Status: {status}")
                except Exception as e:
                    logger.error(f"Error processing response: {str(e)}")
        
        # Set up listeners
        page.on("console", console_handler)
        page.on("pageerror", error_handler)
        
        if self.capture_network:
            page.on("request", request_handler)
            page.on("response", response_handler)
    
    async def _analyze_console_message(self, page, message):
        """Analyze console messages for patterns of interest."""
        # Check for CORS errors
        cors_patterns = [
            "Access to fetch.* has been blocked by CORS policy",
            "Origin .* is not allowed by Access-Control-Allow-Origin"
        ]
        
        for pattern in cors_patterns:
            if re.search(pattern, message.text, re.IGNORECASE):
                logger.warning(f"CORS error detected on page {message.page_id}: {message.text}")
                # Add CORS context to the message
                message.context["issue_type"] = "CORS"
                self._save_console_log(message)
                break
        
        # Check for memory leak warnings
        memory_patterns = [
            "memory leak",
            "increasing memory usage",
            "possible memory leak"
        ]
        
        for pattern in memory_patterns:
            if re.search(pattern, message.text, re.IGNORECASE):
                logger.warning(f"Memory issue detected on page {message.page_id}: {message.text}")
                # Add memory issue context to the message
                message.context["issue_type"] = "Memory"
                self._save_console_log(message)
                break
    
    async def get_console_logs(self, page_id=None, filter_options=None):
        """
        Get console logs for a page or all pages with advanced filtering.
        
        Args:
            page_id: Optional ID of a page to get logs from
            filter_options: Optional dictionary with filtering options:
                {
                    "types": List of message types to include,
                    "patterns": List of regex patterns to match,
                    "exclude_patterns": List of regex patterns to exclude,
                    "limit": Maximum number of messages to return,
                    "since": Timestamp to filter messages from
                }
        
        Returns:
            Dict with console logs
        """
        # Apply filter if provided
        console_filter = None
        if filter_options:
            console_filter = ConsoleFilter(
                types=filter_options.get("types"),
                patterns=filter_options.get("patterns"),
                exclude_patterns=filter_options.get("exclude_patterns"),
                limit=filter_options.get("limit"),
                page_id=page_id
            )
        
        # Get logs for specific page
        if page_id:
            if page_id in self.console_logs:
                logs = self.console_logs[page_id]
                
                # Apply filter if provided
                if console_filter:
                    logs = [log for log in logs if console_filter.matches(log)]
                    # Apply limit if provided
                    if console_filter.limit:
                        logs = logs[-console_filter.limit:]
                
                # Apply since filter if provided
                if filter_options and "since" in filter_options:
                    since_time = filter_options["since"]
                    logs = [log for log in logs if log.timestamp >= since_time]
                
                # Convert to dict for serialization
                return [log.to_dict() for log in logs]
            return []
        
        # Get logs for all pages
        all_logs = []
        for p_id, logs in self.console_logs.items():
            for log in logs:
                # Apply filter if provided
                if console_filter and not console_filter.matches(log):
                    continue
                
                # Apply since filter if provided
                if filter_options and "since" in filter_options:
                    since_time = filter_options["since"]
                    if log.timestamp < since_time:
                        continue
                
                all_logs.append(log.to_dict())
        
        # Apply limit if provided
        if filter_options and "limit" in filter_options:
            limit = filter_options["limit"]
            all_logs = all_logs[-limit:]
        
        return all_logs
    
    async def get_page_errors(self, page_id=None, filter_options=None):
        """
        Get page errors for a page or all pages with advanced filtering.
        
        Args:
            page_id: Optional ID of a page to get errors from
            filter_options: Optional dictionary with filtering options:
                {
                    "patterns": List of regex patterns to match,
                    "exclude_patterns": List of regex patterns to exclude,
                    "limit": Maximum number of errors to return,
                    "since": Timestamp to filter errors from
                }
        
        Returns:
            Dict with page errors
        """
        # Apply filter if provided
        error_filter = None
        if filter_options:
            error_filter = ConsoleFilter(
                types=["error"],
                patterns=filter_options.get("patterns"),
                exclude_patterns=filter_options.get("exclude_patterns"),
                limit=filter_options.get("limit"),
                page_id=page_id
            )
        
        # Get errors for specific page
        if page_id:
            if page_id in self.page_errors:
                errors = self.page_errors[page_id]
                
                # Apply filter if provided
                if error_filter:
                    errors = [error for error in errors if error_filter.matches(error)]
                    # Apply limit if provided
                    if error_filter.limit:
                        errors = errors[-error_filter.limit:]
                
                # Apply since filter if provided
                if filter_options and "since" in filter_options:
                    since_time = filter_options["since"]
                    errors = [error for error in errors if error.timestamp >= since_time]
                
                # Convert to dict for serialization
                return [error.to_dict() for error in errors]
            return []
        
        # Get errors for all pages
        all_errors = []
        for p_id, errors in self.page_errors.items():
            for error in errors:
                # Apply filter if provided
                if error_filter and not error_filter.matches(error):
                    continue
                
                # Apply since filter if provided
                if filter_options and "since" in filter_options:
                    since_time = filter_options["since"]
                    if error.timestamp < since_time:
                        continue
                
                all_errors.append(error.to_dict())
        
        # Apply limit if provided
        if filter_options and "limit" in filter_options:
            limit = filter_options["limit"]
            all_errors = all_errors[-limit:]
        
        return all_errors
    
    async def get_network_requests(self, page_id=None, filter_options=None):
        """
        Get network requests for a page or all pages with advanced filtering.
        
        Args:
            page_id: Optional ID of a page to get requests from
            filter_options: Optional dictionary with filtering options:
                {
                    "url_patterns": List of regex patterns to match URLs,
                    "methods": List of HTTP methods to include,
                    "resource_types": List of resource types to include,
                    "status_codes": List of status codes to include,
                    "limit": Maximum number of requests to return,
                    "since": Timestamp to filter requests from
                }
        
        Returns:
            Dict with network requests
        """
        if not self.capture_network:
            return []
        
        # Get requests for specific page
        if page_id:
            if page_id in self.network_requests:
                requests = self.network_requests[page_id]
                
                # Apply filters if provided
                if filter_options:
                    # Filter by URL patterns
                    if "url_patterns" in filter_options:
                        url_patterns = filter_options["url_patterns"]
                        filtered_requests = []
                        for req in requests:
                            for pattern in url_patterns:
                                if re.search(pattern, req.url, re.IGNORECASE):
                                    filtered_requests.append(req)
                                    break
                        requests = filtered_requests
                    
                    # Filter by HTTP methods
                    if "methods" in filter_options:
                        methods = [m.upper() for m in filter_options["methods"]]
                        requests = [req for req in requests if req.method.upper() in methods]
                    
                    # Filter by resource types
                    if "resource_types" in filter_options:
                        resource_types = filter_options["resource_types"]
                        requests = [req for req in requests if req.resource_type in resource_types]
                    
                    # Filter by status codes
                    if "status_codes" in filter_options:
                        status_codes = filter_options["status_codes"]
                        requests = [
                            req for req in requests 
                            if req.response and req.response.get("status") in status_codes
                        ]
                    
                    # Filter by timestamp
                    if "since" in filter_options:
                        since_time = filter_options["since"]
                        requests = [req for req in requests if req.timestamp >= since_time]
                    
                    # Apply limit
                    if "limit" in filter_options:
                        limit = filter_options["limit"]
                        requests = requests[-limit:]
                
                # Convert to dict for serialization
                return [req.to_dict() for req in requests]
            return []
        
        # Get requests for all pages
        all_requests = []
        for p_id, requests in self.network_requests.items():
            # Apply filters if provided
            filtered_requests = requests
            if filter_options:
                # Filter by URL patterns
                if "url_patterns" in filter_options:
                    url_patterns = filter_options["url_patterns"]
                    filtered_requests = []
                    for req in requests:
                        for pattern in url_patterns:
                            if re.search(pattern, req.url, re.IGNORECASE):
                                filtered_requests.append(req)
                                break
                
                # Filter by HTTP methods
                if "methods" in filter_options:
                    methods = [m.upper() for m in filter_options["methods"]]
                    filtered_requests = [req for req in filtered_requests if req.method.upper() in methods]
                
                # Filter by resource types
                if "resource_types" in filter_options:
                    resource_types = filter_options["resource_types"]
                    filtered_requests = [req for req in filtered_requests if req.resource_type in resource_types]
                
                # Filter by status codes
                if "status_codes" in filter_options:
                    status_codes = filter_options["status_codes"]
                    filtered_requests = [
                        req for req in filtered_requests 
                        if req.response and req.response.get("status") in status_codes
                    ]
                
                # Filter by timestamp
                if "since" in filter_options:
                    since_time = filter_options["since"]
                    filtered_requests = [req for req in filtered_requests if req.timestamp >= since_time]
            
            # Add to result
            all_requests.extend([req.to_dict() for req in filtered_requests])
        
        # Apply limit if provided
        if filter_options and "limit" in filter_options:
            limit = filter_options["limit"]
            all_requests = all_requests[-limit:]
        
        return all_requests
    
    async def execute_console_command(self, page, command, include_result=True):
        """
        Execute a JavaScript command in the console of a page.
        
        Args:
            page: The page to execute the command on
            command: JavaScript code to execute
            include_result: Whether to include the result in the response
            
        Returns:
            Dict with execution result or error
        """
        try:
            # Execute the command
            result = await page.evaluate(command)
            
            # Get page ID
            page_id = next((k for k, v in self.browser_manager.active_pages.items() if v == page), "unknown")
            
            # Log the command
            log_entry = ConsoleMessage(
                page_id=page_id,
                message_type="command",
                text=command[:100] + ("..." if len(command) > 100 else ""),
                location="console API"
            )
            
            # Add result to context
            if include_result:
                if isinstance(result, (dict, list)):
                    log_entry.context["result"] = json.dumps(result, indent=2)
                else:
                    log_entry.context["result"] = str(result)
            
            # Add to console logs
            if page_id not in self.console_logs:
                self.console_logs[page_id] = []
            
            # Add to memory storage (with limit)
            if len(self.console_logs[page_id]) >= self.max_logs_per_page:
                self.console_logs[page_id].pop(0)  # Remove oldest entry
            
            self.console_logs[page_id].append(log_entry)
            
            # Save to file
            self._save_console_log(log_entry)
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            # Get page ID
            page_id = next((k for k, v in self.browser_manager.active_pages.items() if v == page), "unknown")
            
            # Log the error
            error_entry = ConsoleMessage(
                page_id=page_id,
                message_type="error",
                text=f"Error executing command: {str(e)}",
                location="console API",
                args=[command]
            )
            
            # Add to page errors
            if page_id not in self.page_errors:
                self.page_errors[page_id] = []
            
            # Add to memory storage (with limit)
            if len(self.page_errors[page_id]) >= self.max_logs_per_page:
                self.page_errors[page_id].pop(0)  # Remove oldest entry
            
            self.page_errors[page_id].append(error_entry)
            
            # Save to file
            self._save_page_error(error_entry)
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def inject_console_logger(self, page, log_level="info"):
        """
        Inject a console logger into the page to capture all console activity.
        
        Args:
            page: The page to inject the logger into
            log_level: Minimum log level to capture ("debug", "info", "warn", "error")
            
        Returns:
            Success flag
        """
        try:
            # JavaScript to inject logger
            logger_script = """
            (logLevel) => {
                // Don't inject twice
                if (window.__enhanced_logger_injected) return true;
                
                // Map log levels to numeric values
                const LOG_LEVELS = {
                    'debug': 0,
                    'info': 1,
                    'warn': 2,
                    'error': 3
                };
                
                const MIN_LEVEL = LOG_LEVELS[logLevel] || 1;
                
                // Store original console methods
                const originalConsole = {
                    log: console.log,
                    debug: console.debug,
                    info: console.info,
                    warn: console.warn,
                    error: console.error
                };
                
                // Override console methods
                console.log = function() {
                    if (MIN_LEVEL <= LOG_LEVELS.info) {
                        // Call original method
                        originalConsole.log.apply(console, arguments);
                        
                        // Log additional info
                        const stack = new Error().stack.split('\\n')[2];
                        console.__log_info('log', Array.from(arguments), stack);
                    }
                };
                
                console.debug = function() {
                    if (MIN_LEVEL <= LOG_LEVELS.debug) {
                        // Call original method
                        originalConsole.debug.apply(console, arguments);
                        
                        // Log additional info
                        const stack = new Error().stack.split('\\n')[2];
                        console.__log_info('debug', Array.from(arguments), stack);
                    }
                };
                
                console.info = function() {
                    if (MIN_LEVEL <= LOG_LEVELS.info) {
                        // Call original method
                        originalConsole.info.apply(console, arguments);
                        
                        // Log additional info
                        const stack = new Error().stack.split('\\n')[2];
                        console.__log_info('info', Array.from(arguments), stack);
                    }
                };
                
                console.warn = function() {
                    if (MIN_LEVEL <= LOG_LEVELS.warn) {
                        // Call original method
                        originalConsole.warn.apply(console, arguments);
                        
                        // Log additional info
                        const stack = new Error().stack.split('\\n')[2];
                        console.__log_info('warn', Array.from(arguments), stack);
                    }
                };
                
                console.error = function() {
                    if (MIN_LEVEL <= LOG_LEVELS.error) {
                        // Call original method
                        originalConsole.error.apply(console, arguments);
                        
                        // Log additional info
                        const stack = new Error().stack.split('\\n')[2];
                        console.__log_info('error', Array.from(arguments), stack);
                    }
                };
                
                // Custom handler to capture log info that we'll expose for the test automation
                console.__log_info = function(type, args, stack) {
                    // Store in global array for retrieval
                    if (!window.__console_logs) {
                        window.__console_logs = [];
                    }
                    
                    window.__console_logs.push({
                        type: type,
                        args: args,
                        stack: stack,
                        timestamp: new Date().toISOString()
                    });
                    
                    // Keep a reasonable limit
                    if (window.__console_logs.length > 1000) {
                        window.__console_logs.shift();
                    }
                };
                
                // Mark as injected
                window.__enhanced_logger_injected = true;
                
                return true;
            }
            """
            
            # Inject the logger
            result = await page.evaluate(logger_script, log_level)
            
            if result:
                logger.info("Enhanced console logger injected successfully")
                return True
            else:
                logger.warning("Failed to inject enhanced console logger")
                return False
        except Exception as e:
            logger.error(f"Error injecting console logger: {str(e)}")
            return False
    
    async def retrieve_injected_logs(self, page):
        """
        Retrieve logs captured by the injected console logger.
        
        Args:
            page: The page to retrieve logs from
            
        Returns:
            List of captured logs
        """
        try:
            # Check if logger is injected
            is_injected = await page.evaluate("() => window.__enhanced_logger_injected === true")
            
            if not is_injected:
                logger.warning("Enhanced console logger not injected, injecting now")
                await self.inject_console_logger(page)
            
            # Retrieve logs
            logs = await page.evaluate("() => window.__console_logs || []")
            
            # Get page ID
            page_id = next((k for k, v in self.browser_manager.active_pages.items() if v == page), "unknown")
            
            # Process logs
            for log in logs:
                # Create console message
                log_entry = ConsoleMessage(
                    page_id=page_id,
                    message_type=log.get("type", "log"),
                    text=", ".join([str(arg) for arg in log.get("args", [])]),
                    location=log.get("stack"),
                    timestamp=log.get("timestamp") or datetime.now().isoformat()
                )
                
                # Add to console logs
                if page_id not in self.console_logs:
                    self.console_logs[page_id] = []
                
                # Add to memory storage (with limit)
                if len(self.console_logs[page_id]) >= self.max_logs_per_page:
                    self.console_logs[page_id].pop(0)  # Remove oldest entry
                
                self.console_logs[page_id].append(log_entry)
                
                # Save to file
                self._save_console_log(log_entry)
            
            # Clear logs in the page to avoid duplicates
            await page.evaluate("() => window.__console_logs = []")
            
            return logs
        except Exception as e:
            logger.error(f"Error retrieving injected logs: {str(e)}")
            return []
    
    async def monitor_network_performance(self, page):
        """
        Monitor network performance metrics for a page.
        
        Args:
            page: The page to monitor
            
        Returns:
            Dict with performance metrics
        """
        try:
            # Get performance timing metrics from the page
            timing_script = """
            () => {
                const timing = performance.timing || {};
                const navigation = performance.navigation || {};
                
                // Calculate timing metrics
                const metrics = {};
                
                if (timing.navigationStart) {
                    // Navigation timing
                    metrics.navigationStart = timing.navigationStart;
                    metrics.redirectTime = timing.redirectEnd - timing.redirectStart;
                    metrics.dnsTime = timing.domainLookupEnd - timing.domainLookupStart;
                    metrics.connectTime = timing.connectEnd - timing.connectStart;
                    metrics.requestTime = timing.responseStart - timing.requestStart;
                    metrics.responseTime = timing.responseEnd - timing.responseStart;
                    metrics.domProcessingTime = timing.domComplete - timing.domLoading;
                    metrics.domContentLoadedTime = timing.domContentLoadedEventEnd - timing.navigationStart;
                    metrics.loadTime = timing.loadEventEnd - timing.navigationStart;
                }
                
                // Navigation type
                if (navigation.type !== undefined) {
                    metrics.navigationType = ['navigate', 'reload', 'back_forward', 'reserved'][navigation.type] || 'unknown';
                }
                
                // Get resource timing
                const resources = performance.getEntriesByType('resource') || [];
                metrics.resources = resources.map(res => ({
                    name: res.name,
                    entryType: res.entryType,
                    startTime: res.startTime,
                    duration: res.duration,
                    initiatorType: res.initiatorType,
                    transferSize: res.transferSize,
                    decodedBodySize: res.decodedBodySize
                }));
                
                // Get first contentful paint if available
                const paintMetrics = performance.getEntriesByType('paint') || [];
                for (const paint of paintMetrics) {
                    if (paint.name === 'first-contentful-paint') {
                        metrics.firstContentfulPaint = paint.startTime;
                    }
                }
                
                return metrics;
            }
            """
            
            # Get performance metrics
            performance_metrics = await page.evaluate(timing_script)
            
            # Get page ID
            page_id = next((k for k, v in self.browser_manager.active_pages.items() if v == page), "unknown")
            
            # Add timestamp
            performance_metrics["timestamp"] = datetime.now().isoformat()
            performance_metrics["page_id"] = page_id
            performance_metrics["url"] = page.url
            
            return performance_metrics
        except Exception as e:
            logger.error(f"Error monitoring network performance: {str(e)}")
            return {}
    
    async def get_console_stats(self, page_id=None):
        """
        Get statistics about console activity.
        
        Args:
            page_id: Optional ID of a page to get stats for
            
        Returns:
            Dict with console statistics
        """
        # Stats for a specific page
        if page_id:
            if page_id in self.console_logs:
                logs = self.console_logs[page_id]
                
                # Count by log type
                type_counts = {}
                for log in logs:
                    log_type = log.type
                    if log_type not in type_counts:
                        type_counts[log_type] = 0
                    type_counts[log_type] += 1
                
                # Get latest logs
                latest_logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:10]
                
                return {
                    "page_id": page_id,
                    "total_logs": len(logs),
                    "by_type": type_counts,
                    "latest_logs": [log.to_dict() for log in latest_logs]
                }
            return {
                "page_id": page_id,
                "total_logs": 0,
                "by_type": {},
                "latest_logs": []
            }
        
        # Stats for all pages
        all_stats = {
            "total_logs": 0,
            "total_errors": 0,
            "by_page": {},
            "by_type": {}
        }
        
        # Collect stats from console logs
        for p_id, logs in self.console_logs.items():
            # Count logs for this page
            if p_id not in all_stats["by_page"]:
                all_stats["by_page"][p_id] = {
                    "total_logs": 0,
                    "by_type": {}
                }
            
            # Count by log type
            for log in logs:
                log_type = log.type
                
                # Add to page stats
                all_stats["by_page"][p_id]["total_logs"] += 1
                if log_type not in all_stats["by_page"][p_id]["by_type"]:
                    all_stats["by_page"][p_id]["by_type"][log_type] = 0
                all_stats["by_page"][p_id]["by_type"][log_type] += 1
                
                # Add to overall stats
                all_stats["total_logs"] += 1
                if log_type not in all_stats["by_type"]:
                    all_stats["by_type"][log_type] = 0
                all_stats["by_type"][log_type] += 1
        
        # Collect stats from page errors
        for p_id, errors in self.page_errors.items():
            all_stats["total_errors"] += len(errors)
            
            # Add to page stats
            if p_id not in all_stats["by_page"]:
                all_stats["by_page"][p_id] = {
                    "total_logs": 0,
                    "by_type": {}
                }
            
            all_stats["by_page"][p_id]["total_errors"] = len(errors)
        
        return all_stats
    
    async def reset_console_logs(self, page_id=None):
        """
        Reset console logs for a page or all pages.
        
        Args:
            page_id: Optional ID of a page to reset logs for
            
        Returns:
            Success flag
        """
        try:
            if page_id:
                # Reset logs for specific page
                if page_id in self.console_logs:
                    self.console_logs[page_id] = []
                if page_id in self.page_errors:
                    self.page_errors[page_id] = []
                if page_id in self.network_requests:
                    self.network_requests[page_id] = []
                
                # Delete log files
                console_file = self.console_dir / f"console_{page_id}.jsonl"
                error_file = self.console_dir / f"errors_{page_id}.jsonl"
                network_file = self.network_dir / f"network_{page_id}.jsonl"
                
                if console_file.exists():
                    console_file.unlink()
                if error_file.exists():
                    error_file.unlink()
                if network_file.exists():
                    network_file.unlink()
                
                logger.info(f"Reset console logs for page {page_id}")
            else:
                # Reset logs for all pages
                self.console_logs = {}
                self.page_errors = {}
                self.network_requests = {}
                self.request_map = {}
                
                # Delete all log files
                for file in self.console_dir.glob("console_*.jsonl"):
                    file.unlink()
                for file in self.console_dir.glob("errors_*.jsonl"):
                    file.unlink()
                for file in self.network_dir.glob("network_*.jsonl"):
                    file.unlink()
                
                logger.info("Reset all console logs")
            
            return True
        except Exception as e:
            logger.error(f"Error resetting console logs: {str(e)}")
            return False

def register_enhanced_console_tools(mcp, browser_manager):
    """Register enhanced console tools with the MCP server."""
    # Create enhanced console monitor instance
    console_monitor = EnhancedConsoleMonitor(browser_manager)
    
    @mcp.tool()
    async def get_filtered_console_logs(page_id: Optional[str] = None, types: Optional[List[str]] = None, 
                                       patterns: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None,
                                       limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get console logs with advanced filtering options.
        
        Args:
            page_id: Optional ID of a page to get logs from
            types: Optional list of message types to include (e.g., ["log", "info", "warn", "error"])
            patterns: Optional list of regex patterns to match in log messages
            exclude_patterns: Optional list of regex patterns to exclude from log messages
            limit: Optional maximum number of logs to return
            
        Returns:
            Dict with filtered console logs
        """
        logger.info(f"Getting filtered console logs for {'page ' + page_id if page_id else 'all pages'}")
        try:
            # Prepare filter options
            filter_options = {
                "types": types,
                "patterns": patterns,
                "exclude_patterns": exclude_patterns,
                "limit": limit
            }
            
            # Filter out None values
            filter_options = {k: v for k, v in filter_options.items() if v is not None}
            
            # Get logs with filtering
            logs = await console_monitor.get_console_logs(page_id, filter_options)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Retrieved {len(logs)} console log entries"
                    }
                ],
                "success": True,
                "logs": logs,
                "count": len(logs)
            }
        except Exception as e:
            logger.error(f"Error getting filtered console logs: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting filtered console logs: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_filtered_page_errors(page_id: Optional[str] = None, patterns: Optional[List[str]] = None, 
                                     exclude_patterns: Optional[List[str]] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get page errors with advanced filtering options.
        
        Args:
            page_id: Optional ID of a page to get errors from
            patterns: Optional list of regex patterns to match in error messages
            exclude_patterns: Optional list of regex patterns to exclude from error messages
            limit: Optional maximum number of errors to return
            
        Returns:
            Dict with filtered page errors
        """
        logger.info(f"Getting filtered page errors for {'page ' + page_id if page_id else 'all pages'}")
        try:
            # Prepare filter options
            filter_options = {
                "patterns": patterns,
                "exclude_patterns": exclude_patterns,
                "limit": limit
            }
            
            # Filter out None values
            filter_options = {k: v for k, v in filter_options.items() if v is not None}
            
            # Get errors with filtering
            errors = await console_monitor.get_page_errors(page_id, filter_options)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Retrieved {len(errors)} page error entries"
                    }
                ],
                "success": True,
                "errors": errors,
                "count": len(errors)
            }
        except Exception as e:
            logger.error(f"Error getting filtered page errors: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting filtered page errors: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_filtered_network_requests(page_id: Optional[str] = None, url_patterns: Optional[List[str]] = None, 
                                         methods: Optional[List[str]] = None, resource_types: Optional[List[str]] = None,
                                         status_codes: Optional[List[int]] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get network requests with advanced filtering options.
        
        Args:
            page_id: Optional ID of a page to get requests from
            url_patterns: Optional list of regex patterns to match in request URLs
            methods: Optional list of HTTP methods to include (e.g., ["GET", "POST"])
            resource_types: Optional list of resource types to include (e.g., ["document", "xhr", "fetch"])
            status_codes: Optional list of status codes to include (e.g., [200, 404, 500])
            limit: Optional maximum number of requests to return
            
        Returns:
            Dict with filtered network requests
        """
        logger.info(f"Getting filtered network requests for {'page ' + page_id if page_id else 'all pages'}")
        try:
            # Prepare filter options
            filter_options = {
                "url_patterns": url_patterns,
                "methods": methods,
                "resource_types": resource_types,
                "status_codes": status_codes,
                "limit": limit
            }
            
            # Filter out None values
            filter_options = {k: v for k, v in filter_options.items() if v is not None}
            
            # Get requests with filtering
            requests = await console_monitor.get_network_requests(page_id, filter_options)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Retrieved {len(requests)} network request entries"
                    }
                ],
                "success": True,
                "requests": requests,
                "count": len(requests)
            }
        except Exception as e:
            logger.error(f"Error getting filtered network requests: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting filtered network requests: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def enhance_console_command(page_id: str, command: str, include_result: bool = True) -> Dict[str, Any]:
        """
        Execute a JavaScript command with enhanced logging and error handling.
        
        Args:
            page_id: ID of the page to execute the command on
            command: JavaScript code to execute
            include_result: Whether to include the result in the response
            
        Returns:
            Dict with command execution result or error
        """
        logger.info(f"Executing enhanced console command on page {page_id}")
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
            
            # Execute the command
            result = await console_monitor.execute_console_command(page, command, include_result)
            
            if result.get("success", False):
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Console command executed successfully"
                        }
                    ],
                    "success": True,
                    "result": result.get("result") if include_result else None
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing console command: {result.get('error')}"
                        }
                    ],
                    "success": False,
                    "error": result.get("error")
                }
        except Exception as e:
            logger.error(f"Error executing enhanced console command: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing enhanced console command: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def monitor_page_performance(page_id: str) -> Dict[str, Any]:
        """
        Monitor and retrieve performance metrics for a page.
        
        Args:
            page_id: ID of the page to monitor
            
        Returns:
            Dict with performance metrics
        """
        logger.info(f"Monitoring page performance for page {page_id}")
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
            
            # Monitor performance
            metrics = await console_monitor.monitor_network_performance(page)
            
            if metrics:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Page performance metrics retrieved successfully"
                        }
                    ],
                    "success": True,
                    "metrics": metrics
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"No performance metrics available"
                        }
                    ],
                    "success": False,
                    "error": "No performance metrics available"
                }
        except Exception as e:
            logger.error(f"Error monitoring page performance: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error monitoring page performance: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_console_activity_summary(page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of console activity with statistics.
        
        Args:
            page_id: Optional ID of a page to get summary for
            
        Returns:
            Dict with console activity summary
        """
        logger.info(f"Getting console activity summary for {'page ' + page_id if page_id else 'all pages'}")
        try:
            # Get console stats
            stats = await console_monitor.get_console_stats(page_id)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Console activity summary retrieved successfully"
                    }
                ],
                "success": True,
                "summary": stats
            }
        except Exception as e:
            logger.error(f"Error getting console activity summary: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting console activity summary: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def clear_console_data(page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear console logs, errors, and network requests for a page or all pages.
        
        Args:
            page_id: Optional ID of a page to clear data for
            
        Returns:
            Dict with clear operation result
        """
        logger.info(f"Clearing console data for {'page ' + page_id if page_id else 'all pages'}")
        try:
            # Reset console logs
            result = await console_monitor.reset_console_logs(page_id)
            
            if result:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Console data cleared successfully for {'page ' + page_id if page_id else 'all pages'}"
                        }
                    ],
                    "success": True
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to clear console data"
                        }
                    ],
                    "success": False,
                    "error": "Failed to clear console data"
                }
        except Exception as e:
            logger.error(f"Error clearing console data: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error clearing console data: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def inject_page_logger(page_id: str, log_level: str = "info") -> Dict[str, Any]:
        """
        Inject an enhanced console logger into the page to capture all console activity.
        
        Args:
            page_id: ID of the page to inject the logger into
            log_level: Minimum log level to capture ("debug", "info", "warn", "error")
            
        Returns:
            Dict with injection result
        """
        logger.info(f"Injecting page logger into page {page_id} with log level {log_level}")
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
            
            # Inject the logger
            result = await console_monitor.inject_console_logger(page, log_level)
            
            if result:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Console logger injected successfully with log level {log_level}"
                        }
                    ],
                    "success": True
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to inject console logger"
                        }
                    ],
                    "success": False,
                    "error": "Failed to inject console logger"
                }
        except Exception as e:
            logger.error(f"Error injecting console logger: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error injecting console logger: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    # Register the console monitor with the browser manager for page setup
    browser_manager.console_monitor = console_monitor
    
    logger.info("Enhanced console tools registered")
    
    # Return the console monitor instance and tools
    return {
        "console_monitor": console_monitor,
        "get_filtered_console_logs": get_filtered_console_logs,
        "get_filtered_page_errors": get_filtered_page_errors,
        "get_filtered_network_requests": get_filtered_network_requests,
        "enhance_console_command": enhance_console_command,
        "monitor_page_performance": monitor_page_performance,
        "get_console_activity_summary": get_console_activity_summary,
        "clear_console_data": clear_console_data,
        "inject_page_logger": inject_page_logger
    }