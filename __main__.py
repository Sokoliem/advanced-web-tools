"""Main entry point for the MCP server."""

import asyncio
import logging
import sys
import os
from typing import Optional

from .server import mcp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_env():
    """Load environment variables from .env file if present."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning(".env file loading failed - dotenv package not installed")
    except Exception as e:
        logger.warning(f"Error loading .env file: {e}")

async def main_async() -> None:
    """Main async entry point."""
    # Load environment variables from .env file if present
    load_env()
    
    logger.info(f"Starting Claude MCP Scaffold Server")
    
    # Run the server using stdio transport
    await mcp.run_stdio_async()

def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
