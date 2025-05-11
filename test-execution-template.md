# Test Execution Template

Use this template for testing each tool in the advanced-web-tools MCP server.

## Tool Information

**Tool Name**: [Tool Name]  
**Category**: [Navigation/Content Extraction/Element Interaction/etc.]  
**Priority**: [Critical/High/Medium/Low]  
**Test Date**: [Date]  
**Tester**: [Name]  

## Test Overview

**Description**: [Brief description of what the tool does]  
**Expected Behavior**: [What should happen when the tool works correctly]  
**Dependencies**: [Other tools or resources this tool depends on]  

## Test Cases

### Test Case 1: Basic Functionality

**Objective**: Verify basic operation of the tool  
**Pre-conditions**: 
- [ ] Browser instance available
- [ ] Test page loaded
- [ ] Required permissions granted

**Test Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Test Data**:
```json
{
  "input": {
    // Input parameters
  }
}
```

**Expected Result**:
```json
{
  "output": {
    // Expected output
  }
}
```

**Actual Result**:
```json
{
  "output": {
    // Actual output received
  }
}
```

**Status**: [Pass/Fail]  
**Notes**: [Any observations or issues]

### Test Case 2: Error Handling

**Objective**: Verify proper error handling  
**Pre-conditions**: 
- [ ] Tool initialized
- [ ] Invalid input prepared

**Test Steps**:
1. Provide invalid input
2. Execute tool
3. Verify error response

**Test Data**:
```json
{
  "invalid_input": {
    // Invalid parameters
  }
}
```

**Expected Error**:
```json
{
  "error": true,
  "errorCode": "EXPECTED_ERROR_CODE",
  "errorMessage": "Expected error message"
}
```

**Actual Error**:
```json
{
  // Actual error response
}
```

**Status**: [Pass/Fail]  
**Notes**: [Error handling observations]

### Test Case 3: Edge Cases

**Objective**: Test boundary conditions  
**Scenarios**:
- [ ] Empty input
- [ ] Maximum allowed values
- [ ] Special characters
- [ ] Timeout scenarios

**Results**:
| Scenario | Input | Expected | Actual | Status |
|----------|-------|----------|--------|--------|
| Empty input | `{}` | Error | [Result] | [Pass/Fail] |
| Max values | [Data] | [Expected] | [Result] | [Pass/Fail] |
| Special chars | [Data] | [Expected] | [Result] | [Pass/Fail] |
| Timeout | [Data] | [Expected] | [Result] | [Pass/Fail] |

### Test Case 4: Performance

**Objective**: Measure performance metrics  
**Metrics to Track**:
- Response time
- Memory usage
- CPU utilization
- Network traffic

**Test Conditions**:
- Normal load
- High load
- Concurrent operations

**Results**:
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Response Time | < 1s | [Time] | [Pass/Fail] |
| Memory Usage | < 256MB | [Usage] | [Pass/Fail] |
| CPU Usage | < 50% | [Usage] | [Pass/Fail] |
| Network | < 5MB | [Usage] | [Pass/Fail] |

### Test Case 5: Integration

**Objective**: Test integration with other tools  
**Related Tools**: [List of tools this integrates with]  

**Integration Scenarios**:
1. [Scenario 1]
2. [Scenario 2]

**Results**:
| Scenario | Tools Used | Expected | Actual | Status |
|----------|------------|----------|--------|--------|
| [Scenario 1] | [Tools] | [Expected] | [Result] | [Pass/Fail] |
| [Scenario 2] | [Tools] | [Expected] | [Result] | [Pass/Fail] |

## Security Testing

**Security Checks**:
- [ ] Input validation
- [ ] XSS prevention
- [ ] Data sanitization
- [ ] Access control
- [ ] Resource limits

**Security Test Results**:
| Check | Test Performed | Result | Status |
|-------|---------------|--------|--------|
| Input validation | [Test] | [Result] | [Pass/Fail] |
| XSS prevention | [Test] | [Result] | [Pass/Fail] |
| Data sanitization | [Test] | [Result] | [Pass/Fail] |
| Access control | [Test] | [Result] | [Pass/Fail] |
| Resource limits | [Test] | [Result] | [Pass/Fail] |

## Compatibility Testing

**Browser Compatibility**:
| Browser | Version | Status | Notes |
|---------|---------|--------|-------|
| Chrome | [Version] | [Pass/Fail] | [Notes] |
| Firefox | [Version] | [Pass/Fail] | [Notes] |
| Safari | [Version] | [Pass/Fail] | [Notes] |
| Edge | [Version] | [Pass/Fail] | [Notes] |

**Platform Compatibility**:
| Platform | Version | Status | Notes |
|----------|---------|--------|-------|
| Windows | [Version] | [Pass/Fail] | [Notes] |
| macOS | [Version] | [Pass/Fail] | [Notes] |
| Linux | [Version] | [Pass/Fail] | [Notes] |

## Issues Found

### Issue 1
**Description**: [Description of the issue]  
**Severity**: [Critical/High/Medium/Low]  
**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]

**Expected Behavior**: [What should happen]  
**Actual Behavior**: [What actually happens]  
**Workaround**: [If any]  
**Status**: [Open/Closed]  

## Test Summary

**Total Test Cases**: [Number]  
**Passed**: [Number]  
**Failed**: [Number]  
**Blocked**: [Number]  

**Overall Status**: [Pass/Fail/Partial]  
**Recommendation**: [Ready for production/Needs fixes/Requires further testing]  

## Sign-off

**Tested By**: [Name]  
**Date**: [Date]  
**Reviewed By**: [Name]  
**Date**: [Date]  

## Attachments

- [ ] Test logs
- [ ] Screenshots
- [ ] Performance reports
- [ ] Error logs
- [ ] Video recordings (if applicable)

---

### Notes for Testers

1. **Be Thorough**: Test all aspects of the tool, not just the happy path
2. **Document Everything**: Record all observations, even minor ones
3. **Use Real Data**: Test with realistic data whenever possible
4. **Test Incrementally**: Start with basic tests before moving to complex ones
5. **Verify Cleanup**: Ensure the tool properly cleans up resources
6. **Check Documentation**: Verify that actual behavior matches documentation
7. **Consider User Experience**: Note any usability issues or confusing behavior
8. **Test Accessibility**: Consider accessibility requirements where applicable

### Common Issues to Watch For

- Memory leaks
- Unclosed connections
- Improper error messages
- Inconsistent behavior
- Performance degradation
- Security vulnerabilities
- Resource exhaustion
- Race conditions
- Timeout issues
- Data corruption

### Best Practices

1. Always use fresh test data
2. Clear browser state between tests
3. Test in isolation when possible
4. Use automated tests for regression
5. Maintain test data integrity
6. Version control test scripts
7. Share findings with team promptly
8. Update documentation as needed
