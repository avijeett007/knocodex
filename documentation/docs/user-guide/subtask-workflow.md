# Subtask Workflow System

The Subtask Workflow System in Knocodex provides a powerful way to break down complex issues into smaller, manageable subtasks that can be executed in a well-defined order with proper dependency management.

## Overview

When working on large features or complex bugs, it's often beneficial to break down the work into smaller, more manageable tasks. The Subtask Workflow System provides:

- Automatic breakdown of GitHub issues into logical subtasks
- Dependency management between subtasks
- Parallel execution of independent subtasks
- Status tracking for the entire workflow
- Retry mechanisms for failed subtasks

## Key Concepts

### Subtask

A subtask represents a single unit of work in the workflow. Each subtask has:

- **ID**: Unique identifier
- **Title**: Short description
- **Description**: Detailed explanation of what needs to be done
- **Type**: Category of work (ANALYSIS, IMPLEMENTATION, TESTING, etc.)
- **Status**: Current state (PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED)
- **Dependencies**: List of other subtask IDs that must be completed before this subtask can begin
- **Context**: Additional information needed to execute the subtask

### Workflow

A workflow is a collection of related subtasks organized in a dependency graph. Workflows are typically created from GitHub issues and include:

- **Issue Information**: Number, title, and description of the associated GitHub issue
- **Project Information**: ID and name of the project
- **Subtasks**: List of subtasks to be executed
- **Status**: Overall status of the workflow

## Using the CLI

Knocodex provides CLI commands to interact with the subtask workflow system.

### Project Management

Create and manage projects:

```bash
# Create a new project
knocodex project create "My Project" "https://github.com/username/repo" --labels "enhancement,bug"

# List all projects
knocodex project list

# View project status and workflows
knocodex project status my-project-id
```

### Processing GitHub Issues

Process GitHub issues with subtasks:

```bash
# Process a GitHub issue with automatic subtask creation
knocodex workflow process-issue 123 --project my-project-id

# View the status of a workflow
knocodex workflow status workflow-id

# Retry a failed subtask
knocodex workflow retry workflow-id subtask-id
```

## Configuration

Configure the subtask workflow system in your `.knocodex/config.yaml`:

```yaml
subtask_workflow:
  # Maximum number of concurrent workflows
  max_concurrent_workflows: 3
  
  # Maximum number of concurrent subtasks within a workflow
  max_concurrent_subtasks: 10
  
  # Retry settings
  retry:
    max_retries: 3
    retry_delay: 60  # seconds
  
  # GitHub integration
  github:
    update_issue_comments: true
    create_branch_per_issue: true
    auto_create_pr: true
```

## Workflow Lifecycle

1. **Issue Processing**: A GitHub issue is analyzed and broken down into subtasks
2. **Planning**: Subtasks are organized with proper dependencies
3. **Execution**: Subtasks are executed in the correct order based on dependencies
4. **Monitoring**: Progress is tracked and displayed
5. **Completion**: When all subtasks are completed, the workflow is marked as complete
6. **Pull Request**: A pull request can be automatically created with the changes

## Error Handling

The system includes built-in error handling and retry mechanisms:

- Failed subtasks can be retried manually or automatically
- Dependencies are respected during retries
- Errors are logged with detailed information
- The workflow can be resumed from the point of failure

## Best Practices

1. **Issue Description**: Provide detailed issue descriptions to help with subtask breakdown
2. **Labels**: Use specific labels to control processing
3. **Dependencies**: Review the automatically generated dependencies and adjust if needed
4. **Testing**: Include test cases in the issue description for better test subtask generation
5. **Review**: Review the generated subtasks before execution for complex issues

## Advanced Usage

### Custom Subtask Types

You can define custom subtask types in your configuration:

```yaml
subtask_workflow:
  subtask_types:
    - name: RESEARCH
      description: "Research and gather information"
    - name: DESIGN
      description: "Design system architecture or UI"
```

### Integration with CI/CD

The subtask workflow system can be integrated with your CI/CD pipeline:

```yaml
subtask_workflow:
  ci_integration:
    trigger_ci_on_completion: true
    ci_pipeline_url: "https://ci.example.com/pipeline"
```

### Webhook Notifications

Configure webhooks to be notified when subtasks are completed:

```yaml
subtask_workflow:
  webhooks:
    subtask_completed:
      url: "https://your-app.com/webhook/subtask-completed"
      headers:
        Authorization: "Bearer ${WEBHOOK_TOKEN}"
```
