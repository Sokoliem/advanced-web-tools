# Claude MCP Scaffold Tools Inventory

This document provides a comprehensive inventory of all 78 tools available in the Claude MCP Scaffold server, categorized by function with capabilities and use cases.

## Core Utility Tools

### 1. `echo`
**Capabilities:** Returns the input message back to the caller.
- Max message length configurable
- Content type formatting

**Use Cases:**
1. Testing connectivity to the MCP server
2. Validating that the MCP protocol is functioning correctly
3. Echo back processed or formatted text for verification

### 2. `calculator`
**Capabilities:** Performs mathematical operations with configurability.
- Basic operations: add, subtract, multiply, divide
- Advanced operations: power, root, log, modulo
- Configurable precision and output format (standard/scientific)

**Use Cases:**
1. Performing complex calculations within workflows
2. Converting between numeric formats with precision control
3. Support mathematical operations without external calculator dependencies

### 3. `server_status`
**Capabilities:** Provides comprehensive server status information.
- Reports server version, name, and tools count
- Shows browser initialization status and active pages
- Includes enhanced capabilities status
- Displays computer interaction tool availability

**Use Cases:**
1. Diagnosing server health and configuration issues
2. Verifying enabled capabilities before starting operations
3. Troubleshooting browser or computer interaction problems

### 4. `get_config`
**Capabilities:** Retrieves current server configuration.
- Returns full configuration object
- Includes web, computer, and feature settings

**Use Cases:**
1. Checking current server configuration before operations
2. Verifying environment-specific settings
3. Debugging configuration-related issues

### 5. `update_config`
**Capabilities:** Updates a specific configuration value.
- Can modify any section and key in the configuration
- Persists changes to the configuration file
- Returns old and new values for verification

**Use Cases:**
1. Enabling or disabling specific features dynamically
2. Adjusting timeout values based on network conditions
3. Configuring browser or computer interaction parameters

### 6. `reload_config`
**Capabilities:** Reloads configuration from the file.
- Refreshes configuration from disk
- Applies environment variable overrides

**Use Cases:**
1. Refreshing configuration after external changes
2. Resetting to the latest configuration values after testing changes
3. Applying new environment variable settings without restart

## Web Interaction Tools

### 7. `web_interact`
**Capabilities:** Unified tool for multiple web operations in sequence.
- Supports navigation, content extraction, element finding, interaction
- Maintains state between operations
- Handles page creation and management
- Includes debug mode for troubleshooting

**Use Cases:**
1. Multi-step web workflows like form filling and submission
2. Content extraction with pre-navigation and element interaction
3. Automating complex web interactions with state persistence

### 8. `navigate`
**Capabilities:** Navigate to a URL in a browser.
- Creates or reuses browser pages
- Configurable wait conditions (load, domcontentloaded, networkidle)
- Returns page information after navigation

**Use Cases:**
1. Opening a specific web page to begin interaction
2. Navigating between pages in a multi-step workflow
3. Loading web applications for testing or automation

### 9. `extract_page_content`
**Capabilities:** Extracts content from the current page.
- Retrieves visible text content
- Extracts page metadata (title, meta tags)
- Optional HTML content inclusion
- Filters for visible elements only

**Use Cases:**
1. Gathering article or document text for analysis
2. Extracting metadata for cataloging web pages
3. Collecting webpage content for summarization or knowledge extraction

### 10. `semantic_find`
**Capabilities:** Finds elements using natural language descriptions.
- Uses multiple selectors and strategies to locate elements
- Scores elements by relevance to the description
- Returns element details including position and text content
- Handles various element types (buttons, links, inputs, etc.)

**Use Cases:**
1. Finding UI elements described in natural language
2. Locating interactive elements for subsequent automation
3. Identifying content areas based on semantic descriptions

### 11. `interact_with_element`
**Capabilities:** Interacts with elements on the page.
- Supports multiple interaction types: click, type, select, hover, focus, screenshot
- First finds elements semantically before interaction
- Waits after interaction if specified
- Returns page state after interaction

**Use Cases:**
1. Clicking buttons or links in web applications
2. Filling form fields with specified text
3. Taking screenshots of specific elements for verification

### 12. `extract_structured_data`
**Capabilities:** Extracts structured data from web pages.
- Supports multiple data types: product, article, list, table, auto
- Auto-detection of content type
- Extracts JSON-LD data
- Handles various page structures

