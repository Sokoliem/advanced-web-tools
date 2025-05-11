#!/usr/bin/env python3
"""
Integration script for Claude MCP Scaffold enhancements.

This script helps integrate the enhanced components into the existing codebase.
"""

import os
import sys
import shutil
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run the integration process."""
    logger.info("Starting integration of Claude MCP Scaffold enhancements...")
    
    # Get base directory
    base_dir = Path(__file__).parent.absolute()
    logger.info(f"Base directory: {base_dir}")
    
    # Define paths
    web_interaction_dir = base_dir / "web_interaction"
    server_py = base_dir / "server.py"
    server_py_enhanced = base_dir / "server.py.enhanced"
    server_py_backup = base_dir / "server.py.backup"
    
    # Check if the enhanced server.py exists
    if not server_py_enhanced.exists():
        logger.error("Enhanced server.py not found. Make sure server.py.enhanced exists.")
        sys.exit(1)
    
    # Backup current server.py if not already backed up
    if not server_py_backup.exists() and server_py.exists():
        logger.info("Creating backup of current server.py...")
        shutil.copy2(server_py, server_py_backup)
        logger.info(f"Backup created: {server_py_backup}")
    
    # Check for new modules
    new_modules = [
        "enhanced_browser_manager.py",
        "advanced_unified_tool.py",
        "error_handler.py"
    ]
    
    missing_modules = []
    for module in new_modules:
        module_path = web_interaction_dir / module
        if not module_path.exists():
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Missing enhanced modules: {', '.join(missing_modules)}")
        logger.error("Please make sure all enhanced modules are in the web_interaction directory.")
        sys.exit(1)
    
    # Replace server.py with the enhanced version
    logger.info("Replacing server.py with enhanced version...")
    try:
        shutil.copy2(server_py_enhanced, server_py)
        logger.info("server.py updated successfully.")
    except Exception as e:
        logger.error(f"Error updating server.py: {str(e)}")
        sys.exit(1)
    
    # Create __init__.py imports for new modules if needed
    init_py = web_interaction_dir / "__init__.py"
    
    if init_py.exists():
        # Read current __init__.py contents
        with open(init_py, 'r') as f:
            init_content = f.read()
        
        # Check if we need to add imports
        needs_update = False
        
        # Check for enhanced browser manager import
        if "from .enhanced_browser_manager import EnhancedBrowserManager" not in init_content:
            init_content += "\n# Enhanced browser manager\n"
            init_content += "from .enhanced_browser_manager import EnhancedBrowserManager\n"
            needs_update = True
        
        # Check for advanced unified tool import
        if "from .advanced_unified_tool import register_advanced_unified_tool" not in init_content:
            init_content += "\n# Advanced unified tool\n"
            init_content += "from .advanced_unified_tool import register_advanced_unified_tool\n"
            needs_update = True
        
        # Check for error handler import
        if "from .error_handler import register_error_handling_tool" not in init_content:
            init_content += "\n# Error handling tools\n"
            init_content += "from .error_handler import register_error_handling_tool\n"
            needs_update = True
        
        # Update __init__.py if needed
        if needs_update:
            logger.info("Updating web_interaction/__init__.py with new imports...")
            with open(init_py, 'w') as f:
                f.write(init_content)
            logger.info("web_interaction/__init__.py updated successfully.")
    else:
        logger.error("web_interaction/__init__.py not found.")
        sys.exit(1)
    
    # Create or update the README.md, requirements.txt, and setup.py
    readme_path = base_dir / "README.md"
    requirements_path = base_dir / "requirements.txt"
    setup_path = base_dir / "setup.py"
    
    # Check if the files already exist
    updated_files = []
    
    if not readme_path.exists():
        # Create README.md using the one we made
        readme_template = base_dir / "README.md.template"
        if readme_template.exists():
            shutil.copy2(readme_template, readme_path)
            updated_files.append("README.md")
    
    if not requirements_path.exists():
        # Create requirements.txt using the one we made
        requirements_template = base_dir / "requirements.txt.template"
        if requirements_template.exists():
            shutil.copy2(requirements_template, requirements_path)
            updated_files.append("requirements.txt")
    
    if not setup_path.exists():
        # Create setup.py using the one we made
        setup_template = base_dir / "setup.py.template"
        if setup_template.exists():
            shutil.copy2(setup_template, setup_path)
            updated_files.append("setup.py")
    
    if updated_files:
        logger.info(f"Created new files: {', '.join(updated_files)}")
    
    # Create CLAUDE.md file if needed
    claude_md_path = base_dir / "CLAUDE.md"
    if not claude_md_path.exists():
        claude_md_template = base_dir / "CLAUDE.md.template"
        if claude_md_template.exists():
            shutil.copy2(claude_md_template, claude_md_path)
            logger.info("Created CLAUDE.md file for Claude Code instructions.")
    
    # Create the installation script if needed
    install_script_path = base_dir / "install_dependencies.py"
    if not install_script_path.exists():
        install_script_template = base_dir / "install_dependencies.py.template"
        if install_script_template.exists():
            shutil.copy2(install_script_template, install_script_path)
            # Make it executable
            os.chmod(install_script_path, 0o755)
            logger.info("Created install_dependencies.py script.")
    
    # Cleanup temporary files
    logger.info("Cleaning up temporary files...")
    try:
        # Rename template files if they exist
        for template_file in base_dir.glob("*.template"):
            new_name = str(template_file).replace(".template", ".bak")
            os.rename(template_file, new_name)
        
        # Remove the enhanced server.py file
        if server_py_enhanced.exists():
            os.rename(server_py_enhanced, base_dir / "server.py.enhanced.bak")
    except Exception as e:
        logger.warning(f"Error during cleanup: {str(e)}")
    
    logger.info("\n✅ Integration completed successfully!")
    logger.info("\nTo use the enhanced Claude MCP Scaffold:")
    logger.info("1. Run `python install_dependencies.py` to install required dependencies")
    logger.info("2. Launch the server with `python -m claude_mcp_scaffold`")
    logger.info("3. The new enhanced tools will be available:")
    logger.info("   - web_interact_advanced: For advanced web interactions")
    logger.info("   - get_browser_info: For browser session management")
    logger.info("   - diagnostics_report: For troubleshooting and diagnostics")
    
    logger.info("\nNOTE: Your Claude Desktop configuration does not need to be updated.")
    logger.info("The tools will be automatically available when you start the server.")

if __name__ == "__main__":
    main()