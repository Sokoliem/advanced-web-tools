"""Unified Web Interaction Tool Module.

This module provides a single comprehensive tool that can perform multiple
web interaction operations in a single function call, maintaining state
throughout the entire operation sequence.
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

def register_unified_tool(mcp, browser_manager):
    """Register the unified web interaction tool with the MCP server."""
    
    @mcp.tool()
    async def web_interact(
        operations: List[Dict[str, Any]],
        page_id: Optional[str] = None,
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Perform a sequence of web interaction operations.
        
        Args:
            operations: List of operations to perform
            page_id: Optional ID of an existing page to use
            debug: Whether to include debug information in the response
            
        Operation format:
            {
                "type": "navigate" | "extract_content" | "find_element" | "interact" | "extract_structured",
                "params": {
                    # Operation-specific parameters
                }
            }
            
        Returns:
            Dict with operation results
        """
        # Initialize state for persistence during the entire operation
        state = {
            "page_id": page_id,
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
        
        add_debug(f"Starting web_interact with {len(operations)} operations")
        add_debug(f"Initial page_id: {page_id}")
        add_debug(f"Active pages before starting: {list(browser_manager.active_pages.keys())}")
        
        # Initialize browser and get page if not already provided
        try:
            # Ensure the browser is initialized
            await browser_manager.initialize()
            
            # Convert page_id to string if it's provided
            if state["page_id"] is not None:
                state["page_id"] = str(state["page_id"])
                
            # Try to get the page
            if state["page_id"] and state["page_id"] in browser_manager.active_pages:
                state["page"] = browser_manager.active_pages[state["page_id"]]
                add_debug(f"Using existing page with ID {state['page_id']}")
            elif state["page_id"]:
                # Try to get a page with this ID, even if it's not in active_pages
                # This leverages the persistent browser manager's ability to restore pages
                try:
                    state["page"], state["page_id"] = await browser_manager.get_page(state["page_id"])
                    add_debug(f"Restored page with ID {state['page_id']}")
                except Exception as e:
                    add_debug(f"Failed to restore page with ID {state['page_id']}: {str(e)}")
                    # Create a new page as fallback
                    state["page"], state["page_id"] = await browser_manager.get_page()
                    add_debug(f"Created new page with ID {state['page_id']} as fallback")
            else:
                # Create a new page
                state["page"], state["page_id"] = await browser_manager.get_page()
                add_debug(f"Created new page with ID {state['page_id']}")
                
            add_debug(f"Active pages after initialization: {list(browser_manager.active_pages.keys())}")
                
            # Execute each operation in sequence
            results = []
            for i, operation in enumerate(operations):
                operation_type = operation.get("type", "")
                params = operation.get("params", {})
                
                add_debug(f"Executing operation {i+1}: {operation_type}")
                
                try:
                    # Dispatch to appropriate operation handler
                    if operation_type == "navigate":
                        result = await handle_navigate(state, params)
                    elif operation_type == "extract_content":
                        result = await handle_extract_content(state, params)
                    elif operation_type == "find_element":
                        result = await handle_find_element(state, params)
                    elif operation_type == "interact":
                        result = await handle_interact(state, params)
                    elif operation_type == "extract_structured":
                        result = await handle_extract_structured(state, params)
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
    async def handle_navigate(state, params):
        """Handle navigation operation."""
        url = params.get("url", "")
        wait_until = params.get("wait_until", "networkidle")
        
        if not url:
            return {
                "success": False,
                "error": "URL is required for navigation"
            }
            
        try:
            # Validate the URL
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
                
            # Navigate to the URL
            logger.info(f"Navigating to {url} (wait_until: {wait_until})")
            await state["page"].goto(url, wait_until=wait_until)
            
            # Update state
            state["current_url"] = state["page"].url
            state["current_title"] = await state["page"].title()
            
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
            
    async def handle_extract_content(state, params):
        """Handle content extraction operation."""
        include_html = params.get("include_html", False)
        
        try:
            # Extract the visible text content
            text_content = await state["page"].evaluate('''() => {
                return Array.from(document.body.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, a, li, td, th, div:not(:has(*))'))
                    .filter(el => {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               el.offsetWidth > 0 && 
                               el.offsetHeight > 0 &&
                               el.textContent.trim().length > 0;
                    })
                    .map(el => el.textContent.trim())
                    .join('\\n');
            }''')
            
            # Update state
            state["extracted_content"] = text_content
            
            # Extract metadata
            metadata = await state["page"].evaluate('''() => {
                const metadata = {};
                
                // Get meta tags
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
                
                return metadata;
            }''')
            
            result = {
                "success": True,
                "url": state["current_url"],
                "title": state["current_title"],
                "text_content": text_content,
                "word_count": len(text_content.split()),
                "metadata": metadata
            }
            
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
            
    async def handle_find_element(state, params):
        """Handle element finding operation."""
        description = params.get("description", "")
        
        if not description:
            return {
                "success": False,
                "error": "Element description is required for finding elements"
            }
            
        try:
            # Generate selectors based on the description
            selectors = generate_selectors(description)
            
            # Find matching elements
            found_elements = []
            for selector in selectors:
                try:
                    elements = await state["page"].query_selector_all(selector)
                    
                    for element in elements:
                        # Get element attributes
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        text_content = await element.evaluate("el => el.textContent.trim()")
                        is_visible = await element.is_visible()
                        
                        if is_visible and not any(e["text"] == text_content and e["tag"] == tag_name for e in found_elements):
                            # Get element position
                            bounding_box = await element.bounding_box()
                            
                            element_info = {
                                "tag": tag_name,
                                "text": text_content[:100] + ("..." if len(text_content) > 100 else ""),
                                "selector": selector,
                                "position": bounding_box,
                                "score": calculate_relevance_score(description, tag_name, text_content)
                            }
                            found_elements.append(element_info)
                except Exception as selector_error:
                    # Skip selectors that cause errors
                    logger.debug(f"Selector error for '{selector}': {str(selector_error)}")
                    continue
            
            # Sort by relevance score and limit to top results
            found_elements.sort(key=lambda x: x.get("score", 0), reverse=True)
            top_elements = found_elements[:5]
            
            # Update state
            state["found_elements"] = top_elements
            
            logger.info(f"Found {len(top_elements)} elements matching '{description}'")
            return {
                "success": True,
                "found_count": len(top_elements),
                "elements": top_elements
            }
        except Exception as e:
            logger.error(f"Error finding elements: {str(e)}")
            return {
                "success": False,
                "error": f"Error finding elements: {str(e)}"
            }
            
    async def handle_interact(state, params):
        """Handle element interaction operation."""
        action = params.get("action", "")
        element_index = params.get("element_index", 0)
        text_input = params.get("text", "")
        
        if not action:
            return {
                "success": False,
                "error": "Action is required for interaction"
            }
        
        # If no elements have been found yet, run a find operation with a generic selector
        if not state["found_elements"]:
            logger.info("No elements found previously, running generic element search")
            # Try to find any interactive elements on the page
            find_result = await handle_find_element(state, {"description": "button link input"})
            if find_result.get("success") != True or not state["found_elements"]:
                return {
                    "success": False,
                    "error": "No elements found to interact with. The page might not have loaded properly."
                }
        
        try:
            # Convert element_index to integer if it's a string
            if isinstance(element_index, str) and element_index.isdigit():
                element_index = int(element_index)
            
            # Get the element to interact with
            if element_index >= len(state["found_elements"]):
                # If requested index is out of bounds, default to the first element
                logger.warning(f"Requested element index {element_index} is out of bounds. Using element 0 instead.")
                element_index = 0
                
            target_element = state["found_elements"][element_index]
            selector = target_element.get("selector", "")
            
            # Find the element on the page
            element = await state["page"].query_selector(selector)
            if not element:
                return {
                    "success": False,
                    "error": f"Element not found with selector: {selector}"
                }
                
            # Perform the requested action
            action_result = ""
            if action.lower() == "click":
                # Ensure element is visible and scrolled into view
                await element.scroll_into_view_if_needed()
                await element.click()
                action_result = f"Clicked on element"
                
                # Update state after click (URL might have changed)
                state["current_url"] = state["page"].url
                state["current_title"] = await state["page"].title()
                
            elif action.lower() == "type" and text_input:
                await element.click()
                await element.fill(text_input)
                action_result = f"Typed '{text_input}' into element"
                
            elif action.lower() == "select" and text_input:
                # Handle dropdown selection
                await element.select_option(label=text_input)
                action_result = f"Selected '{text_input}' from element"
                
            elif action.lower() == "hover":
                await element.hover()
                action_result = f"Hovered over element"
                
            elif action.lower() == "focus":
                await element.focus()
                action_result = f"Focused on element"
                
            elif action.lower() == "screenshot":
                # Take a screenshot of the element
                screenshot_path = f"element_screenshot_{state['page_id']}_{int(time.time())}.png"
                await element.screenshot(path=screenshot_path)
                action_result = f"Took screenshot of element, saved to {screenshot_path}"
                
            else:
                return {
                    "success": False,
                    "error": f"Unsupported action: {action}"
                }
            
            logger.info(f"{action_result} - Current page: {state['current_title']} ({state['current_url']})")
            return {
                "success": True,
                "action_performed": action,
                "result": action_result,
                "url_after": state["current_url"],
                "title_after": state["current_title"]
            }
        except Exception as e:
            logger.error(f"Error during interaction: {str(e)}")
            return {
                "success": False,
                "error": f"Error during interaction: {str(e)}"
            }
            
    async def handle_extract_structured(state, params):
        """Handle structured data extraction operation."""
        data_type = params.get("data_type", "auto")
        
        try:
            # Get page HTML
            html_content = await state["page"].content()
            
            # Import BeautifulSoup for HTML parsing
            from bs4 import BeautifulSoup
            
            # Use BeautifulSoup for parsing
            soup = BeautifulSoup(html_content, 'lxml')
            
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
                # Extract product information (simplified version)
                product_data = extract_product_data(soup)
                structured_data["type"] = "product"
                structured_data["data"] = product_data
                
            elif data_type == "article":
                # Extract article information (simplified version)
                article_data = extract_article_data(soup)
                structured_data["type"] = "article"
                structured_data["data"] = article_data
                
            elif data_type == "table":
                # Extract table data (simplified version)
                table_data = extract_table_data(soup)
                structured_data["type"] = "table"
                structured_data["data"] = table_data
                
            elif data_type == "list":
                # Extract list data (simplified version)
                list_data = extract_list_data(soup)
                structured_data["type"] = "list"
                structured_data["data"] = list_data
            
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
    
    # Helper functions
    def generate_selectors(description):
        """Generate a list of CSS selectors for an element description."""
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
            "image": ["img", "[role='img']", "svg", "figure"]
        }
        
        selectors = []
        
        # Add type-based selectors
        for elem_type, elem_selectors in element_types.items():
            if elem_type in description_lower:
                selectors.extend(elem_selectors)
        
        # Add selectors for keywords in the description
        keywords = re.sub(r'(button|link|input|search|menu|article|image)', '', description_lower).strip()
        keywords = re.sub(r'\s+', ' ', keywords).split()
        
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
        
        # Add generic selectors
        selectors.append("body")
        
        return selectors
        
    def calculate_relevance_score(description, tag_name, text_content):
        """Calculate relevance score for an element."""
        score = 0
        description_lower = description.lower()
        text_lower = text_content.lower()
        
        # Score based on text match
        for keyword in description_lower.split():
            if keyword in text_lower:
                score += 5
        
        # Score based on tag type
        element_types = {
            "button": ["button", "input"],
            "link": ["a"],
            "input": ["input", "textarea"],
            "search": ["input"],
            "menu": ["nav", "ul"],
            "article": ["article", "div", "main"],
            "image": ["img", "svg", "figure"]
        }
        
        for elem_type, tags in element_types.items():
            if elem_type in description_lower and tag_name in tags:
                score += 3
                
        return score
        
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
        
        # Try to get content
        content_element = soup.find(['article', 'div'], 
                                  class_=lambda c: c and ('content' in c.lower() or 'article' in c.lower()))
        if content_element:
            # Extract paragraphs
            paragraphs = content_element.find_all('p')
            article_data['content'] = "\n\n".join([p.get_text().strip() for p in paragraphs])
            
        return article_data
        
    def extract_table_data(soup):
        """Extract table data from soup."""
        tables = soup.find_all('table')
        table_data = []
        
        for table in tables:
            headers = []
            header_row = table.find('thead')
            if header_row:
                header_cells = header_row.find_all(['th', 'td'])
                headers = [cell.get_text().strip() for cell in header_cells]
            
            rows = []
            body_rows = table.find_all('tr')
            for row in body_rows:
                if row.parent.name != 'thead':  # Skip header rows
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text().strip() for cell in cells]
                    rows.append(row_data)
            
            table_data.append({
                'headers': headers,
                'rows': rows
            })
            
        return table_data
        
    def extract_list_data(soup):
        """Extract list data from soup."""
        list_elements = soup.find_all(['ul', 'ol'])
        list_data = []
        
        for list_element in list_elements:
            items = list_element.find_all('li')
            items_text = [item.get_text().strip() for item in items]
            
            # Only include non-empty lists
            if items_text:
                list_data.append(items_text)
                
        return list_data
        
    # Register additional tools for console access
    @mcp.tool()
    async def execute_console_command(page_id: str, command: str) -> Dict[str, Any]:
        """
        Execute a JavaScript command in the browser console.
        
        Args:
            page_id: ID of the page to run the command on
            command: JavaScript code to execute
            
        Returns:
            Dict with command result or error
        """
        logger.info(f"Executing console command on page {page_id}: {command}")
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
            
            # Make sure page exists
            if page_id not in browser_manager.active_pages:
                logger.error(f"Page {page_id} not found for console command execution")
                
                # Try a fallback page if there are any active pages
                if browser_manager.active_pages:
                    fallback_page_id = next(iter(browser_manager.active_pages.keys()))
                    logger.info(f"Using fallback page {fallback_page_id} instead of {page_id}")
                    page_id = fallback_page_id
                else:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Page {page_id} not found and no fallback pages available"
                            }
                        ],
                        "success": False,
                        "error": f"Page {page_id} not found and no fallback pages available"
                    }
            
            # Execute the command
            result = await browser_manager.execute_console_command(page_id, command)
            
            if result.get("success", False):
                logger.info(f"Console command executed successfully")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Console command executed successfully"
                        }
                    ],
                    "success": True,
                    "result": result.get("result")
                }
            else:
                logger.error(f"Error executing console command: {result.get('error')}")
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
            logger.error(f"Error executing console command: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing console command: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_console_logs(page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get console logs from a page or all pages.
        
        Args:
            page_id: Optional ID of a page to get logs from
            
        Returns:
            Dict with console logs
        """
        logger.info(f"Getting console logs for page {page_id if page_id else 'all'}")
        try:
            logs = await browser_manager.get_console_logs(page_id)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Retrieved {len(logs)} console log entries"
                    }
                ],
                "success": True,
                "logs": logs
            }
        except Exception as e:
            logger.error(f"Error getting console logs: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting console logs: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_page_errors(page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get JavaScript errors from a page or all pages.
        
        Args:
            page_id: Optional ID of a page to get errors from
            
        Returns:
            Dict with page errors
        """
        logger.info(f"Getting page errors for page {page_id if page_id else 'all'}")
        try:
            errors = await browser_manager.get_page_errors(page_id)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Retrieved {len(errors)} page error entries"
                    }
                ],
                "success": True,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Error getting page errors: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting page errors: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_browser_tabs() -> Dict[str, Any]:
        """
        Get detailed information about all open browser tabs.
        
        Returns:
            Dict with tab status information
        """
        logger.info("Getting browser tab status")
        try:
            tab_status = await browser_manager.get_tab_status()
            
            active_count = tab_status.get("active_tabs_count", 0)
            max_tabs = tab_status.get("max_tabs", 0)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Browser currently has {active_count}/{max_tabs} tabs open"
                    }
                ],
                "success": True,
                "tab_status": tab_status
            }
        except Exception as e:
            logger.error(f"Error getting browser tab status: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting browser tab status: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def clean_browser_tabs(force: bool = False) -> Dict[str, Any]:
        """
        Clean up browser tabs by closing inactive or least used tabs.
        
        Args:
            force: Whether to force cleanup even if under the threshold
            
        Returns:
            Dict with cleanup results
        """
        logger.info(f"Cleaning browser tabs (force={force})")
        try:
            results = await browser_manager.cleanup_tabs(force=force)
            
            original_count = results.get("original_tab_count", 0)
            current_count = results.get("current_tab_count", 0)
            closed_count = results.get("total_closed", 0)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Closed {closed_count} browser tabs (from {original_count} to {current_count})"
                    }
                ],
                "success": True,
                "cleanup_results": results
            }
        except Exception as e:
            logger.error(f"Error cleaning browser tabs: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error cleaning browser tabs: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    async def clear_browser_state() -> Dict[str, Any]:
        """
        Clear all saved browser state and close all tabs.
        Use this to reset the browser to a clean state when it opens too many tabs.
        
        Returns:
            Dict with result information
        """
        logger.info("Clearing all browser state")
        try:
            if hasattr(browser_manager, 'clear_browser_state'):
                success = await browser_manager.clear_browser_state()
            else:
                # Fallback for browser managers without the method
                for page_id in list(browser_manager.active_pages.keys()):
                    await browser_manager.close_page(page_id)
                
                # Clear page metadata if possible
                if hasattr(browser_manager, 'page_metadata'):
                    browser_manager.page_metadata = {}
                    
                # Save the empty state if possible
                if hasattr(browser_manager, '_save_state'):
                    browser_manager._save_state()
                
                success = True
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Browser state cleared successfully"
                    }
                ],
                "success": True
            }
        except Exception as e:
            logger.error(f"Error clearing browser state: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error clearing browser state: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }

    logger.info("Unified web interaction tool registered with console access and tab management")
    return {
        "web_interact": web_interact,
        "execute_console_command": execute_console_command,
        "get_console_logs": get_console_logs,
        "get_page_errors": get_page_errors,
        "get_browser_tabs": get_browser_tabs,
        "clean_browser_tabs": clean_browser_tabs,
        "clear_browser_state": clear_browser_state
    }