**Use Cases:**
1. Extracting product information from e-commerce sites
2. Gathering article data from news or blog pages
3. Collecting tabular data from information-rich pages

### 13. `run_web_workflow`
**Capabilities:** Runs multi-step web workflows.
- Processes sequences of URLs and actions
- Supports navigation, clicking, typing, and extraction
- Collects results from each step
- Handles errors at each stage

**Use Cases:**
1. Automating form submission workflows
2. Data collection across multiple related pages
3. Performing sequence of actions for testing or verification

### 14. `puppeteer_click`
**Capabilities:** Low-level click on elements with selector.
- Uses CSS selectors for precise targeting
- Includes retry mechanisms for element finding
- Shows visual feedback during interaction

**Use Cases:**
1. Clicking elements that require precise selector targeting
2. Interacting with complex web applications
3. Automating UI testing with specific element selection

### 15. `puppeteer_fill`
**Capabilities:** Low-level filling of form elements with selector.
- Uses CSS selectors for precise targeting
- Clears existing text before filling
- Handles various input types

**Use Cases:**
1. Filling form fields that require precise selector targeting
2. Automating data entry in complex web forms
3. Setting input values for testing form validation

### 16. `execute_console_command`
**Capabilities:** Executes JavaScript in the browser console.
- Runs custom JavaScript on the page
- Returns execution results
- Handles different JavaScript execution contexts

**Use Cases:**
1. Running custom scripts to extract or modify page data
2. Accessing JavaScript APIs not directly exposed through tools
3. Debugging page behavior with custom scripts

### 17. `get_console_logs`
**Capabilities:** Retrieves console logs from the browser.
- Collects all console messages including errors
- Supports filtering by page ID
- Returns detailed log entries with timestamps

**Use Cases:**
1. Debugging JavaScript errors on pages
2. Monitoring application logging
3. Capturing informational messages from the page

### 18. `get_page_errors`
**Capabilities:** Retrieves JavaScript errors from pages.
- Collects all error messages
- Supports filtering by page ID
- Returns detailed error entries with stack traces

**Use Cases:**
1. Identifying JavaScript errors for debugging
2. Validating page stability and error handling
3. Detecting runtime issues in web applications

### 19. `get_browser_tabs`
**Capabilities:** Gets detailed information about all open browser tabs.
- Lists all active tabs with URLs and titles
- Shows tab activity status and metrics
- Provides information about tab management

**Use Cases:**
1. Monitoring browser resource usage
2. Managing multiple tabs in complex workflows
3. Identifying inactive or problematic tabs

### 20. `clean_browser_tabs`
**Capabilities:** Cleans up browser tabs by closing inactive ones.
- Closes tabs based on inactivity time
- Option to force cleanup regardless of activity
- Returns cleanup statistics

**Use Cases:**
1. Preventing browser resource exhaustion during long sessions
2. Cleaning up after completing multi-tab workflows
3. Managing browser memory usage in automated processes

### 21. `clear_browser_state`
**Capabilities:** Resets all browser state and closes tabs.
- Closes all active pages
- Clears stored metadata and state
- Provides complete browser reset

**Use Cases:**
1. Starting fresh after completing a workflow
2. Recovering from browser state issues
3. Ensuring clean state for new operations

### 22. `web_interact_advanced`
**Capabilities:** Advanced unified tool with improved capabilities.
- Session management for organizing related pages
- Multi-browser support (Chromium, Firefox, WebKit)
- Enhanced element finding and interaction
- Advanced error handling and recovery

**Use Cases:**
1. Complex workflows requiring session organization
2. Cross-browser testing and compatibility
3. Operations requiring sophisticated error recovery

### 23. `diagnostics_report`
**Capabilities:** Generates a comprehensive diagnostic report.
- Collects browser information and status
- Reports error statistics and patterns
- Includes system information
- Provides recommendations for issue resolution

**Use Cases:**
1. Troubleshooting browser automation issues
2. Diagnosing error patterns across sessions
3. Generating reports for technical support

### 24. `fix_common_issues`
**Capabilities:** Attempts to fix common browser issues.
- Clears cookies
- Restarts problematic pages
- Resets error statistics
- Performs general browser maintenance

**Use Cases:**
1. Recovering from common error conditions
2. Resolving cookie or session-related issues
3. Fixing browser state problems without manual intervention

