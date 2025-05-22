# Retry Failed Subtask Command

## Objective
Analyze and retry a failed subtask with improved error handling and recovery strategies.

## Context
You are retrying subtask {{ subtask_id }} from {{ project_name }} Issue #{{ issue_number }}.

**Failure Details:**
- Subtask: {{ subtask_title }}
- Type: {{ subtask_type }}
- Failure Count: {{ failure_count }}
- Last Error: {{ last_error }}
- Failed At: {{ failure_timestamp }}

**Workflow Context:**
- Workflow ID: {{ workflow_id }}
- Branch: {{ branch_name }}
- Dependencies: {{ subtask_dependencies }}

## Instructions

### 1. Failure Analysis
Before retrying, analyze the failure:

**Error Classification:**
- **Transient Error**: Network issues, temporary resource constraints
- **Configuration Error**: Missing dependencies, environment issues  
- **Logic Error**: Code bugs, incorrect implementation
- **External Error**: API failures, service unavailability
- **Dependency Error**: Required subtasks not completed

**Root Cause Analysis:**
- Review error logs and stack traces
- Check if dependencies are properly completed
- Verify environment and configuration
- Identify if this is a recurring pattern

### 2. Pre-Retry Checks
Before attempting retry:

```python
# Verify dependencies are met
dependencies_met = check_subtask_dependencies(subtask_id)

# Check environment readiness
environment_ready = verify_environment()

# Validate configuration
config_valid = validate_subtask_config(subtask_data)
```

### 3. Retry Strategy Selection
Choose appropriate retry strategy based on failure type:

**For Transient Errors:**
- Immediate retry with exponential backoff
- Temporary resource allocation adjustments
- Network timeout adjustments

**For Configuration Errors:**
- Fix configuration issues first
- Update environment variables
- Install missing dependencies

**For Logic Errors:**
- Review and fix implementation
- Add additional error handling
- Update subtask parameters

**For External Errors:**
- Check external service status
- Implement fallback mechanisms
- Adjust timeout settings

**For Dependency Errors:**
- Re-evaluate dependency completion
- Fix dependency chain issues
- Update dependency relationships

### 4. Enhanced Execution
Implement enhanced error handling for retry:

```python
# Enhanced error handling
try:
    result = execute_subtask_with_monitoring(subtask_data)
except SpecificError as e:
    # Handle specific error types
    handle_specific_error(e, subtask_id)
except Exception as e:
    # Generic error handling with detailed logging
    log_detailed_error(e, subtask_id, context)
    raise
```

### 5. Monitoring and Logging
Enhanced monitoring during retry:
- Real-time progress tracking
- Detailed error logging
- Resource usage monitoring
- Dependency status checking

### 6. Success Validation
After retry completion:
- Verify subtask output meets requirements
- Validate integration with other subtasks
- Check for any side effects
- Update workflow status appropriately

### 7. Failure Recovery
If retry fails again:
- Update failure count and patterns
- Escalate to manual intervention if needed
- Mark subtask for human review
- Update workflow to handle permanent failure

## Output Requirements

### Success Case
- Update subtask status to COMPLETED
- Log successful retry with details
- Notify workflow engine of completion
- Trigger dependent subtasks

### Failure Case
- Update failure count and error details
- Determine if further retries are warranted
- Escalate to manual review if max retries reached
- Provide detailed failure analysis

## Error Reporting Format

```markdown
# Subtask Retry Report
**Subtask:** {{ subtask_id }} - {{ subtask_title }}
**Retry Attempt:** {{ retry_attempt }}
**Status:** [SUCCESS/FAILED]

## Failure Analysis
**Error Type:** [Classification]
**Root Cause:** [Detailed analysis]
**Impact:** [Effect on workflow]

## Retry Strategy
**Approach:** [Strategy used]
**Changes Made:** [What was modified]
**Additional Monitoring:** [Enhanced checks]

## Result
**Outcome:** [Success/Failure details]
**Next Steps:** [Required actions]
**Recommendations:** [Future improvements]
```

## Success Criteria
- Failed subtask is successfully retried (if possible)
- Root cause of failure is identified and addressed
- Enhanced error handling prevents similar failures
- Workflow continues with minimal disruption
- Detailed failure analysis is documented for future reference