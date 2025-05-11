"""Advanced Unified Web Interaction Tool Module.

This module provides an enhanced version of the unified web interaction tool
with additional capabilities such as session management, multi-browser support,
advanced data extraction, and more robust interaction capabilities.
"""

import asyncio
import json
import logging
import time
import re
import os
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def register_advanced_unified_tool(mcp, browser_manager):
    """Register the advanced unified web interaction tool with the MCP server."""
    
    @mcp.tool()
    async def web_interact_advanced(
        operations: List[Dict[str, Any]],
        page_id: Optional[str] = None,
        session_id: Optional[str] = None,
        browser_type: Optional[str] = None,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Perform advanced web interaction operations with enhanced capabilities.
        
        Args:
            operations: List of operations to perform sequentially
            page_id: Optional ID of an existing page to use
            session_id: Optional ID of a session to use/create
            browser_type: Browser type to use (chromium, firefox, webkit)
            debug: Whether to include debug information in the response
            
        Operation format:
            {
                "type": "operation_type",
                "params": {
                    # Operation-specific parameters
                }
            }
            
        Supported operation types:
            - session_start: Start a new browser session
            - session_end: End a browser session
            - navigate: Navigate to a URL
            - back: Navigate back in history
            - forward: Navigate forward in history
            - reload: Reload the current page
            - extract_content: Extract visible text content
            - extract_structured: Extract structured data
            - find_element: Find elements using description
            - interact: Interact with elements
            - wait: Wait for a condition
            - screenshot: Take a screenshot
            - execute_js: Execute JavaScript code
            - extract_network: Extract network requests
            - clear_cookies: Clear cookies
            
        Returns:
            Dict with operation results
        """
        # Initialize state for persistence during the entire operation
        state = {
            "page_id": page_id,
            "session_id": session_id,
            "browser_type": browser_type,
            "page": None,
            "current_url": "",
            "current_title": "",
            "found_elements": [],
            "extracted_content": "",
            "extracted_structured": None,
            "debug_log": []
        }
        
        # Add info to debug log
        def add_debug(message):
            logger.info(message)
            if debug:
                state["debug_log"].append(message)
        
        add_debug(f"Starting advanced web_interact with {len(operations)} operations")
        add_debug(f"Initial page_id: {page_id}, session_id: {session_id}, browser_type: {browser_type}")
        
        # Initialize browser and get page if not already provided
        try:
            # Ensure the browser is initialized
            await browser_manager.initialize(browser_type)
            
            # Create or get session if session_id provided
            if session_id:
                session = await browser_manager.get_session(session_id)
                if not session:
                    add_debug(f"Session {session_id} not found, creating new session")
                    state["session_id"] = await browser_manager.create_session(session_id)
                else:
                    add_debug(f"Using existing session: {session_id}")
                    state["session_id"] = session_id
            
            # Convert page_id to string if it's provided
            if state["page_id"] is not None:
                state["page_id"] = str(state["page_id"])
                add_debug(f"Ensuring page_id is string: {state['page_id']}")
            
            # Get or create page
            if state["page_id"]:
                try:
                    state["page"], state["page_id"] = await browser_manager.get_page(
                        page_id=state["page_id"],
                        session_id=state["session_id"],
                        browser_type=state["browser_type"]
                    )
                    add_debug(f"Using page with ID {state['page_id']}")
                except Exception as e:
                    add_debug(f"Error getting page with ID {state['page_id']}: {str(e)}")
                    # Create new page as fallback
                    state["page"], state["page_id"] = await browser_manager.get_page(
                        session_id=state["session_id"],
                        browser_type=state["browser_type"]
                    )
                    add_debug(f"Created new page with ID {state['page_id']} as fallback")
            else:
                state["page"], state["page_id"] = await browser_manager.get_page(
                    session_id=state["session_id"],
                    browser_type=state["browser_type"]
                )
                add_debug(f"Created new page with ID {state['page_id']}")
            
            # Execute each operation in sequence
            results = []
            for i, operation in enumerate(operations):
                operation_type = operation.get("type", "")
                params = operation.get("params", {})
                
                add_debug(f"Executing operation {i+1}: {operation_type}")
                
                try:
                    # Dispatch to appropriate operation handler
                    if operation_type == "session_start":
                        result = await handle_session_start(state, params)
                    elif operation_type == "session_end":
                        result = await handle_session_end(state, params)
                    elif operation_type == "navigate":
                        result = await handle_navigate(state, params)
                    elif operation_type == "back":
                        result = await handle_back(state, params)
                    elif operation_type == "forward":
                        result = await handle_forward(state, params)
                    elif operation_type == "reload":
                        result = await handle_reload(state, params)
                    elif operation_type == "extract_content":
                        result = await handle_extract_content(state, params)
                    elif operation_type == "extract_structured":
                        result = await handle_extract_structured(state, params)
                    elif operation_type == "find_element":
                        result = await handle_find_element(state, params)
                    elif operation_type == "interact":
                        result = await handle_interact(state, params)
                    elif operation_type == "wait":
                        result = await handle_wait(state, params)
                    elif operation_type == "screenshot":
                        result = await handle_screenshot(state, params)
                    elif operation_type == "execute_js":
                        result = await handle_execute_js(state, params)
                    elif operation_type == "extract_network":
                        result = await handle_extract_network(state, params)
                    elif operation_type == "clear_cookies":
                        result = await handle_clear_cookies(state, params)
                    else:
                        result = {
                            "success": False,
                            "error": f"Unknown operation type: {operation_type}"
                        }
                    
                    # Add operation result to results list
                    results.append({
                        "operation": operation_type,
                        "result": result
                    })
                    
                    # Wait after operation if specified
                    wait_time = params.get("wait_after", 0)
                    if wait_time > 0:
                        add_debug(f"Waiting for {wait_time} seconds after operation")
                        await asyncio.sleep(wait_time)
                        
                except Exception as e:
                    # Handle operation error
                    error_message = f"Error executing operation {operation_type}: {str(e)}"
                    logger.error(error_message)
                    results.append({
                        "operation": operation_type,
                        "result": {
                            "success": False,
                            "error": error_message
                        }
                    })
            
            # Create comprehensive response
            response = {
                "content": [
                    {
                        "type": "text",
                        "text": f"Executed {len(operations)} web interaction operations"
                    }
                ],
                "page_id": state["page_id"],
                "session_id": state["session_id"],
                "browser_type": state["browser_type"],
                "url": state["current_url"],
                "title": state["current_title"],
                "results": results
            }
            
            # Add debug log if requested
            if debug:
                response["debug_log"] = state["debug_log"]
                
            return response
            
        except Exception as e:
            # Handle overall execution error
            error_message = f"Error executing web interactions: {str(e)}"
            logger.error(error_message)
            
            # Create error response
            response = {
                "content": [
                    {
                        "type": "text",
                        "text": error_message
                    }
                ],
                "success": False,
                "error": error_message
            }
            
            # Add debug log if requested
            if debug:
                response["debug_log"] = state["debug_log"]
                
            return response
    
    # Operation handlers
    async def handle_session_start(state, params):
        """Handle session creation operation."""
        name = params.get("name", f"Session {int(time.time())}")
        
        try:
            # Create a new session
            session_id = await browser_manager.create_session(name)
            
            # Update state
            state["session_id"] = session_id
            
            return {
                "success": True,
                "session_id": session_id,
                "name": name
            }
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return {
                "success": False,
                "error": f"Error creating session: {str(e)}"
            }
    
    async def handle_session_end(state, params):
        """Handle session termination operation."""
        session_id = params.get("session_id") or state["session_id"]
        
        if not session_id:
            return {
                "success": False,
                "error": "No session ID provided or found in state"
            }
        
        try:
            # Delete the session
            result = await browser_manager.delete_session(session_id)
            
            # Clear session from state if it's the current one
            if state["session_id"] == session_id:
                state["session_id"] = None
            
            return {
                "success": result,
                "message": f"Session {session_id} {'deleted' if result else 'not found'}"
            }
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            return {
                "success": False,
                "error": f"Error ending session: {str(e)}"
            }
    
    async def handle_navigate(state, params):
        """Handle navigation operation."""
        url = params.get("url", "")
        wait_until = params.get("wait_until", "networkidle")
        timeout = params.get("timeout", 30000)
        referer = params.get("referer", None)
        
        if not url:
            return {
                "success": False,
                "error": "URL is required for navigation"
            }
            
        try:
            # Validate the URL
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
            
            # Additional navigation options
            nav_options = {
                "wait_until": wait_until,
                "timeout": timeout
            }
            
            # Add referer if provided
            if referer:
                nav_options["referer"] = referer
                
            # Navigate to the URL
            logger.info(f"Navigating to {url} (wait_until: {wait_until}, timeout: {timeout})")
            await state["page"].goto(url, **nav_options)
            
            # Update state
            state["current_url"] = state["page"].url
            state["current_title"] = await state["page"].title()
            
            # Update page metadata
            await browser_manager.update_page_metadata(
                state["page_id"],
                url=state["current_url"],
                title=state["current_title"]
            )
            
            logger.info(f"Successfully navigated to {state['current_url']} (Title: {state['current_title']})")
            
            return {
                "success": True,
                "url": state["current_url"],
                "title": state["current_title"]
            }
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return {
                "success": False,
                "error": f"Error navigating to {url}: {str(e)}"
            }
    
    async def handle_back(state, params):
        """Handle back navigation operation."""
        try:
            # Navigate back
            await state["page"].go_back()
            
            # Update state
            state["current_url"] = state["page"].url
            state["current_title"] = await state["page"].title()
            
            # Update page metadata
            await browser_manager.update_page_metadata(
                state["page_id"],
                url=state["current_url"],
                title=state["current_title"]
            )
            
            logger.info(f"Navigated back to {state['current_url']} (Title: {state['current_title']})")
            
            return {
                "success": True,
                "url": state["current_url"],
                "title": state["current_title"]
            }
        except Exception as e:
            logger.error(f"Error navigating back: {str(e)}")
            return {
                "success": False,
                "error": f"Error navigating back: {str(e)}"
            }
    
    async def handle_forward(state, params):
        """Handle forward navigation operation."""
        try:
            # Navigate forward
            await state["page"].go_forward()
            
            # Update state
            state["current_url"] = state["page"].url
            state["current_title"] = await state["page"].title()
            
            # Update page metadata
            await browser_manager.update_page_metadata(
                state["page_id"],
                url=state["current_url"],
                title=state["current_title"]
            )
            
            logger.info(f"Navigated forward to {state['current_url']} (Title: {state['current_title']})")
            
            return {
                "success": True,
                "url": state["current_url"],
                "title": state["current_title"]
            }
        except Exception as e:
            logger.error(f"Error navigating forward: {str(e)}")
            return {
                "success": False,
                "error": f"Error navigating forward: {str(e)}"
            }
    
    async def handle_reload(state, params):
        """Handle page reload operation."""
        wait_until = params.get("wait_until", "load")
        timeout = params.get("timeout", 30000)
        
        try:
            # Reload page
            await state["page"].reload(wait_until=wait_until, timeout=timeout)
            
            # Update state
            state["current_url"] = state["page"].url
            state["current_title"] = await state["page"].title()
            
            # Update page metadata
            await browser_manager.update_page_metadata(
                state["page_id"],
                url=state["current_url"],
                title=state["current_title"]
            )
            
            logger.info(f"Reloaded page {state['current_url']} (Title: {state['current_title']})")
            
            return {
                "success": True,
                "url": state["current_url"],
                "title": state["current_title"]
            }
        except Exception as e:
            logger.error(f"Error reloading page: {str(e)}")
            return {
                "success": False,
                "error": f"Error reloading page: {str(e)}"
            }
    
    async def handle_extract_content(state, params):
        """Handle content extraction operation."""
        include_html = params.get("include_html", False)
        include_images = params.get("include_images", False)
        include_links = params.get("include_links", True)
        include_metadata = params.get("include_metadata", True)
        selector = params.get("selector", None)
        max_length = params.get("max_length", 0)
        
        try:
            # Prepare content extraction script
            extract_script = """
            () => {
                // Helper function to check visibility
                function isVisible(el) {
                    if (!el) return false;
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && 
                           style.visibility !== 'hidden' && 
                           el.offsetWidth > 0 && 
                           el.offsetHeight > 0;
                }
                
                // Extract metadata
                const metadata = {};
                const metaTags = document.querySelectorAll('meta');
                metaTags.forEach(tag => {
                    const name = tag.getAttribute('name') || tag.getAttribute('property');
                    const content = tag.getAttribute('content');
                    if (name && content) {
                        metadata[name] = content;
                    }
                });
                
                // Get JSON-LD data
                const jsonldScripts = document.querySelectorAll('script[type="application/ld+json"]');
                metadata.jsonld = Array.from(jsonldScripts).map(script => {
                    try {
                        return JSON.parse(script.textContent);
                    } catch(e) {
                        return null;
                    }
                }).filter(Boolean);
                
                // Extract images if requested
                let images = [];
                if (INCLUDE_IMAGES) {
                    const imgElements = document.querySelectorAll('img');
                    imgElements.forEach(img => {
                        if (isVisible(img) && img.src && !img.src.startsWith('data:')) {
                            images.push({
                                src: img.src,
                                alt: img.alt || '',
                                width: img.width,
                                height: img.height
                            });
                        }
                    });
                }
                
                // Extract links if requested
                let links = [];
                if (INCLUDE_LINKS) {
                    const linkElements = document.querySelectorAll('a');
                    linkElements.forEach(link => {
                        if (isVisible(link) && link.href) {
                            links.push({
                                url: link.href,
                                text: link.textContent.trim(),
                                title: link.title || ''
                            });
                        }
                    });
                }
                
                // Extract text content
                let targetElement = document;
                if (SELECTOR) {
                    targetElement = document.querySelector(SELECTOR);
                    if (!targetElement) {
                        targetElement = document;
                    }
                }
                
                // Extract text from target element
                const textNodes = [];
                const walker = document.createTreeWalker(
                    targetElement,
                    NodeFilter.SHOW_TEXT,
                    {
                        acceptNode: function(node) {
                            const parent = node.parentElement;
                            if (!parent) return NodeFilter.FILTER_REJECT;
                            
                            // Skip script and style tags
                            if (parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE') {
                                return NodeFilter.FILTER_REJECT;
                            }
                            
                            // Only include visible text
                            if (!isVisible(parent)) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            
                            // Skip empty text
                            if (node.textContent.trim() === '') {
                                return NodeFilter.FILTER_REJECT;
                            }
                            
                            return NodeFilter.FILTER_ACCEPT;
                        }
                    }
                );
                
                let node;
                while(node = walker.nextNode()) {
                    textNodes.push(node.textContent.trim());
                }
                
                // Join text nodes with newlines
                let textContent = textNodes.join('\\n');
                
                // Truncate if requested
                if (MAX_LENGTH > 0 && textContent.length > MAX_LENGTH) {
                    textContent = textContent.substring(0, MAX_LENGTH) + '...';
                }
                
                // Return results
                return {
                    text: textContent,
                    metadata: INCLUDE_METADATA ? metadata : null,
                    images: images,
                    links: links
                };
            }
            """
            
            # Replace placeholders with parameter values
            extract_script = extract_script.replace("INCLUDE_IMAGES", "true" if include_images else "false")
            extract_script = extract_script.replace("INCLUDE_LINKS", "true" if include_links else "false")
            extract_script = extract_script.replace("INCLUDE_METADATA", "true" if include_metadata else "false")
            extract_script = extract_script.replace("SELECTOR", f"'{selector}'" if selector else "null")
            extract_script = extract_script.replace("MAX_LENGTH", str(max_length))
            
            # Execute the script
            extraction_result = await state["page"].evaluate(extract_script)
            
            # Update state
            state["extracted_content"] = extraction_result["text"]
            
            # Prepare response
            result = {
                "success": True,
                "url": state["current_url"],
                "title": state["current_title"],
                "text_content": extraction_result["text"],
                "word_count": len(extraction_result["text"].split()),
            }
            
            # Add additional data if requested
            if include_metadata:
                result["metadata"] = extraction_result["metadata"]
            
            if include_images:
                result["images"] = extraction_result["images"]
            
            if include_links:
                result["links"] = extraction_result["links"]
                
            if include_html:
                html_content = await state["page"].content()
                result["html"] = html_content
                
            logger.info(f"Successfully extracted content from {state['current_url']}")
            return result
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return {
                "success": False,
                "error": f"Error extracting content: {str(e)}"
            }
    
    async def handle_extract_structured(state, params):
        """Handle structured data extraction operation."""
        data_type = params.get("data_type", "auto")
        selector = params.get("selector", None)
        
        try:
            # Get page HTML
            html_content = await state["page"].content()
            
            # Import BeautifulSoup for HTML parsing
            from bs4 import BeautifulSoup
            
            # Use BeautifulSoup for parsing
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Apply selector if provided
            if selector:
                target_element = soup.select_one(selector)
                if target_element:
                    # Create a new soup with just this element
                    new_soup = BeautifulSoup("<html><body></body></html>", 'lxml')
                    new_soup.body.append(target_element)
                    soup = new_soup
            
            # Extract JSON-LD data
            jsonld_data = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    jsonld_data.append(json.loads(script.string))
                except Exception as e:
                    logger.debug(f"Error parsing JSON-LD: {str(e)}")
                    pass
            
            # Initialize results structure
            structured_data = {
                "type": "unknown",
                "data": {},
                "metadata": {},
                "jsonld": jsonld_data
            }
            
            # Auto-detect data type if not specified
            if data_type == "auto":
                # Detect type based on page structure and meta tags
                if soup.find('div', class_=lambda c: c and ('product' in c.lower())):
                    data_type = "product"
                elif soup.find('article') or soup.find('div', class_=lambda c: c and ('article' in c.lower() or 'post' in c.lower())):
                    data_type = "article"
                elif soup.find('table') or soup.find('div', class_=lambda c: c and ('table' in c.lower())):
                    data_type = "table"
                elif soup.find('ul', class_=lambda c: c and ('list' in c.lower() or 'results' in c.lower())):
                    data_type = "list"
                elif soup.find('form'):
                    data_type = "form"
                else:
                    # Try to infer from JSON-LD
                    if jsonld_data:
                        for item in jsonld_data:
                            if '@type' in item:
                                item_type = item['@type']
                                if isinstance(item_type, str):
                                    if 'Product' in item_type:
                                        data_type = "product"
                                    elif 'Article' in item_type or 'BlogPosting' in item_type:
                                        data_type = "article"
                                elif isinstance(item_type, list):
                                    if 'Product' in item_type:
                                        data_type = "product"
                                    elif 'Article' in item_type or 'BlogPosting' in item_type:
                                        data_type = "article"
            
            logger.info(f"Detected data type: {data_type}")
            
            # Extract data based on type
            if data_type == "product":
                # Extract product information
                product_data = extract_product_data(soup)
                structured_data["type"] = "product"
                structured_data["data"] = product_data
                
            elif data_type == "article":
                # Extract article information
                article_data = extract_article_data(soup)
                structured_data["type"] = "article"
                structured_data["data"] = article_data
                
            elif data_type == "table":
                # Extract table data
                table_data = extract_table_data(soup)
                structured_data["type"] = "table"
                structured_data["data"] = table_data
                
            elif data_type == "list":
                # Extract list data
                list_data = extract_list_data(soup)
                structured_data["type"] = "list"
                structured_data["data"] = list_data
                
            elif data_type == "form":
                # Extract form data
                form_data = extract_form_data(soup)
                structured_data["type"] = "form"
                structured_data["data"] = form_data
            
            # Extract page metadata
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                name = tag.get('name') or tag.get('property')
                content = tag.get('content')
                if name and content:
                    structured_data["metadata"][name] = content
            
            # Update state
            state["extracted_structured"] = structured_data
            
            logger.info(f"Successfully extracted structured data of type '{data_type}'")
            return {
                "success": True,
                "data_type": data_type,
                "structured_data": structured_data
            }
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return {
                "success": False,
                "error": f"Error extracting structured data: {str(e)}"
            }
    
    async def handle_find_element(state, params):
        """Handle element finding operation."""
        description = params.get("description", "")
        selector = params.get("selector", None)
        limit = params.get("limit", 5)
        
        # Log the parameters
        add_debug = state.get("add_debug", lambda msg: logger.debug(msg))
        add_debug(f"Finding elements with description='{description}', selector='{selector}', limit={limit}")
        
        if not description and not selector:
            add_debug("Both description and selector are empty")
            return {
                "success": False,
                "error": "Either element description or selector is required for finding elements"
            }
            
        try:
            found_elements = []
            
            # If selector is provided, use it directly
            if selector:
                add_debug(f"Using provided selector: {selector}")
                try:
                    elements = await state["page"].query_selector_all(selector)
                    add_debug(f"Found {len(elements)} elements with selector {selector}")
                    
                    for element in elements:
                        # Get element attributes
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        text_content = await element.evaluate("el => el.textContent.trim()")
                        is_visible = await element.is_visible()
                        
                        if is_visible:
                            # Get element position
                            bounding_box = await element.bounding_box()
                            
                            element_info = {
                                "tag": tag_name,
                                "text": text_content[:100] + ("..." if len(text_content) > 100 else ""),
                                "selector": selector,
                                "position": bounding_box,
                                "score": 1.0  # Direct selector match gets highest score
                            }
                            found_elements.append(element_info)
                            add_debug(f"Added visible {tag_name} element with text: {text_content[:30]}...")
                except Exception as selector_error:
                    add_debug(f"Selector error for '{selector}': {str(selector_error)}")
                    logger.debug(f"Selector error for '{selector}': {str(selector_error)}")
            
            # If description is provided, generate selectors based on it
            if description and len(found_elements) < limit:
                add_debug(f"Generating selectors from description: {description}")
                # Generate selectors based on the description
                selectors = generate_selectors(description)
                add_debug(f"Generated {len(selectors)} selectors from description")
                
                # Find matching elements
                found_selectors = []
                for selector in selectors:
                    # Skip if we already have enough elements
                    if len(found_elements) >= limit:
                        break
                        
                    try:
                        elements = await state["page"].query_selector_all(selector)
                        
                        if elements and len(elements) > 0:
                            add_debug(f"Selector '{selector}' matched {len(elements)} elements")
                            found_selectors.append(selector)
                        
                        for element in elements:
                            # Skip if we already have enough elements
                            if len(found_elements) >= limit:
                                break
                                
                            # Get element attributes
                            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                            text_content = await element.evaluate("el => el.textContent.trim()")
                            is_visible = await element.is_visible()
                            
                            if is_visible and not any(e["text"] == text_content and e["tag"] == tag_name for e in found_elements):
                                # Get element position
                                bounding_box = await element.bounding_box()
                                
                                # Calculate relevance score
                                score = calculate_relevance_score(description, tag_name, text_content)
                                
                                element_info = {
                                    "tag": tag_name,
                                    "text": text_content[:100] + ("..." if len(text_content) > 100 else ""),
                                    "selector": selector,
                                    "position": bounding_box,
                                    "score": score
                                }
                                found_elements.append(element_info)
                                add_debug(f"Added {tag_name} with score {score:.2f}, text: {text_content[:30]}...")
                    except Exception as selector_error:
                        # Skip selectors that cause errors
                        add_debug(f"Selector error for '{selector}': {str(selector_error)}")
                        logger.debug(f"Selector error for '{selector}': {str(selector_error)}")
                        continue
                
                # Log successful selectors
                if found_selectors:
                    add_debug(f"Successfully matched selectors: {found_selectors[:5]}")
            
            # Sort by relevance score and limit to requested number
            found_elements.sort(key=lambda x: x.get("score", 0), reverse=True)
            top_elements = found_elements[:limit]
            
            # Update state
            state["found_elements"] = top_elements
            
            if len(top_elements) > 0:
                add_debug(f"Found {len(top_elements)} elements matching '{description or selector}'")
                logger.info(f"Found {len(top_elements)} elements matching '{description or selector}'")
                return {
                    "success": True,
                    "found_count": len(top_elements),
                    "elements": top_elements
                }
            else:
                add_debug(f"No elements found matching '{description or selector}'")
                return {
                    "success": False,
                    "error": f"No elements found matching '{description or selector}'",
                    "found_count": 0,
                    "elements": []
                }
        except Exception as e:
            error_msg = f"Error finding elements: {str(e)}"
            add_debug(error_msg)
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    async def handle_interact(state, params):
        """Handle element interaction operation."""
        action = params.get("action", "")
        element_index = params.get("element_index", 0)
        selector = params.get("selector", None)
        text_input = params.get("text", "")
        force = params.get("force", False)
        highlight = params.get("highlight", True)
        
        # Log parameters for debugging
        add_debug = state.get("add_debug", lambda msg: logger.debug(msg))
        add_debug(f"Interacting with action='{action}', element_index={element_index}, selector='{selector}', text='{text_input}'")
        
        if not action:
            add_debug("No action specified")
            return {
                "success": False,
                "error": "Action is required for interaction"
            }
        
        # Find element to interact with
        target_element = None
        target_selector = None
        
        # If selector is provided, use it directly
        if selector:
            add_debug(f"Using provided selector: {selector}")
            try:
                target_element = await state["page"].query_selector(selector)
                if not target_element:
                    add_debug(f"Element not found with selector: {selector}")
                    return {
                        "success": False,
                        "error": f"Element not found with selector: {selector}"
                    }
                target_selector = selector
                add_debug(f"Found element with selector: {selector}")
            except Exception as e:
                error_msg = f"Error finding element with selector '{selector}': {str(e)}"
                add_debug(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        # Otherwise use previously found elements
        elif state["found_elements"]:
            # Convert element_index to integer if it's a string
            if isinstance(element_index, str):
                if element_index.isdigit():
                    element_index = int(element_index)
                    add_debug(f"Converted element_index string '{element_index}' to integer")
                else:
                    # Try to find an element with matching text
                    for i, element in enumerate(state["found_elements"]):
                        if element_index.lower() in element.get("text", "").lower():
                            add_debug(f"Found element at index {i} with text matching '{element_index}'")
                            element_index = i
                            break
                    else:
                        # If no matching element found, default to first element
                        add_debug(f"No element with text matching '{element_index}' found, using index 0")
                        element_index = 0
            
            # Get the element to interact with
            if element_index >= len(state["found_elements"]):
                # If requested index is out of bounds, default to the first element
                add_debug(f"Requested element index {element_index} is out of bounds. Using element 0 instead.")
                logger.warning(f"Requested element index {element_index} is out of bounds. Using element 0 instead.")
                element_index = 0
            
            # Get the selector from found elements
            if state["found_elements"] and len(state["found_elements"]) > element_index:    
                target_selector = state["found_elements"][element_index].get("selector", "")
                add_debug(f"Using selector '{target_selector}' from found element at index {element_index}")
                
                try:
                    target_element = await state["page"].query_selector(target_selector)
                    if not target_element:
                        add_debug(f"Element not found with selector: {target_selector}")
                        return {
                            "success": False,
                            "error": f"Element not found with selector: {target_selector}",
                            "element_info": state["found_elements"][element_index]
                        }
                    add_debug(f"Found element with selector: {target_selector}")
                except Exception as e:
                    error_msg = f"Error finding element with selector '{target_selector}': {str(e)}"
                    add_debug(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "element_info": state["found_elements"][element_index]
                    }
            else:
                add_debug("No found elements available")
        
        # If no element found after all attempts, return error
        if not target_element:
            add_debug("No element found to interact with")
            return {
                "success": False,
                "error": "No element found to interact with. Provide a selector or find elements first."
            }
        
        try:
            # Highlight element if requested
            if highlight and target_selector:
                add_debug(f"Highlighting element with selector: {target_selector}")
                await browser_manager.highlight_element(state["page"], target_selector)
            
            # Perform the requested action
            action_result = ""
            
            # Ensure element is visible and scrolled into view
            add_debug("Scrolling element into view")
            await target_element.scroll_into_view_if_needed()
            
            # Interaction options
            options = {}
            if force:
                options["force"] = True
                add_debug("Using force option for interaction")
            
            if action.lower() == "click":
                add_debug("Performing click action")
                await target_element.click(**options)
                action_result = f"Clicked on element"
                
                # Update state after click (URL might have changed)
                await asyncio.sleep(0.5)  # Wait for potential navigation
                state["current_url"] = state["page"].url
                state["current_title"] = await state["page"].title()
                add_debug(f"After click: URL={state['current_url']}, Title={state['current_title']}")
                
                # Update page metadata
                await browser_manager.update_page_metadata(
                    state["page_id"],
                    url=state["current_url"],
                    title=state["current_title"]
                )
                
            elif action.lower() == "dblclick":
                add_debug("Performing double-click action")
                await target_element.dblclick(**options)
                action_result = f"Double-clicked on element"
                
            elif action.lower() == "type" and text_input:
                add_debug(f"Typing text: '{text_input}'")
                await target_element.click()
                await target_element.fill(text_input)
                action_result = f"Typed '{text_input}' into element"
                
            elif action.lower() == "select" and text_input:
                # Handle dropdown selection
                add_debug(f"Selecting option: '{text_input}'")
                try:
                    await target_element.select_option(label=text_input)
                    action_result = f"Selected '{text_input}' from element"
                except Exception as select_err:
                    # Try selecting by value if label selection fails
                    try:
                        add_debug(f"Label selection failed, trying value selection")
                        await target_element.select_option(value=text_input)
                        action_result = f"Selected value '{text_input}' from element"
                    except Exception as value_err:
                        raise Exception(f"Failed to select option: {str(select_err)}. Value selection failed: {str(value_err)}")
                
            elif action.lower() == "hover":
                add_debug("Performing hover action")
                await target_element.hover()
                action_result = f"Hovered over element"
                
            elif action.lower() == "focus":
                add_debug("Performing focus action")
                await target_element.focus()
                action_result = f"Focused on element"
                
            elif action.lower() == "clear":
                add_debug("Clearing element content")
                await target_element.fill("")
                action_result = f"Cleared element content"
                
            elif action.lower() == "check":
                add_debug("Checking checkbox element")
                await target_element.check()
                action_result = f"Checked element"
                
            elif action.lower() == "uncheck":
                add_debug("Unchecking checkbox element")
                await target_element.uncheck()
                action_result = f"Unchecked element"
                
            elif action.lower() == "screenshot":
                # Take a screenshot of the element
                add_debug(f"Taking screenshot of element with selector: {target_selector}")
                screenshot_path = await browser_manager.take_screenshot(
                    state["page_id"],
                    False,
                    target_selector
                )
                
                if screenshot_path:
                    action_result = f"Took screenshot of element, saved to {screenshot_path}"
                    add_debug(action_result)
                else:
                    return {
                        "success": False,
                        "error": "Failed to take screenshot of element"
                    }
                
            else:
                error_msg = f"Unsupported action: {action}"
                add_debug(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            
            add_debug(f"Action completed: {action_result}")
            logger.info(f"{action_result} - Current page: {state['current_title']} ({state['current_url']})")
            return {
                "success": True,
                "action_performed": action,
                "result": action_result,
                "selector_used": target_selector,
                "url_after": state["current_url"],
                "title_after": state["current_title"]
            }
        except Exception as e:
            error_msg = f"Error during interaction: {str(e)}"
            add_debug(error_msg)
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "action": action,
                "selector": target_selector
            }
    
    async def handle_wait(state, params):
        """Handle wait operation."""
        wait_type = params.get("wait_type", "timeout")
        timeout = params.get("timeout", 30000)
        selector = params.get("selector", None)
        navigation = params.get("navigation", False)
        condition = params.get("condition", None)
        
        try:
            result = None
            
            if wait_type == "timeout":
                # Simple timeout
                await asyncio.sleep(timeout / 1000)
                result = {
                    "success": True,
                    "waited_for": f"timeout of {timeout}ms"
                }
                
            elif wait_type == "selector" and selector:
                # Wait for selector to appear
                try:
                    await state["page"].wait_for_selector(selector, timeout=timeout)
                    result = {
                        "success": True,
                        "waited_for": f"selector '{selector}'"
                    }
                except Exception as e:
                    result = {
                        "success": False,
                        "error": f"Timeout waiting for selector '{selector}': {str(e)}"
                    }
                
            elif wait_type == "navigation" or navigation:
                # Wait for navigation to complete
                try:
                    await state["page"].wait_for_navigation(timeout=timeout)
                    
                    # Update state after navigation
                    state["current_url"] = state["page"].url
                    state["current_title"] = await state["page"].title()
                    
                    # Update page metadata
                    await browser_manager.update_page_metadata(
                        state["page_id"],
                        url=state["current_url"],
                        title=state["current_title"]
                    )
                    
                    result = {
                        "success": True,
                        "waited_for": "navigation",
                        "url": state["current_url"],
                        "title": state["current_title"]
                    }
                except Exception as e:
                    result = {
                        "success": False,
                        "error": f"Timeout waiting for navigation: {str(e)}"
                    }
                
            elif wait_type == "condition" and condition:
                # Wait for JavaScript condition to be true
                try:
                    await state["page"].wait_for_function(condition, timeout=timeout)
                    result = {
                        "success": True,
                        "waited_for": f"condition '{condition}'"
                    }
                except Exception as e:
                    result = {
                        "success": False,
                        "error": f"Timeout waiting for condition '{condition}': {str(e)}"
                    }
                    
            elif wait_type == "load":
                # Wait for page load state
                try:
                    await state["page"].wait_for_load_state("load", timeout=timeout)
                    result = {
                        "success": True,
                        "waited_for": "page load"
                    }
                except Exception as e:
                    result = {
                        "success": False,
                        "error": f"Timeout waiting for page load: {str(e)}"
                    }
                
            elif wait_type == "networkidle":
                # Wait for network to be idle
                try:
                    await state["page"].wait_for_load_state("networkidle", timeout=timeout)
                    result = {
                        "success": True,
                        "waited_for": "network idle"
                    }
                except Exception as e:
                    result = {
                        "success": False,
                        "error": f"Timeout waiting for network idle: {str(e)}"
                    }
            
            if not result:
                result = {
                    "success": False,
                    "error": f"Invalid wait type: {wait_type}"
                }
                
            return result
        except Exception as e:
            logger.error(f"Error during wait operation: {str(e)}")
            return {
                "success": False,
                "error": f"Error during wait operation: {str(e)}"
            }
    
    async def handle_screenshot(state, params):
        """Handle screenshot operation."""
        full_page = params.get("full_page", False)
        element_selector = params.get("selector", None)
        
        try:
            # Take screenshot
            screenshot_path = await browser_manager.take_screenshot(
                state["page_id"],
                full_page,
                element_selector
            )
            
            if screenshot_path:
                return {
                    "success": True,
                    "screenshot_path": screenshot_path,
                    "type": "element" if element_selector else "page"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to take screenshot"
                }
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return {
                "success": False,
                "error": f"Error taking screenshot: {str(e)}"
            }
    
    async def handle_execute_js(state, params):
        """Handle JavaScript execution operation."""
        code = params.get("code", "")
        args = params.get("args", [])
        
        if not code:
            return {
                "success": False,
                "error": "JavaScript code is required"
            }
            
        try:
            logger.info(f"Executing JavaScript: {code[:100]}{'...' if len(code) > 100 else ''}")
            
            # Detect return statement and modify if needed
            # This helps prevent common errors with the evaluate function
            code_has_return = re.search(r'^\s*return\s+', code.strip())
            if code_has_return:
                # Wrapped in function if code starts with return
                code = f"() => {{ {code} }}"
                logger.info(f"Wrapping code with return statement in function: {code[:100]}...")
            elif not code.strip().startswith('(') and not code.strip().startswith('function') and not code.strip().startswith('async'):
                # Wrap code in a function if it's not already wrapped
                # This helps handle multi-line code blocks
                modified_code = f"""
                () => {{
                    try {{
                        {code}
                    }} catch (e) {{
                        return {{ error: e.toString() }};
                    }}
                }}
                """
                code = modified_code
                logger.info(f"Wrapping code in function for safety: {code[:100]}...")
            
            # Execute JavaScript with more detailed error handling
            try:
                result = await state["page"].evaluate(code, *args)
                
                # Check if result is an error object
                if isinstance(result, dict) and 'error' in result:
                    return {
                        "success": False,
                        "error": f"JavaScript execution error: {result['error']}",
                        "code": code
                    }
                
                logger.info(f"JavaScript execution successful, result type: {type(result).__name__}")
                return {
                    "success": True,
                    "result": result
                }
            except Exception as ee:
                # Try evaluateHandle as fallback for more complex JS
                try:
                    logger.info("Trying evaluateHandle as fallback...")
                    handle = await state["page"].evaluateHandle(code, *args)
                    json_value = await handle.jsonValue()
                    await handle.dispose()
                    return {
                        "success": True,
                        "result": json_value
                    }
                except Exception as eee:
                    logger.error(f"Both evaluate methods failed: {str(ee)} and {str(eee)}")
                    raise Exception(f"JavaScript execution failed: {str(ee)}")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error executing JavaScript: {error_message}")
            
            # Add detailed debugging info
            if "Evaluation failed" in error_message:
                return {
                    "success": False,
                    "error": f"JavaScript evaluation failed. Check syntax or browser console for errors.",
                    "original_error": error_message,
                    "code": code
                }
            
            return {
                "success": False,
                "error": f"Error executing JavaScript: {error_message}",
                "code": code
            }
    
    async def handle_extract_network(state, params):
        """Handle network request extraction operation."""
        # Currently not implemented in the browser manager
        return {
            "success": False,
            "error": "Network request extraction not implemented yet"
        }
    
    async def handle_clear_cookies(state, params):
        """Handle cookie clearing operation."""
        try:
            # Clear cookies
            result = await browser_manager.clear_cookies(state["page_id"])
            
            return {
                "success": result,
                "message": "Cookies cleared successfully" if result else "Failed to clear cookies"
            }
        except Exception as e:
            logger.error(f"Error clearing cookies: {str(e)}")
            return {
                "success": False,
                "error": f"Error clearing cookies: {str(e)}"
            }
    
    # Helper functions for element finding
    def generate_selectors(description):
        """Generate CSS selectors based on a description."""
        description_lower = description.lower()
        
        # Common element types and their selectors
        element_types = {
            "button": ["button", "input[type='button']", "input[type='submit']", 
                       "[role='button']", "a.btn", ".button", ".btn"],
            "link": ["a", "[role='link']"],
            "input": ["input[type='text']", "input:not([type='button']):not([type='submit'])", 
                      "textarea", "[contenteditable='true']"],
            "search": ["input[type='search']", "input[placeholder*='search' i]", 
                       "input[name*='search' i]", "input[aria-label*='search' i]"],
            "menu": ["nav", "[role='navigation']", "ul.menu", ".navigation"],
            "article": ["article", ".article", ".post", "main", "[role='main']", ".content"],
            "image": ["img", "[role='img']", "svg", "figure"],
            "checkbox": ["input[type='checkbox']", "[role='checkbox']"],
            "radio": ["input[type='radio']", "[role='radio']"],
            "select": ["select", "[role='listbox']"],
            "dropdown": ["select", "[role='listbox']", ".dropdown"],
            "form": ["form", "[role='form']"],
            "header": ["header", "h1", "h2", "h3", ".header", ".heading"],
            "footer": ["footer", ".footer"],
            "sidebar": [".sidebar", "aside", "[role='complementary']"],
            "cart": [".cart", ".basket", "[aria-label*='cart' i]", "[aria-label*='basket' i]"],
            "login": ["[aria-label*='login' i]", "[aria-label*='sign in' i]", 
                      "a[href*='login' i]", "a[href*='signin' i]", ".login", ".signin"]
        }
        
        selectors = []
        
        # Add type-based selectors
        for elem_type, elem_selectors in element_types.items():
            if elem_type in description_lower:
                selectors.extend(elem_selectors)
        
        # Add selectors for keywords in the description
        # Remove element type keywords first
        type_keywords = '|'.join(element_types.keys())
        keywords_text = re.sub(f'({type_keywords})', '', description_lower).strip()
        keywords = re.sub(r'\s+', ' ', keywords_text).split()
        
        for keyword in keywords:
            # Text selectors
            selectors.append(f"*:text-matches('{keyword}', 'i')")
            selectors.append(f"*:has-text('{keyword}')")
            
            # Attribute selectors
            selectors.append(f"[aria-label*='{keyword}' i]")
            selectors.append(f"[placeholder*='{keyword}' i]")
            selectors.append(f"[title*='{keyword}' i]")
            selectors.append(f"[alt*='{keyword}' i]")
            selectors.append(f"[name*='{keyword}' i]")
            selectors.append(f"[data-testid*='{keyword}' i]")
            selectors.append(f"[id*='{keyword}' i]")
            selectors.append(f"[class*='{keyword}' i]")
        
        # Add more specific combinations of keywords
        if len(keywords) > 1:
            full_text = ' '.join(keywords)
            selectors.append(f"*:text-matches('{full_text}', 'i')")
            selectors.append(f"*:has-text('{full_text}')")
        
        # Add generic selectors
        selectors.append("body")
        
        return selectors
    
    def calculate_relevance_score(description, tag_name, text_content):
        """Calculate relevance score for an element based on description match."""
        score = 0
        description_lower = description.lower()
        text_lower = text_content.lower()
        
        # Score based on text match
        for keyword in description_lower.split():
            if keyword in text_lower:
                score += 5
                # Bonus for exact word match with word boundaries
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    score += 3
        
        # Bonus for matching multiple words
        words_matched = sum(1 for word in description_lower.split() if word in text_lower)
        if words_matched > 1:
            score += words_matched * 2
        
        # Exact phrase match gets a big bonus
        if description_lower in text_lower:
            score += 20
        
        # Score based on tag type
        element_types = {
            "button": ["button", "input"],
            "link": ["a"],
            "input": ["input", "textarea"],
            "search": ["input"],
            "menu": ["nav", "ul"],
            "article": ["article", "div", "main"],
            "image": ["img", "svg", "figure"],
            "checkbox": ["input"],
            "radio": ["input"],
            "select": ["select"],
            "form": ["form"],
            "header": ["h1", "h2", "h3", "h4", "h5", "h6", "header"],
            "footer": ["footer"],
            "sidebar": ["aside", "div"]
        }
        
        for elem_type, tags in element_types.items():
            if elem_type in description_lower and tag_name.lower() in tags:
                score += 5
                
        # Penalty for very short or very long text
        if len(text_lower) < 2:
            score -= 3
        if len(text_lower) > 200:
            score -= 5
                
        return score
    
    # Helper functions for structured data extraction
    def extract_product_data(soup):
        """Extract product information from soup."""
        product_data = {}
        
        # Try to get product name
        product_name = soup.find('h1')
        if product_name:
            product_data['name'] = product_name.get_text().strip()
        
        # Try to get price
        price_elements = soup.find_all(['span', 'div', 'p'], 
                                      class_=lambda c: c and ('price' in c.lower()))
        if price_elements:
            product_data['price'] = price_elements[0].get_text().strip()
        
        # Try to get description
        description = soup.find(['div', 'p'], 
                               class_=lambda c: c and ('description' in c.lower()))
        if description:
            product_data['description'] = description.get_text().strip()
        
        # Try to get image
        image = soup.find('img', class_=lambda c: c and ('product' in c.lower()))
        if image and image.has_attr('src'):
            product_data['image'] = image['src']
        
        # Try to get product attributes/specifications
        attributes = {}
        attr_table = soup.find('table', class_=lambda c: c and ('specifications' in c.lower() or 'attributes' in c.lower()))
        if attr_table:
            rows = attr_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    if key and value:
                        attributes[key] = value
        
        if attributes:
            product_data['attributes'] = attributes
            
        return product_data
    
    def extract_article_data(soup):
        """Extract article information from soup."""
        article_data = {}
        
        # Try to get title
        title = soup.find('h1')
        if title:
            article_data['title'] = title.get_text().strip()
        
        # Try to get author
        author = soup.find(['span', 'a', 'p'], 
                          class_=lambda c: c and ('author' in c.lower()))
        if author:
            article_data['author'] = author.get_text().strip()
        
        # Try to get date
        date = soup.find(['time', 'span', 'p'], 
                        class_=lambda c: c and ('date' in c.lower() or 'time' in c.lower()))
        if date:
            article_data['date'] = date.get_text().strip()
            # Try to get datetime attribute
            if date.has_attr('datetime'):
                article_data['datetime'] = date['datetime']
        
        # Try to get content
        content_element = soup.find(['article', 'div'], 
                                  class_=lambda c: c and ('content' in c.lower() or 'article' in c.lower()))
        if content_element:
            # Extract paragraphs
            paragraphs = content_element.find_all('p')
            article_data['content'] = "\n\n".join([p.get_text().strip() for p in paragraphs])
            
            # Extract subheadings
            subheadings = content_element.find_all(['h2', 'h3', 'h4'])
            if subheadings:
                article_data['subheadings'] = [h.get_text().strip() for h in subheadings]
            
            # Extract images
            images = content_element.find_all('img')
            if images:
                article_data['images'] = []
                for img in images:
                    if img.has_attr('src'):
                        image_info = {'src': img['src']}
                        if img.has_attr('alt'):
                            image_info['alt'] = img['alt']
                        article_data['images'].append(image_info)
        
        # Try to get categories/tags
        categories = []
        category_elements = soup.find_all(['a', 'span'], 
                                         class_=lambda c: c and ('category' in c.lower() or 'tag' in c.lower()))
        for cat in category_elements:
            cat_text = cat.get_text().strip()
            if cat_text and cat_text not in categories:
                categories.append(cat_text)
        
        if categories:
            article_data['categories'] = categories
            
        return article_data
    
    def extract_table_data(soup):
        """Extract table data from soup."""
        tables = soup.find_all('table')
        table_data = []
        
        for table in tables:
            # Get table caption if available
            caption = table.find('caption')
            table_info = {
                'caption': caption.get_text().strip() if caption else None
            }
            
            # Get headers
            headers = []
            header_row = table.find('thead')
            if header_row:
                header_cells = header_row.find_all(['th', 'td'])
                headers = [cell.get_text().strip() for cell in header_cells]
            
            # Get rows
            rows = []
            body_rows = table.find_all('tr')
            for row in body_rows:
                if row.parent.name != 'thead':  # Skip header rows
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text().strip() for cell in cells]
                    # Only add non-empty rows
                    if any(cell for cell in row_data):
                        rows.append(row_data)
            
            # Create structured table data
            table_info['headers'] = headers
            table_info['rows'] = rows
            
            # If we have headers, also create a list of objects with named keys
            if headers and rows:
                structured_rows = []
                for row in rows:
                    if len(row) >= len(headers):
                        row_obj = {}
                        for i, header in enumerate(headers):
                            row_obj[header] = row[i]
                        structured_rows.append(row_obj)
                table_info['structured_rows'] = structured_rows
            
            table_data.append(table_info)
            
        return table_data
    
    def extract_list_data(soup):
        """Extract list data from soup."""
        list_elements = soup.find_all(['ul', 'ol'])
        list_data = []
        
        for list_element in list_elements:
            # Get list heading if it exists
            heading = None
            prev_element = list_element.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if prev_element and (list_element.get('id') == prev_element.get('id') + '-list' or 
                                 abs(prev_element.sourcepos - list_element.sourcepos < 100)):
                heading = prev_element.get_text().strip()
            
            # Get list items
            items = list_element.find_all('li')
            items_text = [item.get_text().strip() for item in items]
            
            # Only include non-empty lists
            if items_text:
                list_info = {
                    'type': list_element.name,  # 'ul' or 'ol'
                    'items': items_text
                }
                
                if heading:
                    list_info['heading'] = heading
                    
                # Check if this is a nested list
                if list_element.parent and list_element.parent.name == 'li':
                    list_info['nested'] = True
                
                list_data.append(list_info)
                
        return list_data
    
    def extract_form_data(soup):
        """Extract form data from soup."""
        forms = soup.find_all('form')
        form_data = []
        
        for form in forms:
            form_info = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get').upper(),
                'fields': []
            }
            
            # Get form fields
            inputs = form.find_all(['input', 'textarea', 'select'])
            for input_field in inputs:
                field_type = input_field.get('type', 'text') if input_field.name == 'input' else input_field.name
                field_info = {
                    'name': input_field.get('name', ''),
                    'type': field_type,
                    'id': input_field.get('id', ''),
                    'required': input_field.has_attr('required'),
                    'placeholder': input_field.get('placeholder', '')
                }
                
                # Get label if available
                if input_field.has_attr('id'):
                    label = form.find('label', attrs={'for': input_field['id']})
                    if label:
                        field_info['label'] = label.get_text().strip()
                
                # Handle select options
                if input_field.name == 'select':
                    options = input_field.find_all('option')
                    field_info['options'] = [{'value': option.get('value', ''), 
                                             'text': option.get_text().strip()} 
                                            for option in options]
                
                # Handle checkboxes/radios
                if field_type in ['checkbox', 'radio']:
                    field_info['checked'] = input_field.has_attr('checked')
                
                # Add to fields list if it has a name (exclude hidden/submit if desired)
                if field_info['name'] or field_type not in ['hidden', 'submit']:
                    form_info['fields'].append(field_info)
            
            # Get submit buttons
            buttons = form.find_all(['button', 'input[type="submit"]'])
            if buttons:
                form_info['submit_buttons'] = []
                for button in buttons:
                    button_text = button.get_text().strip() if button.name == 'button' else button.get('value', '')
                    form_info['submit_buttons'].append({
                        'type': 'submit',
                        'text': button_text
                    })
            
            form_data.append(form_info)
        
        return form_data
    
    # Register browser information tool
    @mcp.tool()
    async def get_browser_info(include_pages: bool = False, include_sessions: bool = False) -> Dict[str, Any]:
        """
        Get information about the browser, pages, and sessions.
        
        Args:
            include_pages: Whether to include detailed page information
            include_sessions: Whether to include detailed session information
            
        Returns:
            Dict with browser information
        """
        try:
            if not browser_manager.initialized:
                await browser_manager.initialize()
            
            # Basic browser info
            browser_info = {
                "initialized": browser_manager.initialized,
                "browser_types": list(browser_manager.browsers.keys()) if hasattr(browser_manager, 'browsers') else ["chromium"],
                "active_pages_count": len(browser_manager.active_pages),
                "total_pages_count": len(getattr(browser_manager, 'page_metadata', {}))
            }
            
            # Add active page IDs for reference
            browser_info["active_page_ids"] = list(browser_manager.active_pages.keys())
            
            # Add sessions info if available
            if hasattr(browser_manager, 'sessions'):
                browser_info["sessions_count"] = len(browser_manager.sessions)
                
                if include_sessions:
                    if hasattr(browser_manager, 'get_session_info'):
                        sessions_info = await browser_manager.get_session_info()
                        browser_info["sessions"] = sessions_info
                    else:
                        browser_info["sessions"] = list(browser_manager.sessions.keys()) if hasattr(browser_manager, 'sessions') else []
            
            # Add detailed page info if requested
            if include_pages:
                if hasattr(browser_manager, 'get_page_info'):
                    pages_info = await browser_manager.get_page_info()
                    browser_info["pages"] = pages_info
                else:
                    # Create basic page info from active_pages
                    pages_info = {}
                    for page_id, page in browser_manager.active_pages.items():
                        try:
                            # Get basic page info
                            url = page.url
                            title = await page.title()
                            
                            pages_info[page_id] = {
                                "url": url,
                                "title": title,
                                "page_id": page_id
                            }
                        except Exception as page_error:
                            logger.error(f"Error getting page info for page {page_id}: {str(page_error)}")
                            pages_info[page_id] = {
                                "url": "unknown",
                                "title": "unknown",
                                "page_id": page_id,
                                "error": str(page_error)
                            }
                    
                    browser_info["pages"] = pages_info
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Browser information retrieved successfully"
                    }
                ],
                "browser_info": browser_info
            }
        except Exception as e:
            logger.error(f"Error getting browser information: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting browser information: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    # Register screenshot tool
    @mcp.tool()
    async def take_browser_screenshot(page_id: str, full_page: bool = False, element_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Take a screenshot of a page or element.
        
        Args:
            page_id: ID of the page to screenshot
            full_page: Whether to capture the full page or just the viewport
            element_selector: Optional CSS selector of an element to screenshot
            
        Returns:
            Dict with screenshot information
        """
        logger.info(f"Taking screenshot of page {page_id} (full_page={full_page}, element_selector={element_selector})")
        try:
            # Validate parameters
            if page_id is None:
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
            
            # Ensure page_id is a string
            page_id = str(page_id)
            logger.info(f"Converted page_id to string: {page_id}")
            
            # Ensure boolean parameters are handled correctly
            if isinstance(full_page, str):
                if full_page.lower() == "true":
                    full_page = True
                elif full_page.lower() == "false":
                    full_page = False
                else:
                    try:
                        full_page = bool(int(full_page))
                    except ValueError:
                        full_page = False
            
            logger.info(f"Parameters validated: page_id={page_id}, full_page={full_page}, element_selector={element_selector}")
            
            # Check if the page exists
            if page_id not in browser_manager.active_pages:
                logger.warning(f"Page {page_id} not found in active_pages")
                
                # Try a fallback page if there are any active pages
                if browser_manager.active_pages:
                    fallback_page_id = next(iter(browser_manager.active_pages.keys()))
                    logger.info(f"Using fallback page: {fallback_page_id}")
                    page_id = fallback_page_id
                else:
                    # Try creating a new page as a last resort
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
            
            # If element selector is provided, validate it
            if element_selector:
                try:
                    # Try to verify the element exists before taking screenshot
                    page = browser_manager.active_pages.get(page_id)
                    element = await page.query_selector(element_selector)
                    if not element:
                        logger.warning(f"Element not found with selector: {element_selector}")
                        # Fall back to full page screenshot
                        element_selector = None
                        logger.info("Element not found - falling back to full page screenshot")
                except Exception as selector_error:
                    logger.warning(f"Error checking element selector: {str(selector_error)}")
                    # Fall back to full page screenshot
                    element_selector = None
            
            # Take the screenshot
            logger.info(f"Taking screenshot with parameters: page_id={page_id}, full_page={full_page}, element_selector={element_selector}")
            screenshot_path = await browser_manager.take_screenshot(page_id, full_page, element_selector)
            
            if screenshot_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Screenshot taken successfully"
                        }
                    ],
                    "success": True,
                    "screenshot_path": screenshot_path,
                    "page_id": page_id,
                    "type": "element" if element_selector else ("full_page" if full_page else "viewport")
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to take screenshot"
                        }
                    ],
                    "success": False,
                    "error": "Failed to take screenshot",
                    "page_id": page_id
                }
        except Exception as e:
            error_msg = f"Error taking screenshot: {str(e)}"
            logger.error(error_msg)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": error_msg
                    }
                ],
                "success": False,
                "error": error_msg,
                "page_id": page_id if page_id else "unknown"
            }
    
    logger.info("Advanced unified web interaction tool registered")
    return {
        "web_interact_advanced": web_interact_advanced,
        "get_browser_info": get_browser_info,
        "take_browser_screenshot": take_browser_screenshot
    }