### 25. `take_element_debug_screenshot`
**Capabilities:** Takes detailed screenshots of elements with debug info.
- Captures element states with annotations
- Highlights element properties and positioning
- Includes debug overlays for visual diagnosis

**Use Cases:**
1. Debugging element positioning or styling issues
2. Documenting UI element state for reporting
3. Capturing visual element state during automation

### 26. `create_element_visualization`
**Capabilities:** Generates visual representation of element state.
- Creates visual diagrams of element properties
- Shows element hierarchy and relationships
- Visualizes event listeners and dynamic behaviors

**Use Cases:**
1. Analyzing complex element structures
2. Debugging event handling and interaction issues
3. Documenting element properties for development

### 27. `create_page_structure_visualization`
**Capabilities:** Visualizes the DOM structure of a page.
- Generates visual representation of page structure
- Shows element hierarchy and nesting
- Highlights important structural elements

**Use Cases:**
1. Analyzing page layout for automation planning
2. Debugging structural issues in complex pages
3. Creating documentation of page architecture

### 28. `create_debug_timeline`
**Capabilities:** Creates a timeline of page/element interactions.
- Records interaction sequence with timestamps
- Shows state changes over time
- Visualizes page and element lifecycle events

**Use Cases:**
1. Debugging sequence-dependent interactions
2. Analyzing timing issues in web applications
3. Documenting complex interaction flows

### 29. `highlight_element`
**Capabilities:** Highlights elements on the page for debugging.
- Visually emphasizes specified elements
- Configurable highlight styles and duration
- Can highlight multiple elements for comparison

**Use Cases:**
1. Visually identifying elements during automation
2. Debugging element selection issues
3. Demonstrating element locations for documentation

### 30. `compare_element_states`
**Capabilities:** Compares element states before and after actions.
- Records element properties at different points
- Highlights differences in visual and property states
- Shows changes resulting from interactions

**Use Cases:**
1. Validating element state changes after interactions
2. Debugging unexpected element behavior
3. Verifying proper element updates in dynamic applications

### 31. `create_interactive_dom_explorer`
**Capabilities:** Generates an interactive DOM explorer.
- Provides navigable view of page DOM
- Allows interactive inspection of elements
- Shows live property values and relationships

**Use Cases:**
1. Exploring complex DOM structures interactively
2. Debugging element relationships and inheritance
3. Finding specific elements in dense page structures

### 32. `get_console_logs`
**Capabilities:** Retrieves console logs from the browser.
- Collects all console output by type
- Filters logs by level or content
- Provides timestamps and context

**Use Cases:**
1. Debugging JavaScript execution in web applications
2. Monitoring application logging
3. Capturing warning and error messages

### 33. `get_filtered_console_logs`
**Capabilities:** Gets console logs filtered by level or content.
- Filters by log level (info, warning, error)
- Searches log content by keyword
- Organizes logs by type or timestamp

**Use Cases:**
1. Finding specific error messages in verbose logs
2. Monitoring for particular events or conditions
3. Isolating relevant messages in complex applications

### 34. `execute_console_command`
**Capabilities:** Executes JavaScript in console and captures results.
- Runs arbitrary JavaScript in page context
- Returns execution results and errors
- Supports complex multi-line scripts

**Use Cases:**
1. Extracting data not accessible through DOM
2. Modifying page behavior for testing
3. Executing custom logic for specialized interactions

### 35. `monitor_network_requests`
**Capabilities:** Monitors and analyzes network requests.
- Captures HTTP requests and responses
- Tracks API calls and data exchanges
- Records timing and size information

**Use Cases:**
1. Debugging API interactions in web applications
2. Monitoring data transfer during workflows
3. Identifying performance issues in network operations

### 36. `get_performance_metrics`
**Capabilities:** Gets browser performance metrics.
- Measures page load and rendering times
- Reports memory and CPU usage
- Tracks browser resource consumption

**Use Cases:**
1. Profiling web application performance
2. Identifying bottlenecks in complex pages
3. Monitoring resource usage during long-running operations

### 37. `monitor_page_errors`
**Capabilities:** Monitors and captures JavaScript errors.
- Tracks runtime errors and exceptions
- Records error stack traces
- Counts error occurrences by type

**Use Cases:**
1. Monitoring application stability during testing
2. Identifying error patterns in web applications
3. Debugging intermittent JavaScript issues

### 38. `monitor_resource_usage`
**Capabilities:** Monitors resource usage of the browser.
- Tracks memory consumption over time
- Measures CPU utilization
- Reports resource usage by tab

