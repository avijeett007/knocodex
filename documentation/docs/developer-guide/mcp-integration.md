# MCP Integration Guide

This guide covers the Model Context Protocol (MCP) server integration features in Knocodex, designed to enable seamless integration with external AI IDEs and development tools.

## Overview

The MCP server provides REST API endpoints and Server-Sent Events (SSE) for real-time communication with external integrations. It's built on FastAPI and provides comprehensive task management, health monitoring, and system statistics.

## Base URL

The MCP server runs on `http://localhost:8080` by default. All endpoints are prefixed with `/api/v1` unless noted otherwise.

## Integration Endpoints

### CLI Options

Get available CLI options and configurations for external integrations.

```http
GET /api/v1/cli/options
```

**Response:**
```json
{
  "commands": {
    "analyze-github-issue": {
      "description": "Analyze GitHub issue and create implementation plan",
      "required_params": ["issue_url"],
      "optional_params": ["project_path", "custom_instructions"]
    },
    "implement-github-issue": {
      "description": "Implement solution based on analysis plan",
      "required_params": ["plan_path"],
      "optional_params": ["force_implementation", "skip_tests"]
    }
  },
  "options": {
    "project_path": {
      "type": "string",
      "description": "Path to the project directory",
      "default": "."
    },
    "agent_type": {
      "type": "string",
      "description": "AI agent type to use",
      "options": ["claude", "aider"],
      "default": "claude"
    }
  },
  "environment_variables": {
    "ANTHROPIC_API_KEY": "Required for Claude agent",
    "GEMINI_API_KEY": "Required for Aider with Gemini",
    "GITHUB_TOKEN": "Required for GitHub operations"
  },
  "project_structure": {
    "required_directories": [".knocodex", ".claude/commands"],
    "config_files": [".knocodex/config.json", "CLAUDE.md"]
  },
  "integrations": {
    "ide_extensions": {
      "vscode": {
        "extension_id": "knocodex.ai-workflow",
        "settings": ["knocodex.serverUrl", "knocodex.apiKey"]
      },
      "cursor": {
        "integration_type": "mcp_client",
        "server_config": "mcp_server.json"
      }
    }
  }
}
```

### Statistics Summary

Get comprehensive system statistics summary for external integrations.

```http
GET /api/v1/stats/summary?timeframe=24h&include_trends=true
```

**Query Parameters:**
- `timeframe` (optional): Time frame for statistics (`1h`, `6h`, `24h`, `7d`, `30d`). Default: `24h`
- `include_trends` (optional): Include trend analysis. Default: `true`

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "tasks": {
    "total": 150,
    "pending": 5,
    "queued": 2,
    "running": 3,
    "completed": 135,
    "failed": 5,
    "cancelled": 0
  },
  "performance": {
    "avg_task_duration": 45.5,
    "success_rate": 90.0,
    "throughput_per_hour": 12.5,
    "queue_wait_time": 2.3
  },
  "system": {
    "cpu_usage": 25.4,
    "memory_usage": 68.2,
    "disk_usage": 45.1,
    "uptime": 86400
  },
  "queue": {
    "size": 7,
    "processing": 3,
    "failed": 1,
    "retry_count": 2
  },
  "workers": {
    "active": 3,
    "idle": 1,
    "busy": 2,
    "total": 4
  },
  "trends": {
    "task_completion": [12, 15, 18, 14, 16, 13, 17],
    "success_rate": [88.5, 89.2, 90.1, 89.8, 90.0],
    "response_time": [42.1, 44.3, 45.5, 43.8, 45.2]
  },
  "alerts": [
    {
      "type": "warning",
      "message": "Queue size above normal threshold",
      "threshold": 5,
      "current_value": 7,
      "timestamp": "2024-01-15T10:25:00Z"
    }
  ]
}
```

### Integration Health Check

Comprehensive health check endpoint for external integrations.

```http
GET /api/v1/integration/health?include_details=true
```

**Query Parameters:**
- `include_details` (optional): Include detailed health information. Default: `true`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.5,
      "connection_pool": "active",
      "last_check": "2024-01-15T10:30:00Z"
    },
    "workflow_engine": {
      "status": "healthy",
      "active_workflows": 3,
      "pending_tasks": 5,
      "last_check": "2024-01-15T10:30:00Z"
    },
    "claude_api": {
      "status": "healthy",
      "rate_limit_remaining": 95,
      "last_request": "2024-01-15T10:28:00Z"
    }
  },
  "capabilities": [
    "task_management",
    "workflow_execution",
    "sse_streaming",
    "health_monitoring",
    "metrics_collection",
    "github_integration",
    "claude_integration"
  ],
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "system_info": {
    "python_version": "3.11.5",
    "fastapi_version": "0.104.1",
    "redis_version": "7.2.0",
    "platform": "darwin",
    "hostname": "knocodex-server"
  },
  "integration_ready": true
}
```

## Server-Sent Events (SSE)

### Task Events Stream

Real-time stream of task events.

```http
GET /api/v1/events/tasks
```

