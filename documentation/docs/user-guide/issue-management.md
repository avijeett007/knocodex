# Issue Management

This guide covers how to effectively manage GitHub issues with Knocodex, including labeling strategies, issue templates, and workflow optimization.

## Issue Labeling Strategy

### Automation Labels

Use specific labels to control when and how Knocodex processes issues:

- **`knocodex-auto`**: Primary trigger label for automatic processing
- **`knocodex-priority-high`**: High-priority processing (processed first)
- **`knocodex-skip`**: Exclude from automatic processing
- **`knocodex-review-required`**: Requires human review before processing

### Category Labels

Organize issues by type and complexity:

```yaml
# Label configuration in .knocodex/config.yaml
issue_labels:
  automation:
    trigger: "knocodex-auto"
    priority_high: "knocodex-priority-high"
    skip: "knocodex-skip"
    review_required: "knocodex-review-required"
  
  categories:
    bug: "bug"
    feature: "enhancement"
    documentation: "documentation"
    refactoring: "refactor"
    testing: "test"
  
  complexity:
    simple: "complexity-simple"
    moderate: "complexity-moderate"
    complex: "complexity-complex"
```

## Issue Templates

### Bug Report Template

Create `.github/ISSUE_TEMPLATE/bug-report.md`:

```markdown
---
name: Bug Report
about: Report a bug for automatic processing
title: 'Bug: [Brief Description]'
labels: ['bug', 'knocodex-auto']
assignees: ''
---

## Bug Description
A clear and concise description of the bug.

## Steps to Reproduce
1. Step one
2. Step two  
3. Step three
4. Observed behavior

## Expected Behavior
What should happen instead.

## Environment
- OS: [e.g., macOS 12.0, Ubuntu 20.04]
- Python version: [e.g., 3.9.0]
- Knocodex version: [e.g., 1.0.0]

## Additional Context
Any other context, screenshots, or logs.

## Implementation Hints
<!-- Optional: Provide implementation guidance for Knocodex -->
- [ ] Check error handling in module X
- [ ] Review input validation
- [ ] Update unit tests

## Acceptance Criteria
- [ ] Bug is fixed
- [ ] Tests pass
- [ ] No regression in related functionality
```

### Feature Request Template

Create `.github/ISSUE_TEMPLATE/feature-request.md`:

```markdown
---
name: Feature Request  
about: Request a new feature for automatic implementation
title: 'Feature: [Brief Description]'
labels: ['enhancement', 'knocodex-auto']
assignees: ''
---

## Feature Description
A clear description of the feature you want.

## Use Case
Who would use this feature and why?

## Proposed Solution
How should this feature work?

## Acceptance Criteria
- [ ] Feature requirement 1
- [ ] Feature requirement 2
- [ ] Tests are added
- [ ] Documentation is updated

## Implementation Notes
<!-- Optional: Technical guidance for Knocodex -->
- [ ] Modify file X to add functionality Y
- [ ] Create new endpoint/method
- [ ] Update configuration options

## Dependencies
List any dependencies on other issues or external systems.
```

### Documentation Template

Create `.github/ISSUE_TEMPLATE/documentation.md`:

```markdown
---
name: Documentation
about: Documentation updates or improvements
title: 'Docs: [Brief Description]'
labels: ['documentation', 'knocodex-auto']
assignees: ''
---

## Documentation Request
What documentation needs to be created or updated?

## Target Audience  
Who is this documentation for?

## Content Requirements
- [ ] Getting started guide
- [ ] API documentation
- [ ] Examples and tutorials
- [ ] Troubleshooting information

## Files to Update
List specific files that need changes:
- [ ] README.md
- [ ] docs/api.md
- [ ] docs/examples/

## Success Criteria
- [ ] Documentation is complete
- [ ] Code examples work
- [ ] Links are valid
- [ ] Spelling and grammar checked
```

## Workflow Configuration

### Automatic Processing Rules

Configure processing rules in `.knocodex/config.yaml`:

```yaml
issue_processing:
  # Labels that trigger processing
  trigger_labels:
    - "knocodex-auto"
  
  # Labels that prevent processing
  exclusion_labels:
    - "knocodex-skip"
    - "wontfix"
    - "duplicate"
  
  # Priority processing order
  priority_labels:
    high: "knocodex-priority-high"
    medium: "knocodex-priority-medium"  
    low: "knocodex-priority-low"
  
  # Processing constraints
  constraints:
    max_age_days: 30          # Skip issues older than 30 days
    min_words: 20             # Require minimum description length
    require_assignee: false   # Don't require assignee
    require_milestone: false  # Don't require milestone
  
  # Auto-labeling rules
  auto_labels:
    - condition: "title contains 'bug'"
      add_labels: ["bug"]
    - condition: "title contains 'feature'"
      add_labels: ["enhancement"]
    - condition: "body contains 'breaking change'"
      add_labels: ["breaking-change"]
```

### GitHub Actions Integration