**Use Cases:**
1. Identifying memory leaks in long-running sessions
2. Profiling resource usage of different operations
3. Monitoring for resource exhaustion conditions

### 39. `analyze_console_patterns`
**Capabilities:** Analyzes patterns in console logs.
- Identifies recurring message patterns
- Correlates errors with actions
- Summarizes log activity over time

**Use Cases:**
1. Finding patterns in application error logs
2. Analyzing application behavior through logging
3. Discovering hidden issues through log analysis

### 40. `create_data_session`
**Capabilities:** Creates a session for storing related data.
- Establishes persistent data container
- Optional expiration for temporary data
- Named sessions for organization

**Use Cases:**
1. Organizing related data from multi-step workflows
2. Creating persistent storage for app state
3. Maintaining context across multiple operations

### 41. `persist_page_content`
**Capabilities:** Stores page content in the persistence layer.
- Saves text content, metadata, and structure
- Organizes content by page and session
- Optionally includes full HTML

**Use Cases:**
1. Archiving page content for later analysis
2. Collecting content across multiple pages for comparison
3. Creating persistent copies of dynamic web content

### 42. `persist_element_data`
**Capabilities:** Stores element data in the persistence layer.
- Saves element properties and content
- Organizes by element type and session
- Includes position and attributes

**Use Cases:**
1. Tracking element changes across sessions
2. Collecting specific element data from multiple pages
3. Creating datasets of element properties for analysis

### 43. `create_data_entry`
**Capabilities:** Creates a new data entry with custom fields.
- Stores structured data with schema validation
- Associates entries with sessions
- Supports custom field types

**Use Cases:**
1. Creating structured records from web data
2. Building datasets from multiple sources
3. Storing application-specific structured information

### 44. `query_persisted_data`
**Capabilities:** Queries stored data by various criteria.
- Filters by session, type, or content
- Supports complex query conditions
- Returns matching entries with metadata

**Use Cases:**
1. Searching across collected data
2. Filtering information by specific criteria
3. Retrieving related data for analysis

### 45. `list_data_sessions`
**Capabilities:** Lists all available data sessions.
- Shows session metadata and statistics
- Reports data entry counts by type
- Provides session creation and access times

**Use Cases:**
1. Managing multiple data collection sessions
2. Monitoring data growth across sessions
3. Finding relevant sessions for data retrieval

### 46. `get_session_data`
**Capabilities:** Gets all data for a specific session.
- Returns all entries in a session
- Includes session metadata
- Optional filtering by entry type

**Use Cases:**
1. Retrieving complete datasets from sessions
2. Exporting session data for external analysis
3. Reviewing all collected information in a session

### 47. `update_persisted_data`
**Capabilities:** Updates previously stored data.
- Modifies existing data entries
- Supports partial updates
- Maintains update history

**Use Cases:**
1. Correcting or enhancing stored information
2. Adding additional fields to existing entries
3. Maintaining data consistency across sessions

### 48. `delete_persisted_data`
**Capabilities:** Deletes data from persistence.
- Removes specific entries or entire sessions
- Optional soft deletion with retention period
- Cleanup of expired or temporary data

**Use Cases:**
1. Managing storage space by removing unneeded data
2. Implementing data retention policies
3. Clearing test or temporary data

### 49. `export_page_to_format`
**Capabilities:** Exports a page to various formats.
- Supports PDF, HTML, text export
- Configurable formatting options
- Saves to specified location

**Use Cases:**
1. Creating PDF archives of web content
2. Exporting cleaned HTML for processing
3. Converting web pages to different formats for sharing

### 50. `export_table_data_to_csv`
**Capabilities:** Exports table data to CSV format.
- Extracts and formats tabular data
- Handles complex table structures
- Configurable delimiters and formatting

**Use Cases:**
1. Exporting data tables for analysis in spreadsheets
2. Converting web tables to machine-readable format
3. Capturing tabular data for reporting

### 51. `export_form_data_to_json`
**Capabilities:** Exports form data to JSON format.
- Captures form field names and values
- Preserves field relationships and hierarchy
- Includes metadata about form structure

**Use Cases:**
1. Storing form configurations for later use
2. Capturing form data for processing
3. Creating form templates from existing pages

### 52. `export_session_data`
**Capabilities:** Exports all data from a session.
- Supports multiple export formats
- Includes session metadata
- Organizes hierarchical data structure

