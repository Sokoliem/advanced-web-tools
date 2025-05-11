"""Advanced Workflow Tools for Web Interaction."""

import logging
import asyncio
from typing import Dict, List, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

def register_workflow_tools(mcp, browser_manager):
    """Register workflow tools with the MCP server."""
    
    # Get direct references to the needed tool functions
    core_navigate = None
    core_extract_content = None
    advanced_interact = None
    data_extract_structured = None
    
    @mcp.tool()
    async def run_web_workflow(
        urls: List[str], 
        actions: List[Dict[str, Any]], 
        data_extraction: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a complete workflow across multiple pages.
        
        Args:
            urls: List of starting URLs for the workflow
            actions: List of actions to perform (see format below)
            data_extraction: Optional specifications for data to extract
            
        Action format:
            {
                "type": "navigate"|"click"|"type"|"extract",
                "target": "element description" (if applicable),
                "value": "text to type" (if applicable),
                "wait_after": seconds to wait (default: 1)
            }
            
        Returns:
            Dict with workflow results and extracted data
        """
        logger.info(f"Running web workflow with {len(urls)} URLs and {len(actions)} actions")
        try:            
            # Create a new browser page for this workflow
            page, page_id = await browser_manager.get_page()
            
            workflow_results = []
            extracted_data = []
            
            # Track the current URL in the workflow
            current_url = ""
            
            # Start with the first URL
            if urls:
                logger.info(f"Starting workflow with initial URL: {urls[0]}")
                # Navigate directly using page object
                try:
                    # Validate the URL
                    url = urls[0]
                    if not url.startswith(('http://', 'https://')):
                        url = f"https://{url}"
                    
                    # Navigate to the URL
                    await page.goto(url, wait_until="networkidle")
                    
                    # Get page information
                    title = await page.title()
                    current_url = page.url
                    
                    navigate_result = {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Successfully navigated to {current_url} (Title: {title})"
                            }
                        ],
                        "page_id": page_id,
                        "url": current_url,
                        "title": title
                    }
                    
                    workflow_results.append({
                        "step": "initial_navigation",
                        "url": urls[0],
                        "result": navigate_result
                    })
                except Exception as e:
                    logger.error(f"Error navigating to {urls[0]}: {str(e)}")
                    return {
                        "content": [
                            {
                                "type": "text", 
                                "text": f"Error running workflow: Failed to navigate to {urls[0]}: {str(e)}"
                            }
                        ]
                    }
            
            # Execute each action in sequence
            for i, action in enumerate(actions):
                action_type = action.get("type", "").lower()
                target = action.get("target", "")
                value = action.get("value", "")
                wait_after = action.get("wait_after", 1)
                
                logger.info(f"Executing workflow action {i+1}: {action_type} {target} {value}")
                step_result = None
                
                if action_type == "navigate":
                    # If we need to navigate to a new URL
                    nav_url = value if value else (urls[i + 1] if i + 1 < len(urls) else "")
                    if nav_url:
                        try:
                            # Validate the URL
                            if not nav_url.startswith(('http://', 'https://')):
                                nav_url = f"https://{nav_url}"
                            
                            # Navigate to the URL
                            await page.goto(nav_url, wait_until="networkidle")
                            
                            # Get page information
                            title = await page.title()
                            current_url = page.url
                            
                            step_result = {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Successfully navigated to {current_url} (Title: {title})"
                                    }
                                ],
                                "page_id": page_id,
                                "url": current_url,
                                "title": title
                            }
                        except Exception as e:
                            logger.error(f"Error navigating to {nav_url}: {str(e)}")
                            step_result = {
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": f"Error navigating to {nav_url}: {str(e)}"
                                    }
                                ]
                            }
                
                elif action_type == "click" and target:
                    # Click on an element
                    try:
                        # Find element with the description
                        selectors = get_selectors_for_description(target)
                        element = None
                        
                        # Try each selector until we find the element
                        for selector in selectors:
                            try:
                                element = await page.query_selector(selector)
                                if element:
                                    break
                            except:
                                pass
                        
                        if element:
                            # Ensure element is visible and scrolled into view
                            await element.scroll_into_view_if_needed()
                            await element.click()
                            
                            # Get updated page information
                            title = await page.title()
                            current_url = page.url
                            
                            step_result = {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Clicked on {target}\nCurrent page: {title} ({current_url})"
                                    }
                                ],
                                "action_performed": "click",
                                "element_description": target,
                                "url_after": current_url,
                                "title_after": title
                            }
                        else:
                            step_result = {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"No elements found matching '{target}'"
                                    }
                                ]
                            }
                    except Exception as e:
                        logger.error(f"Error clicking on {target}: {str(e)}")
                        step_result = {
                            "content": [
                                {
                                    "type": "text", 
                                    "text": f"Error clicking on {target}: {str(e)}"
                                }
                            ]
                        }
                
                elif action_type == "type" and target:
                    # Type into an element
                    try:
                        # Find element with the description
                        selectors = get_selectors_for_description(target)
                        element = None
                        
                        # Try each selector until we find the element
                        for selector in selectors:
                            try:
                                element = await page.query_selector(selector)
                                if element:
                                    break
                            except:
                                pass
                        
                        if element:
                            await element.click()
                            await element.fill(value)
                            
                            step_result = {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Typed '{value}' into {target}"
                                    }
                                ],
                                "action_performed": "type",
                                "element_description": target,
                                "text_input": value
                            }
                        else:
                            step_result = {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"No elements found matching '{target}'"
                                    }
                                ]
                            }
                    except Exception as e:
                        logger.error(f"Error typing into {target}: {str(e)}")
                        step_result = {
                            "content": [
                                {
                                    "type": "text", 
                                    "text": f"Error typing into {target}: {str(e)}"
                                }
                            ]
                        }
                
                elif action_type == "extract":
                    # Extract data from the current page
                    if target == "content":
                        try:
                            # Extract the visible text content
                            text_content = await page.evaluate('''() => {
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
                            
                            # Extract metadata
                            metadata = await page.evaluate('''() => {
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
                                
                                return metadata;
                            }''')
                            
                            title = await page.title()
                            
                            step_result = {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Content extracted from {current_url} (Title: {title})\n\nPage contains approximately {len(text_content.split())} words."
                                    }
                                ],
                                "url": current_url,
                                "title": title,
                                "text_content": text_content,
                                "metadata": metadata
                            }
                            
                            extracted_data.append({
                                "url": current_url,
                                "extraction_type": "content",
                                "data": step_result
                            })
                        except Exception as e:
                            logger.error(f"Error extracting content: {str(e)}")
                            step_result = {
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": f"Error extracting content: {str(e)}"
                                    }
                                ]
                            }
                    elif target == "structured":
                        try:
                            from bs4 import BeautifulSoup
                            
                            data_type = value if value else "auto"
                            html_content = await page.content()
                            
                            # Use BeautifulSoup for parsing
                            soup = BeautifulSoup(html_content, 'lxml')
                            
                            # Extract structured data based on type (simplified version)
                            structured_data = {
                                "type": data_type,
                                "data": {},
                                "url": current_url,
                                "title": await page.title()
                            }
                            
                            step_result = {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Extracted structured data of type '{data_type}' from the page."
                                    }
                                ],
                                "data_type": data_type,
                                "structured_data": structured_data
                            }
                            
                            extracted_data.append({
                                "url": current_url,
                                "extraction_type": "structured",
                                "data": step_result
                            })
                        except Exception as e:
                            logger.error(f"Error extracting structured data: {str(e)}")
                            step_result = {
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": f"Error extracting structured data: {str(e)}"
                                    }
                                ]
                            }
                
                # Wait after interaction if specified
                if wait_after > 0:
                    await asyncio.sleep(wait_after)
                
                # Store the results of this step
                if step_result:
                    workflow_results.append({
                        "step": f"action_{i+1}",
                        "action": action,
                        "result": step_result
                    })
            
            # Close the page when done
            await page.close()
            
            logger.info(f"Workflow completed with {len(workflow_results)} steps and {len(extracted_data)} extracted data items")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Completed web workflow with {len(workflow_results)} steps and extracted data from {len(extracted_data)} pages."
                    }
                ],
                "workflow_results": workflow_results,
                "extracted_data": extracted_data
            }
        except Exception as e:
            logger.error(f"Error running web workflow: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error running web workflow: {str(e)}"
                    }
                ]
            }
    
    # Helper function for element finding
    def get_selectors_for_description(description):
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
        
        # Add selectors for other keywords in the description
        keywords = description_lower.split()
        for keyword in keywords:
            # Text selectors
            selectors.append(f"*:text-matches('{keyword}', 'i')")
            selectors.append(f"*[text*='{keyword}' i]")
            
            # Attribute selectors
            selectors.append(f"[aria-label*='{keyword}' i]")
            selectors.append(f"[placeholder*='{keyword}' i]")
            selectors.append(f"[title*='{keyword}' i]")
            selectors.append(f"[alt*='{keyword}' i]")
            selectors.append(f"[name*='{keyword}' i]")
        
        # Add selectors for ID or class that might match
        for keyword in keywords:
            selectors.append(f"#{keyword}")
            selectors.append(f".{keyword}")
            selectors.append(f"[id*='{keyword}']")
            selectors.append(f"[class*='{keyword}']")
        
        # Add the most generic selector that might catch visible text
        selectors.append("body")
        
        return selectors
    
    logger.info("Workflow tools registered")
    return {
        "run_web_workflow": run_web_workflow
    }
