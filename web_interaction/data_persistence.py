"""Data Persistence Module for Web Interaction.

This module provides capabilities for persisting and managing data collected
during web interaction sessions, including page content, session data, 
and extracted information.
"""

import asyncio
import json
import logging
import time
import os
import sqlite3
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class DataEntry:
    """Base class for persistent data entries."""
    
    def __init__(self, entry_id=None, entry_type=None, timestamp=None, data=None, metadata=None):
        """Initialize the data entry."""
        self.id = entry_id or str(int(time.time() * 1000))
        self.type = entry_type or "unknown"
        self.timestamp = timestamp or datetime.now().isoformat()
        self.data = data or {}
        self.metadata = metadata or {}
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary after deserialization."""
        return cls(
            entry_id=data.get("id"),
            entry_type=data.get("type"),
            timestamp=data.get("timestamp"),
            data=data.get("data", {}),
            metadata=data.get("metadata", {})
        )

class FileStorage:
    """File-based storage for persistent data."""
    
    def __init__(self, storage_dir, subfolder="data"):
        """Initialize the file storage."""
        self.storage_dir = Path(storage_dir) / subfolder
        self.storage_dir.mkdir(exist_ok=True)
        
        # Create index file for faster lookups
        self.index_file = self.storage_dir / "index.json"
        self.index = self._load_index()
    
    def _load_index(self):
        """Load index from file."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading index: {str(e)}")
                return {}
        return {}
    
    def _save_index(self):
        """Save index to file."""
        try:
            with open(self.index_file, "w") as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
    
    def save(self, entry):
        """Save a data entry to file."""
        try:
            # Create filename based on ID
            filename = f"{entry.id}.json"
            file_path = self.storage_dir / filename
            
            # Save entry to file
            with open(file_path, "w") as f:
                json.dump(entry.to_dict(), f, indent=2)
            
            # Update index
            self.index[entry.id] = {
                "type": entry.type,
                "timestamp": entry.timestamp,
                "path": str(file_path)
            }
            self._save_index()
            
            logger.debug(f"Saved entry {entry.id} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving entry {entry.id}: {str(e)}")
            return False
    
    def load(self, entry_id):
        """Load a data entry from file."""
        try:
            # Check if entry exists in index
            if entry_id not in self.index:
                return None
            
            # Get file path from index
            file_path = self.index[entry_id]["path"]
            
            # Load entry from file
            with open(file_path, "r") as f:
                data = json.load(f)
                entry = DataEntry.from_dict(data)
                
            logger.debug(f"Loaded entry {entry_id} from {file_path}")
            return entry
        except Exception as e:
            logger.error(f"Error loading entry {entry_id}: {str(e)}")
            return None
    
    def delete(self, entry_id):
        """Delete a data entry."""
        try:
            # Check if entry exists in index
            if entry_id not in self.index:
                return False
            
            # Get file path from index
            file_path = self.index[entry_id]["path"]
            
            # Delete file
            Path(file_path).unlink(missing_ok=True)
            
            # Remove from index
            del self.index[entry_id]
            self._save_index()
            
            logger.debug(f"Deleted entry {entry_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting entry {entry_id}: {str(e)}")
            return False
    
    def query(self, entry_type=None, start_time=None, end_time=None, limit=None):
        """Query data entries."""
        try:
            # Get all entries from index
            entries = []
            for entry_id, entry_info in self.index.items():
                # Filter by type
                if entry_type and entry_info["type"] != entry_type:
                    continue
                
                # Filter by time range
                if start_time and entry_info["timestamp"] < start_time:
                    continue
                if end_time and entry_info["timestamp"] > end_time:
                    continue
                
                # Load entry
                entry = self.load(entry_id)
                if entry:
                    entries.append(entry)
            
            # Sort by timestamp
            entries.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            if limit is not None:
                entries = entries[:limit]
            
            logger.debug(f"Query returned {len(entries)} entries")
            return entries
        except Exception as e:
            logger.error(f"Error querying entries: {str(e)}")
            return []

