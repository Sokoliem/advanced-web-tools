"""Test script for data persistence functionality.

This script tests the data persistence functions to verify they work correctly.
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path to import modules
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock MCP for testing
class MockMCP:
    """Simple MCP mock for registering and calling tools."""
    
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        """Decorator for registering tools."""
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator
    
    async def call_tool(self, tool_name, *args, **kwargs):
        """Call a registered tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not registered")
        return await self.tools[tool_name](*args, **kwargs)

# Mock browser manager for testing
class MockBrowserManager:
    """Simple browser manager mock."""
    
    def __init__(self):
        self.active_pages = {}
        self.page_metadata = {}

async def run_tests():
    """Run data persistence tests."""
    try:
        logger.info("Starting data persistence tests")
        
        # Initialize mock objects
        mcp = MockMCP()
        browser_manager = MockBrowserManager()
        
        # Import and register data persistence tools
        sys.path.append(str(Path(__file__).parent))
        from data_persistence import register_data_persistence_tools
        
        # Register data persistence tools
        persistence_tools = register_data_persistence_tools(mcp, browser_manager)
        logger.info(f"Registered persistence tools: {list(persistence_tools.keys())}")
        
        # Test 1: Create a session
        logger.info("Test 1: Creating a data session")
        create_result = await mcp.call_tool("create_data_session", name="Test Session")
        logger.info(f"Created session result: {json.dumps(create_result, indent=2)}")
        
        if not create_result.get("success", False):
            logger.error("Failed to create session")
            return
        
        session_id = create_result.get("session_id")
        logger.info(f"Created session with ID: {session_id}")
        
        # Test 2: Set values in the session
        logger.info("Test 2: Setting session values")
        set_tests = [
            # Standard string key/value
            {"key": "test_string", "value": "Hello World"},
            # Numeric value
            {"key": "test_number", "value": 42},
            # Complex nested object
            {"key": "test_object", "value": {"name": "Test", "attributes": [1, 2, 3]}},
            # Array value
            {"key": "test_array", "value": [1, 2, 3, "four"]},
            # Boolean value
            {"key": "test_boolean", "value": True},
        ]
        
        for test in set_tests:
            set_result = await mcp.call_tool("set_session_value", session_id=session_id, key=test["key"], value=test["value"])
            logger.info(f"Set session value result for key '{test['key']}': {json.dumps(set_result, indent=2)}")
        
        # Test 3: Edge case - Set value with numeric session ID (should work with fix)
        logger.info("Test 3: Setting value with numeric session ID")
        numeric_id = int(session_id) if session_id.isdigit() else 12345
        set_numeric_result = await mcp.call_tool("set_session_value", session_id=numeric_id, key="numeric_id_test", value="This was set with a numeric ID")
        logger.info(f"Set value with numeric ID result: {json.dumps(set_numeric_result, indent=2)}")
        
        # Test 4: Get session info
        logger.info("Test 4: Getting session info")
        info_result = await mcp.call_tool("get_data_session", session_id=session_id)
        logger.info(f"Session info result: {json.dumps(info_result, indent=2)}")
        
        # Test 5: Get values from the session
        logger.info("Test 5: Getting session values")
        for test in set_tests:
            get_result = await mcp.call_tool("get_session_value", session_id=session_id, key=test["key"])
            logger.info(f"Get session value result for key '{test['key']}': {json.dumps(get_result, indent=2)}")
            
            # Verify the value matches what we set
            if get_result.get("success", False):
                retrieved_value = get_result.get("value")
                expected_value = test["value"]
                if retrieved_value == expected_value:
                    logger.info(f"Value verification PASSED for key '{test['key']}'")
                else:
                    logger.error(f"Value verification FAILED for key '{test['key']}'. Expected: {expected_value}, Got: {retrieved_value}")
        
        # Test 6: Edge case - Get value with numeric session ID
        logger.info("Test 6: Getting value with numeric session ID")
        get_numeric_result = await mcp.call_tool("get_session_value", session_id=numeric_id, key="numeric_id_test")
        logger.info(f"Get value with numeric ID result: {json.dumps(get_numeric_result, indent=2)}")
        
        # Test 7: Edge case - Get non-existent key
        logger.info("Test 7: Getting non-existent key")
        get_nonexistent_result = await mcp.call_tool("get_session_value", session_id=session_id, key="non_existent_key", default="default_value")
        logger.info(f"Get non-existent key result: {json.dumps(get_nonexistent_result, indent=2)}")
        
        # Test 8: Edge case - Get value from non-existent session
        logger.info("Test 8: Getting value from non-existent session")
        get_nonexistent_session_result = await mcp.call_tool("get_session_value", session_id="non_existent_session", key="test_key")
        logger.info(f"Get value from non-existent session result: {json.dumps(get_nonexistent_session_result, indent=2)}")
        
        # Test 9: Delete the session
        logger.info("Test 9: Deleting the session")
        delete_result = await mcp.call_tool("delete_data_session", session_id=session_id)
        logger.info(f"Delete session result: {json.dumps(delete_result, indent=2)}")
        
        logger.info("All tests completed")
        
    except Exception as e:
        logger.error(f"Error during tests: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(run_tests())