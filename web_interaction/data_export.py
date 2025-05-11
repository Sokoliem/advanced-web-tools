"""Data Export Module for Web Interaction.

This module provides capabilities for exporting data from web interactions
into various formats, including CSV, JSON, Excel, HTML, and more.
"""

import asyncio
import csv
import json
import logging
import os
import time
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, IO

# Configure logging
logger = logging.getLogger(__name__)

class DataExporter:
    """Base class for data exporters."""
    
    def __init__(self, storage_dir=None):
        """Initialize the data exporter."""
        # Set storage directory
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".claude_web_interaction")
        
        # Set up export directory
        self.export_dir = Path(self.storage_dir) / "exports"
        self.export_dir.mkdir(exist_ok=True)
    
    def get_export_path(self, filename, subfolder=None):
        """Get a path for an export file."""
        # Add timestamp to filename to make it unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name, ext = os.path.splitext(filename)
        timestamped_filename = f"{base_name}_{timestamp}{ext}"
        
        # Use subfolder if provided
        if subfolder:
            folder = self.export_dir / subfolder
            folder.mkdir(exist_ok=True)
            return folder / timestamped_filename
        
        return self.export_dir / timestamped_filename

    def export_to_csv(self, data, filename="export.csv", headers=None, subfolder=None):
        """
        Export data to CSV format.
        
        Args:
            data: List of dictionaries or list of lists to export
            filename: Name of the export file
            headers: Optional list of column headers
            subfolder: Optional subfolder within exports directory
            
        Returns:
            Path to the exported file
        """
        try:
            # Get export path
            export_path = self.get_export_path(filename, subfolder)
            
            with open(export_path, "w", newline="", encoding="utf-8") as f:
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], dict):
                        # Data is a list of dictionaries
                        if headers is None:
                            # Use keys from first dictionary as headers
                            headers = list(data[0].keys())
                        
                        writer = csv.DictWriter(f, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(data)
                    else:
                        # Data is a list of lists
                        writer = csv.writer(f)
                        if headers:
                            writer.writerow(headers)
                        writer.writerows(data)
                else:
                    # Empty data or not a list
                    if headers:
                        writer = csv.writer(f)
                        writer.writerow(headers)
            
            logger.info(f"Exported data to CSV: {export_path}")
            return str(export_path)
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return None
    
    def export_to_json(self, data, filename="export.json", pretty=True, subfolder=None):
        """
        Export data to JSON format.
        
        Args:
            data: Data to export
            filename: Name of the export file
            pretty: Whether to format JSON with indentation
            subfolder: Optional subfolder within exports directory
            
        Returns:
            Path to the exported file
        """
        try:
            # Get export path
            export_path = self.get_export_path(filename, subfolder)
            
            with open(export_path, "w", encoding="utf-8") as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            logger.info(f"Exported data to JSON: {export_path}")
            return str(export_path)
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            return None
    
    def export_to_excel(self, data, filename="export.xlsx", sheet_name="Sheet1", headers=None, subfolder=None):
        """
        Export data to Excel format.
        
        Args:
            data: List of dictionaries or list of lists to export
            filename: Name of the export file
            sheet_name: Name of the Excel sheet
            headers: Optional list of column headers
            subfolder: Optional subfolder within exports directory
            
        Returns:
            Path to the exported file
        """
        try:
            # Import pandas and openpyxl for Excel export
            import pandas as pd
            
            # Get export path
            export_path = self.get_export_path(filename, subfolder)
            
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # Convert list of dictionaries to DataFrame
                    df = pd.DataFrame(data)
                    
                    # Reorder columns if headers provided
                    if headers:
                        # Only use headers that exist in the DataFrame
                        valid_headers = [h for h in headers if h in df.columns]
                        df = df[valid_headers]
                else:
                    # Convert list of lists to DataFrame
                    if headers:
                        df = pd.DataFrame(data, columns=headers)
                    else:
                        df = pd.DataFrame(data)
            else:
                # Empty data or not a list
                df = pd.DataFrame()
            
            # Export to Excel
            df.to_excel(export_path, sheet_name=sheet_name, index=False)
            
            logger.info(f"Exported data to Excel: {export_path}")
            return str(export_path)
        except ImportError:
            logger.error("Pandas and openpyxl are required for Excel export. Install with: pip install pandas openpyxl")
            return None
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            return None
    
    def export_to_html(self, data, filename="export.html", title="Data Export", headers=None, subfolder=None):
        """
        Export data to HTML format.
        
        Args:
            data: List of dictionaries or list of lists to export
            filename: Name of the export file
            title: Title of the HTML document
            headers: Optional list of column headers
            subfolder: Optional subfolder within exports directory
            
        Returns:
            Path to the exported file
        """
        try:
            # Get export path
            export_path = self.get_export_path(filename, subfolder)
            
            # Start HTML document
            html = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            """
            
            # Add table
            html += """
                <table>
                    <thead>
                        <tr>
            """
            
            # Process data and add table contents
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # Data is a list of dictionaries
                    if headers is None:
                        # Use keys from first dictionary as headers
                        headers = list(data[0].keys())
                    
                    # Add headers
                    for header in headers:
                        html += f"""
                            <th>{header}</th>"""
                    
                    html += """
                        </tr>
                    </thead>
                    <tbody>
                    """
                    
                    # Add rows
                    for item in data:
                        html += """
                        <tr>"""
                        for header in headers:
                            value = item.get(header, "")
                            html += f"""
                            <td>{value}</td>"""
                        html += """
                        </tr>"""
                else:
                    # Data is a list of lists
                    if headers:
                        # Add headers
                        for header in headers:
                            html += f"""
                            <th>{header}</th>"""
                    else:
                        # Generate generic headers
                        for i in range(len(data[0])):
                            html += f"""
                            <th>Column {i+1}</th>"""
                    
                    html += """
                        </tr>
                    </thead>
                    <tbody>
                    """
                    
                    # Add rows
                    for row in data:
                        html += """
                        <tr>"""
                        for value in row:
                            html += f"""
                            <td>{value}</td>"""
                        html += """
                        </tr>"""
            
            # Close table and HTML document
            html += """
                    </tbody>
                </table>
            </body>
            </html>
            """
            
            # Write HTML to file
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            logger.info(f"Exported data to HTML: {export_path}")
            return str(export_path)
        except Exception as e:
            logger.error(f"Error exporting to HTML: {str(e)}")
            return None
    
    def export_to_markdown(self, data, filename="export.md", title="Data Export", headers=None, subfolder=None):
        """
        Export data to Markdown format.
        
        Args:
            data: List of dictionaries or list of lists to export
            filename: Name of the export file
            title: Title of the Markdown document
            headers: Optional list of column headers
            subfolder: Optional subfolder within exports directory
            
        Returns:
            Path to the exported file
        """
        try:
            # Get export path
            export_path = self.get_export_path(filename, subfolder)
            
            # Start Markdown document
            markdown = f"# {title}\n\n"
            markdown += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Process data and add table
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # Data is a list of dictionaries
                    if headers is None:
                        # Use keys from first dictionary as headers
                        headers = list(data[0].keys())
                    
                    # Add headers
                    markdown += "| " + " | ".join(headers) + " |\n"
                    markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                    
                    # Add rows
                    for item in data:
                        row_values = [str(item.get(header, "")) for header in headers]
                        markdown += "| " + " | ".join(row_values) + " |\n"
                else:
                    # Data is a list of lists
                    if headers:
                        # Add headers
                        markdown += "| " + " | ".join(headers) + " |\n"
                        markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                    else:
                        # Generate generic headers
                        header_count = len(data[0])
                        headers = [f"Column {i+1}" for i in range(header_count)]
                        markdown += "| " + " | ".join(headers) + " |\n"
                        markdown += "| " + " | ".join(["---"] * header_count) + " |\n"
                    
                    # Add rows
                    for row in data:
                        row_values = [str(value) for value in row]
                        markdown += "| " + " | ".join(row_values) + " |\n"
            
            # Write Markdown to file
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            
            logger.info(f"Exported data to Markdown: {export_path}")
            return str(export_path)
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {str(e)}")
            return None
    
    def export_to_text(self, data, filename="export.txt", title="Data Export", subfolder=None):
        """
        Export data to plain text format.
        
        Args:
            data: Data to export (will be converted to string)
            filename: Name of the export file
            title: Title of the text document
            subfolder: Optional subfolder within exports directory
            
        Returns:
            Path to the exported file
        """
        try:
            # Get export path
            export_path = self.get_export_path(filename, subfolder)
            
            # Start text document
            text = f"{title}\n"
            text += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Convert data to string representation
            if isinstance(data, str):
                # Data is already a string
                text += data
            elif isinstance(data, dict):
                # Data is a dictionary
                for key, value in data.items():
                    text += f"{key}: {value}\n"
            elif isinstance(data, list):
                # Data is a list
                if len(data) > 0 and isinstance(data[0], dict):
                    # List of dictionaries
                    for i, item in enumerate(data):
                        text += f"Item {i+1}:\n"
                        for key, value in item.items():
                            text += f"  {key}: {value}\n"
                        text += "\n"
                else:
                    # Simple list
                    for i, item in enumerate(data):
                        text += f"{i+1}. {item}\n"
            else:
                # Other data types
                text += str(data)
            
            # Write text to file
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            logger.info(f"Exported data to text: {export_path}")
            return str(export_path)
        except Exception as e:
            logger.error(f"Error exporting to text: {str(e)}")
            return None
    
    def export_to_pdf(self, data, filename="export.pdf", title="Data Export", headers=None, subfolder=None):
        """
        Export data to PDF format.
        
        Args:
            data: List of dictionaries or list of lists to export
            filename: Name of the export file
            title: Title of the PDF document
            headers: Optional list of column headers
            subfolder: Optional subfolder within exports directory
            
        Returns:
            Path to the exported file
        """
        try:
            # Import reportlab for PDF generation
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            # Get export path
            export_path = self.get_export_path(filename, subfolder)
            
            # Create PDF document
            doc = SimpleDocTemplate(str(export_path), pagesize=letter)
            elements = []
            
            # Add title
            styles = getSampleStyleSheet()
            elements.append(Paragraph(title, styles["Title"]))
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
            elements.append(Spacer(1, 12))
            
            # Process data and add table
            table_data = []
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # Data is a list of dictionaries
                    if headers is None:
                        # Use keys from first dictionary as headers
                        headers = list(data[0].keys())
                    
                    # Add headers to table
                    table_data.append(headers)
                    
                    # Add rows to table
                    for item in data:
                        row = [item.get(header, "") for header in headers]
                        table_data.append(row)
                else:
                    # Data is a list of lists
                    if headers:
                        # Add headers to table
                        table_data.append(headers)
                    
                    # Add rows to table
                    table_data.extend(data)
            
            # Create table
            if table_data:
                table = Table(table_data)
                
                # Add table style
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                
                # Apply alternate row coloring
                for i in range(1, len(table_data), 2):
                    style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
                
                table.setStyle(style)
                elements.append(table)
            
            # Build PDF
            doc.build(elements)
            
            logger.info(f"Exported data to PDF: {export_path}")
            return str(export_path)
        except ImportError:
            logger.error("ReportLab is required for PDF export. Install with: pip install reportlab")
            return None
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            return None
    
    def export_page_screenshot(self, screenshot_data, filename="screenshot.png", subfolder=None):
        """
        Export a page screenshot to a file.
        
        Args:
            screenshot_data: Base64-encoded screenshot data or path to screenshot file
            filename: Name of the export file
            subfolder: Optional subfolder within exports directory
            
        Returns:
            Path to the exported file
        """
        try:
            # Get export path
            export_path = self.get_export_path(filename, subfolder)
            
            # Check if screenshot_data is a base64 string
            if isinstance(screenshot_data, str) and screenshot_data.startswith("data:image"):
                # Extract base64 data from data URL
                header, encoded = screenshot_data.split(",", 1)
                screenshot_data = encoded
            
            if isinstance(screenshot_data, str) and os.path.exists(screenshot_data):
                # screenshot_data is a file path
                with open(screenshot_data, "rb") as src_file:
                    with open(export_path, "wb") as dst_file:
                        dst_file.write(src_file.read())
            elif isinstance(screenshot_data, str):
                # Assume screenshot_data is base64-encoded data
                try:
                    decoded_data = base64.b64decode(screenshot_data)
                    with open(export_path, "wb") as f:
                        f.write(decoded_data)
                except Exception as e:
                    logger.error(f"Error decoding base64 data: {str(e)}")
                    return None
            else:
                logger.error("Invalid screenshot data format")
                return None
            
            logger.info(f"Exported screenshot to: {export_path}")
            return str(export_path)
        except Exception as e:
            logger.error(f"Error exporting screenshot: {str(e)}")
            return None
    
    def generate_html_report(self, sections, filename="report.html", title="Web Interaction Report", subfolder=None):
        """
        Generate an HTML report with multiple sections.
        
        Args:
            sections: List of report sections, each containing:
                {
                    "title": Section title,
                    "content": Section content (string, list, dict, etc.),
                    "type": Content type ("text", "table", "json", "image", etc.)
                }
            filename: Name of the export file
            title: Title of the report
            subfolder: Optional subfolder within exports directory
            
        Returns:
            Path to the exported file
        """
        try:
            # Get export path
            export_path = self.get_export_path(filename, subfolder)
            
            # Start HTML document
            html = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                    h1 {{ color: #2c3e50; margin-bottom: 10px; }}
                    h2 {{ color: #3498db; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                    .section {{ margin-bottom: 30px; }}
                    .content {{ margin-left: 15px; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    code {{ background-color: #f8f8f8; padding: 2px 5px; border-radius: 3px; }}
                    pre {{ background-color: #f8f8f8; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                    .image-container {{ margin: 10px 0; }}
                    .image-container img {{ max-width: 100%; border: 1px solid #ddd; }}
                    .meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 5px; }}
                    .toc {{ background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .toc-item {{ margin: 5px 0; }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <p class="meta">Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            """
            
            # Add table of contents
            if len(sections) > 2:
                html += """
                <div class="toc">
                    <h2>Table of Contents</h2>
                """
                
                for i, section in enumerate(sections):
                    section_title = section.get("title", f"Section {i+1}")
                    # Create anchor-friendly ID
                    section_id = section_title.lower().replace(" ", "-")
                    html += f"""
                    <div class="toc-item"><a href="#{section_id}">{section_title}</a></div>
                    """
                
                html += """
                </div>
                """
            
            # Add sections
            for i, section in enumerate(sections):
                section_title = section.get("title", f"Section {i+1}")
                section_content = section.get("content", "")
                section_type = section.get("type", "text")
                
                # Create anchor-friendly ID
                section_id = section_title.lower().replace(" ", "-")
                
                html += f"""
                <div class="section" id="{section_id}">
                    <h2>{section_title}</h2>
                    <div class="content">
                """
                
                # Process content based on type
                if section_type == "text":
                    # Plain text content
                    if isinstance(section_content, str):
                        # Format text with paragraphs
                        paragraphs = section_content.split("\n\n")
                        for paragraph in paragraphs:
                            html += f"<p>{paragraph.replace('\n', '<br>')}</p>"
                    else:
                        html += f"<p>{section_content}</p>"
                
                elif section_type == "table":
                    # Table content
                    html += "<table>"
                    
                    if isinstance(section_content, list) and len(section_content) > 0:
                        if isinstance(section_content[0], dict):
                            # List of dictionaries
                            headers = section.get("headers", list(section_content[0].keys()))
                            
                            # Add headers
                            html += "<thead><tr>"
                            for header in headers:
                                html += f"<th>{header}</th>"
                            html += "</tr></thead>"
                            
                            # Add rows
                            html += "<tbody>"
                            for item in section_content:
                                html += "<tr>"
                                for header in headers:
                                    value = item.get(header, "")
                                    html += f"<td>{value}</td>"
                                html += "</tr>"
                            html += "</tbody>"
                        else:
                            # List of lists
                            headers = section.get("headers")
                            
                            if headers:
                                # Add headers
                                html += "<thead><tr>"
                                for header in headers:
                                    html += f"<th>{header}</th>"
                                html += "</tr></thead>"
                            
                            # Add rows
                            html += "<tbody>"
                            for row in section_content:
                                html += "<tr>"
                                for value in row:
                                    html += f"<td>{value}</td>"
                                html += "</tr>"
                            html += "</tbody>"
                    
                    html += "</table>"
                
                elif section_type == "json":
                    # JSON content
                    if isinstance(section_content, (dict, list)):
                        json_str = json.dumps(section_content, indent=2)
                        html += f"<pre><code>{json_str}</code></pre>"
                    else:
                        html += f"<pre><code>{section_content}</code></pre>"
                
                elif section_type == "code":
                    # Code content
                    language = section.get("language", "")
                    html += f'<pre><code class="{language}">{section_content}</code></pre>'
                
                elif section_type == "image":
                    # Image content
                    caption = section.get("caption", "")
                    html += '<div class="image-container">'
                    
                    if isinstance(section_content, str):
                        if section_content.startswith("data:image"):
                            # Data URL
                            html += f'<img src="{section_content}" alt="{caption}" />'
                        elif os.path.exists(section_content):
                            # File path - read and encode to data URL
                            with open(section_content, "rb") as f:
                                image_data = base64.b64encode(f.read()).decode("utf-8")
                            
                            # Determine image type
                            if section_content.lower().endswith(".png"):
                                mime_type = "image/png"
                            elif section_content.lower().endswith((".jpg", ".jpeg")):
                                mime_type = "image/jpeg"
                            else:
                                mime_type = "image/png"  # Default
                            
                            data_url = f"data:{mime_type};base64,{image_data}"
                            html += f'<img src="{data_url}" alt="{caption}" />'
                        else:
                            # Assume it's a URL
                            html += f'<img src="{section_content}" alt="{caption}" />'
                    
                    if caption:
                        html += f'<p><em>{caption}</em></p>'
                    
                    html += '</div>'
                
                html += """
                    </div>
                </div>
                """
            
            # Close HTML document
            html += """
            </body>
            </html>
            """
            
            # Write HTML to file
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            logger.info(f"Generated HTML report: {export_path}")
            return str(export_path)
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            return None

class DataExportManager:
    """Manages data export operations."""
    
    def __init__(self, browser_manager, persistence_manager=None, storage_dir=None):
        """Initialize the data export manager."""
        self.browser_manager = browser_manager
        self.persistence_manager = persistence_manager
        
        # Set storage directory
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".claude_web_interaction")
        
        # Create data exporter
        self.exporter = DataExporter(self.storage_dir)
    
    async def export_page_content(self, page_id, format="html", include_screenshots=True, include_console=False):
        """
        Export content from a page.
        
        Args:
            page_id: ID of the page
            format: Export format ("html", "json", "text", etc.)
            include_screenshots: Whether to include screenshots
            include_console: Whether to include console logs
            
        Returns:
            Path to the exported file
        """
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
            
            # Get the page
            page = self.browser_manager.active_pages.get(page_id)
            if not page:
                logger.error(f"Page {page_id} not found")
                return None
            
            # Extract page data
            url = page.url
            title = await page.title()
            
            # Extract page content
            content = await page.evaluate('''() => {
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
            
            # Take screenshot if requested
            screenshot_path = None
            if include_screenshots:
                temp_path = os.path.join(self.storage_dir, "temp_screenshot.png")
                await page.screenshot(path=temp_path, full_page=True)
                screenshot_path = temp_path
            
            # Get console logs if requested
            console_logs = None
            if include_console and hasattr(self.browser_manager, 'console_monitor'):
                console_logs = await self.browser_manager.console_monitor.get_console_logs(page_id)
            
            # Prepare data for export
            page_data = {
                "url": url,
                "title": title,
                "content": content,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
            
            # Export based on format
            if format == "html":
                report_sections = [
                    {
                        "title": "Page Information",
                        "content": {
                            "URL": url,
                            "Title": title,
                            "Exported": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        },
                        "type": "table"
                    },
                    {
                        "title": "Page Content",
                        "content": content,
                        "type": "text"
                    }
                ]
                
                # Add metadata section
                if metadata:
                    report_sections.append({
                        "title": "Page Metadata",
                        "content": metadata,
                        "type": "json"
                    })
                
                # Add screenshot section
                if screenshot_path:
                    report_sections.append({
                        "title": "Page Screenshot",
                        "content": screenshot_path,
                        "type": "image",
                        "caption": f"Screenshot of {title} ({url})"
                    })
                
                # Add console logs section
                if console_logs:
                    report_sections.append({
                        "title": "Console Logs",
                        "content": console_logs,
                        "type": "json"
                    })
                
                # Generate HTML report
                export_path = self.exporter.generate_html_report(
                    report_sections,
                    filename=f"page_export_{page_id}.html",
                    title=f"Page Export: {title}",
                    subfolder="pages"
                )
            
            elif format == "json":
                # Add screenshot as base64 if requested
                if screenshot_path:
                    with open(screenshot_path, "rb") as f:
                        screenshot_data = base64.b64encode(f.read()).decode("utf-8")
                    page_data["screenshot"] = screenshot_data
                
                # Add console logs if requested
                if console_logs:
                    page_data["console_logs"] = console_logs
                
                # Export to JSON
                export_path = self.exporter.export_to_json(
                    page_data,
                    filename=f"page_export_{page_id}.json",
                    subfolder="pages"
                )
            
            elif format == "text":
                # Format as text
                text_content = f"Page Export: {title}\n"
                text_content += f"URL: {url}\n"
                text_content += f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                text_content += f"--- Content ---\n\n{content}\n\n"
                
                if metadata:
                    text_content += "--- Metadata ---\n\n"
                    for key, value in metadata.items():
                        if key != "jsonld":
                            text_content += f"{key}: {value}\n"
                
                # Export to text
                export_path = self.exporter.export_to_text(
                    text_content,
                    filename=f"page_export_{page_id}.txt",
                    subfolder="pages"
                )
            
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
            
            # Clean up temporary screenshot
            if screenshot_path and os.path.exists(screenshot_path):
                os.unlink(screenshot_path)
            
            logger.info(f"Exported page {page_id} to {format}: {export_path}")
            return export_path
        except Exception as e:
            logger.error(f"Error exporting page content: {str(e)}")
            return None
    
    async def export_table_data(self, data, format="csv", headers=None, filename=None):
        """
        Export table data to various formats.
        
        Args:
            data: Table data (list of dictionaries or list of lists)
            format: Export format ("csv", "json", "excel", "html", etc.)
            headers: Optional list of column headers
            filename: Optional custom filename
            
        Returns:
            Path to the exported file
        """
        try:
            # Generate default filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"table_export_{timestamp}.{format}"
            
            # Export based on format
            if format == "csv":
                export_path = self.exporter.export_to_csv(data, filename, headers, "tables")
            elif format == "json":
                export_path = self.exporter.export_to_json(data, filename, subfolder="tables")
            elif format == "excel":
                export_path = self.exporter.export_to_excel(data, filename, headers=headers, subfolder="tables")
            elif format == "html":
                export_path = self.exporter.export_to_html(data, filename, "Table Export", headers, "tables")
            elif format == "markdown":
                export_path = self.exporter.export_to_markdown(data, filename, "Table Export", headers, "tables")
            elif format == "pdf":
                export_path = self.exporter.export_to_pdf(data, filename, "Table Export", headers, "tables")
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
            
            logger.info(f"Exported table data to {format}: {export_path}")
            return export_path
        except Exception as e:
            logger.error(f"Error exporting table data: {str(e)}")
            return None
    
    async def export_session(self, session_id, format="html"):
        """
        Export session data.
        
        Args:
            session_id: ID of the session to export
            format: Export format ("html", "json", etc.)
            
        Returns:
            Path to the exported file
        """
        try:
            # Check if persistence manager is available
            if not self.persistence_manager:
                logger.error("Persistence manager not available")
                return None
            
            # Get session
            session = self.persistence_manager.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return None
            
            # Prepare session data
            session_data = session.to_dict()
            
            # Export based on format
            if format == "html":
                # Create report sections
                report_sections = [
                    {
                        "title": "Session Information",
                        "content": [
                            {"Name": session.name},
                            {"ID": session.id},
                            {"Created At": datetime.fromisoformat(session_data["created_at"]).strftime("%Y-%m-%d %H:%M:%S")},
                            {"Last Accessed": datetime.fromisoformat(session_data["last_accessed"]).strftime("%Y-%m-%d %H:%M:%S")},
                            {"Expiration": f"{session.expiration} seconds" if session.expiration else "Never"}
                        ],
                        "type": "table"
                    },
                    {
                        "title": "Session Data",
                        "content": session_data["data"],
                        "type": "json"
                    }
                ]
                
                # Generate HTML report
                export_path = self.exporter.generate_html_report(
                    report_sections,
                    filename=f"session_export_{session_id}.html",
                    title=f"Session Export: {session.name}",
                    subfolder="sessions"
                )
            
            elif format == "json":
                # Export to JSON
                export_path = self.exporter.export_to_json(
                    session_data,
                    filename=f"session_export_{session_id}.json",
                    subfolder="sessions"
                )
            
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
            
            logger.info(f"Exported session {session_id} to {format}: {export_path}")
            return export_path
        except Exception as e:
            logger.error(f"Error exporting session: {str(e)}")
            return None
    
    async def export_persisted_data(self, entry_id, format="json"):
        """
        Export persisted data.
        
        Args:
            entry_id: ID of the data entry to export
            format: Export format ("json", "html", etc.)
            
        Returns:
            Path to the exported file
        """
        try:
            # Check if persistence manager is available
            if not self.persistence_manager:
                logger.error("Persistence manager not available")
                return None
            
            # Load data entry
            entry = self.persistence_manager.load_persisted_data(entry_id)
            if not entry:
                logger.error(f"Data entry {entry_id} not found")
                return None
            
            # Prepare entry data
            entry_data = entry.to_dict()
            
            # Export based on format
            if format == "json":
                # Export to JSON
                export_path = self.exporter.export_to_json(
                    entry_data,
                    filename=f"data_export_{entry_id}.json",
                    subfolder="persisted_data"
                )
            
            elif format == "html":
                # Create report sections
                report_sections = [
                    {
                        "title": "Data Information",
                        "content": [
                            {"ID": entry.id},
                            {"Type": entry.type},
                            {"Timestamp": datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")}
                        ],
                        "type": "table"
                    },
                    {
                        "title": "Metadata",
                        "content": entry.metadata,
                        "type": "json"
                    },
                    {
                        "title": "Data",
                        "content": entry.data,
                        "type": "json"
                    }
                ]
                
                # Generate HTML report
                export_path = self.exporter.generate_html_report(
                    report_sections,
                    filename=f"data_export_{entry_id}.html",
                    title=f"Data Export: {entry.type}",
                    subfolder="persisted_data"
                )
            
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
            
            logger.info(f"Exported persisted data {entry_id} to {format}: {export_path}")
            return export_path
        except Exception as e:
            logger.error(f"Error exporting persisted data: {str(e)}")
            return None
    
    async def generate_browser_session_report(self, include_screenshots=True, include_console=True):
        """
        Generate a comprehensive report of the current browser session.
        
        Args:
            include_screenshots: Whether to include screenshots
            include_console: Whether to include console logs
            
        Returns:
            Path to the report file
        """
        try:
            # Prepare report sections
            report_sections = []
            
            # Add browser information section
            browser_info = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Active Pages": len(self.browser_manager.active_pages),
                "Total Pages": len(self.browser_manager.page_metadata) if hasattr(self.browser_manager, 'page_metadata') else "Unknown"
            }
            
            # Add browser types if available
            if hasattr(self.browser_manager, 'browsers'):
                browser_info["Browser Types"] = ", ".join(self.browser_manager.browsers.keys())
            
            report_sections.append({
                "title": "Browser Information",
                "content": [browser_info],
                "type": "table"
            })
            
            # Add active pages section
            active_pages_data = []
            for page_id, page in self.browser_manager.active_pages.items():
                # Get page info
                try:
                    url = page.url
                    title = await page.title()
                    
                    page_info = {
                        "Page ID": page_id,
                        "URL": url,
                        "Title": title
                    }
                    
                    # Add metadata if available
                    if hasattr(self.browser_manager, 'page_metadata') and page_id in self.browser_manager.page_metadata:
                        metadata = self.browser_manager.page_metadata[page_id]
                        page_info["Created At"] = datetime.fromtimestamp(metadata.get("created_at", 0)).strftime("%Y-%m-%d %H:%M:%S")
                        page_info["Last Accessed"] = datetime.fromtimestamp(metadata.get("last_accessed", 0)).strftime("%Y-%m-%d %H:%M:%S")
                    
                    active_pages_data.append(page_info)
                    
                    # Take screenshot if requested
                    if include_screenshots:
                        # Take screenshot and save to temporary file
                        temp_path = os.path.join(self.storage_dir, f"temp_screenshot_{page_id}.png")
                        await page.screenshot(path=temp_path)
                        
                        # Add screenshot section
                        report_sections.append({
                            "title": f"Screenshot: Page {page_id} - {title}",
                            "content": temp_path,
                            "type": "image",
                            "caption": f"Screenshot of {title} ({url})"
                        })
                    
                    # Add console logs if requested
                    if include_console and hasattr(self.browser_manager, 'console_monitor'):
                        console_logs = await self.browser_manager.console_monitor.get_console_logs(page_id)
                        if console_logs:
                            report_sections.append({
                                "title": f"Console Logs: Page {page_id}",
                                "content": console_logs,
                                "type": "json"
                            })
                except Exception as e:
                    logger.error(f"Error processing page {page_id}: {str(e)}")
            
            # Add active pages section
            if active_pages_data:
                report_sections.append({
                    "title": "Active Pages",
                    "content": active_pages_data,
                    "type": "table"
                })
            
            # Generate report
            export_path = self.exporter.generate_html_report(
                report_sections,
                filename=f"browser_session_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                title="Browser Session Report",
                subfolder="reports"
            )
            
            # Clean up temporary screenshots
            for page_id in self.browser_manager.active_pages:
                temp_path = os.path.join(self.storage_dir, f"temp_screenshot_{page_id}.png")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
            logger.info(f"Generated browser session report: {export_path}")
            return export_path
        except Exception as e:
            logger.error(f"Error generating browser session report: {str(e)}")
            return None

def register_data_export_tools(mcp, browser_manager, persistence_manager=None):
    """Register data export tools with the MCP server."""
    # Create data export manager instance
    export_manager = DataExportManager(browser_manager, persistence_manager)
    
    @mcp.tool()
    async def export_page_to_html(page_id: str, include_screenshots: bool = True, include_console: bool = False) -> Dict[str, Any]:
        """
        Export page content to HTML format.
        
        Args:
            page_id: ID of the page to export
            include_screenshots: Whether to include screenshots in the export
            include_console: Whether to include console logs in the export
            
        Returns:
            Dict with export information
        """
        logger.info(f"Exporting page {page_id} to HTML")
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
            
            # Handle boolean parameters if they're passed as strings
            if isinstance(include_screenshots, str):
                if include_screenshots.lower() == "true":
                    include_screenshots = True
                elif include_screenshots.lower() == "false":
                    include_screenshots = False
                else:
                    try:
                        include_screenshots = bool(int(include_screenshots))
                    except ValueError:
                        include_screenshots = True
            
            if isinstance(include_console, str):
                if include_console.lower() == "true":
                    include_console = True
                elif include_console.lower() == "false":
                    include_console = False
                else:
                    try:
                        include_console = bool(int(include_console))
                    except ValueError:
                        include_console = False
                        
            logger.info(f"Parameters validated: page_id={page_id}, include_screenshots={include_screenshots}, include_console={include_console}")
            
            # Check if page exists
            if page_id not in browser_manager.active_pages:
                logger.warning(f"Page {page_id} not found for HTML export")
                
                # Try a fallback page if there are any active pages
                if browser_manager.active_pages:
                    fallback_page_id = next(iter(browser_manager.active_pages.keys()))
                    logger.info(f"Using fallback page: {fallback_page_id}")
                    page_id = fallback_page_id
                else:
                    # Create a new page as a last resort
                    try:
                        logger.info("No active pages available, creating a new page")
                        page, page_id = await browser_manager.get_page()
                        await page.goto("about:blank")
                        logger.info(f"Created new page with ID {page_id} for HTML export")
                    except Exception as create_error:
                        logger.error(f"Error creating new page for HTML export: {str(create_error)}")
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
            
            # Export page content with retry
            max_retries = 3
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    export_path = await export_manager.export_page_content(page_id, "html", include_screenshots, include_console)
                    if export_path:
                        logger.info(f"Successfully exported page {page_id} to HTML: {export_path}")
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Page exported successfully to HTML"
                                }
                            ],
                            "success": True,
                            "export_path": export_path,
                            "format": "html"
                        }
                    retry_count += 1
                    await asyncio.sleep(1)  # Wait before retrying
                except Exception as e:
                    logger.error(f"Error on attempt {retry_count+1}: {str(e)}")
                    last_error = e
                    retry_count += 1
                    await asyncio.sleep(1)  # Wait before retrying
            
            # If we get here, all retries failed
            error_message = f"Failed to export page to HTML after {max_retries} attempts"
            if last_error:
                error_message += f": {str(last_error)}"
                
            logger.error(error_message)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": error_message
                    }
                ],
                "success": False,
                "error": error_message
            }
        except Exception as e:
            logger.error(f"Error exporting page to HTML: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error exporting page to HTML: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def export_page_to_json(page_id: str, include_screenshots: bool = True, include_console: bool = False) -> Dict[str, Any]:
        """
        Export page content to JSON format.
        
        Args:
            page_id: ID of the page to export
            include_screenshots: Whether to include screenshots in the export
            include_console: Whether to include console logs in the export
            
        Returns:
            Dict with export information
        """
        logger.info(f"Exporting page {page_id} to JSON")
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
            
            # Export page content
            export_path = await export_manager.export_page_content(page_id, "json", include_screenshots, include_console)
            
            if export_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Page exported successfully to JSON"
                        }
                    ],
                    "success": True,
                    "export_path": export_path,
                    "format": "json"
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to export page to JSON"
                        }
                    ],
                    "success": False,
                    "error": "Failed to export page to JSON"
                }
        except Exception as e:
            logger.error(f"Error exporting page to JSON: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error exporting page to JSON: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def export_table_data_to_csv(data: List[Any], headers: Optional[List[str]] = None, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Export table data to CSV format.
        
        Args:
            data: Table data (list of dictionaries or list of lists)
            headers: Optional list of column headers
            filename: Optional custom filename
            
        Returns:
            Dict with export information
        """
        logger.info(f"Exporting table data to CSV")
        try:
            # Validate parameters
            if not data:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: data must be provided"
                        }
                    ],
                    "success": False,
                    "error": "data must be provided"
                }
                
            # Handle case where data might be a string representation of JSON
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                    logger.info(f"Converted data string to JSON object")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse data string as JSON: {str(e)}")
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Invalid JSON data provided. {str(e)}"
                            }
                        ],
                        "success": False,
                        "error": f"Invalid JSON data provided. {str(e)}"
                    }
            
            # Ensure data is a list
            if not isinstance(data, list):
                logger.error(f"Data must be a list, got {type(data)}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Data must be a list, got {type(data)}"
                        }
                    ],
                    "success": False,
                    "error": f"Data must be a list, got {type(data)}"
                }
                
            # If data is empty list, create a minimal CSV
            if len(data) == 0:
                logger.warning("Data list is empty, creating minimal CSV")
                if headers:
                    # Use provided headers
                    minimal_data = [dict.fromkeys(headers, "") for _ in range(1)]
                    data = minimal_data
                else:
                    # Create minimal empty data
                    data = [{"empty": ""}]
                    headers = ["empty"]
                    
            # Validate headers if provided
            if headers and not isinstance(headers, list):
                try:
                    # Try to convert to list if it's a string representation of JSON
                    if isinstance(headers, str):
                        headers = json.loads(headers)
                        if not isinstance(headers, list):
                            raise ValueError("Headers must be a list")
                except Exception as e:
                    logger.error(f"Invalid headers format: {str(e)}")
                    headers = None  # Use default headers based on data
            
            # Sanitize filename if provided
            if filename:
                # Ensure filename has safe characters
                filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
                # Add .csv extension if not present
                if not filename.lower().endswith(".csv"):
                    filename += ".csv"
                    
            # Export data with retry mechanism
            max_retries = 3
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    export_path = await export_manager.export_table_data(data, "csv", headers, filename)
                    
                    if export_path:
                        logger.info(f"Successfully exported table data to CSV: {export_path}")
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Table data exported successfully to CSV"
                                }
                            ],
                            "success": True,
                            "export_path": export_path,
                            "format": "csv",
                            "rows_exported": len(data)
                        }
                    
                    retry_count += 1
                    await asyncio.sleep(1)  # Wait before retrying
                except Exception as e:
                    logger.error(f"Error on attempt {retry_count+1}: {str(e)}")
                    last_error = e
                    retry_count += 1
                    await asyncio.sleep(1)  # Wait before retrying
            
            # If we get here, all retries failed
            error_message = f"Failed to export table data to CSV after {max_retries} attempts"
            if last_error:
                error_message += f": {str(last_error)}"
                
            logger.error(error_message)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": error_message
                    }
                ],
                "success": False,
                "error": error_message
            }
        except Exception as e:
            logger.error(f"Error exporting table data to CSV: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error exporting table data to CSV: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def export_table_data_to_excel(data: List[Any], headers: Optional[List[str]] = None, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Export table data to Excel format.
        
        Args:
            data: Table data (list of dictionaries or list of lists)
            headers: Optional list of column headers
            filename: Optional custom filename
            
        Returns:
            Dict with export information
        """
        logger.info(f"Exporting table data to Excel")
        try:
            # Export data
            export_path = await export_manager.export_table_data(data, "excel", headers, filename)
            
            if export_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Table data exported successfully to Excel"
                        }
                    ],
                    "success": True,
                    "export_path": export_path,
                    "format": "excel"
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to export table data to Excel"
                        }
                    ],
                    "success": False,
                    "error": "Failed to export table data to Excel"
                }
        except Exception as e:
            logger.error(f"Error exporting table data to Excel: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error exporting table data to Excel: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def export_session_data(session_id: str, format: str = "html") -> Dict[str, Any]:
        """
        Export session data to various formats.
        
        Args:
            session_id: ID of the session to export
            format: Export format ("html", "json")
            
        Returns:
            Dict with export information
        """
        logger.info(f"Exporting session {session_id} to {format}")
        try:
            # Export session
            export_path = await export_manager.export_session(session_id, format)
            
            if export_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Session exported successfully to {format}"
                        }
                    ],
                    "success": True,
                    "export_path": export_path,
                    "format": format
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to export session to {format}"
                        }
                    ],
                    "success": False,
                    "error": f"Failed to export session to {format}"
                }
        except Exception as e:
            logger.error(f"Error exporting session: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error exporting session: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def export_persisted_data_entry(entry_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Export persisted data to various formats.
        
        Args:
            entry_id: ID of the data entry to export
            format: Export format ("json", "html")
            
        Returns:
            Dict with export information
        """
        logger.info(f"Exporting persisted data {entry_id} to {format}")
        try:
            # Export data
            export_path = await export_manager.export_persisted_data(entry_id, format)
            
            if export_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Persisted data exported successfully to {format}"
                        }
                    ],
                    "success": True,
                    "export_path": export_path,
                    "format": format
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to export persisted data to {format}"
                        }
                    ],
                    "success": False,
                    "error": f"Failed to export persisted data to {format}"
                }
        except Exception as e:
            logger.error(f"Error exporting persisted data: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error exporting persisted data: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def generate_session_report(include_screenshots: bool = True, include_console: bool = True) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the current browser session.
        
        Args:
            include_screenshots: Whether to include screenshots in the report
            include_console: Whether to include console logs in the report
            
        Returns:
            Dict with report information
        """
        logger.info(f"Generating browser session report")
        try:
            # Generate report
            report_path = await export_manager.generate_browser_session_report(include_screenshots, include_console)
            
            if report_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Browser session report generated successfully"
                        }
                    ],
                    "success": True,
                    "report_path": report_path
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to generate browser session report"
                        }
                    ],
                    "success": False,
                    "error": "Failed to generate browser session report"
                }
        except Exception as e:
            logger.error(f"Error generating browser session report: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error generating browser session report: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def create_html_report(title: str, sections: List[Dict[str, Any]], filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a custom HTML report with multiple sections.
        
        Args:
            title: Title of the report
            sections: List of report sections, each containing:
                {
                    "title": Section title,
                    "content": Section content (string, list, dict, etc.),
                    "type": Content type ("text", "table", "json", "image", etc.)
                }
            filename: Optional custom filename
            
        Returns:
            Dict with report information
        """
        logger.info(f"Creating HTML report: {title}")
        try:
            # Generate default filename if not provided
            if not filename:
                # Create a filename-friendly version of the title
                safe_title = title.lower().replace(" ", "_")
                safe_title = "".join(c for c in safe_title if c.isalnum() or c == "_")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{safe_title}_{timestamp}.html"
            
            # Generate report
            report_path = export_manager.exporter.generate_html_report(
                sections,
                filename=filename,
                title=title,
                subfolder="reports"
            )
            
            if report_path:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"HTML report created successfully"
                        }
                    ],
                    "success": True,
                    "report_path": report_path
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to create HTML report"
                        }
                    ],
                    "success": False,
                    "error": "Failed to create HTML report"
                }
        except Exception as e:
            logger.error(f"Error creating HTML report: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error creating HTML report: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    logger.info("Data export tools registered")
    
    # Return the export manager instance and tools
    return {
        "export_manager": export_manager,
        "export_page_to_html": export_page_to_html,
        "export_page_to_json": export_page_to_json,
        "export_table_data_to_csv": export_table_data_to_csv,
        "export_table_data_to_excel": export_table_data_to_excel,
        "export_session_data": export_session_data,
        "export_persisted_data_entry": export_persisted_data_entry,
        "generate_session_report": generate_session_report,
        "create_html_report": create_html_report
    }