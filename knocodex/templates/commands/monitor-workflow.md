# Monitor Workflow Command

## Objective
Monitor and report on the status of a subtask-based workflow for a GitHub issue.

## Context
You are monitoring the workflow for {{ project_name }} Issue #{{ issue_number }}.

**Workflow Details:**
- Workflow ID: {{ workflow_id }}
- Total Subtasks: {{ total_subtasks }}
- Branch: {{ branch_name }}
- Started: {{ start_time }}

## Instructions

### 1. Workflow Status Check
Check the current status of all subtasks in the workflow:

```python
# Use workflow engine to get current status
workflow_status = workflow_engine.get_workflow_status(workflow_id)
```

### 2. Report Generation
Generate a comprehensive status report including:

**Overall Progress:**
- Total subtasks: X
- Completed: X
- In Progress: X  
- Pending: X
- Failed: X
- Blocked: X

**Detailed Subtask Status:**
For each subtask, report:
- Subtask ID and title
- Current status
- Dependencies (completed/pending)
- Estimated vs actual time
- Any error messages

**Workflow Health:**
- Identify any bottlenecks
- Check for dependency deadlocks
- Monitor resource usage
- Track execution timeline

### 3. Issue Identification
Look for common issues:
- **Blocked Subtasks**: Dependencies not met
- **Failed Subtasks**: Need retry or intervention
- **Stalled Workflow**: No progress for extended time
- **Resource Constraints**: Queue backlog or worker issues

### 4. Recommendations
Based on status, provide actionable recommendations:

**For Blocked Subtasks:**
- Identify missing dependencies
- Suggest dependency resolution order
- Recommend manual intervention if needed

**For Failed Subtasks:**
- Analyze failure reasons
- Suggest retry strategies
- Recommend workflow adjustments

**For Performance Issues:**
- Identify bottlenecks
- Suggest parallel execution opportunities
- Recommend resource allocation changes

### 5. Alerting
If critical issues detected:
- Mark urgent items requiring immediate attention
- Suggest escalation paths
- Provide clear action items

## Output Format

```markdown
# Workflow Status Report
**Project:** {{ project_name }} Issue #{{ issue_number }}
**Workflow ID:** {{ workflow_id }}
**Generated:** {{ current_time }}

## Summary
- 🟢 **Completed:** X/Y subtasks
- 🟡 **In Progress:** X subtasks  
- 🔴 **Failed:** X subtasks
- ⚫ **Blocked:** X subtasks

## Progress Timeline
[ASCII progress bar or timeline visualization]

## Subtask Details
### Completed ✅
- [List completed subtasks with timestamps]

### In Progress 🟡
- [List in-progress subtasks with estimated completion]

### Failed ❌
- [List failed subtasks with error details]

### Blocked 🚫
- [List blocked subtasks with dependency issues]

## Health Check
- **Workflow Status:** [Healthy/Warning/Critical]
- **Estimated Completion:** [Time estimate]
- **Bottlenecks:** [Identified issues]

## Recommendations
[Specific actionable recommendations]

## Next Steps
[Immediate actions needed]
```

## Success Criteria
- Complete and accurate status reporting
- Clear identification of issues and blockers
- Actionable recommendations provided
- Easy-to-understand progress visualization
- Timely alerts for critical issues