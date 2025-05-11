"""Advanced Web Interaction MCP Extension module.

This module provides tools for browsing the web, interacting with web pages,
and extracting data from web pages with improved state persistence, robust
error handling, enhanced debugging, data persistence, and export capabilities.
"""

import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Import enhanced browser manager (preferred when available)
try:
    from .enhanced_browser_manager import EnhancedBrowserManager
    # Create enhanced browser manager instance
    browser_manager = EnhancedBrowserManager()
except ImportError:
    # Fall back to standard browser manager
    from .persistent_browser import PersistentBrowserManager
    # Create persistent browser manager instance
    browser_manager = PersistentBrowserManager()

# Import tool registration functions
from .unified_tool import register_unified_tool
from .advanced_unified_tool import register_advanced_unified_tool
from .error_handler import register_error_handling_tool

# Keep old imports for backward compatibility
from .core_tools import register_core_tools
from .advanced_tools import register_advanced_tools
from .data_extraction import register_data_extraction_tools
from .workflows import register_workflow_tools

# Import new enhanced capabilities
from .visual_debugger import register_visual_debugging_tools
from .enhanced_console import register_enhanced_console_tools
from .data_persistence import register_data_persistence_tools
from .data_export import register_data_export_tools
from .web_diagnostic_toolkit import register_web_diagnostic_tools

__all__ = [
    'browser_manager',
    'register_unified_tool',
    'register_advanced_unified_tool',
    'register_error_handling_tool',
    'register_core_tools',
    'register_advanced_tools',
    'register_data_extraction_tools',
    'register_workflow_tools',
    'register_visual_debugging_tools',
    'register_enhanced_console_tools',
    'register_data_persistence_tools',
    'register_data_export_tools',
    'register_web_diagnostic_tools',
    'register_all_tools'
]

def register_all_tools(mcp: Any, browser_manager: Any) -> Dict[str, Any]:
    """Register all web interaction tools with the MCP server."""
    tools_registry = {}
    
    # Register core tools
    try:
        logger.info("Registering core web interaction tools...")
        core_tools = register_core_tools(mcp, browser_manager)
        tools_registry.update(core_tools)
    except Exception as e:
        logger.error(f"Error registering core tools: {str(e)}")
    
    # Register advanced tools
    try:
        logger.info("Registering advanced web interaction tools...")
        advanced_tools = register_advanced_tools(mcp, browser_manager)
        tools_registry.update(advanced_tools)
    except Exception as e:
        logger.error(f"Error registering advanced tools: {str(e)}")
    
    # Register data extraction tools
    try:
        logger.info("Registering data extraction tools...")
        data_tools = register_data_extraction_tools(mcp, browser_manager)
        tools_registry.update(data_tools)
    except Exception as e:
        logger.error(f"Error registering data extraction tools: {str(e)}")
    
    # Register workflow tools
    try:
        logger.info("Registering workflow tools...")
        workflow_tools = register_workflow_tools(mcp, browser_manager)
        tools_registry.update(workflow_tools)
    except Exception as e:
        logger.error(f"Error registering workflow tools: {str(e)}")
    
    # Register unified tool
    try:
        logger.info("Registering unified web interaction tool...")
        unified_tools = register_unified_tool(mcp, browser_manager)
        tools_registry.update(unified_tools)
    except Exception as e:
        logger.error(f"Error registering unified tool: {str(e)}")
    
    # Register advanced unified tool
    try:
        logger.info("Registering advanced unified web interaction tool...")
        adv_unified_tools = register_advanced_unified_tool(mcp, browser_manager)
        tools_registry.update(adv_unified_tools)
    except Exception as e:
        logger.error(f"Error registering advanced unified tool: {str(e)}")
    
    # Register error handling tool
    try:
        logger.info("Registering error handling tools...")
        error_tools = register_error_handling_tool(mcp, browser_manager)
        tools_registry.update(error_tools)
    except Exception as e:
        logger.error(f"Error registering error handling tools: {str(e)}")
    
    # Register visual debugging tools
    try:
        logger.info("Registering visual debugging tools...")
        visual_tools = register_visual_debugging_tools(mcp, browser_manager)
        tools_registry.update(visual_tools)
    except Exception as e:
        logger.error(f"Error registering visual debugging tools: {str(e)}")
    
    # Register enhanced console tools
    try:
        logger.info("Registering enhanced console tools...")
        console_tools = register_enhanced_console_tools(mcp, browser_manager)
        tools_registry.update(console_tools)
    except Exception as e:
        logger.error(f"Error registering enhanced console tools: {str(e)}")
    
    # Register data persistence tools
    try:
        logger.info("Registering data persistence tools...")
        # Get persistence manager if available
        persistence_manager = None
        if 'console_tools' in locals() and 'console_monitor' in console_tools:
            # Create persistence manager with console monitor
            from .data_persistence import DataPersistenceManager
            persistence_manager = DataPersistenceManager(browser_manager)
        
        # Register persistence tools
        persistence_tools = register_data_persistence_tools(mcp, browser_manager)
        tools_registry.update(persistence_tools)
        
        # Store persistence manager for later use
        if 'persistence_manager' in persistence_tools:
            persistence_manager = persistence_tools['persistence_manager']
    except Exception as e:
        logger.error(f"Error registering data persistence tools: {str(e)}")
        persistence_manager = None
    
    # Register data export tools
    try:
        logger.info("Registering data export tools...")
        export_tools = register_data_export_tools(mcp, browser_manager, persistence_manager)
        tools_registry.update(export_tools)
    except Exception as e:
        logger.error(f"Error registering data export tools: {str(e)}")
        
    # Register web diagnostic toolkit
    try:
        logger.info("Registering web diagnostic toolkit...")
        diagnostic_tools = register_web_diagnostic_tools(mcp, browser_manager)
        tools_registry.update(diagnostic_tools)
    except Exception as e:
        logger.error(f"Error registering web diagnostic toolkit: {str(e)}")
    
    logger.info(f"Registered {len(tools_registry)} web interaction tools")
    return tools_registry