# Advanced Web Tools MCP Server - Complete Tool Inventory

This document provides a complete inventory of all 78 tools available in the advanced-web-tools MCP server, organized by category with descriptions and testing priorities.

## Navigation & Page Management (11 tools)

1. **navigate** - Navigate to a URL in a browser
   - Priority: Critical
   - Test Focus: URL handling, wait conditions, page state

2. **get_browser_tabs** - Get information about all open browser tabs
   - Priority: High
   - Test Focus: Tab enumeration, state tracking

3. **clean_browser_tabs** - Clean up browser tabs by closing inactive ones
   - Priority: Medium
   - Test Focus: Tab cleanup logic, resource management

4. **clear_browser_state** - Clear all browser state and close all tabs
   - Priority: High
   - Test Focus: Complete state reset, cleanup verification

5. **get_browser_info** - Get information about browser, pages, and sessions
   - Priority: Medium
   - Test Focus: Information accuracy, completeness

6. **diagnostics_report** - Generate diagnostic report for web interaction
   - Priority: Medium
   - Test Focus: Report completeness, debugging value

7. **fix_common_issues** - Attempt to fix common browser issues
   - Priority: Low
   - Test Focus: Issue detection, fix effectiveness

8. **list_windows** - Get information about all open windows
   - Priority: Medium
   - Test Focus: Window enumeration, state tracking

9. **get_active_window** - Get information about currently active window
   - Priority: Medium
   - Test Focus: Active window detection

10. **puppeteer_navigate** - Navigate to URL using Puppeteer
    - Priority: High
    - Test Focus: Navigation reliability, state management

11. **create_diagnostic_session** - Create diagnostic session for debugging
    - Priority: Low
    - Test Focus: Session creation, diagnostic data collection

## Content Extraction (12 tools)

12. **extract_page_content** - Extract content from current page
    - Priority: Critical
    - Test Focus: Content accuracy, format handling

13. **extract_structured_data** - Extract structured data from page
    - Priority: Critical
    - Test Focus: Data type detection, parsing accuracy

14. **semantic_find** - Find elements using natural language
    - Priority: High
    - Test Focus: Search accuracy, relevance scoring

15. **capture_dom_state** - Capture DOM snapshot with styles
    - Priority: Medium
    - Test Focus: DOM capture completeness

16. **get_debug_info** - Get debugging information for pages
    - Priority: Low
    - Test Focus: Debug data completeness

17. **get_console_logs** - Get console logs from pages
    - Priority: Medium
    - Test Focus: Log capture, filtering

18. **get_page_errors** - Get JavaScript errors from pages
    - Priority: High
    - Test Focus: Error detection, reporting

19. **get_filtered_console_logs** - Get filtered console logs
    - Priority: Medium
    - Test Focus: Filter accuracy, pattern matching

20. **get_filtered_page_errors** - Get filtered page errors
    - Priority: Medium
    - Test Focus: Error filtering, categorization

21. **get_filtered_network_requests** - Get filtered network requests
    - Priority: High
    - Test Focus: Request filtering, data completeness

22. **find_text_on_screen** - Find text using OCR
    - Priority: Medium
    - Test Focus: OCR accuracy, performance

23. **capture_screenshot** - Capture screenshot of screen/region
    - Priority: High
    - Test Focus: Image quality, region selection

## Element Interaction (15 tools)

24. **interact_with_element** - Interact with page elements
    - Priority: Critical
    - Test Focus: Interaction reliability, element selection

25. **puppeteer_click** - Click element using Puppeteer
    - Priority: Critical
    - Test Focus: Click accuracy, event handling

26. **puppeteer_fill** - Fill text into element
    - Priority: Critical
    - Test Focus: Text input, form handling

27. **puppeteer_hover** - Hover over element
    - Priority: Medium
    - Test Focus: Hover effects, mouse events

28. **puppeteer_select** - Select option in dropdown
    - Priority: High
    - Test Focus: Selection accuracy, option handling

29. **enhance_console_command** - Execute JavaScript with enhanced logging
    - Priority: Medium
    - Test Focus: Script execution, result capture

30. **execute_console_command** - Execute JavaScript in browser
    - Priority: High
    - Test Focus: Code execution, return values

