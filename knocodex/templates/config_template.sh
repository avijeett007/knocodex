#!/usr/bin/env bash
# Knocodex configuration

# Project settings
PROJECT_PATH="{{PROJECT_PATH}}"
DOCS_PATH="{{PROJECT_PATH}}/docs"
GITHUB_REPO="{{GITHUB_REPO}}"
GITHUB_ISSUE_LABEL="knocodex"

# Operation settings
POLLING_INTERVAL=300
REDIS_URL="redis://localhost:6379"
REDIS_QUEUE="knocodex"

# Paths
CLAUDE_CODE_PATH="{{CLAUDE_CODE_PATH}}"

# MCP servers
MCP_SERVERS_ENABLED=true
# Add any custom MCP servers here
# Example: MCP_SERVER_GITHUB="docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN ghcr.io/github/github-mcp-server"

# PR review settings
PR_REVIEW_ENABLED=true
PR_AUTO_REVIEW=true
PR_AUTO_REVIEW_DELAY=300
PR_REVIEW_MAX_RETRIES=3
PR_REVIEW_RETRY_DELAY=300
MIN_REREVIEW_HOURS=24
REVIEW_ONLY_OWN_PRS=true

# PR review behavior configuration
PR_REVIEW_MODE="never_repeat"  # Options: never_repeat, on_updates, manual_only
PR_STATE_STORAGE_PATH=""  # Path for PR state storage (empty = use default)
PR_UPDATE_DETECTION_ENABLED=true  # Enable PR update detection
