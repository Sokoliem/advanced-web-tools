"""Web Diagnostic Toolkit for Systematic Debugging and Testing.

This module provides a comprehensive toolkit for systematically collecting diagnostic 
information from web applications, aggregating data from various sources including
console logs, network traffic, DOM state, performance metrics, and visual snapshots.
"""

import asyncio
import json
import logging
import os
import time
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logger = logging.getLogger(__name__)

class WebDiagnosticToolkit:
    """Comprehensive toolkit for web application diagnostics and debugging."""
    
    def __init__(self, browser_manager, console_monitor=None, visual_debugger=None, error_handler=None):
        """
        Initialize the web diagnostic toolkit.
        
        Args:
            browser_manager: Browser manager instance
            console_monitor: Optional console monitor instance 
            visual_debugger: Optional visual debugger instance
            error_handler: Optional error handler instance
        """
        self.browser_manager = browser_manager
        self.console_monitor = console_monitor
        self.visual_debugger = visual_debugger
        self.error_handler = error_handler
        
        # Initialize storage directory
        self.storage_dir = Path(browser_manager.storage_dir) if hasattr(browser_manager, 'storage_dir') else Path(os.path.expanduser("~")) / '.claude_web_interaction'
        self.diagnostic_dir = self.storage_dir / 'diagnostics'
        self.diagnostic_dir.mkdir(exist_ok=True)
        
        # Initialize diagnostic sessions
        self.diagnostic_sessions = {}
        self.active_session_id = None
        
        # Performance metrics tracking
        self.metrics_tracking = False
        self.performance_samples = {}
        
        # Create core diagnostic directories
        self.screenshots_dir = self.diagnostic_dir / 'screenshots'
        self.screenshots_dir.mkdir(exist_ok=True)
        
        self.reports_dir = self.diagnostic_dir / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        self.performance_dir = self.diagnostic_dir / 'performance'
        self.performance_dir.mkdir(exist_ok=True)
        
        self.network_dir = self.diagnostic_dir / 'network'
        self.network_dir.mkdir(exist_ok=True)
        
        logger.info(f"Web Diagnostic Toolkit initialized. Storage directory: {self.diagnostic_dir}")
    
    async def create_diagnostic_session(self, name=None, description=None, context=None):
        """
        Create a new diagnostic session to group related diagnostics.
        
        Args:
            name: Optional name for the session
            description: Optional description of the session purpose
            context: Optional context information for the session
            
        Returns:
            Session ID
        """
        session_id = f"session_{int(time.time())}"
        session_name = name or f"Diagnostic Session {session_id}"
        
        # Create session structure
        session = {
            "id": session_id,
            "name": session_name,
            "description": description or "Web application diagnostic session",
            "created_at": datetime.now().isoformat(),
            "context": context or {},
            "artifacts": [],
            "events": [],
            "metrics": {},
            "summary": {}
        }
        
        # Store session
        self.diagnostic_sessions[session_id] = session
        self.active_session_id = session_id
        
        # Create session directory
        session_dir = self.diagnostic_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Save session metadata
        self._save_session_metadata(session_id)
        
        logger.info(f"Created diagnostic session {session_id}: {session_name}")
        return session_id
    
    def _save_session_metadata(self, session_id):
        """Save session metadata to file."""
        if session_id in self.diagnostic_sessions:
            session_dir = self.diagnostic_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            metadata_file = session_dir / 'metadata.json'
            with open(metadata_file, 'w') as f:
                # Create a copy to avoid modifying the original
                metadata = dict(self.diagnostic_sessions[session_id])
                # Remove artifacts list as it might be too large
                metadata['artifacts_count'] = len(metadata.get('artifacts', []))
                metadata['artifacts'] = []
                json.dump(metadata, f, indent=2)
    
    async def collect_full_diagnostic(self, page_id, options=None):
        """
        Collect comprehensive diagnostics for a specific page.
        
        Args:
            page_id: ID of the page to diagnose
            options: Optional configuration options
            
        Returns:
            Dictionary with diagnostic results
        """
        if page_id is not None:
            page_id = str(page_id)
        
        # Default options
        default_options = {
            "collect_console": True,
            "collect_network": True,
            "collect_dom": True,
            "collect_visual": True,
            "collect_performance": True,
            "collect_errors": True,
            "take_screenshot": True,
            "session_id": self.active_session_id
        }
        
        # Merge with provided options
        opts = {**default_options, **(options or {})}
        session_id = opts["session_id"]
        
        # Ensure we have an active session
        if not session_id:
            session_id = await self.create_diagnostic_session(
                name=f"Diagnostics for Page {page_id}",
                description=f"Automatically created diagnostic session for page {page_id}"
            )
        
        logger.info(f"Collecting comprehensive diagnostics for page {page_id} in session {session_id}")
        
        # Start timestamp
        start_time = time.time()
        timestamp = int(start_time * 1000)
        
        # Get the page
        page = self.browser_manager.active_pages.get(page_id)
        if not page:
            error_msg = f"Page {page_id} not found"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id
            }
        
        # Collect basic page information
        try:
            url = page.url
            title = await page.title()
        except Exception as e:
            logger.warning(f"Error getting basic page info: {str(e)}")
            url = "unknown"
            title = "unknown"
        
        # Prepare results container
        results = {
            "success": True,
            "timestamp": timestamp,
            "session_id": session_id,
            "page_id": page_id,
            "url": url,
            "title": title,
            "artifacts": []
        }
        
        # Add browser metadata from browser manager
        if hasattr(self.browser_manager, 'page_metadata') and page_id in self.browser_manager.page_metadata:
            results["page_metadata"] = self.browser_manager.page_metadata[page_id]
        
        # Collect diagnostics in parallel
        collection_tasks = []
        
        # Console logs
        if opts["collect_console"] and self.console_monitor:
            collection_tasks.append(self._collect_console_logs(page_id, session_id, timestamp))
        
        # Network requests
        if opts["collect_network"] and self.console_monitor:
            collection_tasks.append(self._collect_network_requests(page_id, session_id, timestamp))
        
        # DOM snapshot
        if opts["collect_dom"] and self.visual_debugger:
            collection_tasks.append(self._collect_dom_snapshot(page, page_id, session_id, timestamp))
        
        # Visual snapshot (screenshot)
        if opts["take_screenshot"]:
            collection_tasks.append(self._take_page_screenshot(page, page_id, session_id, timestamp))
        
        # Performance metrics
        if opts["collect_performance"]:
            collection_tasks.append(self._collect_performance_metrics(page, page_id, session_id, timestamp))
        
        # Error information
        if opts["collect_errors"] and self.error_handler:
            collection_tasks.append(self._collect_error_information(page_id, session_id, timestamp))
        
        # Execute all collection tasks concurrently
        if collection_tasks:
            collection_results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            # Process results
            for result in collection_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in diagnostic collection: {str(result)}")
                    continue
                    
                if isinstance(result, dict) and 'artifact' in result:
                    # Add to session artifacts
                    if session_id in self.diagnostic_sessions:
                        self.diagnostic_sessions[session_id]['artifacts'].append(result['artifact'])
                    
                    # Add to results
                    if 'artifacts' in results:
                        results['artifacts'].append(result['artifact'])
        
        # Calculate total time
        end_time = time.time()
        results["collection_time_ms"] = int((end_time - start_time) * 1000)
        
        # Add to session events
        if session_id in self.diagnostic_sessions:
            self.diagnostic_sessions[session_id]['events'].append({
                "type": "diagnostic_collection",
                "timestamp": datetime.now().isoformat(),
                "page_id": page_id,
                "url": url,
                "artifacts_count": len(results.get('artifacts', []))
            })
            
            # Save updated session metadata
            self._save_session_metadata(session_id)
        
        logger.info(f"Comprehensive diagnostics collection completed in {results['collection_time_ms']}ms with {len(results.get('artifacts', []))} artifacts")
        return results
    
    async def _collect_console_logs(self, page_id, session_id, timestamp):
        """Collect console logs for a page."""
        try:
            console_logs = await self.console_monitor.get_console_logs(page_id)
            
            # Create artifact
            artifact = {
                "type": "console_logs",
                "timestamp": timestamp,
                "page_id": page_id,
                "session_id": session_id,
                "content": console_logs
            }
            
            # Save to file
            artifact_file = self.diagnostic_dir / session_id / f"console_logs_{page_id}_{timestamp}.json"
            with open(artifact_file, 'w') as f:
                json.dump(console_logs, f, indent=2)
            
            artifact["path"] = str(artifact_file)
            
            return {"artifact": artifact}
        except Exception as e:
            logger.error(f"Error collecting console logs: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_network_requests(self, page_id, session_id, timestamp):
        """Collect network requests for a page."""
        try:
            network_requests = await self.console_monitor.get_network_requests(page_id)
            
            # Create artifact
            artifact = {
                "type": "network_requests",
                "timestamp": timestamp,
                "page_id": page_id,
                "session_id": session_id,
                "content": network_requests
            }
            
            # Save to file
            artifact_file = self.diagnostic_dir / session_id / f"network_requests_{page_id}_{timestamp}.json"
            with open(artifact_file, 'w') as f:
                json.dump(network_requests, f, indent=2)
            
            artifact["path"] = str(artifact_file)
            
            return {"artifact": artifact}
        except Exception as e:
            logger.error(f"Error collecting network requests: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_dom_snapshot(self, page, page_id, session_id, timestamp):
        """Collect DOM snapshot for a page."""
        try:
            # Use visual debugger if available, otherwise do it directly
            if self.visual_debugger:
                snapshot_path = await self.visual_debugger.capture_dom_snapshot(page, include_styles=True)
                
                # Read the captured snapshot
                if snapshot_path:
                    with open(snapshot_path, 'r') as f:
                        dom_snapshot = json.load(f)
                else:
                    # Fallback if capture failed
                    dom_snapshot = await self._capture_dom_directly(page)
            else:
                # Direct capture
                dom_snapshot = await self._capture_dom_directly(page)
            
            # Create artifact
            artifact = {
                "type": "dom_snapshot",
                "timestamp": timestamp,
                "page_id": page_id,
                "session_id": session_id,
                "content_summary": "DOM structure snapshot with element properties and styles"
            }
            
            # Save to file
            artifact_file = self.diagnostic_dir / session_id / f"dom_snapshot_{page_id}_{timestamp}.json"
            with open(artifact_file, 'w') as f:
                json.dump(dom_snapshot, f, indent=2)
            
            artifact["path"] = str(artifact_file)
            
            return {"artifact": artifact}
        except Exception as e:
            logger.error(f"Error collecting DOM snapshot: {str(e)}")
            return {"error": str(e)}
    
    async def _capture_dom_directly(self, page):
        """Capture DOM structure directly."""
        # Script to capture DOM structure
        dom_script = """
        () => {
            function processElement(element, maxDepth = 10, currentDepth = 0) {
                if (currentDepth > maxDepth) return null;
                
                // Basic element info
                const result = {
                    tagName: element.tagName,
                    id: element.id || null,
                    className: element.className || null,
                    textContent: element.textContent ? element.textContent.trim().substring(0, 100) : null,
                    attributes: {},
                    children: []
                };
                
                // Add attributes
                for (const attr of element.attributes) {
                    result.attributes[attr.name] = attr.value;
                }
                
                // Add computed styles (selected important ones)
                const styles = window.getComputedStyle(element);
                result.styles = {};
                ['display', 'visibility', 'position', 'z-index', 'width', 'height'].forEach(prop => {
                    result.styles[prop] = styles[prop];
                });
                
                // Add position
                const rect = element.getBoundingClientRect();
                result.position = {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    visible: rect.width > 0 && rect.height > 0
                };
                
                // Process children (limit to avoid too large objects)
                if (currentDepth < maxDepth) {
                    for (const child of element.children) {
                        const childResult = processElement(child, maxDepth, currentDepth + 1);
                        if (childResult) {
                            result.children.push(childResult);
                        }
                    }
                }
                
                return result;
            }
            
            return {
                url: window.location.href,
                title: document.title,
                doctype: document.doctype ? document.doctype.name : null,
                root: processElement(document.documentElement, 5) // Limit depth to 5 levels
            };
        }
        """
        
        return await page.evaluate(dom_script)
    
    async def _take_page_screenshot(self, page, page_id, session_id, timestamp):
        """Take a screenshot of the page."""
        try:
            # Create screenshot filename
            screenshot_filename = f"screenshot_{page_id}_{timestamp}.png"
            screenshot_path = str(self.screenshots_dir / screenshot_filename)
            
            # Take screenshot
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # Create artifact
            artifact = {
                "type": "screenshot",
                "timestamp": timestamp,
                "page_id": page_id,
                "session_id": session_id,
                "path": screenshot_path
            }
            
            # Create a copy in the session directory
            session_screenshot_path = self.diagnostic_dir / session_id / screenshot_filename
            import shutil
            shutil.copy2(screenshot_path, session_screenshot_path)
            
            return {"artifact": artifact}
        except Exception as e:
            logger.error(f"Error taking page screenshot: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_performance_metrics(self, page, page_id, session_id, timestamp):
        """Collect performance metrics for a page."""
        try:
            # Get performance metrics using JavaScript
            metrics_script = """
            () => {
                const metrics = {};
                
                // Navigation timing data
                if (window.performance && window.performance.timing) {
                    const timing = window.performance.timing;
                    metrics.timing = {
                        navigationStart: timing.navigationStart,
                        unloadEventStart: timing.unloadEventStart,
                        unloadEventEnd: timing.unloadEventEnd,
                        redirectStart: timing.redirectStart,
                        redirectEnd: timing.redirectEnd,
                        fetchStart: timing.fetchStart,
                        domainLookupStart: timing.domainLookupStart,
                        domainLookupEnd: timing.domainLookupEnd,
                        connectStart: timing.connectStart,
                        connectEnd: timing.connectEnd,
                        secureConnectionStart: timing.secureConnectionStart,
                        requestStart: timing.requestStart,
                        responseStart: timing.responseStart,
                        responseEnd: timing.responseEnd,
                        domLoading: timing.domLoading,
                        domInteractive: timing.domInteractive,
                        domContentLoadedEventStart: timing.domContentLoadedEventStart,
                        domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                        domComplete: timing.domComplete,
                        loadEventStart: timing.loadEventStart,
                        loadEventEnd: timing.loadEventEnd
                    };
                    
                    // Calculate durations
                    metrics.durations = {
                        total: timing.loadEventEnd - timing.navigationStart,
                        dns: timing.domainLookupEnd - timing.domainLookupStart,
                        tcp: timing.connectEnd - timing.connectStart,
                        request: timing.responseStart - timing.requestStart,
                        response: timing.responseEnd - timing.responseStart,
                        processing: timing.domComplete - timing.responseEnd,
                        onload: timing.loadEventEnd - timing.loadEventStart,
                        domContentLoaded: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart
                    };
                }
                
                // Resource timing data
                if (window.performance && window.performance.getEntriesByType) {
                    const resources = window.performance.getEntriesByType('resource');
                    
                    // Group resources by type
                    const resourcesByType = {};
                    resources.forEach(resource => {
                        const type = resource.initiatorType || 'other';
                        if (!resourcesByType[type]) {
                            resourcesByType[type] = [];
                        }
                        
                        resourcesByType[type].push({
                            name: resource.name,
                            duration: resource.duration,
                            transferSize: resource.transferSize,
                            decodedBodySize: resource.decodedBodySize
                        });
                    });
                    
                    metrics.resources = {
                        count: resources.length,
                        totalSize: resources.reduce((total, r) => total + (r.transferSize || 0), 0),
                        totalDuration: resources.reduce((total, r) => total + r.duration, 0),
                        byType: resourcesByType
                    };
                }
                
                // Memory info
                if (window.performance && window.performance.memory) {
                    metrics.memory = {
                        totalJSHeapSize: window.performance.memory.totalJSHeapSize,
                        usedJSHeapSize: window.performance.memory.usedJSHeapSize,
                        jsHeapSizeLimit: window.performance.memory.jsHeapSizeLimit
                    };
                }
                
                // Layout metrics
                metrics.layout = {
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    },
                    documentSize: {
                        width: document.documentElement.scrollWidth,
                        height: document.documentElement.scrollHeight
                    },
                    elementCount: document.querySelectorAll('*').length
                };
                
                return metrics;
            }
            """
            
            # Execute the script
            metrics = await page.evaluate(metrics_script)
            
            # Add timestamp
            metrics['timestamp'] = timestamp
            metrics['collected_at'] = datetime.now().isoformat()
            
            # Create artifact
            artifact = {
                "type": "performance_metrics",
                "timestamp": timestamp,
                "page_id": page_id,
                "session_id": session_id,
                "content": metrics
            }
            
            # Save to file
            artifact_file = self.diagnostic_dir / session_id / f"performance_{page_id}_{timestamp}.json"
            with open(artifact_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            artifact["path"] = str(artifact_file)
            
            # Store in session metrics
            if session_id in self.diagnostic_sessions:
                if 'metrics' not in self.diagnostic_sessions[session_id]:
                    self.diagnostic_sessions[session_id]['metrics'] = {}
                
                # Store the latest metrics
                self.diagnostic_sessions[session_id]['metrics'][page_id] = {
                    'timestamp': timestamp,
                    'url': page.url,
                    'summary': {
                        'loadTime': metrics.get('durations', {}).get('total', 0),
                        'resourceCount': metrics.get('resources', {}).get('count', 0),
                        'resourceSize': metrics.get('resources', {}).get('totalSize', 0),
                        'elementCount': metrics.get('layout', {}).get('elementCount', 0)
                    }
                }
            
            return {"artifact": artifact}
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {str(e)}")
            return {"error": str(e)}
    
    async def _collect_error_information(self, page_id, session_id, timestamp):
        """Collect error information for a page."""
        try:
            # Get page errors from console monitor
            page_errors = await self.console_monitor.get_page_errors(page_id)
            
            # Get error statistics from error handler
            error_stats = {}
            if self.error_handler:
                error_stats = self.error_handler.get_error_stats()
            
            # Combine the data
            error_data = {
                "page_errors": page_errors,
                "error_stats": error_stats,
                "timestamp": timestamp,
                "collected_at": datetime.now().isoformat()
            }
            
            # Create artifact
            artifact = {
                "type": "error_information",
                "timestamp": timestamp,
                "page_id": page_id,
                "session_id": session_id,
                "content": error_data
            }
            
            # Save to file
            artifact_file = self.diagnostic_dir / session_id / f"errors_{page_id}_{timestamp}.json"
            with open(artifact_file, 'w') as f:
                json.dump(error_data, f, indent=2)
            
            artifact["path"] = str(artifact_file)
            
            return {"artifact": artifact}
        except Exception as e:
            logger.error(f"Error collecting error information: {str(e)}")
            return {"error": str(e)}
    
    async def start_performance_monitoring(self, page_id, interval_seconds=5):
        """
        Start continuous performance monitoring for a page.
        
        Args:
            page_id: ID of the page to monitor
            interval_seconds: Sampling interval in seconds
            
        Returns:
            Success flag
        """
        logger.info(f"Starting performance monitoring for page {page_id} with interval {interval_seconds}s")
        
        # Validate parameters
        if page_id is None:
            logger.error("No page_id provided for performance monitoring")
            return False
            
        # Ensure page_id is a string
        page_id = str(page_id)
        logger.info(f"Converted page_id to string: {page_id}")
        
        # Parse interval_seconds as int if it's a string
        if isinstance(interval_seconds, str):
            try:
                interval_seconds = int(interval_seconds)
                logger.info(f"Converted interval_seconds to int: {interval_seconds}")
            except ValueError:
                interval_seconds = 5
                logger.warning(f"Invalid interval_seconds value, using default: {interval_seconds}")
        
        # Check if the page exists
        page = self.browser_manager.active_pages.get(page_id)
        if not page:
            logger.error(f"Page {page_id} not found for performance monitoring")
            
            # Try to use fallback page if any exists
            if self.browser_manager.active_pages:
                fallback_page_id = next(iter(self.browser_manager.active_pages.keys()))
                logger.info(f"Using fallback page {fallback_page_id} for performance monitoring")
                page_id = fallback_page_id
                page = self.browser_manager.active_pages[page_id]
            else:
                # Try to create a new page if no pages exist
                try:
                    logger.info("No active pages, creating a new page for performance monitoring")
                    page, page_id = await self.browser_manager.get_page()
                    await page.goto("about:blank")
                    logger.info(f"Created new page with ID {page_id} for performance monitoring")
                except Exception as e:
                    logger.error(f"Failed to create a page for performance monitoring: {str(e)}")
                    return False
        
        # Check if monitoring is already active for this page
        if page_id in self.performance_samples and len(self.performance_samples[page_id]) > 0:
            logger.info(f"Performance monitoring already active for page {page_id}")
            return True
        
        # Set up monitoring for this page
        if page_id not in self.performance_samples:
            self.performance_samples[page_id] = []
        
        # Start monitoring if not already started
        if not self.metrics_tracking:
            self.metrics_tracking = True
            
            # Start the monitoring task
            asyncio.create_task(self._performance_monitoring_task(interval_seconds))
            
            logger.info(f"Started performance monitoring for page {page_id} with {interval_seconds}s interval")
            return True
        else:
            logger.info(f"Performance monitoring already active, added page {page_id}")
            return True
    
    async def _performance_monitoring_task(self, interval_seconds):
        """Background task for performance monitoring."""
        while self.metrics_tracking:
            try:
                # Sample metrics for all pages
                for page_id in list(self.browser_manager.active_pages.keys()):
                    page = self.browser_manager.active_pages.get(page_id)
                    if not page:
                        continue
                    
                    # Use session ID if active, otherwise None
                    session_id = self.active_session_id
                    
                    # Collect metrics for this page
                    timestamp = int(time.time() * 1000)
                    try:
                        # Execute minimal performance script
                        metrics_script = """
                        () => {
                            return {
                                memory: window.performance.memory ? {
                                    usedJSHeapSize: window.performance.memory.usedJSHeapSize,
                                    totalJSHeapSize: window.performance.memory.totalJSHeapSize
                                } : {},
                                timing: window.performance.timing ? {
                                    loadTime: window.performance.timing.loadEventEnd - window.performance.timing.navigationStart,
                                    domContentLoaded: window.performance.timing.domContentLoadedEventEnd - window.performance.timing.navigationStart
                                } : {},
                                resources: {
                                    count: window.performance.getEntriesByType ? window.performance.getEntriesByType('resource').length : 0
                                },
                                layout: {
                                    elementCount: document.querySelectorAll('*').length
                                }
                            };
                        }
                        """
                        
                        metrics = await page.evaluate(metrics_script)
                        
                        # Add timestamp and page info
                        metrics['timestamp'] = timestamp
                        metrics['page_id'] = page_id
                        metrics['url'] = page.url
                        
                        # Store the sample
                        if page_id in self.performance_samples:
                            # Limit to last 100 samples
                            samples = self.performance_samples[page_id]
                            samples.append(metrics)
                            if len(samples) > 100:
                                samples.pop(0)
                        
                        # Add to session if active
                        if session_id in self.diagnostic_sessions:
                            if 'performance_samples' not in self.diagnostic_sessions[session_id]:
                                self.diagnostic_sessions[session_id]['performance_samples'] = {}
                            
                            if page_id not in self.diagnostic_sessions[session_id]['performance_samples']:
                                self.diagnostic_sessions[session_id]['performance_samples'][page_id] = []
                            
                            # Add sample and limit to last 20 samples in session
                            samples = self.diagnostic_sessions[session_id]['performance_samples'][page_id]
                            samples.append(metrics)
                            if len(samples) > 20:
                                samples.pop(0)
                    
                    except Exception as e:
                        logger.debug(f"Error collecting performance sample for page {page_id}: {str(e)}")
                
                # Sleep until next sample
                await asyncio.sleep(interval_seconds)
            
            except Exception as e:
                logger.error(f"Error in performance monitoring task: {str(e)}")
                await asyncio.sleep(interval_seconds)
    
    async def stop_performance_monitoring(self, page_id=None):
        """
        Stop performance monitoring.
        
        Args:
            page_id: Optional ID of the page to stop monitoring. If None, stops all monitoring.
            
        Returns:
            Success flag
        """
        if page_id is not None:
            page_id = str(page_id)
            
            # Stop monitoring for specific page
            if page_id in self.performance_samples:
                del self.performance_samples[page_id]
                logger.info(f"Stopped performance monitoring for page {page_id}")
                
                # If no more pages, stop the task
                if not self.performance_samples:
                    self.metrics_tracking = False
                
                return True
            return False
        else:
            # Stop all monitoring
            self.metrics_tracking = False
            self.performance_samples = {}
            logger.info("Stopped all performance monitoring")
            return True
    
    async def get_performance_report(self, page_id=None, session_id=None):
        """
        Generate a performance report for a page or session.
        
        Args:
            page_id: Optional ID of the page to report on
            session_id: Optional ID of the session to report on
            
        Returns:
            Performance report data
        """
        if page_id is not None:
            page_id = str(page_id)
        
        session_id = session_id or self.active_session_id
        
        # Get samples
        samples = []
        if page_id:
            # Get samples for specific page
            samples = self.performance_samples.get(page_id, [])
        elif session_id in self.diagnostic_sessions:
            # Get samples from session
            for page_id, page_samples in self.diagnostic_sessions[session_id].get('performance_samples', {}).items():
                for sample in page_samples:
                    samples.append(sample)
        
        if not samples:
            return {
                "success": False,
                "error": "No performance samples found",
                "page_id": page_id,
                "session_id": session_id
            }
        
        # Calculate statistics
        stats = self._calculate_performance_stats(samples)
        
        # Create report
        report = {
            "success": True,
            "timestamp": int(time.time() * 1000),
            "page_id": page_id,
            "session_id": session_id,
            "sample_count": len(samples),
            "stats": stats,
            "samples": samples
        }
        
        # Save report
        report_file = self.reports_dir / f"performance_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        report["report_path"] = str(report_file)
        
        return report
    
    def _calculate_performance_stats(self, samples):
        """Calculate statistics from performance samples."""
        if not samples:
            return {}
        
        # Extract metrics
        memory_used = [s.get('memory', {}).get('usedJSHeapSize', 0) for s in samples if 'memory' in s]
        load_times = [s.get('timing', {}).get('loadTime', 0) for s in samples if 'timing' in s]
        dom_ready_times = [s.get('timing', {}).get('domContentLoaded', 0) for s in samples if 'timing' in s]
        element_counts = [s.get('layout', {}).get('elementCount', 0) for s in samples if 'layout' in s]
        resource_counts = [s.get('resources', {}).get('count', 0) for s in samples if 'resources' in s]
        
        # Clean up lists
        memory_used = [m for m in memory_used if m > 0]
        load_times = [t for t in load_times if t > 0]
        dom_ready_times = [t for t in dom_ready_times if t > 0]
        element_counts = [c for c in element_counts if c > 0]
        resource_counts = [c for c in resource_counts if c > 0]
        
        # Calculate statistics
        stats = {}
        
        if memory_used:
            stats['memory_used_mb'] = {
                'min': min(memory_used) / (1024 * 1024),
                'max': max(memory_used) / (1024 * 1024),
                'avg': sum(memory_used) / len(memory_used) / (1024 * 1024)
            }
        
        if load_times:
            stats['load_time_ms'] = {
                'min': min(load_times),
                'max': max(load_times),
                'avg': sum(load_times) / len(load_times)
            }
        
        if dom_ready_times:
            stats['dom_ready_time_ms'] = {
                'min': min(dom_ready_times),
                'max': max(dom_ready_times),
                'avg': sum(dom_ready_times) / len(dom_ready_times)
            }
        
        if element_counts:
            stats['element_count'] = {
                'min': min(element_counts),
                'max': max(element_counts),
                'avg': sum(element_counts) / len(element_counts)
            }
        
        if resource_counts:
            stats['resource_count'] = {
                'min': min(resource_counts),
                'max': max(resource_counts),
                'avg': sum(resource_counts) / len(resource_counts)
            }
        
        return stats
    
    async def create_diagnostic_report(self, page_id=None, session_id=None, include_artifacts=False):
        """
        Create a comprehensive diagnostic report.
        
        Args:
            page_id: Optional page ID to focus report on
            session_id: Optional session ID (uses active session if not specified)
            include_artifacts: Whether to include full artifacts or just references
            
        Returns:
            Diagnostic report data
        """
        logger.info(f"Creating diagnostic report for page_id={page_id}, session_id={session_id}")
        
        # Ensure page_id is a string if provided
        if page_id is not None:
            page_id = str(page_id)
            logger.info(f"Converted page_id to string: {page_id}")
        
        # Get session ID - use provided or active
        session_id = session_id or self.active_session_id
        logger.info(f"Using session_id: {session_id}")
        
        # Create a new session if none exists
        if not session_id or session_id not in self.diagnostic_sessions:
            try:
                logger.info("No valid session found, creating a new diagnostic session")
                session_id = await self.create_session("Auto-created session")
                logger.info(f"Created new session with ID {session_id}")
                
                # If page_id is provided, collect basic diagnostics for that page
                if page_id and page_id in self.browser_manager.active_pages:
                    logger.info(f"Collecting diagnostics for page {page_id} in new session")
                    await self.collect_web_diagnostics(page_id, session_id)
            except Exception as e:
                logger.error(f"Error creating diagnostic session: {str(e)}")
        
        # Check again if we have a valid session after potential creation
        if not session_id or session_id not in self.diagnostic_sessions:
            return {
                "success": False,
                "error": "No valid diagnostic session found. Please create a diagnostic session first with create_diagnostic_session."
            }
        
        # Get session data
        session = self.diagnostic_sessions[session_id]
        
        # Filter artifacts if needed
        artifacts = session.get('artifacts', [])
        if page_id:
            artifacts = [a for a in artifacts if a.get('page_id') == page_id]
        
        # Group artifacts by type
        artifacts_by_type = {}
        for artifact in artifacts:
            artifact_type = artifact.get('type', 'unknown')
            if artifact_type not in artifacts_by_type:
                artifacts_by_type[artifact_type] = []
            
            # Include full artifact or just reference
            if include_artifacts:
                artifacts_by_type[artifact_type].append(artifact)
            else:
                # Include minimal information
                artifacts_by_type[artifact_type].append({
                    'timestamp': artifact.get('timestamp'),
                    'page_id': artifact.get('page_id'),
                    'path': artifact.get('path')
                })
        
        # Get performance statistics if available
        performance_stats = {}
        if 'performance_samples' in session:
            samples = []
            for p_id, page_samples in session['performance_samples'].items():
                if not page_id or p_id == page_id:
                    samples.extend(page_samples)
            
            if samples:
                performance_stats = self._calculate_performance_stats(samples)
        
        # Create report
        report = {
            "success": True,
            "timestamp": int(time.time() * 1000),
            "generated_at": datetime.now().isoformat(),
            "session_id": session_id,
            "session_name": session.get('name'),
            "session_created_at": session.get('created_at'),
            "page_id": page_id,
            "artifact_counts": {k: len(v) for k, v in artifacts_by_type.items()},
            "artifacts_by_type": artifacts_by_type,
            "performance_stats": performance_stats,
            "events": session.get('events', [])
        }
        
        # Save report
        report_name = f"diagnostic_report_{session_id}"
        if page_id:
            report_name += f"_{page_id}"
        report_name += f"_{int(time.time())}.json"
        
        report_file = self.reports_dir / report_name
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        report["report_path"] = str(report_file)
        
        # Create HTML report
        html_report = await self._create_html_report(report, session)
        if html_report:
            report["html_report_path"] = html_report
        
        return report
    
    async def _create_html_report(self, report_data, session):
        """Create an HTML report from the report data."""
        try:
            # Create HTML report filename
            report_name = f"report_{session['id']}_{int(time.time())}.html"
            html_path = str(self.reports_dir / report_name)
            
            # Generate HTML content
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Diagnostic Report - {session.get('name', 'Unnamed Session')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    h1, h2, h3 {{ color: #333; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .card {{ 
                        border: 1px solid #ddd; 
                        border-radius: 4px; 
                        padding: 15px; 
                        margin-bottom: 20px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .header {{ background-color: #f5f5f5; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
                    .stats {{ display: flex; flex-wrap: wrap; gap: 10px; }}
                    .stat-box {{ 
                        flex: 1; 
                        min-width: 200px; 
                        background-color: #f8f8f8; 
                        padding: 10px; 
                        border-radius: 4px;
                        border-left: 4px solid #007bff;
                    }}
                    .artifacts {{ margin-top: 20px; }}
                    .artifact-group {{ margin-bottom: 30px; }}
                    .tables {{ border-collapse: collapse; width: 100%; }}
                    .tables th, .tables td {{ 
                        border: 1px solid #ddd; 
                        padding: 8px; 
                        text-align: left;
                    }}
                    .tables th {{ background-color: #f2f2f2; }}
                    .tables tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .screenshot {{ max-width: 300px; border: 1px solid #ddd; margin: 10px 0; }}
                    .tab {{ overflow: hidden; border: 1px solid #ccc; background-color: #f1f1f1; }}
                    .tab button {{ 
                        background-color: inherit; 
                        float: left; 
                        border: none; 
                        outline: none; 
                        cursor: pointer; 
                        padding: 14px 16px; 
                        transition: 0.3s;
                    }}
                    .tab button:hover {{ background-color: #ddd; }}
                    .tab button.active {{ background-color: #ccc; }}
                    .tabcontent {{ 
                        display: none; 
                        padding: 6px 12px; 
                        border: 1px solid #ccc; 
                        border-top: none;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Diagnostic Report</h1>
                        <p><strong>Session:</strong> {session.get('name', 'Unnamed')}</p>
                        <p><strong>Created:</strong> {session.get('created_at', 'Unknown')}</p>
                        <p><strong>Report Generated:</strong> {report_data.get('generated_at', 'Unknown')}</p>
                        {f"<p><strong>Page ID:</strong> {report_data.get('page_id', 'All pages')}</p>" if report_data.get('page_id') else ""}
                    </div>
                    
                    <div class="tab">
                        <button class="tablinks active" onclick="openTab(event, 'Summary')">Summary</button>
                        <button class="tablinks" onclick="openTab(event, 'Performance')">Performance</button>
                        <button class="tablinks" onclick="openTab(event, 'Artifacts')">Artifacts</button>
                        <button class="tablinks" onclick="openTab(event, 'Events')">Events</button>
                        <button class="tablinks" onclick="openTab(event, 'Screenshots')">Screenshots</button>
                    </div>
                    
                    <div id="Summary" class="tabcontent" style="display: block;">
                        <h2>Summary</h2>
                        <div class="card">
                            <h3>Artifact Counts</h3>
                            <div class="stats">
            """
            
            # Add artifact count stats
            for artifact_type, count in report_data.get('artifact_counts', {}).items():
                html += f"""
                                <div class="stat-box">
                                    <div>{artifact_type.replace('_', ' ').title()}</div>
                                    <div style="font-size: 24px; font-weight: bold;">{count}</div>
                                </div>
                """
            
            html += """
                            </div>
                        </div>
            """
            
            # Add performance summary if available
            if report_data.get('performance_stats'):
                html += """
                        <div class="card">
                            <h3>Performance Summary</h3>
                            <div class="stats">
                """
                
                stats = report_data['performance_stats']
                
                # Add load time
                if 'load_time_ms' in stats:
                    html += f"""
                                <div class="stat-box">
                                    <div>Load Time</div>
                                    <div style="font-size: 24px; font-weight: bold;">{stats['load_time_ms']['avg']:.0f} ms</div>
                                    <div>Min: {stats['load_time_ms']['min']:.0f} ms, Max: {stats['load_time_ms']['max']:.0f} ms</div>
                                </div>
                    """
                
                # Add DOM ready time
                if 'dom_ready_time_ms' in stats:
                    html += f"""
                                <div class="stat-box">
                                    <div>DOM Ready</div>
                                    <div style="font-size: 24px; font-weight: bold;">{stats['dom_ready_time_ms']['avg']:.0f} ms</div>
                                    <div>Min: {stats['dom_ready_time_ms']['min']:.0f} ms, Max: {stats['dom_ready_time_ms']['max']:.0f} ms</div>
                                </div>
                    """
                
                # Add memory usage
                if 'memory_used_mb' in stats:
                    html += f"""
                                <div class="stat-box">
                                    <div>Memory Usage</div>
                                    <div style="font-size: 24px; font-weight: bold;">{stats['memory_used_mb']['avg']:.1f} MB</div>
                                    <div>Min: {stats['memory_used_mb']['min']:.1f} MB, Max: {stats['memory_used_mb']['max']:.1f} MB</div>
                                </div>
                    """
                
                # Add element count
                if 'element_count' in stats:
                    html += f"""
                                <div class="stat-box">
                                    <div>DOM Elements</div>
                                    <div style="font-size: 24px; font-weight: bold;">{stats['element_count']['avg']:.0f}</div>
                                    <div>Min: {stats['element_count']['min']:.0f}, Max: {stats['element_count']['max']:.0f}</div>
                                </div>
                    """
                
                # Add resource count
                if 'resource_count' in stats:
                    html += f"""
                                <div class="stat-box">
                                    <div>Resources</div>
                                    <div style="font-size: 24px; font-weight: bold;">{stats['resource_count']['avg']:.0f}</div>
                                    <div>Min: {stats['resource_count']['min']:.0f}, Max: {stats['resource_count']['max']:.0f}</div>
                                </div>
                    """
                
                html += """
                            </div>
                        </div>
                """
            
            html += """
                    </div>
                    
                    <div id="Performance" class="tabcontent">
                        <h2>Performance Metrics</h2>
            """
            
            # Add performance details
            if report_data.get('performance_stats'):
                html += """
                        <div class="card">
                            <h3>Performance Statistics</h3>
                            <table class="tables">
                                <tr>
                                    <th>Metric</th>
                                    <th>Average</th>
                                    <th>Minimum</th>
                                    <th>Maximum</th>
                                </tr>
                """
                
                stats = report_data['performance_stats']
                
                # Add load time
                if 'load_time_ms' in stats:
                    html += f"""
                                <tr>
                                    <td>Page Load Time</td>
                                    <td>{stats['load_time_ms']['avg']:.1f} ms</td>
                                    <td>{stats['load_time_ms']['min']:.1f} ms</td>
                                    <td>{stats['load_time_ms']['max']:.1f} ms</td>
                                </tr>
                    """
                
                # Add DOM ready time
                if 'dom_ready_time_ms' in stats:
                    html += f"""
                                <tr>
                                    <td>DOM Content Loaded</td>
                                    <td>{stats['dom_ready_time_ms']['avg']:.1f} ms</td>
                                    <td>{stats['dom_ready_time_ms']['min']:.1f} ms</td>
                                    <td>{stats['dom_ready_time_ms']['max']:.1f} ms</td>
                                </tr>
                    """
                
                # Add memory usage
                if 'memory_used_mb' in stats:
                    html += f"""
                                <tr>
                                    <td>Memory Usage</td>
                                    <td>{stats['memory_used_mb']['avg']:.1f} MB</td>
                                    <td>{stats['memory_used_mb']['min']:.1f} MB</td>
                                    <td>{stats['memory_used_mb']['max']:.1f} MB</td>
                                </tr>
                    """
                
                # Add element count
                if 'element_count' in stats:
                    html += f"""
                                <tr>
                                    <td>DOM Elements</td>
                                    <td>{stats['element_count']['avg']:.0f}</td>
                                    <td>{stats['element_count']['min']:.0f}</td>
                                    <td>{stats['element_count']['max']:.0f}</td>
                                </tr>
                    """
                
                # Add resource count
                if 'resource_count' in stats:
                    html += f"""
                                <tr>
                                    <td>Resource Count</td>
                                    <td>{stats['resource_count']['avg']:.0f}</td>
                                    <td>{stats['resource_count']['min']:.0f}</td>
                                    <td>{stats['resource_count']['max']:.0f}</td>
                                </tr>
                    """
                
                html += """
                            </table>
                        </div>
                """
            else:
                html += """
                        <div class="card">
                            <p>No performance metrics available.</p>
                        </div>
                """
            
            html += """
                    </div>
                    
                    <div id="Artifacts" class="tabcontent">
                        <h2>Collected Artifacts</h2>
            """
            
            # Add artifacts by type
            artifacts_by_type = report_data.get('artifacts_by_type', {})
            for artifact_type, artifacts in artifacts_by_type.items():
                if not artifacts:
                    continue
                
                html += f"""
                        <div class="artifact-group card">
                            <h3>{artifact_type.replace('_', ' ').title()} ({len(artifacts)})</h3>
                            <table class="tables">
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Page ID</th>
                                    <th>File Path</th>
                                </tr>
                """
                
                for artifact in artifacts:
                    timestamp_str = datetime.fromtimestamp(artifact.get('timestamp', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S') if artifact.get('timestamp') else 'Unknown'
                    
                    html += f"""
                                <tr>
                                    <td>{timestamp_str}</td>
                                    <td>{artifact.get('page_id', 'Unknown')}</td>
                                    <td>{artifact.get('path', 'N/A')}</td>
                                </tr>
                    """
                
                html += """
                            </table>
                        </div>
                """
            
            html += """
                    </div>
                    
                    <div id="Events" class="tabcontent">
                        <h2>Session Events</h2>
            """
            
            # Add events
            events = report_data.get('events', [])
            if events:
                html += """
                        <div class="card">
                            <table class="tables">
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Type</th>
                                    <th>Page ID</th>
                                    <th>Details</th>
                                </tr>
                """
                
                for event in events:
                    html += f"""
                                <tr>
                                    <td>{event.get('timestamp', 'Unknown')}</td>
                                    <td>{event.get('type', 'Unknown').replace('_', ' ').title()}</td>
                                    <td>{event.get('page_id', 'N/A')}</td>
                                    <td>
                    """
                    
                    # Add event details
                    for key, value in event.items():
                        if key not in ['timestamp', 'type', 'page_id']:
                            html += f"<strong>{key}:</strong> {value}<br>"
                    
                    html += """
                                    </td>
                                </tr>
                    """
                
                html += """
                            </table>
                        </div>
                """
            else:
                html += """
                        <div class="card">
                            <p>No session events recorded.</p>
                        </div>
                """
            
            html += """
                    </div>
                    
                    <div id="Screenshots" class="tabcontent">
                        <h2>Screenshots</h2>
            """
            
            # Add screenshots
            screenshots = artifacts_by_type.get('screenshot', [])
            if screenshots:
                html += """
                        <div class="card">
                            <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                """
                
                for screenshot in screenshots:
                    if 'path' in screenshot:
                        timestamp_str = datetime.fromtimestamp(screenshot.get('timestamp', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S') if screenshot.get('timestamp') else 'Unknown'
                        
                        # Read the image as base64
                        try:
                            with open(screenshot['path'], 'rb') as img_file:
                                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                            
                            html += f"""
                                <div style="width: 300px; margin-bottom: 20px;">
                                    <img src="data:image/png;base64,{img_data}" class="screenshot" />
                                    <div>Page: {screenshot.get('page_id', 'Unknown')}</div>
                                    <div>Time: {timestamp_str}</div>
                                </div>
                            """
                        except Exception as e:
                            logger.error(f"Error loading screenshot {screenshot['path']}: {str(e)}")
                
                html += """
                            </div>
                        </div>
                """
            else:
                html += """
                        <div class="card">
                            <p>No screenshots available.</p>
                        </div>
                """
            
            html += """
                    </div>
                </div>
                
                <script>
                    function openTab(evt, tabName) {
                        var i, tabcontent, tablinks;
                        tabcontent = document.getElementsByClassName("tabcontent");
                        for (i = 0; i < tabcontent.length; i++) {
                            tabcontent[i].style.display = "none";
                        }
                        tablinks = document.getElementsByClassName("tablinks");
                        for (i = 0; i < tablinks.length; i++) {
                            tablinks[i].className = tablinks[i].className.replace(" active", "");
                        }
                        document.getElementById(tabName).style.display = "block";
                        evt.currentTarget.className += " active";
                    }
                </script>
            </body>
            </html>
            """
            
            # Write HTML to file
            with open(html_path, 'w') as f:
                f.write(html)
            
            return html_path
        except Exception as e:
            logger.error(f"Error creating HTML report: {str(e)}")
            return None
    
    async def get_all_sessions(self):
        """
        Get all diagnostic sessions.
        
        Returns:
            Dict with session information
        """
        # Create a summary of sessions
        sessions_summary = []
        for session_id, session in self.diagnostic_sessions.items():
            # Calculate artifact counts by type
            artifact_counts = {}
            for artifact in session.get('artifacts', []):
                artifact_type = artifact.get('type', 'unknown')
                artifact_counts[artifact_type] = artifact_counts.get(artifact_type, 0) + 1
            
            # Add session summary
            sessions_summary.append({
                "id": session_id,
                "name": session.get('name'),
                "description": session.get('description'),
                "created_at": session.get('created_at'),
                "artifact_count": len(session.get('artifacts', [])),
                "artifact_counts_by_type": artifact_counts,
                "event_count": len(session.get('events', [])),
                "is_active": session_id == self.active_session_id
            })
        
        # Sort by creation time (newest first)
        sessions_summary.sort(key=lambda s: s.get('created_at', ''), reverse=True)
        
        return {
            "sessions": sessions_summary,
            "active_session_id": self.active_session_id,
            "count": len(sessions_summary)
        }
    
    async def clean_up_sessions(self, older_than_days=None, session_ids=None):
        """
        Clean up old diagnostic sessions.
        
        Args:
            older_than_days: Optional days threshold for cleanup
            session_ids: Optional specific session IDs to clean up
            
        Returns:
            Dict with cleanup results
        """
        sessions_to_clean = []
        
        if session_ids:
            # Clean specific sessions
            sessions_to_clean = [s_id for s_id in session_ids if s_id in self.diagnostic_sessions]
        elif older_than_days:
            # Clean sessions older than threshold
            threshold = datetime.now() - timedelta(days=older_than_days)
            threshold_str = threshold.isoformat()
            
            sessions_to_clean = [
                s_id for s_id, session in self.diagnostic_sessions.items()
                if session.get('created_at', '') < threshold_str and s_id != self.active_session_id
            ]
        
        if not sessions_to_clean:
            return {
                "success": True,
                "message": "No sessions matched the cleanup criteria",
                "cleaned_count": 0
            }
        
        # Delete sessions
        cleaned_count = 0
        for session_id in sessions_to_clean:
            try:
                # Remove from memory
                if session_id in self.diagnostic_sessions:
                    del self.diagnostic_sessions[session_id]
                    cleaned_count += 1
                
                # Remove directory
                session_dir = self.diagnostic_dir / session_id
                if session_dir.exists():
                    import shutil
                    shutil.rmtree(session_dir)
            except Exception as e:
                logger.error(f"Error cleaning session {session_id}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} sessions",
            "cleaned_count": cleaned_count,
            "cleaned_sessions": sessions_to_clean
        }


def register_web_diagnostic_tools(mcp, browser_manager):
    """Register web diagnostic tools with the MCP server."""
    # Get references to other components for integration
    console_monitor = None
    visual_debugger = None
    error_handler = None
    
    # Try to get console monitor from browser manager
    if hasattr(browser_manager, 'console_monitor'):
        console_monitor = browser_manager.console_monitor
    
    # Try to get visual debugger and error handler from global scope
    if 'visual_debugger' in globals():
        visual_debugger = globals()['visual_debugger']
    
    if 'error_handler' in globals():
        error_handler = globals()['error_handler']
    
    # Create diagnostic toolkit instance
    diagnostic_toolkit = WebDiagnosticToolkit(
        browser_manager=browser_manager,
        console_monitor=console_monitor,
        visual_debugger=visual_debugger,
        error_handler=error_handler
    )
    
    @mcp.tool()
    async def create_diagnostic_session(name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new diagnostic session for testing and debugging.
        
        Args:
            name: Optional name for the session
            description: Optional description of the session purpose
            
        Returns:
            Dict with session information
        """
        logger.info(f"Creating diagnostic session: {name or 'Unnamed'}")
        try:
            session_id = await diagnostic_toolkit.create_diagnostic_session(name, description)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Diagnostic session created: {session_id}"
                    }
                ],
                "success": True,
                "session_id": session_id,
                "name": name or f"Diagnostic Session {session_id}"
            }
        except Exception as e:
            logger.error(f"Error creating diagnostic session: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error creating diagnostic session: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def collect_web_diagnostics(page_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect comprehensive diagnostics from a web page.
        
        Args:
            page_id: ID of the page to diagnose
            options: Optional configuration options:
                - collect_console: Whether to collect console logs (default: True)
                - collect_network: Whether to collect network requests (default: True)
                - collect_dom: Whether to collect DOM snapshot (default: True)
                - collect_visual: Whether to collect visual information (default: True)
                - collect_performance: Whether to collect performance metrics (default: True)
                - collect_errors: Whether to collect error information (default: True)
                - take_screenshot: Whether to take a screenshot (default: True)
                - session_id: Optional session ID to add diagnostics to
            
        Returns:
            Dict with diagnostic results
        """
        logger.info(f"Collecting web diagnostics for page {page_id}")
        try:
            results = await diagnostic_toolkit.collect_full_diagnostic(page_id, options)
            
            if results.get('success'):
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Collected {len(results.get('artifacts', []))} diagnostic artifacts for page {page_id}"
                        }
                    ],
                    "success": True,
                    "session_id": results.get('session_id'),
                    "page_id": page_id,
                    "artifacts_count": len(results.get('artifacts', [])),
                    "artifacts": results.get('artifacts', [])
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error collecting diagnostics: {results.get('error', 'Unknown error')}"
                        }
                    ],
                    "success": False,
                    "error": results.get('error', 'Unknown error')
                }
        except Exception as e:
            logger.error(f"Error collecting web diagnostics: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error collecting web diagnostics: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def start_performance_monitoring(page_id: str, interval_seconds: int = 5) -> Dict[str, Any]:
        """
        Start monitoring performance metrics for a web page.
        
        Args:
            page_id: ID of the page to monitor
            interval_seconds: Sampling interval in seconds (default: 5)
            
        Returns:
            Dict with monitoring status
        """
        logger.info(f"Starting performance monitoring for page {page_id}")
        try:
            success = await diagnostic_toolkit.start_performance_monitoring(page_id, interval_seconds)
            
            if success:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Performance monitoring started for page {page_id} with {interval_seconds}s interval"
                        }
                    ],
                    "success": True,
                    "page_id": page_id,
                    "interval_seconds": interval_seconds
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to start performance monitoring for page {page_id}"
                        }
                    ],
                    "success": False,
                    "error": "Page not found or monitoring already active"
                }
        except Exception as e:
            logger.error(f"Error starting performance monitoring: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error starting performance monitoring: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def stop_performance_monitoring(page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Stop performance monitoring for a page or all pages.
        
        Args:
            page_id: Optional ID of the page to stop monitoring. If None, stops all monitoring.
            
        Returns:
            Dict with stopping status
        """
        logger.info(f"Stopping performance monitoring for {'page ' + page_id if page_id else 'all pages'}")
        try:
            success = await diagnostic_toolkit.stop_performance_monitoring(page_id)
            
            if success:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Performance monitoring stopped for {'page ' + page_id if page_id else 'all pages'}"
                        }
                    ],
                    "success": True,
                    "page_id": page_id
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"No active monitoring found for page {page_id}"
                        }
                    ],
                    "success": False,
                    "error": "No active monitoring found"
                }
        except Exception as e:
            logger.error(f"Error stopping performance monitoring: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error stopping performance monitoring: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_performance_report(page_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a performance report for a page or session.
        
        Args:
            page_id: Optional ID of the page to report on
            session_id: Optional ID of the session to report on
            
        Returns:
            Dict with performance report
        """
        logger.info(f"Generating performance report for {'page ' + page_id if page_id else 'active session'}")
        try:
            report = await diagnostic_toolkit.get_performance_report(page_id, session_id)
            
            if report.get('success') != False:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Performance report generated with {report.get('sample_count', 0)} samples"
                        }
                    ],
                    "success": True,
                    "page_id": page_id,
                    "session_id": report.get('session_id'),
                    "sample_count": report.get('sample_count', 0),
                    "stats": report.get('stats', {})
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error generating performance report: {report.get('error', 'No samples found')}"
                        }
                    ],
                    "success": False,
                    "error": report.get('error', 'No samples found')
                }
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error generating performance report: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def create_web_diagnostic_report(page_id: Optional[str] = None, session_id: Optional[str] = None, include_artifacts: bool = False) -> Dict[str, Any]:
        """
        Create a comprehensive diagnostic report.
        
        Args:
            page_id: Optional page ID to focus report on
            session_id: Optional session ID (uses active session if not specified)
            include_artifacts: Whether to include full artifacts or just references
            
        Returns:
            Dict with report information
        """
        logger.info(f"Creating web diagnostic report for {'page ' + page_id if page_id else 'active session'}")
        try:
            report = await diagnostic_toolkit.create_diagnostic_report(page_id, session_id, include_artifacts)
            
            if report.get('success') != False:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Diagnostic report created successfully"
                        }
                    ],
                    "success": True,
                    "page_id": page_id,
                    "session_id": report.get('session_id'),
                    "report_path": report.get('report_path'),
                    "html_report_path": report.get('html_report_path'),
                    "artifact_counts": report.get('artifact_counts', {})
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error creating diagnostic report: {report.get('error', 'No valid session found')}"
                        }
                    ],
                    "success": False,
                    "error": report.get('error', 'No valid session found')
                }
        except Exception as e:
            logger.error(f"Error creating web diagnostic report: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error creating web diagnostic report: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def list_diagnostic_sessions() -> Dict[str, Any]:
        """
        List all diagnostic sessions.
        
        Returns:
            Dict with session information
        """
        logger.info("Listing diagnostic sessions")
        try:
            sessions = await diagnostic_toolkit.get_all_sessions()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Found {sessions.get('count', 0)} diagnostic sessions"
                    }
                ],
                "success": True,
                "sessions": sessions.get('sessions', []),
                "active_session_id": sessions.get('active_session_id')
            }
        except Exception as e:
            logger.error(f"Error listing diagnostic sessions: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error listing diagnostic sessions: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    logger.info("Web diagnostic tools registered")
    
    # Return the toolkit instance and tools
    return {
        "diagnostic_toolkit": diagnostic_toolkit,
        "create_diagnostic_session": create_diagnostic_session,
        "collect_web_diagnostics": collect_web_diagnostics,
        "start_performance_monitoring": start_performance_monitoring,
        "stop_performance_monitoring": stop_performance_monitoring,
        "get_performance_report": get_performance_report,
        "create_web_diagnostic_report": create_web_diagnostic_report,
        "list_diagnostic_sessions": list_diagnostic_sessions
    }