class SQLiteStorage:
    """SQLite-based storage for persistent data."""
    
    def __init__(self, storage_dir, subfolder="data"):
        """Initialize the SQLite storage."""
        self.storage_dir = Path(storage_dir) / subfolder
        self.storage_dir.mkdir(exist_ok=True)
        
        self.db_file = self.storage_dir / "persistence.db"
        self.conn = self._get_connection()
        self._create_tables()
    
    def _get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(str(self.db_file))
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            cursor = self.conn.cursor()
            
            # Create entries table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                type TEXT,
                timestamp TEXT,
                data BLOB,
                metadata BLOB
            )
            ''')
            
            # Create index on type and timestamp
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON entries (type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON entries (timestamp)')
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
    
    def save(self, entry):
        """Save a data entry to database."""
        try:
            # Serialize data and metadata
            data_blob = pickle.dumps(entry.data)
            metadata_blob = pickle.dumps(entry.metadata)
            
            cursor = self.conn.cursor()
            
            # Insert or replace entry
            cursor.execute('''
            INSERT OR REPLACE INTO entries (id, type, timestamp, data, metadata)
            VALUES (?, ?, ?, ?, ?)
            ''', (entry.id, entry.type, entry.timestamp, data_blob, metadata_blob))
            
            self.conn.commit()
            
            logger.debug(f"Saved entry {entry.id} to database")
            return True
        except Exception as e:
            logger.error(f"Error saving entry {entry.id} to database: {str(e)}")
            return False
    
    def load(self, entry_id):
        """Load a data entry from database."""
        try:
            cursor = self.conn.cursor()
            
            # Query entry by ID
            cursor.execute('SELECT id, type, timestamp, data, metadata FROM entries WHERE id = ?', (entry_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Deserialize data and metadata
            entry_id, entry_type, timestamp, data_blob, metadata_blob = row
            data = pickle.loads(data_blob)
            metadata = pickle.loads(metadata_blob)
            
            # Create entry
            entry = DataEntry(
                entry_id=entry_id,
                entry_type=entry_type,
                timestamp=timestamp,
                data=data,
                metadata=metadata
            )
            
            logger.debug(f"Loaded entry {entry_id} from database")
            return entry
        except Exception as e:
            logger.error(f"Error loading entry {entry_id} from database: {str(e)}")
            return None
    
    def delete(self, entry_id):
        """Delete a data entry from database."""
        try:
            cursor = self.conn.cursor()
            
            # Delete entry by ID
            cursor.execute('DELETE FROM entries WHERE id = ?', (entry_id,))
            self.conn.commit()
            
            logger.debug(f"Deleted entry {entry_id} from database")
            return True
        except Exception as e:
            logger.error(f"Error deleting entry {entry_id} from database: {str(e)}")
            return False
    
    def query(self, entry_type=None, start_time=None, end_time=None, limit=None):
        """Query data entries from database."""
        try:
            cursor = self.conn.cursor()
            
            # Build query
            query = 'SELECT id, type, timestamp, data, metadata FROM entries'
            params = []
            
            # Add conditions
            conditions = []
            if entry_type:
                conditions.append('type = ?')
                params.append(entry_type)
            if start_time:
                conditions.append('timestamp >= ?')
                params.append(start_time)
            if end_time:
                conditions.append('timestamp <= ?')
                params.append(end_time)
            
            # Add WHERE clause if there are conditions
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            # Add ORDER BY clause
            query += ' ORDER BY timestamp DESC'
            
            # Add LIMIT clause if specified
            if limit is not None:
                query += ' LIMIT ?'
                params.append(limit)
            
            # Execute query
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Create entries from rows
            entries = []
            for row in rows:
                entry_id, entry_type, timestamp, data_blob, metadata_blob = row
                data = pickle.loads(data_blob)
                metadata = pickle.loads(metadata_blob)
                
                entry = DataEntry(
                    entry_id=entry_id,
                    entry_type=entry_type,
                    timestamp=timestamp,
                    data=data,
                    metadata=metadata
                )
                entries.append(entry)
            
            logger.debug(f"Query returned {len(entries)} entries")
            return entries
        except Exception as e:
            logger.error(f"Error querying entries from database: {str(e)}")
            return []
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

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
    
    def is_expired(self):
        """Check if the session is expired."""
        if self.expiration is None:
            return False
        
        expiration_time = self.last_accessed + timedelta(seconds=self.expiration)
        return datetime.now() > expiration_time
    
    def update_access_time(self):
        """Update the last accessed time."""
        self.last_accessed = datetime.now()
    
    def set_value(self, key, value):
        """Set a value in the session data."""
        self.data[key] = value
        self.update_access_time()
    
    def get_value(self, key, default=None):
        """Get a value from the session data."""
        self.update_access_time()
        return self.data.get(key, default)
    
    def delete_value(self, key):
        """Delete a value from the session data."""
        if key in self.data:
            del self.data[key]
        self.update_access_time()
    
    def clear(self):
        """Clear all session data."""
        self.data = {}
        self.update_access_time()
    
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
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary after deserialization."""
        session = cls(
            session_id=data.get("id"),
            name=data.get("name"),
            expiration=data.get("expiration")
        )
        session.created_at = datetime.fromisoformat(data.get("created_at"))
        session.last_accessed = datetime.fromisoformat(data.get("last_accessed"))
        session.data = data.get("data", {})
        return session

class DataPersistenceManager:
    """Manages data persistence for web interactions."""
    
    def __init__(self, browser_manager, storage_dir=None):
        """Initialize the data persistence manager."""
        self.browser_manager = browser_manager
        
        # Set storage directory
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".claude_web_interaction")
        
        # Set up storage backends
        self.file_storage = FileStorage(self.storage_dir, "file_data")
        self.db_storage = SQLiteStorage(self.storage_dir, "db_data")
        
        # Set up session storage
        self.sessions_dir = Path(self.storage_dir) / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        self.active_sessions = {}
        
        # Load existing sessions
        self._load_sessions()
    
    def _load_sessions(self):
        """Load existing sessions from storage."""
        try:
            # Look for session files
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    with open(session_file, "r") as f:
                        session_data = json.load(f)
                        session = SessionState.from_dict(session_data)
                        
                        # Skip expired sessions
                        if not session.is_expired():
                            self.active_sessions[session.id] = session
                except Exception as e:
                    logger.error(f"Error loading session from {session_file}: {str(e)}")
            
            logger.info(f"Loaded {len(self.active_sessions)} active sessions")
        except Exception as e:
            logger.error(f"Error loading sessions: {str(e)}")
    
    def _save_session(self, session):
        """Save a session to storage."""
        try:
            session_file = self.sessions_dir / f"{session.id}.json"
            with open(session_file, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
            
            logger.debug(f"Saved session {session.id} to {session_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving session {session.id}: {str(e)}")
            return False
    
    def create_session(self, name=None, expiration=None):
        """Create a new session."""
        try:
            # Create session
            session = SessionState(name=name, expiration=expiration)
            
            # Store in active sessions
            self.active_sessions[session.id] = session
            
            # Save to storage
            self._save_session(session)
            
            logger.info(f"Created new session {session.id}")
            return session
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return None
    
    def get_session(self, session_id):
        """Get a session by ID."""
        try:
            # Check if session is in active sessions
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Check if expired
                if session.is_expired():
                    logger.info(f"Session {session_id} has expired")
                    self.delete_session(session_id)
                    return None
                
                # Update access time
                session.update_access_time()
                self._save_session(session)
                
                return session
            
            # Try to load from storage
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                try:
                    with open(session_file, "r") as f:
                        session_data = json.load(f)
                        session = SessionState.from_dict(session_data)
                        
                        # Check if expired
                        if session.is_expired():
                            logger.info(f"Session {session_id} has expired")
                            session_file.unlink(missing_ok=True)
                            return None
                        
                        # Update access time
                        session.update_access_time()
                        self._save_session(session)
                        
                        # Add to active sessions
                        self.active_sessions[session.id] = session
                        
                        return session
                except Exception as e:
                    logger.error(f"Error loading session {session_id}: {str(e)}")
            
            logger.warning(f"Session {session_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    def delete_session(self, session_id):
        """Delete a session."""
        try:
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Delete session file
            session_file = self.sessions_dir / f"{session_id}.json"
            session_file.unlink(missing_ok=True)
            
            logger.info(f"Deleted session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    def clean_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            # Check active sessions
            expired_sessions = []
            for session_id, session in list(self.active_sessions.items()):
                if session.is_expired():
                    expired_sessions.append(session_id)
            
            # Delete expired sessions
            for session_id in expired_sessions:
                self.delete_session(session_id)
            
            # Check session files
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    with open(session_file, "r") as f:
                        session_data = json.load(f)
                        session = SessionState.from_dict(session_data)
                        
                        if session.is_expired():
                            session_file.unlink(missing_ok=True)
                            logger.info(f"Deleted expired session file for {session.id}")
                except Exception as e:
                    logger.error(f"Error checking session file {session_file}: {str(e)}")
            
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            return len(expired_sessions)
        except Exception as e:
            logger.error(f"Error cleaning expired sessions: {str(e)}")
            return 0
    
    def persist_page_data(self, page_id, data_type, data, metadata=None):
        """Persist data for a page."""
        try:
            # Create data entry
            entry = DataEntry(
                entry_type=f"page_{data_type}",
                data=data,
                metadata=metadata or {"page_id": page_id}
            )
            
            # Add page info to metadata if available
            if page_id in self.browser_manager.page_metadata:
                page_info = self.browser_manager.page_metadata[page_id]
                entry.metadata.update({
                    "url": page_info.get("last_url", ""),
                    "title": page_info.get("title", "")
                })
            
            # Save to both storage backends
            self.file_storage.save(entry)
            self.db_storage.save(entry)
            
            logger.info(f"Persisted {data_type} data for page {page_id}")
            return entry.id
        except Exception as e:
            logger.error(f"Error persisting {data_type} data for page {page_id}: {str(e)}")
            return None
    
    def persist_extracted_data(self, data_type, data, metadata=None):
        """Persist extracted data."""
        try:
            # Create data entry
            entry = DataEntry(
                entry_type=f"extracted_{data_type}",
                data=data,
                metadata=metadata or {}
            )
            
            # Save to both storage backends
            self.file_storage.save(entry)
            self.db_storage.save(entry)
            
            logger.info(f"Persisted extracted {data_type} data")
            return entry.id
        except Exception as e:
            logger.error(f"Error persisting extracted {data_type} data: {str(e)}")
            return None
    
    def load_persisted_data(self, entry_id):
        """Load persisted data."""
        try:
            # Try to load from database first (faster)
            entry = self.db_storage.load(entry_id)
            
            # Fall back to file storage
            if not entry:
                entry = self.file_storage.load(entry_id)
            
            if entry:
                logger.info(f"Loaded persisted data entry {entry_id}")
                return entry
            
            logger.warning(f"Data entry {entry_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error loading persisted data {entry_id}: {str(e)}")
            return None
    
    def delete_persisted_data(self, entry_id):
        """Delete persisted data."""
        try:
            # Delete from both storage backends
            self.file_storage.delete(entry_id)
            self.db_storage.delete(entry_id)
            
            logger.info(f"Deleted persisted data entry {entry_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting persisted data {entry_id}: {str(e)}")
            return False
    
    def query_persisted_data(self, entry_type=None, start_time=None, end_time=None, limit=None, use_db=True):
        """Query persisted data."""
        try:
            # Use database for queries if requested (typically faster for complex queries)
            if use_db:
                entries = self.db_storage.query(entry_type, start_time, end_time, limit)
            else:
                entries = self.file_storage.query(entry_type, start_time, end_time, limit)
            
            logger.info(f"Query returned {len(entries)} persisted data entries")
            return entries
        except Exception as e:
            logger.error(f"Error querying persisted data: {str(e)}")
            return []
    
    def close(self):
        """Close all storage resources."""
        try:
            # Close database connection
            self.db_storage.close()
            
            # Save active sessions
            for session in self.active_sessions.values():
                self._save_session(session)
            
            logger.info("Closed data persistence resources")
        except Exception as e:
            logger.error(f"Error closing data persistence resources: {str(e)}")

def register_data_persistence_tools(mcp, browser_manager):
    """Register data persistence tools with the MCP server."""
    # Create data persistence manager instance
    persistence_manager = DataPersistenceManager(browser_manager)
    
    @mcp.tool()
    async def create_data_session(name: Optional[str] = None, expiration: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new data persistence session.
        
        Args:
            name: Optional name for the session
            expiration: Optional number of seconds until session expiration
            
        Returns:
            Dict with session information
        """
        logger.info(f"Creating data session with name: {name}, expiration: {expiration}")
        try:
            # Create session
            session = persistence_manager.create_session(name, expiration)
            
            if session:
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
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to create data session"
                        }
                    ],
                    "success": False,
                    "error": "Failed to create data session"
                }
        except Exception as e:
            logger.error(f"Error creating data session: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error creating data session: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_data_session(session_id: str) -> Dict[str, Any]:
        """
        Get information about a data session.
        
        Args:
            session_id: ID of the session to get
            
        Returns:
            Dict with session information
        """
        logger.info(f"Getting data session {session_id}")
        try:
            # Get session
            session = persistence_manager.get_session(session_id)
            
            if session:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Data session retrieved successfully"
                        }
                    ],
                    "success": True,
                    "session_id": session.id,
                    "name": session.name,
                    "created_at": session.created_at.isoformat(),
                    "last_accessed": session.last_accessed.isoformat(),
                    "expiration": session.expiration,
                    "data_count": len(session.data)
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Data session {session_id} not found"
                        }
                    ],
                    "success": False,
                    "error": f"Data session {session_id} not found"
                }
        except Exception as e:
            logger.error(f"Error getting data session {session_id}: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting data session {session_id}: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def delete_data_session(session_id: str) -> Dict[str, Any]:
        """
        Delete a data session.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            Dict with deletion result
        """
        logger.info(f"Deleting data session {session_id}")
        try:
            # Delete session
            result = persistence_manager.delete_session(session_id)
            
            if result:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Data session {session_id} deleted successfully"
                        }
                    ],
                    "success": True
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to delete data session {session_id}"
                        }
                    ],
                    "success": False,
                    "error": f"Failed to delete data session {session_id}"
                }
        except Exception as e:
            logger.error(f"Error deleting data session {session_id}: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error deleting data session {session_id}: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def set_session_value(session_id: str, key: str, value: Any) -> Dict[str, Any]:
        """
        Set a value in a data session.
        
        Args:
            session_id: ID of the session
            key: Key to set
            value: Value to set
            
        Returns:
            Dict with result
        """
        logger.info(f"Setting value for key '{key}' in session {session_id}")
        try:
            # Ensure session_id is a string
            if session_id is not None:
                session_id = str(session_id)
                logger.info(f"Ensuring session_id is string: {session_id}")
            
            # Get session
            session = persistence_manager.get_session(session_id)
            
            # If session not found, try to create it
            if not session:
                logger.warning(f"Session {session_id} not found, trying to create it")
                
                # Try to create a new session with this ID
                session = SessionState(session_id=session_id, name=f"Auto-created session {session_id}")
                persistence_manager.active_sessions[session_id] = session
                persistence_manager._save_session(session)
                logger.info(f"Created new session with ID {session_id}")
            
            # Set value
            session.set_value(key, value)
            
            # Save session
            persistence_manager._save_session(session)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Value set successfully for key '{key}' in session {session_id}"
                    }
                ],
                "success": True,
                "session_id": session_id,
                "key": key
            }
        except Exception as e:
            error_msg = f"Error setting session value: {str(e)}"
            logger.error(error_msg)
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
    
    @mcp.tool()
    async def get_session_value(session_id: str, key: str, default: Optional[Any] = None) -> Dict[str, Any]:
        """
        Get a value from a data session.
        
        Args:
            session_id: ID of the session
            key: Key to get
            default: Default value if key not found
            
        Returns:
            Dict with value
        """
        logger.info(f"Getting value for key '{key}' from session {session_id}")
        try:
            # Ensure session_id is a string
            if session_id is not None:
                session_id = str(session_id)
                logger.info(f"Ensuring session_id is string: {session_id}")
            
            # Get session
            session = persistence_manager.get_session(session_id)
            
            # If session not found, try to create it
            if not session:
                logger.warning(f"Session {session_id} not found, trying to create it")
                
                # Try to create a new session with this ID
                session = SessionState(session_id=session_id, name=f"Auto-created session {session_id}")
                persistence_manager.active_sessions[session_id] = session
                persistence_manager._save_session(session)
                logger.info(f"Created new session with ID {session_id}")
                
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
            logger.error(error_msg)
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
    
    @mcp.tool()
    async def persist_page_content(page_id: str, data_type: str = "content", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Persist content from a page.
        
        Args:
            page_id: ID of the page
            data_type: Type of data to persist ("content", "html", "screenshot", etc.)
            metadata: Optional metadata to store with the content
            
        Returns:
            Dict with persistence result
        """
        logger.info(f"Persisting {data_type} for page {page_id}")
        try:
            # Ensure page_id is a string
            if page_id is not None:
                page_id = str(page_id)
            
            # Get the page
            page = browser_manager.active_pages.get(page_id)
            if not page:
                logger.error(f"Page {page_id} not found")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Page {page_id} not found"
                        }
                    ],
                    "success": False,
                    "error": f"Page {page_id} not found"
                }
            
            # Extract data based on type
            data = {}
            
            if data_type == "content":
                # Extract visible text content
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
                
                data["text_content"] = text_content
                data["url"] = page.url
                data["title"] = await page.title()
                
            elif data_type == "html":
                # Get page HTML
                html_content = await page.content()
                data["html"] = html_content
                data["url"] = page.url
                data["title"] = await page.title()
                
            elif data_type == "screenshot":
                # Take screenshot and convert to base64
                screenshot_path = str(Path(persistence_manager.storage_dir) / "temp_screenshot.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                
                # Read screenshot file and convert to base64
                import base64
                with open(screenshot_path, "rb") as f:
                    screenshot_data = base64.b64encode(f.read()).decode("utf-8")
                
                # Remove temporary file
                Path(screenshot_path).unlink(missing_ok=True)
                
                data["screenshot"] = screenshot_data
                data["url"] = page.url
                data["title"] = await page.title()
                
            elif data_type == "metadata":
                # Extract page metadata
                meta_data = await page.evaluate('''() => {
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
                
                data["metadata"] = meta_data
                data["url"] = page.url
                data["title"] = await page.title()
            
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unsupported data type: {data_type}"
                        }
                    ],
                    "success": False,
                    "error": f"Unsupported data type: {data_type}"
                }
            
            # Include metadata if provided
            meta = metadata or {}
            meta["page_id"] = page_id
            meta["data_type"] = data_type
            meta["timestamp"] = datetime.now().isoformat()
            
            # Persist data
            entry_id = persistence_manager.persist_page_data(page_id, data_type, data, meta)
            
            if entry_id:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"{data_type} data persisted successfully for page {page_id}"
                        }
                    ],
                    "success": True,
                    "entry_id": entry_id,
                    "page_id": page_id,
                    "data_type": data_type
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to persist {data_type} data for page {page_id}"
                        }
                    ],
                    "success": False,
                    "error": f"Failed to persist {data_type} data for page {page_id}"
                }
        except Exception as e:
            logger.error(f"Error persisting page content: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error persisting page content: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def persist_extracted_data(data_type: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Persist extracted data.
        
        Args:
            data_type: Type of data to persist ("json", "table", "list", etc.)
            data: Data to persist
            metadata: Optional metadata to store with the data
            
        Returns:
            Dict with persistence result
        """
        logger.info(f"Persisting extracted {data_type} data")
        try:
            # Include metadata if provided
            meta = metadata or {}
            meta["data_type"] = data_type
            meta["timestamp"] = datetime.now().isoformat()
            
            # Persist data
            entry_id = persistence_manager.persist_extracted_data(data_type, data, meta)
            
            if entry_id:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Extracted {data_type} data persisted successfully"
                        }
                    ],
                    "success": True,
                    "entry_id": entry_id,
                    "data_type": data_type
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to persist extracted {data_type} data"
                        }
                    ],
                    "success": False,
                    "error": f"Failed to persist extracted {data_type} data"
                }
        except Exception as e:
            logger.error(f"Error persisting extracted data: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error persisting extracted data: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def get_persisted_data(entry_id: str) -> Dict[str, Any]:
        """
        Get persisted data by ID.
        
        Args:
            entry_id: ID of the data entry to get
            
        Returns:
            Dict with data
        """
        logger.info(f"Getting persisted data {entry_id}")
        try:
            # Load data
            entry = persistence_manager.load_persisted_data(entry_id)
            
            if entry:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Persisted data retrieved successfully"
                        }
                    ],
                    "success": True,
                    "entry_id": entry.id,
                    "type": entry.type,
                    "timestamp": entry.timestamp,
                    "data": entry.data,
                    "metadata": entry.metadata
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Persisted data {entry_id} not found"
                        }
                    ],
                    "success": False,
                    "error": f"Persisted data {entry_id} not found"
                }
        except Exception as e:
            logger.error(f"Error getting persisted data {entry_id}: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting persisted data {entry_id}: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def query_persisted_data(entry_type: Optional[str] = None, start_time: Optional[str] = None, 
                                 end_time: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Query persisted data.
        
        Args:
            entry_type: Optional type of data to query
            start_time: Optional start time ISO string for query range
            end_time: Optional end time ISO string for query range
            limit: Optional maximum number of entries to return
            
        Returns:
            Dict with query results
        """
        logger.info(f"Querying persisted data with type: {entry_type}, limit: {limit}")
        try:
            # Query data
            entries = persistence_manager.query_persisted_data(entry_type, start_time, end_time, limit)
            
            # Convert entries to dictionaries
            entry_dicts = [entry.to_dict() for entry in entries]
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Retrieved {len(entries)} persisted data entries"
                    }
                ],
                "success": True,
                "entries": entry_dicts,
                "count": len(entries)
            }
        except Exception as e:
            logger.error(f"Error querying persisted data: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error querying persisted data: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def delete_persisted_data(entry_id: str) -> Dict[str, Any]:
        """
        Delete persisted data by ID.
        
        Args:
            entry_id: ID of the data entry to delete
            
        Returns:
            Dict with deletion result
        """
        logger.info(f"Deleting persisted data {entry_id}")
        try:
            # Delete data
            result = persistence_manager.delete_persisted_data(entry_id)
            
            if result:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Persisted data {entry_id} deleted successfully"
                        }
                    ],
                    "success": True
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to delete persisted data {entry_id}"
                        }
                    ],
                    "success": False,
                    "error": f"Failed to delete persisted data {entry_id}"
                }
        except Exception as e:
            logger.error(f"Error deleting persisted data {entry_id}: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error deleting persisted data {entry_id}: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    @mcp.tool()
    async def cleanup_expired_sessions() -> Dict[str, Any]:
        """
        Clean up expired sessions.
        
        Returns:
            Dict with cleanup result
        """
        logger.info("Cleaning up expired sessions")
        try:
            # Clean up sessions
            count = persistence_manager.clean_expired_sessions()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Cleaned up {count} expired sessions"
                    }
                ],
                "success": True,
                "count": count
            }
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error cleaning up expired sessions: {str(e)}"
                    }
                ],
                "success": False,
                "error": str(e)
            }
    
    # Register cleanup on exit
    import atexit
    atexit.register(persistence_manager.close)
    
    logger.info("Data persistence tools registered")
    
    # Return the persistence manager instance and tools
    return {
        "persistence_manager": persistence_manager,
        "create_data_session": create_data_session,
        "get_data_session": get_data_session,
        "delete_data_session": delete_data_session,
        "set_session_value": set_session_value,
        "get_session_value": get_session_value,
        "persist_page_content": persist_page_content,
        "persist_extracted_data": persist_extracted_data,
        "get_persisted_data": get_persisted_data,
        "query_persisted_data": query_persisted_data,
        "delete_persisted_data": delete_persisted_data,
        "cleanup_expired_sessions": cleanup_expired_sessions
    }