**Use Cases:**
1. Creating complete exports of collected session data
2. Transferring datasets between environments
3. Archiving completed data collection sessions

### 53. `generate_data_report`
**Capabilities:** Generates a comprehensive report from session data.
- Creates formatted reports in multiple formats
- Includes data visualizations and summaries
- Customizable templates and layouts

**Use Cases:**
1. Creating executive summaries of collected data
2. Generating formatted reports from web research
3. Producing documentation from session activities

### 54. `export_visualization`
**Capabilities:** Exports a visualization to an image format.
- Renders data visualizations as images
- Supports multiple chart and graph types
- Configurable resolution and formatting

**Use Cases:**
1. Creating visual representations of collected data
2. Generating charts for reports and presentations
3. Visualizing relationships in complex datasets

### 55. `export_multiple_pages`
**Capabilities:** Exports multiple pages in batch.
- Processes multiple pages in sequence
- Applies consistent formatting
- Organizes output by page and session

**Use Cases:**
1. Batch processing multiple pages for content extraction
2. Creating archives of related pages
3. Generating multi-page reports or documents

### 56. `create_data_archive`
**Capabilities:** Creates a compressed archive of exported data.
- Compresses multiple exports into a single file
- Supports various archive formats
- Includes session metadata and structure

**Use Cases:**
1. Creating portable archives of collected data
2. Reducing storage space for large datasets
3. Packaging multiple exports for transfer

### 57. `create_diagnostic_session`
**Capabilities:** Creates a new diagnostic session for testing.
- Establishes isolated diagnostic environment
- Configures detailed logging and monitoring
- Sets up performance tracking

**Use Cases:**
1. Creating isolated environments for troubleshooting
2. Setting up specialized diagnostic configurations
3. Isolating testing from production operations

### 58. `collect_web_diagnostics`
**Capabilities:** Collects comprehensive diagnostics from a page.
- Gathers console logs, errors, and warnings
- Captures network activity and resource usage
- Records page performance metrics

**Use Cases:**
1. Troubleshooting page-specific issues
2. Gathering complete diagnostic information for support
3. Creating detailed diagnostic reports for complex problems

### 59. `start_performance_monitoring`
**Capabilities:** Starts monitoring performance metrics.
- Tracks page load and rendering times
- Measures memory and CPU usage
- Records network activity and resource loading

**Use Cases:**
1. Profiling application performance
2. Identifying performance bottlenecks
3. Monitoring resource usage patterns

### 60. `stop_performance_monitoring`
**Capabilities:** Stops performance monitoring.
- Finalizes performance data collection
- Generates preliminary analysis
- Prepares data for reporting

**Use Cases:**
1. Ending performance measurement periods
2. Completing benchmark tests
3. Finalizing performance data collection

### 61. `get_performance_report`
**Capabilities:** Generates a performance report.
- Creates detailed performance analysis
- Compares against baselines or thresholds
- Includes visualizations and recommendations

**Use Cases:**
1. Reviewing application performance characteristics
2. Identifying optimization opportunities
3. Documenting performance for stakeholders

### 62. `create_web_diagnostic_report`
**Capabilities:** Creates a comprehensive diagnostic report.
- Compiles all diagnostic information
- Analyzes patterns and issues
- Generates recommendations and next steps

**Use Cases:**
1. Creating complete diagnostic documentation
2. Analyzing complex multi-issue scenarios
3. Generating support documentation for escalation

### 63. `list_diagnostic_sessions`
**Capabilities:** Lists all diagnostic sessions.
- Shows session metadata and status
- Reports diagnostic coverage and completeness
- Provides session management options

**Use Cases:**
1. Managing multiple diagnostic investigations
2. Tracking diagnostic activities over time
3. Finding relevant diagnostic data for analysis

## Computer Interaction Tools

### 64. `computer_use`
**Capabilities:** Unified tool for computer interactions.
- Executes sequences of computer operations
- Supports screen, mouse, keyboard, window, and system operations
- Maintains state between operations
- Returns detailed operation results

**Use Cases:**
1. Automating desktop application workflows
2. Performing system operations in sequence
3. Controlling computer peripherals for testing

### 65. `capture_screenshot`
**Capabilities:** Captures screenshots of the screen or regions.
- Captures full screen or specific regions
- Optional element highlighting
- Returns image as base64
- Configurable quality settings

