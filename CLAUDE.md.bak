# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Lint/Test Commands

- **Run the server**: `python -m claude_mcp_scaffold`
- **Install dependencies**: `pip install -r requirements.txt` (if present)
- **Install dev dependencies**: `pip install -e ".[dev]"` (for development)
- **Lint code**: `flake8 claude_mcp_scaffold web_interaction`
- **Type check**: `mypy claude_mcp_scaffold web_interaction`
- **Run tests**: `pytest tests/`
- **Run single test**: `pytest tests/file_name.py::test_function_name`

## Code Style Guidelines

- **Type hints**: Use type annotations for all function parameters and return values
- **Docstrings**: Use Google-style docstrings with Args/Returns sections
- **Imports**: Group imports in order: standard library, third-party, local
- **Error handling**: Use try/except blocks with specific exceptions, log errors with logger
- **Logging**: Use the module-level logger (`logger = logging.getLogger(__name__)`)
- **Naming**: 
  - Functions/variables: snake_case
  - Classes: PascalCase
  - Constants: UPPER_SNAKE_CASE
- **Async**: Use async/await consistently in asynchronous code paths
- **Environment variables**: Load with dotenv, use fallback values for optional settings
- **Comments**: Include comments for complex logic, avoid redundant comments

## MCP Tools Structure

- Web interaction tools should follow the pattern used in unified_tool.py
- Register tools with the MCP server in server.py
- Tools should log their actions at INFO level for debugging
- Properly document each tool with docstrings explaining parameters and return values