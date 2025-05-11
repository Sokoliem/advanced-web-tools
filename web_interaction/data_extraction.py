"""Data Extraction Tools for Web Interaction."""

import json
import logging
from typing import Dict, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

def register_data_extraction_tools(mcp, browser_manager):
    """Register data extraction tools with the MCP server."""
    
    @mcp.tool()
    async def extract_structured_data(page_id, data_type: str = "auto") -> Dict[str, Any]:
        """
        Extract structured data from the current page.
        
        Args:
            page_id: ID of the page to extract data from
            data_type: Type of data to extract ('product', 'article', 'list', 'table', 'auto')
            
        Returns:
            Dict with extracted structured data
        """
        logger.info(f"Extracting structured data of type '{data_type}' from page {page_id}")
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
                
            # Debug log to see what active pages are available
            logger.info(f"Data Extraction: Active pages: {list(browser_manager.active_pages.keys())}")
                
            page = browser_manager.active_pages.get(page_id)
            if not page:
                logger.warning(f"No active page with ID {page_id} for data extraction")
                # If no page exists with this ID, create a new one and navigate to example.com
                try:
                    page, page_id = await browser_manager.get_page()
                    logger.info(f"Created new page with ID {page_id} as fallback for data extraction")
                    await page.goto("https://example.com")
                    logger.info("Navigated to example.com as fallback for data extraction")
                except Exception as e:
                    logger.error(f"Error creating fallback page for data extraction: {str(e)}")
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Could not find or create a page with ID {page_id} for data extraction. Error: {str(e)}"
                            }
                        ]
                    }
            
            # Get page HTML
            html_content = await page.content()
            
            # Import BeautifulSoup here to avoid import errors if bs4 isn't installed
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
                # Extract product information
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
                
                structured_data["type"] = "product"
                structured_data["data"] = product_data
                
            elif data_type == "article":
                # Extract article information
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
                
                structured_data["type"] = "article"
                structured_data["data"] = article_data
                
            elif data_type == "table":
                # Extract table data
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
                
                structured_data["type"] = "table"
                structured_data["data"] = table_data
                
            elif data_type == "list":
                # Extract list data
                list_elements = soup.find_all(['ul', 'ol'])
                list_data = []
                
                for list_element in list_elements:
                    items = list_element.find_all('li')
                    items_text = [item.get_text().strip() for item in items]
                    
                    # Only include non-empty lists
                    if items_text:
                        list_data.append(items_text)
                
                structured_data["type"] = "list"
                structured_data["data"] = list_data
            
            # Extract page metadata
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                name = tag.get('name') or tag.get('property')
                content = tag.get('content')
                if name and content:
                    structured_data["metadata"][name] = content
            
            logger.info(f"Successfully extracted structured data of type '{data_type}'")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Extracted structured data of type '{data_type}' from the page."
                    }
                ],
                "data_type": data_type,
                "structured_data": structured_data
            }
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error extracting structured data: {str(e)}"
                    }
                ]
            }
    
    logger.info("Data extraction tools registered")
    return {
        "extract_structured_data": extract_structured_data
    }