31. **puppeteer_evaluate** - Execute JavaScript in browser context
    - Priority: High
    - Test Focus: Context isolation, return handling

32. **click_at** - Click at specific coordinates
    - Priority: Medium
    - Test Focus: Coordinate accuracy, click types

33. **type_text** - Type text using keyboard
    - Priority: High
    - Test Focus: Typing accuracy, special characters

34. **set_clipboard** - Set clipboard content
    - Priority: Low
    - Test Focus: Content setting, format support

35. **get_clipboard** - Get clipboard content
    - Priority: Low
    - Test Focus: Content retrieval, format handling

36. **execute_system_command** - Execute system command
    - Priority: Medium
    - Test Focus: Command execution, security

37. **computer_use** - Perform computer use operations
    - Priority: High
    - Test Focus: Operation sequences, error handling

38. **system_info** - Get system information
    - Priority: Low
    - Test Focus: Information accuracy, completeness

## Data Management (14 tools)

39. **create_data_session** - Create data persistence session
    - Priority: High
    - Test Focus: Session creation, isolation

40. **get_data_session** - Get information about data session
    - Priority: Medium
    - Test Focus: Session retrieval, state accuracy

41. **delete_data_session** - Delete data session
    - Priority: Medium
    - Test Focus: Cleanup verification, data removal

42. **set_session_value** - Set value in data session
    - Priority: High
    - Test Focus: Data storage, type handling

43. **get_session_value** - Get value from data session
    - Priority: High
    - Test Focus: Data retrieval, default handling

44. **persist_page_content** - Persist content from page
    - Priority: Medium
    - Test Focus: Content storage, metadata handling

45. **persist_extracted_data** - Persist extracted data
    - Priority: Medium
    - Test Focus: Data persistence, format support

46. **query_persisted_data** - Query persisted data
    - Priority: High
    - Test Focus: Query accuracy, performance

47. **get_persisted_data** - Get persisted data by ID
    - Priority: Medium
    - Test Focus: Data retrieval, integrity

48. **delete_persisted_data** - Delete persisted data
    - Priority: Medium
    - Test Focus: Data deletion, cleanup

49. **cleanup_expired_sessions** - Clean up expired sessions
    - Priority: Low
    - Test Focus: Cleanup logic, resource management

50. **list_diagnostic_sessions** - List all diagnostic sessions
    - Priority: Low
    - Test Focus: Session enumeration

51. **collect_web_diagnostics** - Collect comprehensive diagnostics
    - Priority: Medium
    - Test Focus: Diagnostic completeness

52. **create_web_diagnostic_report** - Create diagnostic report
    - Priority: Medium
    - Test Focus: Report generation, formatting

## Export & Reporting (11 tools)

53. **export_page_to_html** - Export page content to HTML
    - Priority: Medium
    - Test Focus: HTML generation, formatting

54. **export_page_to_json** - Export page content to JSON
    - Priority: Medium
    - Test Focus: JSON structure, data completeness

55. **export_table_data_to_csv** - Export table data to CSV
    - Priority: High
    - Test Focus: CSV formatting, encoding

56. **export_table_data_to_excel** - Export table data to Excel
    - Priority: High
    - Test Focus: Excel formatting, compatibility

57. **export_session_data** - Export session data
    - Priority: Medium
    - Test Focus: Data export, format options

58. **export_persisted_data_entry** - Export persisted data entry
    - Priority: Medium
    - Test Focus: Entry export, format support

59. **generate_session_report** - Generate session report
    - Priority: Low
    - Test Focus: Report completeness, formatting

60. **create_html_report** - Create custom HTML report
    - Priority: Medium
    - Test Focus: HTML generation, section handling

61. **get_performance_report** - Generate performance report
    - Priority: Medium
    - Test Focus: Metrics accuracy, visualization

62. **get_console_activity_summary** - Get console activity summary
    - Priority: Low
    - Test Focus: Summary accuracy, statistics

63. **clear_console_data** - Clear console logs and errors
    - Priority: Low
    - Test Focus: Data clearing, verification

## Advanced Automation (15 tools)

64. **run_web_workflow** - Run complete workflow across pages
    - Priority: Critical
    - Test Focus: Workflow execution, error handling