Create `.github/workflows/knocodex-issue-processing.yml`:

```yaml
name: Knocodex Issue Processing

on:
  issues:
    types: [opened, labeled, edited]
  
jobs:
  process-issue:
    if: contains(github.event.issue.labels.*.name, 'knocodex-auto')
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install Knocodex
        run: pip install knocodex
      
      - name: Process Issue
        run: |
          knocodex process-issue \
            --issue-number ${{ github.event.issue.number }} \
            --priority ${{ contains(github.event.issue.labels.*.name, 'knocodex-priority-high') && 'high' || 'normal' }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          KNOCODEX_REDIS_URL: ${{ secrets.REDIS_URL }}
```

## Issue Quality Guidelines

### Writing Effective Issues

**Do:**
- Use clear, descriptive titles
- Provide detailed descriptions with context
- Include reproduction steps for bugs
- Specify acceptance criteria
- Add relevant labels and milestones
- Link to related issues or PRs

**Don't:**
- Use vague titles like "Fix bug" or "Add feature"
- Skip reproduction steps for bugs
- Forget to specify expected vs. actual behavior  
- Leave acceptance criteria undefined
- Mix multiple requests in one issue

### Examples

**Good Bug Report:**
```markdown
# Bug: User authentication fails with special characters in password

## Description
Users cannot log in when their password contains special characters like @, #, or %.

## Reproduction
1. Create account with password "Test@123#"
2. Log out
3. Try to log in with same credentials
4. Authentication fails with "Invalid credentials"

## Expected: User logs in successfully
## Actual: Authentication error displayed

## Environment
- Browser: Chrome 95.0
- OS: macOS 12.0
- App version: 2.1.0
```

**Good Feature Request:**
```markdown  
# Feature: Add export functionality to user dashboard

## Use Case
Users want to export their data for backup or migration purposes.

## Requirements
- Export user profile data as JSON
- Export activity history as CSV
- Email export file to user
- Support batch exports for admins

## Acceptance Criteria
- [ ] Export button in user dashboard
- [ ] JSON export includes all profile data
- [ ] CSV export includes activity history
- [ ] Email notification when export ready
- [ ] Admin can export multiple users
```

## Monitoring and Metrics

### Issue Processing Stats

Monitor processing effectiveness:

```bash
# View processing statistics
knocodex stats issues --period 7d

# Check success rates
knocodex stats success-rate --by-label

# View processing times  
knocodex stats timing --percentiles 50,90,95
```

### Quality Metrics

Track issue quality indicators:

- **Time to first response**: How quickly issues are acknowledged
- **Resolution time**: Time from label to completion
- **Success rate**: Percentage of successfully processed issues
- **Rework rate**: Issues requiring multiple attempts

### Dashboard Monitoring

Use the RQ dashboard to monitor:

```bash
# Start monitoring dashboard
knocodex dashboard

# Monitor from command line
knocodex monitor --refresh 30s
```

## Best Practices

### For Project Maintainers

1. **Set Clear Guidelines**: Document labeling conventions and expectations
2. **Use Templates**: Create comprehensive issue templates
3. **Monitor Quality**: Regularly review generated PRs and provide feedback
4. **Adjust Rules**: Fine-tune processing rules based on results
5. **Train Contributors**: Help others write better issues

### For Contributors

1. **Follow Templates**: Use provided issue templates when available
2. **Be Specific**: Provide detailed descriptions and reproduction steps
3. **Test Locally**: Verify issues exist before reporting
4. **Stay Engaged**: Respond to questions and review generated PRs
5. **Provide Feedback**: Help improve the automation by giving feedback

### For Teams

1. **Establish Workflows**: Define clear processes for issue management
2. **Review Regularly**: Schedule regular reviews of automated work
3. **Measure Impact**: Track time savings and quality improvements
4. **Iterate**: Continuously improve labels, templates, and processes
5. **Document Learnings**: Share successful patterns and avoid pitfalls

## Advanced Configuration

### Custom Issue Processors

Create custom processors for special issue types:

```python
# .knocodex/processors/security_issue.py
from knocodex.processors import BaseProcessor

class SecurityIssueProcessor(BaseProcessor):
    def can_process(self, issue):
        return 'security' in [label.name for label in issue.labels]
    
    def process(self, issue):
        # Custom security issue processing
        return self.create_security_fix_plan(issue)
```

### Integration Hooks

Set up webhooks for external integrations:

```yaml
# .knocodex/config.yaml  
webhooks:
  issue_processed:
    url: "https://your-app.com/webhook/issue-processed"
    headers:
      Authorization: "Bearer your-token"
  
  processing_failed:
    url: "https://your-app.com/webhook/processing-failed"
    headers:
      Authorization: "Bearer your-token"
```

## Next Steps

- [Troubleshooting Guide](troubleshooting.md)
- [Developer Documentation](../developer-guide/architecture.md)
- [API Reference](../developer-guide/api-reference.md)