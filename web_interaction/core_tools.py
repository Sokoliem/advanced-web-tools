"""Core Web Interaction Tools."""

import asyncio
import logging
import os
import time
from typing import Dict, Optional, Any
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

def register_core_tools(mcp, browser_manager):
    # Set up screenshot directory if browser manager has debug screenshots enabled
    screenshot_dir = None
    if hasattr(browser_manager, 'debug_screenshots') and browser_manager.debug_screenshots:
        screenshot_dir = Path(browser_manager.screenshot_dir)
        if not screenshot_dir.exists():
            screenshot_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Core tools will save screenshots to {screenshot_dir}")
    """Register core web interaction tools with the MCP server."""
    
    @mcp.tool()
    async def navigate(url: str, page_id: Optional[str] = None, wait_until: str = "networkidle") -> Dict[str, Any]:
        """
        Navigate to a URL in a browser.
        
        Args:
            url: The URL to navigate to
            page_id: ID of the page to use (will create new if None)
            wait_until: When to consider navigation complete 
                       ('load', 'domcontentloaded', 'networkidle')
        
        Returns:
            Dict with page information
        """
        logger.info(f"Navigating to {url} (page_id: {page_id}, wait_until: {wait_until})")
        try:
            page, page_id = await browser_manager.get_page(page_id)
            
            # Validate the URL
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
                logger.info(f"Modified URL to include https://: {url}")
                
            # Navigate to the URL
            await page.goto(url, wait_until=wait_until)
            
            # Get page information
            title = await page.title()
            current_url = page.url
            
            # Take screenshot if debug screenshots are enabled
            screenshot_path = None
            if hasattr(browser_manager, 'debug_screenshots') and browser_manager.debug_screenshots:
                timestamp = int(time.time())
                screenshot_path = str(browser_manager.screenshot_dir / f"navigate_{page_id}_{timestamp}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"Saved navigation screenshot to {screenshot_path}")
            
            logger.info(f"Successfully navigated to {current_url} (Title: {title})")
            return {
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
            logger.error(f"Error navigating to {url}: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Error navigating to {url}: {str(e)}"
                    }
                ]
            }

    @mcp.tool()
    async def extract_page_content(page_id, include_html: bool = False) -> Dict[str, Any]:
        """
        Extract the content from the current page.
        
        Args:
            page_id: ID of the page to extract content from
            include_html: Whether to include the raw HTML in the response
            
        Returns:
            Dict with page content, structured data, etc.
        """
        logger.info(f"Extracting content from page {page_id} (include_html: {include_html})")
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
            
            # Extract page content
            title = await page.title()
            url = page.url
            
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
            
            # Extract structured metadata
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
                "content": [
                    {
                        "type": "text",
                        "text": f"Content extracted from {url} (Title: {title})\n\nPage contains approximately {len(text_content.split())} words."
                    }
                ],
                "url": url,
                "title": title,
                "text_content": text_content,
                "metadata": metadata
            }
            
            if include_html:
                html_content = await page.content()
                result["html"] = html_content
            
            # Take screenshot if debug screenshots are enabled
            if hasattr(browser_manager, 'debug_screenshots') and browser_manager.debug_screenshots:
                timestamp = int(time.time())
                screenshot_path = str(browser_manager.screenshot_dir / f"extract_{page_id}_{timestamp}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"Saved content extraction screenshot to {screenshot_path}")
                
                # Add visual markers to show the content being extracted
                await page.evaluate('''
                () => {
                    // Highlight the content being extracted
                    const highlightDiv = document.createElement('div');
                    highlightDiv.id = 'mcp-highlight-overlay';
                    highlightDiv.style.position = 'fixed';
                    highlightDiv.style.top = '10px';
                    highlightDiv.style.right = '10px';
                    highlightDiv.style.padding = '10px';
                    highlightDiv.style.backgroundColor = 'rgba(0, 100, 255, 0.8)';
                    highlightDiv.style.color = 'white';
                    highlightDiv.style.borderRadius = '5px';
                    highlightDiv.style.zIndex = '9999';
                    highlightDiv.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';
                    highlightDiv.textContent = 'MCP Content Extraction Active';
                    document.body.appendChild(highlightDiv);
                    
                    // Remove after 5 seconds
                    setTimeout(() => {
                        document.body.removeChild(highlightDiv);
                    }, 5000);
                }
                ''')
                
                # Take another screenshot with visual markers
                await asyncio.sleep(0.5)  # Wait for the highlight to appear
                screenshot_path_marked = str(browser_manager.screenshot_dir / f"extract_highlighted_{page_id}_{timestamp}.png")
                await page.screenshot(path=screenshot_path_marked, full_page=False)
                logger.info(f"Saved highlighted extraction screenshot to {screenshot_path_marked}")
                
            logger.info(f"Successfully extracted content from {url}")
            return result
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error extracting content: {str(e)}"
                    }
                ]
            }
    
    logger.info("Core web interaction tools registered")
    return {
        "navigate": navigate,
        "extract_page_content": extract_page_content
    }