**Use Cases:**
1. Documenting system state for verification
2. Capturing specific UI elements for analysis
3. Creating visual records of application states

### 66. `find_text_on_screen`
**Capabilities:** Finds text on screen using OCR.
- Uses OCR to locate text in screen images
- Returns text locations with bounding boxes
- Configurable language settings
- Multiple detection algorithms

**Use Cases:**
1. Finding text in applications without accessibility hooks
2. Verifying text display in UI testing
3. Automating interactions with text-based interfaces

### 67. `click_at`
**Capabilities:** Clicks at specific screen coordinates.
- Supports different mouse buttons
- Configurable number of clicks
- Optional movement duration
- Returns result with new cursor position

**Use Cases:**
1. Automating UI interactions in desktop applications
2. Clicking specific positions in graphics applications
3. Controlling systems through UI interaction

### 68. `type_text`
**Capabilities:** Types text using the keyboard.
- Configurable typing speed
- Optional Enter key press
- Works with any application with keyboard focus
- Returns typing result and status

**Use Cases:**
1. Entering text in form fields or documents
2. Automating text input in desktop applications
3. Sending keyboard commands to applications

### 69. `get_active_window`
**Capabilities:** Gets information about the active window.
- Returns window title, position, and size
- Indicates window state (maximized, minimized)
- Provides window handle for further operations
- Cross-platform compatible

**Use Cases:**
1. Determining the current active application
2. Getting window properties for positioning
3. Verifying correct window focus in automation

### 70. `list_windows`
**Capabilities:** Gets information about all open windows.
- Lists all visible windows with properties
- Returns window titles, positions, and sizes
- Shows window states and visibility
- Sorts windows by various criteria

**Use Cases:**
1. Finding specific application windows
2. Monitoring all open applications
3. Managing multiple windows in automation scripts

### 71. `system_info`
**Capabilities:** Gets system information.
- Returns OS details and version
- Reports CPU and memory information
- Shows disk usage and system load
- Provides platform-specific information

**Use Cases:**
1. Checking system capabilities before operations
2. Logging system state for diagnostics
3. Adapting operations to available resources

### 72. `execute_system_command`
**Capabilities:** Executes a system command.
- Runs shell commands safely
- Captures stdout and stderr
- Configurable timeout
- Returns execution result and exit code

**Use Cases:**
1. Running system utilities and commands
2. Executing scripts for system configuration
3. Performing operations requiring command line

### 73. `get_clipboard`
**Capabilities:** Gets clipboard content.
- Retrieves text from system clipboard
- Reports content length and type
- Cross-platform compatible
- Handles encoding issues

**Use Cases:**
1. Retrieving copied text for processing
2. Transferring data between applications
3. Verifying clipboard contents in testing

### 74. `set_clipboard`
**Capabilities:** Sets clipboard content.
- Places text in system clipboard
- Confirms successful operation
- Cross-platform compatible
- Returns operation status

**Use Cases:**
1. Setting up text for pasting in applications
2. Transferring data between automation steps
3. Preparing content for application input

### 75. `find_on_screen`
**Capabilities:** Finds an image on the screen.
- Locates image templates on screen
- Configurable matching confidence
- Returns matched locations and scores
- Optional grayscale matching

**Use Cases:**
1. Finding graphical elements on screen
2. Locating UI elements for interaction
3. Verifying visual elements in testing

### 76. `detect_elements`
**Capabilities:** Detects UI elements in screenshot.
- Identifies buttons, text fields, and other elements
- Uses computer vision for detection
- Returns element types and positions
- Configurable detection parameters

**Use Cases:**
1. Finding interactive elements automatically
2. Analyzing UI layouts for testing
3. Creating element maps of applications

### 77. `compare_screenshots`
**Capabilities:** Compares two screenshots.
- Multiple comparison methods: structural, histogram, pixel
- Returns similarity scores and differences
- Identifies changed regions
- Configurable comparison parameters

**Use Cases:**
1. Verifying UI changes after operations
2. Detecting unexpected visual differences
3. Testing UI stability across actions

### 78. `find_template`
**Capabilities:** Finds a template image within screenshot.
- Template matching with configurable threshold
- Returns match positions and confidence
- Supports multiple matches
- Configurable matching parameters

**Use Cases:**
1. Locating specific visual elements or icons
2. Finding recurring patterns in interfaces
3. Identifying visual landmarks for navigation