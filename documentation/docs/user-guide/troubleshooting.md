# Troubleshooting

This guide helps you diagnose and resolve common issues with Knocodex.

## Quick Diagnostics

### Health Check Commands

```bash
# Run comprehensive health check
knocodex health --verbose

# Check individual components
knocodex test github    # Test GitHub API connection
knocodex test redis     # Test Redis connection
knocodex test claude    # Test Claude Code CLI

# Validate configuration
knocodex config validate

# Check service status
knocodex status
```

### Log Analysis

```bash
# View recent logs
knocodex logs --tail 100

# Filter by log level
knocodex logs --level error

# View logs for specific timeframe
knocodex logs --since 1h

# Follow logs in real-time
knocodex logs --follow
```

## Common Issues

### 1. Service Won't Start

**Symptoms:**
- `knocodex start` fails or times out
- "Connection refused" errors
- Services show as "stopped" in status

**Diagnosis:**
```bash
# Check what's preventing startup
knocodex start --verbose

# Verify prerequisites
redis-cli ping                    # Should return "PONG"
claude-code --version            # Should show version
python --version                 # Should be 3.8+
```

**Solutions:**

**Redis Not Running:**
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis-server

# Docker
docker run -d -p 6379:6379 redis:alpine
```

**Claude Code CLI Missing:**
```bash
# Reinstall Claude Code
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code
```

**Port Conflicts:**
```bash
# Check if ports are in use
lsof -i :6379  # Redis port
netstat -an | grep 6379

# Kill conflicting processes if needed
sudo kill -9 <process_id>
```

### 2. GitHub API Issues

**Symptoms:**
- "Authentication failed" errors  
- "API rate limit exceeded"
- Issues not being detected

**Diagnosis:**
```bash
# Test GitHub connection
knocodex test github

# Check rate limits
curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/rate_limit

# Verify repository access
gh repo view owner/repo
```  

**Solutions:**

**Invalid Token:**
```bash
# Generate new token at https://github.com/settings/tokens
# Required scopes: repo, workflow
export GITHUB_TOKEN="your_new_token"

# Or update config
knocodex config set github.token "your_new_token"
```

**Rate Limiting:**
```yaml
# Reduce polling frequency in config.yaml
github:
  poll_interval: 600  # Increase from 300 to 600 seconds
  max_issues_per_poll: 5  # Reduce from 10 to 5
```

**Repository Access:**
```bash
# Verify repository exists and you have access
gh repo view your-org/your-repo

# Check if token has correct permissions
gh auth status
```

### 3. Queue Processing Problems

**Symptoms:**
- Jobs stuck in queue
- Workers not processing tasks
- Tasks failing repeatedly

**Diagnosis:**
```bash
# Open RQ dashboard
knocodex dashboard

# Check queue status via CLI
redis-cli llen knocodex  # Queue length
redis-cli keys "rq:*"   # All RQ keys

# Check worker status
ps aux | grep rq
```

**Solutions:**

**Clear Stuck Jobs:**
```bash
# Clear all jobs from queue
redis-cli del knocodex

# Clear failed jobs
redis-cli del rq:failed:knocodex

# Restart workers
knocodex restart
```

**Increase Workers:**
```yaml
# In config.yaml
queue:
  max_workers: 6  # Increase worker count
  default_timeout: 7200  # Increase timeout
```

**Memory Issues:**
```bash
# Check Redis memory usage
redis-cli info memory

# Clear Redis cache if needed
redis-cli flushdb

# Optimize Redis config
redis-cli config set maxmemory-policy allkeys-lru
```

### 4. Claude Code Integration Issues

**Symptoms:**
- "Claude command failed" errors
- Timeouts during implementation
- Malformed output from Claude

**Diagnosis:**
```bash
# Test Claude Code directly
claude-code --version
claude-code /help

# Check if running in headless mode
ps aux | grep claude

# Verify command templates exist
ls -la .claude/commands/
```

**Solutions:**

**Command Timeouts:**
```yaml
# Increase timeout in config.yaml
claude:
  timeout: 7200  # Increase from 3600 to 7200 seconds
  max_retries: 5  # Increase retry attempts
```

**Missing Command Templates:**
```bash
# Recreate default command templates
knocodex init --reset-commands