**Event Types:**
- `task_created`: New task created
- `task_updated`: Task status or details updated
- `task_started`: Task execution started
- `task_completed`: Task completed successfully
- `task_failed`: Task execution failed
- `task_cancelled`: Task cancelled

**Event Format:**
```
event: task_created
data: {"task_id": "abc123", "timestamp": "2024-01-15T10:30:00Z", "data": {...}}

event: task_updated
data: {"task_id": "abc123", "timestamp": "2024-01-15T10:31:00Z", "data": {...}}
```

### System Metrics Stream

Real-time stream of system metrics.

```http
GET /api/v1/events/metrics
```

**Metrics Include:**
- Task statistics
- System performance
- Queue status
- Worker status
- Resource usage

## Authentication

By default, the MCP server runs without authentication. To enable authentication:

1. Set `auth_enabled: true` in configuration
2. Set `auth_secret` to a secure secret key
3. Include `Authorization: Bearer <token>` header in requests

## Rate Limiting

The server implements rate limiting by default:
- Global: 100 requests per minute per IP
- Integration endpoints: 60 requests per minute per IP

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "invalid_request",
  "message": "Detailed error description",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123"
}
```

**Common Error Codes:**
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Configuration

### MCP Server Configuration

```json
{
  "mcp_server": {
    "enabled": true,
    "host": "localhost",
    "port": 8080,
    "cors_origins": ["*"],
    "auth_enabled": false,
    "max_connections": 100,
    "sse_heartbeat_interval": 30,
    "metrics_retention_days": 7,
    "rate_limit_enabled": true,
    "rate_limit_requests": 100,
    "log_level": "INFO"
  }
}
```

### Integration Configuration

```json
{
  "integration": {
    "enabled": true,
    "cli_commands_enabled": true,
    "stats_enabled": true,
    "health_checks_enabled": true,
    "allowed_origins": ["*"],
    "api_key_required": false,
    "rate_limit_per_minute": 60,
    "cache_ttl_seconds": 300
  }
}
```

## SDK Examples

### Python SDK

```python
import asyncio
import aiohttp

class KnocodexClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
    
    async def get_health(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/v1/integration/health") as resp:
                return await resp.json()
    
    async def get_stats(self, timeframe="24h"):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/stats/summary",
                params={"timeframe": timeframe}
            ) as resp:
                return await resp.json()
    
    async def listen_task_events(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/v1/events/tasks") as resp:
                async for line in resp.content:
                    if line.startswith(b"data: "):
                        yield line[6:].decode().strip()

# Usage
client = KnocodexClient()
health = await client.get_health()
print(f"System status: {health['status']}")
```

### JavaScript SDK

```javascript
class KnocodexClient {
    constructor(baseUrl = 'http://localhost:8080') {
        this.baseUrl = baseUrl;
    }
    
    async getHealth() {
        const response = await fetch(`${this.baseUrl}/api/v1/integration/health`);
        return response.json();
    }
    
    async getStats(timeframe = '24h') {
        const response = await fetch(`${this.baseUrl}/api/v1/stats/summary?timeframe=${timeframe}`);
        return response.json();
    }
    
    listenTaskEvents(callback) {
        const eventSource = new EventSource(`${this.baseUrl}/api/v1/events/tasks`);
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            callback(data);
        };
        
        return eventSource;
    }
}

// Usage
const client = new KnocodexClient();
const health = await client.getHealth();
console.log(`System status: ${health.status}`);

// Listen for task events
const eventSource = client.listenTaskEvents((event) => {
    console.log('Task event:', event);
});
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure MCP server is running
   - Check port configuration
   - Verify firewall settings

2. **Authentication Errors**
   - Verify API key configuration
   - Check token expiration
   - Ensure proper headers

3. **Rate Limiting**
   - Implement exponential backoff
   - Reduce request frequency
   - Use batch operations when available

4. **SSE Connection Issues**
   - Check network connectivity
   - Verify SSE client implementation
   - Monitor connection timeouts

### Debug Mode

Enable debug logging by setting `log_level: "DEBUG"` in configuration:

```json
{
  "mcp_server": {
    "log_level": "DEBUG"
  }
}
```

### Health Monitoring

Regular health checks are recommended:

```bash
# Quick health check
curl -f http://localhost:8080/api/v1/integration/health || echo "Server unhealthy"

# Detailed health with system info
curl "http://localhost:8080/api/v1/integration/health?include_details=true"
```

## Best Practices

1. **Connection Management**
   - Use connection pooling for HTTP clients
   - Implement proper timeout handling
   - Monitor connection health

2. **Error Handling**
   - Implement retry logic with exponential backoff
   - Log errors with context
   - Handle rate limiting gracefully

3. **Performance**
   - Cache responses when appropriate
   - Use SSE for real-time updates
   - Batch operations when possible

4. **Security**
   - Use HTTPS in production
   - Implement proper authentication
   - Validate all inputs

5. **Monitoring**
   - Monitor health endpoints
   - Track response times
   - Set up alerting for failures