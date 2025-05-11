"""
Data Persistence Functionality Test Script.

This script tests the data persistence functionality by:
1. Creating test sessions
2. Setting session values
3. Getting session values
4. Getting session information
5. Testing edge cases and error handling
"""

import asyncio
import logging
import sys
import time
import json
from typing import Any, Dict, Optional, List, Union

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("data_persistence_test")

# Import the server to access the MCP object
try:
    from claude_mcp_scaffold.server import mcp
    logger.info("Imported MCP from claude_mcp_scaffold.server")
except ImportError:
    try:
        sys.path.append('.')  # Add current directory to path
        from server import mcp
        logger.info("Imported MCP from server")
    except ImportError:
        logger.error("Failed to import MCP. Make sure you're running this from the project root directory.")
        sys.exit(1)

class DiagnosticResult:
    """Class to store test results and metrics."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = {}
        self.start_time = time.time()
        
    def add_result(self, test_name: str, success: bool, response: Any, error: Optional[str] = None):
        """Add a test result."""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
            
        self.results[test_name] = {
            "success": success,
            "response": response,
            "error": error
        }
        
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the test results."""
        duration = time.time() - self.start_time
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "pass_rate": f"{(self.tests_passed / self.tests_run) * 100:.2f}%" if self.tests_run > 0 else "N/A",
            "duration_seconds": f"{duration:.2f}",
            "results": self.results
        }
        
    def print_summary(self):
        """Print a summary of the test results."""
        summary = self.get_summary()
        print("\n" + "="*50)
        print(f"TEST SUMMARY")
        print("="*50)
        print(f"Tests Run: {summary['tests_run']}")
        print(f"Tests Passed: {summary['tests_passed']}")
        print(f"Tests Failed: {summary['tests_failed']}")
        print(f"Pass Rate: {summary['pass_rate']}")
        print(f"Duration: {summary['duration_seconds']} seconds")
        print("="*50)
        
        # Print individual test results
        print("\nDETAILED RESULTS:")
        for test_name, result in summary['results'].items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{status} - {test_name}")
            if not result["success"] and result["error"]:
                print(f"  Error: {result['error']}")
                
        print("="*50)