65. **web_interact** - Perform sequence of operations
    - Priority: Critical
    - Test Focus: Operation sequencing, state management

66. **web_interact_advanced** - Advanced web interaction operations
    - Priority: High
    - Test Focus: Advanced features, performance

67. **start_performance_monitoring** - Start performance monitoring
    - Priority: Medium
    - Test Focus: Metric collection, accuracy

68. **stop_performance_monitoring** - Stop performance monitoring
    - Priority: Medium
    - Test Focus: Monitoring control, data retention

69. **monitor_page_performance** - Monitor page performance metrics
    - Priority: Medium
    - Test Focus: Metric accuracy, real-time updates

70. **inject_page_logger** - Inject enhanced console logger
    - Priority: Low
    - Test Focus: Logger injection, data capture

71. **clear_debug_data** - Clear debugging data
    - Priority: Low
    - Test Focus: Data cleanup, verification

72. **create_debug_timeline** - Create timeline visualization
    - Priority: Medium
    - Test Focus: Timeline accuracy, visualization

73. **create_element_visualization** - Create element state visualization
    - Priority: Medium
    - Test Focus: Visualization quality, data accuracy

74. **take_browser_screenshot** - Take browser screenshot
    - Priority: High
    - Test Focus: Screenshot quality, options

75. **take_element_debug_screenshot** - Take element debug screenshot
    - Priority: Medium
    - Test Focus: Element capture, annotation

76. **take_annotated_page_screenshot** - Take annotated screenshot
    - Priority: Medium
    - Test Focus: Annotation accuracy, formatting

77. **get_config** - Get server configuration
    - Priority: Low
    - Test Focus: Configuration retrieval

78. **server_status** - Get server status including capabilities
    - Priority: Low
    - Test Focus: Status accuracy, health checks

## Testing Priority Matrix

### Critical Priority (Must Test First) - 8 tools
- navigate
- extract_page_content
- extract_structured_data
- interact_with_element
- puppeteer_click
- puppeteer_fill
- run_web_workflow
- web_interact

### High Priority (Core Functionality) - 20 tools
- get_browser_tabs
- clear_browser_state
- semantic_find
- get_page_errors
- get_filtered_network_requests
- puppeteer_navigate
- puppeteer_select
- execute_console_command
- puppeteer_evaluate
- type_text
- computer_use
- create_data_session
- set_session_value
- get_session_value
- query_persisted_data
- export_table_data_to_csv
- export_table_data_to_excel
- web_interact_advanced
- capture_screenshot
- take_browser_screenshot

### Medium Priority (Important Features) - 35 tools
- clean_browser_tabs
- get_browser_info
- diagnostics_report
- list_windows
- get_active_window
- capture_dom_state
- get_console_logs
- get_filtered_console_logs
- get_filtered_page_errors
- find_text_on_screen
- puppeteer_hover
- enhance_console_command
- click_at
- execute_system_command
- get_data_session
- delete_data_session
- persist_page_content
- persist_extracted_data
- get_persisted_data
- delete_persisted_data
- collect_web_diagnostics
- create_web_diagnostic_report
- export_page_to_html
- export_page_to_json
- export_session_data
- export_persisted_data_entry
- create_html_report
- get_performance_report
- start_performance_monitoring
- stop_performance_monitoring
- monitor_page_performance
- create_debug_timeline
- create_element_visualization
- take_element_debug_screenshot
- take_annotated_page_screenshot

### Low Priority (Nice to Have) - 15 tools
- fix_common_issues
- create_diagnostic_session
- get_debug_info
- set_clipboard
- get_clipboard
- system_info
- cleanup_expired_sessions
- list_diagnostic_sessions
- generate_session_report
- get_console_activity_summary
- clear_console_data
- inject_page_logger
- clear_debug_data
- get_config
- server_status

## Test Coverage Goals

- **Critical Priority**: 100% coverage required
- **High Priority**: 95% coverage required
- **Medium Priority**: 80% coverage required
- **Low Priority**: 60% coverage required

## Testing Timeline

- Week 1: Critical priority tools (8 tools)
- Week 2: High priority tools (20 tools)
- Week 3-4: Medium priority tools (35 tools)
- Week 4: Low priority tools (15 tools)

Total testing duration: 4 weeks for comprehensive coverage of all 78 tools.