# Or manually create
mkdir -p .claude/commands
cp knocodex/templates/commands/* .claude/commands/
```

**Headless Mode Issues:**
```yaml
# In config.yaml
claude:
  headless: true    # Ensure headless mode
  model: "claude-3-5-sonnet"  # Specify model
```

### 5. Permission and Access Issues

**Symptoms:**
- "Permission denied" errors
- Can't create files or directories
- Branch creation failures

**Diagnosis:**
```bash
# Check file permissions
ls -la .knocodex/
ls -la .claude/

# Verify Git configuration
git remote -v
git config user.name
git config user.email
```

**Solutions:**

**File Permission Issues:**
```bash
# Fix .knocodex directory permissions
chmod -R 755 .knocodex/
chown -R $USER:$USER .knocodex/

# Fix .claude directory permissions
chmod -R 755 .claude/
chown -R $USER:$USER .claude/
```

**Git Configuration:**
```bash
# Set up Git identity if missing
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify remote URL
git remote set-url origin https://github.com/username/repo.git
```

## Advanced Troubleshooting

### Debug Mode

Enable detailed logging for troubleshooting:

```yaml
# config.yaml
logging:
  level: "DEBUG"
  console: true
  file: ".knocodex/logs/debug.log"

# Environment variable
export KNOCODEX_DEBUG=true
```

### Network Issues

**Proxy Configuration:**
```bash
# If behind corporate proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

**SSL Certificate Issues:**
```bash
# Skip SSL verification (not recommended for production)
export PYTHONHTTPSVERIFY=0
export CURL_CA_BUNDLE=""
```

### Database Issues

**Redis Corruption:**
```bash
# Check Redis integrity
redis-cli --scan --pattern "*"

# Backup and restore
redis-cli --rdb /tmp/dump.rdb
redis-cli debug restart
```

**Connection Pool Exhaustion:**
```yaml
# Increase connection pool in config.yaml
redis:
  connection_pool_size: 20
  socket_keepalive: true
  socket_timeout: 30
```

## Performance Troubleshooting

### Slow Processing

**Diagnosis:**
```bash
# Check system resources
top
htop
df -h  # Disk space
free -h  # Memory usage
```

**Solutions:**
```yaml
# Optimize queue settings
queue:
  max_workers: 4  # Match CPU cores
  chunk_size: 50  # Reduce batch size
  prefetch_multiplier: 2

# Optimize Redis
redis:
  socket_keepalive: true
  health_check_interval: 60
```

### Memory Usage

**Monitor Memory:**
```bash
# Python memory usage
ps aux | grep python | awk '{print $6}'

# Redis memory
redis-cli info memory

# System memory
free -h
```

**Optimize Memory:**
```yaml
# Limit concurrent operations
claude:
  max_concurrent: 2

# Clear old results
queue:
  result_ttl: 3600    # Keep results for 1 hour only
  failure_ttl: 86400  # Keep failures for 1 day
```

## Getting Help

### Collect Diagnostic Information

Before seeking help, collect this information:

```bash
# System information
knocodex --version
python --version
redis-cli --version
claude-code --version

# Configuration
knocodex config show

# Recent logs
knocodex logs --level error --since 24h

# Health check results
knocodex health --verbose
```

### Create Support Bundle

```bash
# Generate diagnostic bundle
knocodex support bundle

# This creates .knocodex/support-bundle.zip with:
# - Configuration (sanitized)
# - Recent logs
# - System information
# - Health check results
```

### Community Support

- **GitHub Issues**: [Report bugs and feature requests](https://github.com/knocodex/knocodex/issues)
- **Discussions**: [Ask questions and share experiences](https://github.com/knocodex/knocodex/discussions)
- **Discord**: [Join our community chat](https://discord.gg/knocodex)

### FAQ

**Q: Why aren't my issues being processed?**
A: Check that issues have the correct labels, verify GitHub API access, and ensure Knocodex is running.

**Q: Can I process issues from multiple repositories?**
A: Yes, configure multiple repository settings or run separate Knocodex instances.

**Q: How do I handle sensitive code or private repositories?**
A: Ensure proper token permissions and consider running Knocodex on secure infrastructure.

**Q: What happens if processing fails?**
A: Failed jobs are moved to a failed queue and can be retried manually or automatically based on configuration.

**Q: How do I update Knocodex?**
A: Run `pip install --upgrade knocodex` and restart services with `knocodex restart`.

## Prevention Tips

### Regular Maintenance

```bash
# Weekly maintenance script
#!/bin/bash
knocodex health --verbose
knocodex cleanup --older-than 7d
knocodex logs --level warning --since 7d
redis-cli info memory
```

### Monitoring Setup

```yaml
# config.yaml - Set up alerts
notifications:
  slack:
    webhook_url: "your-webhook"
    alerts:
      - queue_size > 50
      - processing_time > 1800
      - error_rate > 0.1
```

### Backup Strategy

```bash
# Backup configuration and logs
tar -czf knocodex-backup-$(date +%Y%m%d).tar.gz .knocodex/

# Backup Redis data
redis-cli --rdb backup-$(date +%Y%m%d).rdb
```

Remember: Most issues can be resolved by restarting services, checking configuration, and verifying external dependencies (Redis, GitHub API, Claude Code CLI).