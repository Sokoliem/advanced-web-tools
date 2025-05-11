"""System operations and process management."""

import os
import psutil
import platform
import subprocess
import logging
from typing import Dict, Any, List, Optional

from .config_manager import computer_config

logger = logging.getLogger(__name__)


class SystemOperations:
    """Handles system-level operations."""
    
    def __init__(self):
        self.platform = platform.system().lower()
    
    async def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information.
        
        Returns:
            Dict containing system information
        """
        try:
            info = {
                "platform": self.platform,
                "platform_details": platform.platform(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                }
            }
            return info
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {"error": f"Failed to get system info: {str(e)}"}
    
    async def list_processes(self, 
                           filter_name: Optional[str] = None,
                           sort_by: str = "memory") -> Dict[str, Any]:
        """
        List running processes.
        
        Args:
            filter_name: Optional filter by process name
            sort_by: Sort by 'memory', 'cpu', or 'name'
        
        Returns:
            Dict containing process information
        """
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    if filter_name and filter_name.lower() not in info['name'].lower():
                        continue
                    
                    processes.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "cpu_percent": info['cpu_percent'],
                        "memory_percent": info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort processes
            if sort_by == "memory":
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            elif sort_by == "cpu":
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda x: x['name'])
            
            return {
                "processes": processes,
                "count": len(processes)
            }
            
        except Exception as e:
            logger.error(f"Error listing processes: {str(e)}")
            return {"error": f"Failed to list processes: {str(e)}"}
    
    async def start_application(self, 
                              application_path: str,
                              arguments: Optional[List[str]] = None,
                              wait: bool = False) -> Dict[str, Any]:
        """
        Start an application.
        
        Args:
            application_path: Path to the application
            arguments: Optional arguments
            wait: Whether to wait for the process to complete
        
        Returns:
            Dict with the result
        """
        try:
            cmd = [application_path]
            if arguments:
                cmd.extend(arguments)
            
            if wait:
                result = subprocess.run(cmd, capture_output=True, text=True)
                return {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                process = subprocess.Popen(cmd)
                return {
                    "success": True,
                    "pid": process.pid
                }
                
        except Exception as e:
            logger.error(f"Error starting application: {str(e)}")
            return {"error": f"Failed to start application: {str(e)}"}
    
    async def kill_process(self, 
                          pid: Optional[int] = None,
                          name: Optional[str] = None) -> Dict[str, Any]:
        """
        Kill a process by PID or name.
        
        Args:
            pid: Process ID
            name: Process name
        
        Returns:
            Dict with the result
        """
        try:
            killed = []
            
            if pid:
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    killed.append({"pid": pid, "name": proc.name()})
                except psutil.NoSuchProcess:
                    return {"error": f"Process with PID {pid} not found"}
            
            elif name:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if name.lower() in proc.info['name'].lower():
                            proc.terminate()
                            killed.append({"pid": proc.info['pid'], "name": proc.info['name']})
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                if not killed:
                    return {"error": f"No processes found with name '{name}'"}
            
            else:
                return {"error": "Either PID or name must be provided"}
            
            return {
                "success": True,
                "killed": killed
            }
            
        except Exception as e:
            logger.error(f"Error killing process: {str(e)}")
            return {"error": f"Failed to kill process: {str(e)}"}
    
    async def execute_command(self, 
                            command: str,
                            shell: bool = True,
                            timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute a shell command.
        
        Args:
            command: Command to execute
            shell: Whether to use shell
            timeout: Optional timeout in seconds
        
        Returns:
            Dict with the result
        """
        # Check if command is blocked
        blocked_commands = computer_config.get('safety', 'blocked_commands', [])
        for blocked in blocked_commands:
            if blocked in command:
                return {"error": f"Command blocked for safety: contains '{blocked}'"}
        
        # Use config timeout if not provided
        if timeout is None:
            timeout = computer_config.get('system', 'command_timeout', 30.0)
        
        # Check if confirmation required
        if computer_config.get('safety', 'require_confirmation_for_commands', False):
            logger.warning(f"Command execution requires confirmation: {command}")
            # In a real implementation, this would prompt for user confirmation
            # For now, we'll just log it
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return {"error": f"Failed to execute command: {str(e)}"}
    
    async def get_environment_variables(self) -> Dict[str, Any]:
        """
        Get environment variables.
        
        Returns:
            Dict containing environment variables
        """
        try:
            return {
                "variables": dict(os.environ),
                "count": len(os.environ)
            }
        except Exception as e:
            logger.error(f"Error getting environment variables: {str(e)}")
            return {"error": f"Failed to get environment variables: {str(e)}"}
    
    async def set_environment_variable(self, 
                                     name: str, 
                                     value: str) -> Dict[str, Any]:
        """
        Set an environment variable.
        
        Args:
            name: Variable name
            value: Variable value
        
        Returns:
            Dict with the result
        """
        try:
            os.environ[name] = value
            return {
                "success": True,
                "variable": name,
                "value": value
            }
        except Exception as e:
            logger.error(f"Error setting environment variable: {str(e)}")
            return {"error": f"Failed to set environment variable: {str(e)}"}
    
    async def get_clipboard_content(self) -> Dict[str, Any]:
        """
        Get clipboard content.
        
        Returns:
            Dict with clipboard content
        """
        try:
            import pyperclip
            content = pyperclip.paste()
            return {
                "content": content,
                "length": len(content)
            }
        except ImportError:
            return {"error": "pyperclip not installed"}
        except Exception as e:
            logger.error(f"Error getting clipboard content: {str(e)}")
            return {"error": f"Failed to get clipboard content: {str(e)}"}
    
    async def set_clipboard_content(self, content: str) -> Dict[str, Any]:
        """
        Set clipboard content.
        
        Args:
            content: Content to set
        
        Returns:
            Dict with the result
        """
        try:
            import pyperclip
            pyperclip.copy(content)
            return {
                "success": True,
                "length": len(content)
            }
        except ImportError:
            return {"error": "pyperclip not installed"}
        except Exception as e:
            logger.error(f"Error setting clipboard content: {str(e)}")
            return {"error": f"Failed to set clipboard content: {str(e)}"}
