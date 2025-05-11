"""Test script to validate data session fixes.

This script simulates the behavior of the data persistence functions
to validate our fixes to session handling.
"""

import json
import time
from datetime import datetime
from pathlib import Path
import os

class SessionState:
    """Represents a persistent session state."""
    
    def __init__(self, session_id=None, name=None, expiration=None):
        """Initialize the session state."""
        self.id = session_id or str(int(time.time() * 1000))
        self.name = name or f"Session {self.id}"
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.expiration = expiration  # Seconds until expiration, None for no expiration
        self.data = {}
    
    def set_value(self, key, value):
        """Set a value in the session data."""
        self.data[key] = value
        self.last_accessed = datetime.now()
    
    def get_value(self, key, default=None):
        """Get a value from the session data."""
        self.last_accessed = datetime.now()
        return self.data.get(key, default)
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expiration": self.expiration,
            "data": self.data
        }

def set_session_value(session_id, key, value):
    """Set a value in a data session."""
    try:
        # Ensure session_id is a string
        if session_id is not None:
            session_id = str(session_id)
            print(f"Ensuring session_id is string: {session_id}")
        
        # Try to get the session or create it
        session = get_session(session_id)
        
        # If session not found, try to create it
        if not session:
            print(f"Session {session_id} not found, creating it")
            session = SessionState(session_id=session_id, name=f"Auto-created session {session_id}")
            active_sessions[session_id] = session
            
        # Set value and save
        session.set_value(key, value)
        
        return {
            "content": [{"type": "text", "text": f"Value set successfully"}],
            "success": True,
            "session_id": session_id,
            "key": key
        }
    except Exception as e:
        # Enhanced error reporting
        error_msg = f"Error setting session value: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

def get_session_value(session_id, key, default=None):
    """Get a value from a data session."""
    try:
        # Ensure session_id is a string
        if session_id is not None:
            session_id = str(session_id)
            print(f"Ensuring session_id is string: {session_id}")
        
        # Get session
        session = get_session(session_id)
        
        # If session not found, try to create it
        if not session:
            print(f"Session {session_id} not found, creating it")
            session = SessionState(session_id=session_id, name=f"Auto-created session {session_id}")
            active_sessions[session_id] = session
            
            # Since this is a new session, the key won't exist yet
            value = default
        else:
            # Get value from existing session
            value = session.get_value(key, default)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Value retrieved successfully for key '{key}' from session {session_id}"
                }
            ],
            "success": True,
            "value": value,
            "session_id": session_id,
            "key": key,
            "found": key in (session.data if session else {})
        }
    except Exception as e:
        error_msg = f"Error getting session value: {str(e)}"
        print(error_msg)
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_msg
                }
            ],
            "success": False,
            "error": error_msg,
            "session_id": session_id,
            "key": key
        }

def get_session(session_id):
    """Get a session by ID."""
    if session_id in active_sessions:
        return active_sessions[session_id]
    return None

def create_data_session(name=None, expiration=None):
    """Create a new data session."""
    try:
        # Create session
        session = SessionState(name=name, expiration=expiration)
        
        # Store in active sessions
        active_sessions[session.id] = session
        
        print(f"Created new session {session.id}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Data session created successfully"
                }
            ],
            "success": True,
            "session_id": session.id,
            "name": session.name,
            "created_at": session.created_at.isoformat(),
            "expiration": session.expiration
        }
    except Exception as e:
        print(f"Error creating session: {str(e)}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error creating session: {str(e)}"
                }
            ],
            "success": False,
            "error": str(e)
        }

def main():
    """Run session tests."""
    global active_sessions
    active_sessions = {}
    
    print("Testing Data Session Functions")
    print("=============================")
    
    # Test 1: Create a session
    print("\nTest 1: Creating a data session")
    create_result = create_data_session(name="Test Session")
    print(f"Create session result: {json.dumps(create_result, indent=2)}")
    
    if not create_result.get("success", False):
        print("Failed to create session")
        return
    
    session_id = create_result.get("session_id")
    print(f"Created session with ID: {session_id}")
    
    # Test 2: Set values in the session
    print("\nTest 2: Setting session values")
    set_test_cases = [
        {"key": "string_val", "value": "Hello World"},
        {"key": "int_val", "value": 42},
        {"key": "dict_val", "value": {"name": "Test", "items": [1, 2, 3]}}
    ]
    
    for test in set_test_cases:
        set_result = set_session_value(session_id, test["key"], test["value"])
        print(f"Set session value result for key '{test['key']}': {json.dumps(set_result, indent=2)}")
    
    # Test 3: Get values from the session
    print("\nTest 3: Getting session values")
    for test in set_test_cases:
        get_result = get_session_value(session_id, test["key"])
        print(f"Get session value result for key '{test['key']}': {json.dumps(get_result, indent=2)}")
        
        # Verify the value matches what we set
        if get_result.get("success", False):
            retrieved_value = get_result.get("value")
            expected_value = test["value"]
            if retrieved_value == expected_value:
                print(f"Value verification PASSED for key '{test['key']}'")
            else:
                print(f"Value verification FAILED for key '{test['key']}'. Expected: {expected_value}, Got: {retrieved_value}")
    
    # Test 4: Edge case - Numeric session ID
    print("\nTest 4: Testing numeric session ID")
    numeric_id = 12345
    set_numeric_result = set_session_value(numeric_id, "test_key", "Value set with numeric ID")
    print(f"Set value with numeric ID result: {json.dumps(set_numeric_result, indent=2)}")
    
    # Get the value we just set with numeric ID
    get_numeric_result = get_session_value(numeric_id, "test_key")
    print(f"Get value with numeric ID result: {json.dumps(get_numeric_result, indent=2)}")
    
    # Test 5: Edge case - Create a new session by using non-existent ID
    print("\nTest 5: Testing auto-creation of session")
    auto_create_result = set_session_value("non_existent_session", "auto_key", "Auto-created session value")
    print(f"Auto-creation session result: {json.dumps(auto_create_result, indent=2)}")
    
    # Get the value from the auto-created session
    get_auto_result = get_session_value("non_existent_session", "auto_key")
    print(f"Get value from auto-created session result: {json.dumps(get_auto_result, indent=2)}")
    
    # Test 6: Edge case - Default value for non-existent key
    print("\nTest 6: Testing default value for non-existent key")
    default_result = get_session_value(session_id, "non_existent_key", "default_value")
    print(f"Get non-existent key with default value result: {json.dumps(default_result, indent=2)}")
    
    print("\nAll tests completed")

if __name__ == "__main__":
    main()