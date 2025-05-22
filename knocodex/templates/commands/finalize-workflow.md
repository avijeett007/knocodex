# Finalize Workflow Command

## Objective
Complete the final steps of a subtask-based workflow and create a pull request for the GitHub issue.

## Context
You are finalizing the workflow for {{ project_name }} Issue #{{ issue_number }}.

**Workflow Summary:**
- Workflow ID: {{ workflow_id }}
- Total Subtasks: {{ total_subtasks }}
- Completed Subtasks: {{ completed_subtasks }}
- Branch: {{ branch_name }}
- Started: {{ start_time }}
- Duration: {{ total_duration }}

## Instructions

### 1. Final Status Verification
Verify all subtasks are properly completed:

```python
# Check workflow completion status
workflow_status = workflow_engine.get_workflow_status(workflow_id)
all_completed = workflow_status['status'] == 'COMPLETED'
```

**Verification Checklist:**
- [ ] All subtasks marked as COMPLETED
- [ ] No failed or blocked subtasks
- [ ] All dependencies satisfied
- [ ] Code changes committed to branch
- [ ] Tests passing (if applicable)

### 2. Quality Assurance
Perform final quality checks:

**Code Quality:**
- Run linting and formatting tools
- Check for code smells or issues
- Verify coding standards compliance
- Review error handling and edge cases

**Testing:**
- Run full test suite
- Verify all tests pass
- Check test coverage
- Run integration tests if available

**Documentation:**
- Ensure all code is properly documented
- Update relevant README files
- Check API documentation
- Verify examples are working

### 3. Branch Preparation
Prepare the branch for pull request:

```bash
# Ensure branch is up to date
git checkout {{ branch_name }}
git pull origin {{ base_branch }}

# Resolve any merge conflicts
# Run final tests
# Commit any final changes
```

### 4. Pull Request Creation
Create a comprehensive pull request:

**PR Title Format:**
```
[Issue #{{ issue_number }}] {{ issue_title }}
```

**PR Description Template:**
```markdown
## Summary
Fixes #{{ issue_number }}

{{ issue_description }}

## Implementation Overview
This PR implements a subtask-based approach with the following components:

### Completed Subtasks
{% for subtask in completed_subtasks %}
- **{{ subtask.type }}**: {{ subtask.title }}
  - {{ subtask.description }}
  - Effort: {{ subtask.actual_effort }}
{% endfor %}

## Changes Made
- [List major changes and new files]
- [Describe architectural decisions]
- [Note any breaking changes]

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed
- [ ] Integration tests pass

## Documentation
- [ ] Code is well-documented
- [ ] README updated if needed
- [ ] API documentation updated
- [ ] Examples provided

## Review Checklist
- [ ] Code follows project conventions
- [ ] No security vulnerabilities introduced
- [ ] Performance implications considered
- [ ] Backward compatibility maintained
- [ ] Error handling is comprehensive

## Additional Notes
{{ additional_notes }}
```

### 5. Workflow Cleanup
Clean up workflow resources:

```python
# Update workflow status to COMPLETED
workflow_engine.complete_workflow(workflow_id)

# Clean up temporary files and resources
cleanup_workflow_resources(workflow_id)

# Update project statistics
update_project_metrics(project_id, workflow_metrics)
```

### 6. Notification and Reporting
Send completion notifications:

**Workflow Summary Report:**
```markdown
# Workflow Completion Report
**Project:** {{ project_name }}
**Issue:** #{{ issue_number }} - {{ issue_title }}
**Branch:** {{ branch_name }}
**Status:** ✅ COMPLETED

## Metrics
- **Total Subtasks:** {{ total_subtasks }}
- **Duration:** {{ total_duration }}
- **Estimated vs Actual:** {{ time_comparison }}
- **Success Rate:** {{ success_rate }}%

## Deliverables
- **Pull Request:** [PR Link]
- **Branch:** {{ branch_name }}
- **Files Changed:** {{ files_changed }}
- **Lines Added/Removed:** +{{ lines_added }}/-{{ lines_removed }}

## Quality Metrics
- **Tests:** {{ test_count }} tests, {{ test_coverage }}% coverage
- **Documentation:** {{ doc_updates }} files updated
- **Code Quality:** {{ quality_score }}

## Next Steps
1. Review pull request
2. Address any review feedback
3. Merge when approved
4. Deploy if applicable
```

### 7. Archive and Documentation
Archive workflow data for future reference:

```python
# Archive workflow data
archive_workflow_data(workflow_id, {
    'issue_number': issue_number,
    'subtasks': completed_subtasks,
    'metrics': workflow_metrics,
    'lessons_learned': lessons_learned
})
```

## Success Criteria
- All subtasks successfully completed
- Code quality standards met
- Comprehensive pull request created
- Workflow properly archived
- Team notified of completion
- Ready for code review and merge

## Error Handling
If finalization fails:
- Document incomplete items
- Create action items for manual completion
- Notify team of partial completion
- Preserve workflow state for debugging