class DataPersistenceTester:
    """
    Tester class for data persistence functionality.
    """
    
    def __init__(self):
        self.results = DiagnosticResult()
        # Store session IDs to track them across test functions
        self.session_ids = {}
    
    async def create_test_session(self, name: Optional[str] = None, expiration: Optional[int] = None) -> Dict[str, Any]:
        """
        Test creating a new data session.
        
        Args:
            name: Optional name for the session
            expiration: Optional number of seconds until session expiration
            
        Returns:
            Dict with test result
        """
        logger.info(f"Creating test session with name: {name}, expiration: {expiration}")
        try:
            # Call the create_data_session tool
            create_tool = mcp.tools.get("create_data_session")
            if not create_tool:
                error_msg = "create_data_session tool not found"
                logger.error(error_msg)
                self.results.add_result(f"create_test_session({name}, {expiration})", False, None, error_msg)
                return {"success": False, "error": error_msg}
            
            response = await create_tool(name=name, expiration=expiration)
            
            # Store the session ID if successful
            success = response.get("success", False)
            if success:
                session_id = response.get("session_id")
                session_name = name or f"Unnamed-{session_id}"
                self.session_ids[session_name] = session_id
                logger.info(f"Successfully created session {session_name} with ID {session_id}")
            else:
                error_msg = response.get("error", "Unknown error")
                logger.error(f"Failed to create session: {error_msg}")
            
            # Record test result
            self.results.add_result(
                f"create_test_session({name}, {expiration})", 
                success, 
                response,
                None if success else response.get("error")
            )
            
            return response
        except Exception as e:
            error_msg = f"Error in create_test_session: {str(e)}"
            logger.error(error_msg)
            self.results.add_result(f"create_test_session({name}, {expiration})", False, None, error_msg)
            return {"success": False, "error": error_msg}
    
    async def set_session_values(self, session_id: str, values: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Test setting multiple values in a session.
        
        Args:
            session_id: ID of the session
            values: Dictionary of key-value pairs to set
            
        Returns:
            Dict with test results for each key-value pair
        """
        logger.info(f"Setting {len(values)} values in session {session_id}")
        results = {"results": []}
        
        try:
            # Get the set_session_value tool
            set_tool = mcp.tools.get("set_session_value")
            if not set_tool:
                error_msg = "set_session_value tool not found"
                logger.error(error_msg)
                self.results.add_result(f"set_session_values({session_id}, {len(values)} values)", False, None, error_msg)
                return {"success": False, "error": error_msg}
            
            # Set each value and track results
            for key, value in values.items():
                try:
                    logger.info(f"Setting {key}={value} in session {session_id}")
                    response = await set_tool(session_id=session_id, key=key, value=value)
                    success = response.get("success", False)
                    
                    test_name = f"set_session_value({session_id}, {key}, {value})"
                    self.results.add_result(
                        test_name,
                        success,
                        response,
                        None if success else response.get("error")
                    )
                    
                    results["results"].append({
                        "key": key,
                        "value": value,
                        "success": success,
                        "response": response
                    })
                    
                    if not success:
                        logger.warning(f"Failed to set {key}={value} in session {session_id}")
                except Exception as e:
                    error_msg = f"Error setting {key}={value}: {str(e)}"
                    logger.error(error_msg)
                    
                    test_name = f"set_session_value({session_id}, {key}, {value})"
                    self.results.add_result(test_name, False, None, error_msg)
                    
                    results["results"].append({
                        "key": key,
                        "value": value,
                        "success": False,
                        "error": error_msg
                    })
            
            # Overall success if all individual operations succeeded
            all_success = all(result["success"] for result in results["results"])
            results["success"] = all_success
            if all_success:
                logger.info(f"Successfully set all {len(values)} values in session {session_id}")
            else:
                logger.warning(f"Failed to set some values in session {session_id}")
                
            # Record overall test result
            self.results.add_result(
                f"set_session_values({session_id}, {len(values)} values)",
                all_success,
                results,
                None if all_success else "One or more values failed to set"
            )
            
            return results
        except Exception as e:
            error_msg = f"Error in set_session_values: {str(e)}"
            logger.error(error_msg)
            self.results.add_result(f"set_session_values({session_id}, {len(values)} values)", False, None, error_msg)
            return {"success": False, "error": error_msg}
    
    async def get_session_values(self, session_id: str, keys: List[str], defaults: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Test getting multiple values from a session.
        
        Args:
            session_id: ID of the session
            keys: List of keys to get
            defaults: Optional list of default values, one for each key
            
        Returns:
            Dict with test results for each key
        """
        logger.info(f"Getting {len(keys)} values from session {session_id}")
        
        # If defaults not provided, use None for all keys
        if defaults is None:
            defaults = [None] * len(keys)
        elif len(defaults) < len(keys):
            # Pad defaults with None if not enough provided
            defaults.extend([None] * (len(keys) - len(defaults)))
        
        results = {"values": {}, "results": []}
        
        try:
            # Get the get_session_value tool
            get_tool = mcp.tools.get("get_session_value")
            if not get_tool:
                error_msg = "get_session_value tool not found"
                logger.error(error_msg)
                self.results.add_result(f"get_session_values({session_id}, {len(keys)} keys)", False, None, error_msg)
                return {"success": False, "error": error_msg}
            
            # Get each value and track results
            for i, key in enumerate(keys):
                default = defaults[i]
                try:
                    logger.info(f"Getting value for key {key} from session {session_id}")
                    response = await get_tool(session_id=session_id, key=key, default=default)
                    success = response.get("success", False)
                    
                    test_name = f"get_session_value({session_id}, {key}, default={default})"
                    self.results.add_result(
                        test_name,
                        success,
                        response,
                        None if success else response.get("error")
                    )
                    
                    if success:
                        results["values"][key] = response.get("value")
                    
                    results["results"].append({
                        "key": key,
                        "default": default,
                        "found": response.get("found", False),
                        "value": response.get("value"),
                        "success": success,
                        "response": response
                    })
                    
                    if not success:
                        logger.warning(f"Failed to get value for {key} from session {session_id}")
                except Exception as e:
                    error_msg = f"Error getting value for {key}: {str(e)}"
                    logger.error(error_msg)
                    
                    test_name = f"get_session_value({session_id}, {key}, default={default})"
                    self.results.add_result(test_name, False, None, error_msg)
                    
                    results["results"].append({
                        "key": key,
                        "default": default,
                        "success": False,
                        "error": error_msg
                    })
            
            # Overall success if all individual operations succeeded
            all_success = all(result["success"] for result in results["results"])
            results["success"] = all_success
            if all_success:
                logger.info(f"Successfully retrieved all {len(keys)} values from session {session_id}")
            else:
                logger.warning(f"Failed to retrieve some values from session {session_id}")
                
            # Record overall test result
            self.results.add_result(
                f"get_session_values({session_id}, {len(keys)} keys)",
                all_success,
                results,
                None if all_success else "One or more values failed to retrieve"
            )
            
            return results
        except Exception as e:
            error_msg = f"Error in get_session_values: {str(e)}"
            logger.error(error_msg)
            self.results.add_result(f"get_session_values({session_id}, {len(keys)} keys)", False, None, error_msg)
            return {"success": False, "error": error_msg}
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Test getting session information.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dict with session information
        """
        logger.info(f"Getting information for session {session_id}")
        try:
            # Call the get_data_session tool
            get_info_tool = mcp.tools.get("get_data_session")
            if not get_info_tool:
                error_msg = "get_data_session tool not found"
                logger.error(error_msg)
                self.results.add_result(f"get_session_info({session_id})", False, None, error_msg)
                return {"success": False, "error": error_msg}
            
            response = await get_info_tool(session_id=session_id)
            
            # Record test result
            success = response.get("success", False)
            self.results.add_result(
                f"get_session_info({session_id})", 
                success, 
                response,
                None if success else response.get("error")
            )
            
            if success:
                logger.info(f"Successfully retrieved information for session {session_id}")
            else:
                logger.warning(f"Failed to retrieve information for session {session_id}")
            
            return response
        except Exception as e:
            error_msg = f"Error in get_session_info: {str(e)}"
            logger.error(error_msg)
            self.results.add_result(f"get_session_info({session_id})", False, None, error_msg)
            return {"success": False, "error": error_msg}

    async def test_edge_cases(self) -> Dict[str, Any]:
        """
        Test various edge cases for session persistence functionality.
        
        Returns:
            Dict with test results
        """
        logger.info("Testing edge cases for session persistence")
        
        edge_case_results = {
            "numeric_id": None,
            "empty_key": None,
            "non_existent_session": None,
            "non_existent_key": None,
            "special_characters": None,
            "complex_data_structures": None,
            "large_value": None,
        }
        
        try:
            # Test 1: Using numeric ID instead of string
            logger.info("Testing numeric session ID")
            numeric_id_response = await self.create_test_session(name="NumericTest")
            if numeric_id_response.get("success", False):
                numeric_id = numeric_id_response["session_id"]
                # Try to use numeric version of ID
                try:
                    numeric_id_int = int(numeric_id)
                    numeric_set_response = await self.set_session_values(
                        str(numeric_id_int),  # Convert to int and back to string
                        {"numeric_test": "value"}
                    )
                    edge_case_results["numeric_id"] = numeric_set_response
                except (ValueError, TypeError):
                    edge_case_results["numeric_id"] = {"success": False, "error": "ID could not be converted to numeric"}
            else:
                edge_case_results["numeric_id"] = numeric_id_response
            
            # Test 2: Empty key
            logger.info("Testing empty key")
            test_session_response = await self.create_test_session(name="EmptyKeyTest")
            if test_session_response.get("success", False):
                session_id = test_session_response["session_id"]
                set_tool = mcp.tools.get("set_session_value")
                
                if set_tool:
                    try:
                        empty_key_response = await set_tool(session_id=session_id, key="", value="empty_key_value")
                        edge_case_results["empty_key"] = empty_key_response
                        
                        # Try to retrieve the empty key value
                        if empty_key_response.get("success", False):
                            get_tool = mcp.tools.get("get_session_value")
                            empty_key_get_response = await get_tool(session_id=session_id, key="")
                            # Include retrieval result
                            edge_case_results["empty_key_retrieval"] = empty_key_get_response
                    except Exception as e:
                        edge_case_results["empty_key"] = {"success": False, "error": str(e)}
            
            # Test 3: Non-existent session
            logger.info("Testing non-existent session")
            non_existent_session_id = "non_existent_session_" + str(int(time.time()))
            get_info_tool = mcp.tools.get("get_data_session")
            
            if get_info_tool:
                try:
                    non_existent_response = await get_info_tool(session_id=non_existent_session_id)
                    edge_case_results["non_existent_session"] = non_existent_response
                except Exception as e:
                    edge_case_results["non_existent_session"] = {"success": False, "error": str(e)}
            
            # Test 4: Non-existent key
            logger.info("Testing non-existent key")
            test_session_response = await self.create_test_session(name="NonExistentKeyTest")
            if test_session_response.get("success", False):
                session_id = test_session_response["session_id"]
                get_tool = mcp.tools.get("get_session_value")
                
                if get_tool:
                    try:
                        non_existent_key_response = await get_tool(
                            session_id=session_id, 
                            key="non_existent_key_" + str(int(time.time())),
                            default="default_value"
                        )
                        edge_case_results["non_existent_key"] = non_existent_key_response
                    except Exception as e:
                        edge_case_results["non_existent_key"] = {"success": False, "error": str(e)}
            
            # Test 5: Special characters in keys and values
            logger.info("Testing special characters")
            test_session_response = await self.create_test_session(name="SpecialCharTest")
            if test_session_response.get("success", False):
                session_id = test_session_response["session_id"]
                
                special_char_data = {
                    "key!@#$%^&*()": "value with spaces",
                    "unicode_key_🔑": "unicode_value_💻",
                    "key/with/slashes": "value\\with\\backslashes",
                    "key.with.dots": "value-with-dashes",
                    "key+with+plus": "value=with=equals"
                }
                
                special_char_response = await self.set_session_values(session_id, special_char_data)
                if special_char_response.get("success", False):
                    # Try to retrieve values
                    special_char_get_response = await self.get_session_values(session_id, list(special_char_data.keys()))
                    edge_case_results["special_characters"] = {
                        "set": special_char_response,
                        "get": special_char_get_response
                    }
                else:
                    edge_case_results["special_characters"] = special_char_response
            
            # Test 6: Complex data structures (nested dictionaries, lists, etc.)
            logger.info("Testing complex data structures")
            test_session_response = await self.create_test_session(name="ComplexDataTest")
            if test_session_response.get("success", False):
                session_id = test_session_response["session_id"]
                
                complex_data = {
                    "nested_dict": {
                        "level1": {
                            "level2": {
                                "level3": "deep_value"
                            }
                        },
                        "sibling": "value"
                    },
                    "mixed_list": [1, "string", True, None, {"key": "value"}, [1, 2, 3]],
                    "boolean_value": True,
                    "null_value": None
                }
                
                complex_data_response = await self.set_session_values(session_id, complex_data)
                if complex_data_response.get("success", False):
                    # Try to retrieve values
                    complex_data_get_response = await self.get_session_values(session_id, list(complex_data.keys()))
                    edge_case_results["complex_data_structures"] = {
                        "set": complex_data_response,
                        "get": complex_data_get_response
                    }
                else:
                    edge_case_results["complex_data_structures"] = complex_data_response
            
            # Test 7: Large value
            logger.info("Testing large value")
            test_session_response = await self.create_test_session(name="LargeValueTest")
            if test_session_response.get("success", False):
                session_id = test_session_response["session_id"]
                
                # Create a large string value (approximately 200KB)
                large_value = "x" * 200000
                
                set_tool = mcp.tools.get("set_session_value")
                if set_tool:
                    try:
                        large_value_response = await set_tool(session_id=session_id, key="large_value", value=large_value)
                        
                        if large_value_response.get("success", False):
                            # Try to retrieve the large value
                            get_tool = mcp.tools.get("get_session_value")
                            large_value_get_response = await get_tool(session_id=session_id, key="large_value")
                            
                            # Verify data integrity
                            retrieved_value = large_value_get_response.get("value", "")
                            data_integrity = (retrieved_value == large_value)
                            
                            edge_case_results["large_value"] = {
                                "set": large_value_response,
                                "get": large_value_get_response,
                                "data_integrity": data_integrity,
                                "original_size": len(large_value),
                                "retrieved_size": len(retrieved_value) if isinstance(retrieved_value, str) else 0
                            }
                        else:
                            edge_case_results["large_value"] = large_value_response
                    except Exception as e:
                        edge_case_results["large_value"] = {"success": False, "error": str(e)}
            
            # Record overall test result
            edge_case_success = all(
                result is not None and (isinstance(result, dict) and result.get("success", False))
                for result in edge_case_results.values()
                if result is not None
            )
            
            self.results.add_result(
                "test_edge_cases",
                edge_case_success,
                edge_case_results,
                None if edge_case_success else "One or more edge cases failed"
            )
            
            return {
                "success": edge_case_success,
                "results": edge_case_results
            }
        except Exception as e:
            error_msg = f"Error in test_edge_cases: {str(e)}"
            logger.error(error_msg)
            self.results.add_result("test_edge_cases", False, None, error_msg)
            return {"success": False, "error": error_msg}
    
    async def run_diagnostic_tests(self):
        """
        Run all diagnostic tests for data persistence functionality.
        
        Returns:
            DiagnosticResult with all test results
        """
        logger.info("Starting data persistence diagnostic tests")
        
        try:
            # Test 1: Create a standard session
            logger.info("Creating standard test session")
            standard_session_response = await self.create_test_session(name="DiagnosticTest")
            if not standard_session_response.get("success", False):
                logger.error("Failed to create standard test session, aborting further tests")
                return self.results
            
            standard_session_id = standard_session_response["session_id"]
            
            # Test 2: Create a session with expiration
            logger.info("Creating session with expiration")
            await self.create_test_session(name="ExpiringTest", expiration=3600)  # 1 hour expiration
            
            # Test 3: Set various values in the standard session
            logger.info("Setting values in standard session")
            test_values = {
                "string_value": "test string",
                "integer_value": 42,
                "float_value": 3.14159,
                "boolean_value": True,
                "list_value": [1, 2, 3, 4, 5],
                "dict_value": {"key1": "value1", "key2": "value2"}
            }
            await self.set_session_values(standard_session_id, test_values)
            
            # Test 4: Get the values back
            logger.info("Getting values from standard session")
            await self.get_session_values(standard_session_id, list(test_values.keys()))
            
            # Test 5: Get session info
            logger.info("Getting session info")
            await self.get_session_info(standard_session_id)
            
            # Test 6: Edge cases
            logger.info("Testing edge cases")
            await self.test_edge_cases()
            
            # Print results summary
            self.results.print_summary()
            
            return self.results
        except Exception as e:
            logger.error(f"Error running diagnostic tests: {str(e)}")
            self.results.add_result("run_diagnostic_tests", False, None, str(e))
            self.results.print_summary()
            return self.results


async def main():
    """Main function to run the diagnostic tests."""
    try:
        # Wait a moment for any server startup processes to complete
        await asyncio.sleep(1)
        
        # Create and run the tester
        tester = DataPersistenceTester()
        results = await tester.run_diagnostic_tests()
        
        # Output the results in JSON format
        output_file = "data_persistence_test_results.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(results.get_summary(), f, indent=2, default=str)
            logger.info(f"Detailed results written to {output_file}")
        except Exception as e:
            logger.error(f"Error writing results to file: {str(e)}")
        
        return results
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        sys.exit(0 if results.tests_failed == 0 else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        sys.exit(1)