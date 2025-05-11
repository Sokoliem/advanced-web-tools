"""Console monitoring module for web interaction.

This module provides functionality to monitor and capture browser console logs, errors, and network requests.
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class ConsoleMonitor:
    """Monitors and captures browser console activity."""
    
    def __init__(self, storage_dir=None):
        """Initialize the console monitor."""
        # Set storage directory
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".claude_web_interaction")
        
        # Console logs directory
        self.console_dir = Path(self.storage_dir) / 'console_logs'
        self.console_dir.mkdir(exist_ok=True)
        
        # Storage for console logs, errors, and network requests
        self.console_logs = {}
        self.page_errors = {}
        self.network_requests = {}
        
        # Configuration
        self.capture_console = True
        self.capture_network = os.environ.get('MCP_CAPTURE_NETWORK', 'false').lower() == 'true'
    
    async def setup_page_monitoring(self, page, page_id):
        """Set up console monitoring for a page."""
        if not self.capture_console:
            return
            
        # Initialize containers for this page
        if page_id not in self.console_logs:
            self.console_logs[page_id] = []
            
        if page_id not in self.page_errors:
            self.page_errors[page_id] = []
            
        if self.capture_network and page_id not in self.network_requests:
            self.network_requests[page_id] = []
        
        # Console log listener
        async def console_handler(msg):
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': msg.type,
                'text': msg.text,
                'location': str(msg.location) if hasattr(msg, 'location') else None,
                'args': [str(arg) for arg in msg.args] if hasattr(msg, 'args') else []
            }
            self.console_logs[page_id].append(log_entry)
            
            # Log to console
            log_level = getattr(logging, msg.type.upper(), logging.INFO)
            logger.log(log_level, f"[Console:{page_id}] {msg.type}: {msg.text}")
            
            # Save to file
            self._save_console_log(page_id, log_entry)
        
        # Page error listener
        async def error_handler(error):
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': str(error),
                'stack': getattr(error, 'stack', 'No stack trace')
            }
            self.page_errors[page_id].append(error_entry)
            logger.error(f"[PageError:{page_id}] {error}")
            
            # Save to file
            self._save_page_error(page_id, error_entry)
        
        # Network request listener
        async def request_handler(request):
            if not self.capture_network:
                return
                
            request_entry = {
                'timestamp': datetime.now().isoformat(),
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers) if hasattr(request, 'headers') else {},
                'resource_type': request.resource_type
            }
            self.network_requests[page_id].append(request_entry)
            
            # Only log certain request types to avoid noise
            if request.resource_type in ['document', 'xhr', 'fetch']:
                logger.info(f"[Network:{page_id}] {request.method} {request.url}")
        
        # Set up listeners
        page.on("console", console_handler)
        page.on("pageerror", error_handler)
        if self.capture_network:
            page.on("request", request_handler)
    
    def _save_console_log(self, page_id, log_entry):
        """Save console log to file."""
        try:
            log_file = self.console_dir / f"console_{page_id}.jsonl"
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error saving console log: {str(e)}")
    
    def _save_page_error(self, page_id, error_entry):
        """Save page error to file."""
        try:
            error_file = self.console_dir / f"errors_{page_id}.jsonl"
            with open(error_file, 'a') as f:
                f.write(json.dumps(error_entry) + '\n')
        except Exception as e:
            logger.error(f"Error saving page error: {str(e)}")
    
    async def get_console_logs(self, page_id=None):
        """Get console logs for a page or all pages."""
        if page_id:
            return self.console_logs.get(page_id, [])
        return self.console_logs
    
    async def get_page_errors(self, page_id=None):
        """Get page errors for a page or all pages."""
        if page_id:
            return self.page_errors.get(page_id, [])
        return self.page_errors
    
    async def get_network_requests(self, page_id=None):
        """Get network requests for a page or all pages."""
        if not self.capture_network:
            return {}
            
        if page_id:
            return self.network_requests.get(page_id, [])
        return self.network_requests
    
    async def execute_console_command(self, page, command):
        """Execute a JavaScript command in the console of a page."""
        try:
            result = await page.evaluate(command)
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
