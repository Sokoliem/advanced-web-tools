"""Advanced Web Interaction Tools."""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

def register_advanced_tools(mcp, browser_manager):
    """Register advanced web interaction tools with the MCP server."""
    
    async def construct_selector_for_element(page, element_info):
        """
        Construct a unique selector for an element based on available information.
        
        Args:
            page: The browser page
            element_info: Information about the element
            
        Returns:
            A CSS selector for the element
        """
        if "tag" not in element_info or not element_info["tag"]:
            return "body"  # Fallback
        
        tag = element_info["tag"]
        text = element_info.get("text", "")
        
        # First try text content
        if text:
            # Escape single quotes
            text_escaped = text.replace("'", "\\'")
            selectors = [
                f"{tag}:text('{text_escaped}')",
                f"{tag}:text-matches('{text_escaped}', 'i')",
                f"{tag}:has-text('{text_escaped}')"
            ]
            
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if len(elements) == 1:
                        return selector
                except:
                    pass
        
        # Try position-based selector as fallback
        if "position" in element_info and element_info["position"]:
            pos = element_info["position"]
            center_x = pos["x"] + pos["width"] / 2
            center_y = pos["y"] + pos["height"] / 2
            
            return f"document.elementFromPoint({center_x}, {center_y})"
        
        # Final fallback - less reliable
        return tag
    
    @mcp.tool()
    async def semantic_find(page_id, description: str) -> Dict[str, Any]:
        """
        Find elements on a page based on natural language descriptions.
        
        Args:
            page_id: ID of the page to search
            description: Natural language description of what to find
                        (e.g., "login button", "search box", "main article content")
        
        Returns:
            Dict with found elements information
        """
        logger.info(f"Searching for '{description}' on page {page_id}")
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
                
            # Debug log to see what active pages are available
            logger.info(f"Active pages: {list(browser_manager.active_pages.keys())}")
                
            page = browser_manager.active_pages.get(page_id)
            if not page:
                logger.warning(f"No active page with ID {page_id}")
                # If no page exists with this ID, create a new one and navigate to example.com
                try:
                    page, page_id = await browser_manager.get_page()
                    logger.info(f"Created new page with ID {page_id} as fallback")
                    await page.goto("https://example.com")
                    logger.info("Navigated to example.com as fallback")
                except Exception as e:
                    logger.error(f"Error creating fallback page: {str(e)}")
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Could not find or create a page with ID {page_id}. Error: {str(e)}"
                            }
                        ]
                    }
            
            # Complex logic to identify elements based on semantic understanding
            # This is a simplified version that handles common cases
            
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
            
            description_lower = description.lower()
            element_type = next((k for k in element_types if k in description_lower), None)
            
            selectors = []
            if element_type:
                selectors.extend(element_types[element_type])
            
            # Add semantic selectors based on text content and attributes
            keywords = re.sub(r'(button|link|input|search|menu|article|image)', '', description_lower).strip()
            keywords = re.sub(r'\\s+', ' ', keywords).split()
            
            for keyword in keywords:
                # Add selectors based on visible text
                selectors.append(f":is(button, a, [role='button'])[text*='{keyword}' i]")
                selectors.append(f":is(button, a, [role='button']) :text('{keyword}')")
                
                # Add selectors based on common attributes
                selectors.append(f"[aria-label*='{keyword}' i]")
                selectors.append(f"[placeholder*='{keyword}' i]")
                selectors.append(f"[title*='{keyword}' i]")
                selectors.append(f"[alt*='{keyword}' i]")
                selectors.append(f"[name*='{keyword}' i]")
            
            # Execute each selector and collect results
            found_elements = []
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        # Get element attributes
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        text_content = await element.evaluate("el => el.textContent.trim()")
                        is_visible = await element.is_visible()
                        
                        if is_visible and (tag_name not in [e["tag_name"] for e in found_elements] or 
                                          text_content not in [e["text"] for e in found_elements]):
                            
                            # Get element position
                            bounding_box = await element.bounding_box()
                            
                            element_info = {
                                "tag_name": tag_name,
                                "text": text_content[:100] + ("..." if len(text_content) > 100 else ""),
                                "selector": selector,
                                "position": bounding_box,
                                "element_handle": element
                            }
                            found_elements.append(element_info)
                except Exception as selector_error:
                    # Skip selectors that cause errors
                    logger.debug(f"Selector error for '{selector}': {str(selector_error)}")
                    pass
            
            # Sort elements by relevance (this is a simplified scoring mechanism)
            for element in found_elements:
                score = 0
                
                # Score based on text match
                for keyword in keywords:
                    if keyword in element["text"].lower():
                        score += 5
                
                # Score based on tag type
                if element_type and element["tag_name"] in "".join(element_types.get(element_type, [])):
                    score += 3
                    
                # Score based on visibility and position
                if element["position"] and element["position"]["x"] > 0 and element["position"]["y"] > 0:
                    score += 2
                    
                element["relevance_score"] = score
                
            # Sort by relevance score
            found_elements.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Limit to top 5 results
            top_results = found_elements[:5]
            
            # Create a clean result object (without element handles)
            clean_results = []
            for e in top_results:
                clean_result = {
                    "tag": e["tag_name"],
                    "text": e["text"],
                    "position": e["position"],
                    "relevance_score": e["relevance_score"]
                }
                clean_results.append(clean_result)
            
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": f"Found {len(top_results)} elements matching '{description}'"
                    }
                ],
                "elements": clean_results
            }
            
            logger.info(f"Found {len(top_results)} elements matching '{description}'")
            return result
        except Exception as e:
            logger.error(f"Error finding elements: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error finding elements: {str(e)}"
                    }
                ]
            }

    @mcp.tool()
    async def interact_with_element(
        page_id, 
        action: str, 
        element_description: str,
        text_input: Optional[str] = None,
        wait_after: int = 1
    ) -> Dict[str, Any]:
        """
        Interact with an element on the page.
        
        Args:
            page_id: ID of the page to interact with
            action: Type of interaction ('click', 'type', 'select', 'hover', 'focus', 'screenshot')
            element_description: Natural language description of the element
            text_input: Text to type if action is 'type'
            wait_after: Seconds to wait after interaction
            
        Returns:
            Dict with interaction results
        """
        logger.info(f"Interacting with '{element_description}' on page {page_id} using action '{action}'")
        try:
            # First find the element
            find_result = await semantic_find(page_id, element_description)
            if "elements" not in find_result or not find_result["elements"]:
                logger.warning(f"No elements found matching '{element_description}'")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"No elements found matching '{element_description}'"
                        }
                    ]
                }
            
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
                
            # Debug log to see what active pages are available
            logger.info(f"Interaction: Active pages: {list(browser_manager.active_pages.keys())}")
                
            page = browser_manager.active_pages.get(page_id)
            if not page:
                logger.warning(f"No active page with ID {page_id} for interaction")
                # If no page exists with this ID, use the page from the find_result
                # This should work since we just ran semantic_find successfully
                try:
                    # Create a new page as fallback
                    page, page_id = await browser_manager.get_page()
                    logger.info(f"Created new page with ID {page_id} as fallback for interaction")
                    await page.goto("https://example.com")
                    logger.info("Navigated to example.com as fallback for interaction")
                    
                    # Run semantic_find again on the new page
                    find_result = await semantic_find(page_id, element_description)
                    if "elements" not in find_result or not find_result["elements"]:
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"No elements found matching '{element_description}' on the fallback page"
                                }
                            ]
                        }
                except Exception as e:
                    logger.error(f"Error creating fallback page for interaction: {str(e)}")
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Could not find or create a page with ID {page_id} for interaction. Error: {str(e)}"
                            }
                        ]
                    }
            
            # Get the highest scored element
            top_element = find_result["elements"][0]
            
            # Get the element handle using a selector
            selector = await construct_selector_for_element(page, top_element)
            logger.info(f"Using selector: {selector}")
            
            element = await page.query_selector(selector)
            
            if not element:
                logger.warning(f"Could not locate the element on the page using selector: {selector}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Could not locate the element on the page using selector: {selector}"
                        }
                    ]
                }
            
            # Perform the requested action
            action_result = ""
            if action.lower() == "click":
                # Ensure element is visible and scrolled into view
                await element.scroll_into_view_if_needed()
                await element.click()
                action_result = f"Clicked on {element_description}"
                
            elif action.lower() == "type" and text_input:
                await element.click()
                await element.fill(text_input)
                action_result = f"Typed '{text_input}' into {element_description}"
                
            elif action.lower() == "select" and text_input:
                # Handle dropdown selection
                await element.select_option(label=text_input)
                action_result = f"Selected '{text_input}' from {element_description}"
                
            elif action.lower() == "hover":
                await element.hover()
                action_result = f"Hovered over {element_description}"
                
            elif action.lower() == "focus":
                await element.focus()
                action_result = f"Focused on {element_description}"
                
            elif action.lower() == "screenshot":
                # Take a screenshot of the element
                screenshot_path = f"element_screenshot_{page_id}_{int(time.time())}.png"
                await element.screenshot(path=screenshot_path)
                action_result = f"Took screenshot of {element_description}, saved to {screenshot_path}"
                
            else:
                logger.warning(f"Unsupported action: {action}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unsupported action: {action}"
                        }
                    ]
                }
            
            # Wait after interaction if specified
            if wait_after > 0:
                await asyncio.sleep(wait_after)
                
            # Get any page changes after interaction
            current_url = page.url
            title = await page.title()
            
            logger.info(f"{action_result} - Current page: {title} ({current_url})")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"{action_result}\nCurrent page: {title} ({current_url})"
                    }
                ],
                "action_performed": action,
                "element_description": element_description,
                "url_after": current_url,
                "title_after": title
            }
        except Exception as e:
            logger.error(f"Error during interaction: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error during interaction: {str(e)}"
                    }
                ]
            }
    
    @mcp.tool()
    async def puppeteer_click(page_id: str, selector: str) -> Dict[str, Any]:
        """
        Click on an element identified by selector.
        
        Args:
            page_id: ID of the page to interact with
            selector: CSS selector for the element
            
        Returns:
            Dict with click result
        """
        logger.info(f"Puppeteer click on selector '{selector}' on page {page_id}")
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
                
            # Get the page
            page = browser_manager.active_pages.get(page_id)
            if not page:
                logger.error(f"Page {page_id} not found for puppeteer_click")
                
                # Try a fallback page if there are any active pages
                if browser_manager.active_pages:
                    fallback_page_id = next(iter(browser_manager.active_pages.keys()))
                    logger.info(f"Using fallback page {fallback_page_id} instead of {page_id}")
                    page_id = fallback_page_id
                    page = browser_manager.active_pages[page_id]
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
            
            # Try to find the element
            try:
                element = await page.query_selector(selector)
                if not element:
                    logger.warning(f"Element not found with selector: {selector}")
                    
                    # Try to use a more flexible selector approach
                    if selector.startswith('#') or selector.startswith('.'):
                        # Try attribute contains instead of exact match
                        flexible_selector = selector.replace('#', '[id*="').replace('.', '[class*="') + '"]'
                        logger.info(f"Trying flexible selector: {flexible_selector}")
                        element = await page.query_selector(flexible_selector)
                    
                    if not element:
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error: Element not found with selector: {selector}"
                                }
                            ],
                            "success": False,
                            "error": f"Element not found with selector: {selector}"
                        }
            except Exception as selector_error:
                logger.error(f"Error with selector '{selector}': {str(selector_error)}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error with selector '{selector}': {str(selector_error)}"
                        }
                    ],
                    "success": False,
                    "error": f"Error with selector '{selector}': {str(selector_error)}"
                }
            
            # Ensure element is visible and scrolled into view
            await element.scroll_into_view_if_needed()
            
            # Take a screenshot for debugging (optional)
            await browser_manager.highlight_element(page, selector, color='red', duration=1)
            
            # Click the element
            await element.click()
            
            # Wait a moment for any page updates
            await asyncio.sleep(1)
            
            # Get current URL after clicking
            current_url = page.url
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Successfully clicked element with selector: {selector}"
                    }
                ],
                "success": True,
                "page_id": page_id,
                "url_after": current_url
            }
        except Exception as e:
            logger.error(f"Error clicking element: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error clicking element: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def puppeteer_fill(page_id: str, selector: str, text: str) -> Dict[str, Any]:
        """
        Fill text into an element identified by selector.
        
        Args:
            page_id: ID of the page to interact with
            selector: CSS selector for the element
            text: Text to fill
            
        Returns:
            Dict with fill result
        """
        logger.info(f"Puppeteer fill on selector '{selector}' with text '{text}' on page {page_id}")
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
                
            # Get the page
            page = browser_manager.active_pages.get(page_id)
            if not page:
                logger.error(f"Page {page_id} not found for puppeteer_fill")
                
                # Try a fallback page if there are any active pages
                if browser_manager.active_pages:
                    fallback_page_id = next(iter(browser_manager.active_pages.keys()))
                    logger.info(f"Using fallback page {fallback_page_id} instead of {page_id}")
                    page_id = fallback_page_id
                    page = browser_manager.active_pages[page_id]
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
            
            # Try to find the element
            try:
                element = await page.query_selector(selector)
                if not element:
                    logger.warning(f"Element not found with selector: {selector}")
                    
                    # Try to use a more flexible selector approach
                    if selector.startswith('#') or selector.startswith('.'):
                        # Try attribute contains instead of exact match
                        flexible_selector = selector.replace('#', '[id*="').replace('.', '[class*="') + '"]'
                        logger.info(f"Trying flexible selector: {flexible_selector}")
                        element = await page.query_selector(flexible_selector)
                    
                    # Try input-specific selectors if still not found
                    if not element:
                        input_selectors = [
                            f"input[placeholder*='{selector.replace('#', '').replace('.', '')}']",
                            f"input[name*='{selector.replace('#', '').replace('.', '')}']",
                            f"textarea[placeholder*='{selector.replace('#', '').replace('.', '')}']"
                        ]
                        
                        for input_selector in input_selectors:
                            logger.info(f"Trying input selector: {input_selector}")
                            element = await page.query_selector(input_selector)
                            if element:
                                break
                    
                    if not element:
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error: Element not found with selector: {selector}"
                                }
                            ],
                            "success": False,
                            "error": f"Element not found with selector: {selector}"
                        }
            except Exception as selector_error:
                logger.error(f"Error with selector '{selector}': {str(selector_error)}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error with selector '{selector}': {str(selector_error)}"
                        }
                    ],
                    "success": False,
                    "error": f"Error with selector '{selector}': {str(selector_error)}"
                }
            
            # Ensure element is visible and scrolled into view
            await element.scroll_into_view_if_needed()
            
            # Take a screenshot for debugging (optional)
            await browser_manager.highlight_element(page, selector, color='blue', duration=1)
            
            # Clear existing text and focus the element
            await element.click({
                "clickCount": 3  # Triple-click to select all text
            })
            
            # Fill the element with new text
            await element.fill(text)
            
            # Wait a moment for any page updates
            await asyncio.sleep(1)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Successfully filled element with selector: {selector}"
                    }
                ],
                "success": True,
                "page_id": page_id,
                "text": text
            }
        except Exception as e:
            logger.error(f"Error filling element: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error filling element: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    logger.info("Advanced web interaction tools registered")
    return {
        "semantic_find": semantic_find,
        "interact_with_element": interact_with_element,
        "puppeteer_click": puppeteer_click,
        "puppeteer_fill": puppeteer_fill
    }
