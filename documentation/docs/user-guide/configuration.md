# Configuration

Knocodex offers extensive configuration options to customize its behavior for your specific needs. This guide covers all available configuration options and how to use them.

## Configuration Files

Knocodex uses a hierarchical configuration system:

1. **Global Config**: `~/.knocodex/config.json` (system-wide settings)
2. **Project Config**: `.knocodex/config.json` (project-specific settings)
3. **Environment Variables**: Override any configuration value

Project settings override global settings, and environment variables override both.

## PR Review Configuration

Knocodex includes an advanced PR review deduplication system to prevent reviewing the same PR multiple times:

```json
{
  "pr_review_enabled": true,
  "pr_review_mode": "never_repeat",
  "pr_state_storage_path": null,
  "pr_update_detection_enabled": true
}
```

### PR Review Modes

- **`never_repeat`**: Review each PR only once, never again (default)
- **`on_updates`**: Re-review PRs when new commits are pushed
- **`manual_only`**: Disable automatic PR reviews entirely

## Basic Configuration

### GitHub Integration

```yaml
github:
  token: "ghp_xxxxxxxxxxxx"        # GitHub Personal Access Token
  owner: "your-username"           # Repository owner
  repo: "your-repo-name"          # Repository name
  issue_label: "knocodex-auto"    # Label to trigger automation
  poll_interval: 300              # Polling interval in seconds
  max_issues_per_poll: 10         # Max issues to process per poll
  base_branch: "main"             # Default base branch for PRs
```

### Redis Configuration

```yaml
redis:
  host: "localhost"               # Redis server host
  port: 6379                     # Redis server port
  db: 0                          # Redis database number
  password: null                 # Redis password (if required)
  socket_timeout: 30             # Connection timeout
  socket_keepalive: true         # Keep connection alive
  health_check_interval: 30      # Health check interval
```

### Claude Code Settings

```yaml
claude:
  headless: true                 # Run Claude Code in headless mode
  timeout: 3600                  # Command timeout in seconds
  max_retries: 3                # Maximum retry attempts
  retry_delay: 30               # Delay between retries
  model: "claude-3-5-sonnet"    # Claude model to use
  temperature: 0.1              # Model temperature
```

## Advanced Configuration

### Queue Settings

```yaml
queue:
  name: "knocodex"              # Queue name
  default_timeout: 3600         # Default job timeout
  result_ttl: 86400            # Result time-to-live in seconds
  failure_ttl: 604800          # Failed job TTL in seconds
  max_workers: 4               # Maximum concurrent workers
  worker_ttl: 420              # Worker time-to-live
```

### Logging Configuration

```yaml
logging:
  level: "INFO"                # Log level (DEBUG, INFO, WARNING, ERROR)
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: ".knocodex/logs/knocodex.log"
  max_size: "10MB"             # Log file max size
  backup_count: 5              # Number of backup log files
  console: true                # Enable console logging
```

### Custom Commands

```yaml
commands:
  analyze_issue: "/project:analyze-github-issue"
  implement_issue: "/project:implement-github-issue"
  document_project: "/project:document-project"
  review_pr: "/project:review-pull-request"
  custom_command: "/project:your-custom-command"
```

### Issue Processing Rules

```yaml
issue_rules:
  required_labels:             # Issues must have these labels
    - "bug"
    - "enhancement"
  excluded_labels:             # Skip issues with these labels
    - "wontfix"
    - "duplicate"
  min_priority: 1              # Minimum priority level
  max_age_days: 30            # Skip issues older than X days
  assignee_required: false     # Require assignee
  milestone_required: false    # Require milestone
```

### Notification Settings

```yaml
notifications:
  slack:
    webhook_url: "https://hooks.slack.com/..."
    channel: "#development"
    username: "Knocodex"
    icon_emoji: ":robot_face:"
  
  email:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    from_email: "knocodex@yourcompany.com"
    to_emails:
      - "dev-team@yourcompany.com"
```

## Environment Variables

All configuration options can be overridden using environment variables with the `KNOCODEX_` prefix:

```bash
# GitHub configuration
export KNOCODEX_GITHUB_TOKEN="your-token"
export KNOCODEX_GITHUB_OWNER="your-username"
export KNOCODEX_GITHUB_REPO="your-repo"

# Redis configuration
export KNOCODEX_REDIS_HOST="localhost"
export KNOCODEX_REDIS_PORT="6379"

# Claude configuration
export KNOCODEX_CLAUDE_HEADLESS="true"
export KNOCODEX_CLAUDE_TIMEOUT="3600"
```

Nested configuration uses double underscores:

```bash
export KNOCODEX_GITHUB__TOKEN="your-token"
export KNOCODEX_REDIS__HOST="localhost"
export KNOCODEX_NOTIFICATIONS__SLACK__WEBHOOK_URL="https://..."
```

## Configuration Templates

### Minimal Configuration

```yaml
# .knocodex/config.yaml
github:
  token: "your-github-token"
  owner: "your-username"
  repo: "your-repo"

redis:
  host: "localhost"
  port: 6379
```

### Production Configuration

```yaml
# .knocodex/config.yaml
github:
  token: "your-github-token"
  owner: "your-org"
  repo: "your-repo"
  issue_label: "auto-implement"
  poll_interval: 180
  max_issues_per_poll: 5
  base_branch: "develop"

redis:
  host: "redis.yourcompany.com"
  port: 6379
  password: "your-redis-password"
  db: 1

claude:
  headless: true
  timeout: 7200
  max_retries: 3
  model: "claude-3-5-sonnet"

queue:
  max_workers: 8
  default_timeout: 7200

logging:
  level: "INFO"
  file: "/var/log/knocodex/knocodex.log"

notifications:
  slack:
    webhook_url: "your-slack-webhook"
    channel: "#ai-development"
```

## Validation

Validate your configuration:

```bash
# Check configuration syntax
knocodex config validate

# Display current configuration
knocodex config show

# Test GitHub connection
knocodex test github

# Test Redis connection
knocodex test redis
```

## Security Considerations

- **Never commit tokens to version control**
- Use environment variables or external secret management
- Limit GitHub token permissions to minimum required
- Use Redis AUTH if running in production
- Consider network security for distributed deployments

## Next Steps

- [Learn Basic Usage](usage.md)
- [Set Up Issue Management](issue-management.md)
- [Troubleshooting Guide](troubleshooting.md)