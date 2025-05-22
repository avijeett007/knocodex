"""MCP Server Implementation

This module implements the Model Context Protocol (MCP) server with FastAPI,
providing REST API endpoints and Server-Sent Events for real-time communication.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from .api.tasks import router as tasks_router
from .api.events import router as events_router
from .api.metrics import router as metrics_router
from .api.config import router as config_router
from .models.mcp_task import MCPServerConfig
from .config import get_config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server class that manages the FastAPI application and server lifecycle"""
    
    def __init__(self, config: MCPServerConfig = None):
        """Initialize MCP server with configuration"""
        self.config = config or self._load_config()
        self.app = None
        self.server = None
        self._setup_app()
    
    def _load_config(self) -> MCPServerConfig:
        """Load MCP server configuration from main config"""
        try:
            main_config = get_config()
            mcp_config = main_config.get("mcp_server", {})
            return MCPServerConfig(**mcp_config)
        except Exception as e:
            logger.warning(f"Failed to load MCP config, using defaults: {e}")
            return MCPServerConfig()
    
    def _setup_app(self):
        """Setup FastAPI application with middleware and routes"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan manager"""
            logger.info("MCP Server starting up...")
            yield
            logger.info("MCP Server shutting down...")
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Knocodex MCP Server",
            description="Model Context Protocol server for task management and automation",
            version="1.0.0",
            docs_url="/docs" if not self.config.auth_enabled else None,
            redoc_url="/redoc" if not self.config.auth_enabled else None,
            lifespan=lifespan
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add trusted host middleware for security
        if self.config.host != "*":
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=[self.config.host, "localhost", "127.0.0.1"]
            )
        
        # Add custom middleware for rate limiting if enabled
        if self.config.rate_limit_enabled:
            self._setup_rate_limiting()
        
        # Add authentication middleware if enabled
        if self.config.auth_enabled:
            self._setup_authentication()
        
        # Setup error handlers
        self._setup_error_handlers()
        
        # Include API routers
        self.app.include_router(tasks_router, prefix="/api/v1")
        self.app.include_router(events_router, prefix="/api/v1")
        self.app.include_router(metrics_router, prefix="/api/v1")
        self.app.include_router(config_router, prefix="/api/v1")
        
        # Add root endpoint
        @self.app.get("/")
        async def root():
            """Root endpoint with server information"""
            return {
                "name": "Knocodex MCP Server",
                "version": "1.0.0",
                "status": "running",
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "auth_enabled": self.config.auth_enabled,
                    "rate_limit_enabled": self.config.rate_limit_enabled
                }
            }
        
        # Add health check endpoint
        @self.app.get("/health")
        async def health_check():
            """Simple health check endpoint"""
            return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
    
    def _setup_rate_limiting(self):
        """Setup rate limiting middleware"""
        # Note: This is a simplified rate limiting implementation
        # In production, consider using redis-based rate limiting
        from collections import defaultdict
        from time import time
        
        request_counts = defaultdict(list)
        
        @self.app.middleware("http")
        async def rate_limit_middleware(request, call_next):
            client_ip = request.client.host
            now = time()
            minute_ago = now - 60
            
            # Clean old requests
            request_counts[client_ip] = [
                req_time for req_time in request_counts[client_ip] 
                if req_time > minute_ago
            ]
            
            # Check rate limit
            if len(request_counts[client_ip]) >= self.config.rate_limit_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"}
                )
            
            # Add current request
            request_counts[client_ip].append(now)
            
            response = await call_next(request)
            return response
    
    def _setup_authentication(self):
        """Setup authentication middleware"""
        from fastapi import Header, HTTPException
        
        @self.app.middleware("http")
        async def auth_middleware(request, call_next):
            # Skip auth for health check and docs
            if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
                return await call_next(request)
            
            # Check for auth header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing or invalid authorization header"}
                )
            
            token = auth_header.split(" ")[1]
            if token != self.config.auth_secret:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication token"}
                )
            
            response = await call_next(request)
            return response
    
    def _setup_error_handlers(self):
        """Setup custom error handlers"""
        
        @self.app.exception_handler(404)
        async def not_found_handler(request, exc):
            return JSONResponse(
                status_code=404,
                content={"detail": "Resource not found"}
            )
        
        @self.app.exception_handler(500)
        async def internal_error_handler(request, exc):
            logger.error(f"Internal server error: {exc}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
    
    async def start(self):
        """Start the MCP server"""
        if not self.config.enabled:
            logger.info("MCP Server is disabled in configuration")
            return
        
        try:
            logger.info(f"Starting MCP Server on {self.config.host}:{self.config.port}")
            
            config = uvicorn.Config(
                self.app,
                host=self.config.host,
                port=self.config.port,
                log_level=self.config.log_level.lower(),
                access_log=True
            )
            
            self.server = uvicorn.Server(config)
            await self.server.serve()
            
        except Exception as e:
            logger.error(f"Failed to start MCP Server: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server"""
        if self.server:
            logger.info("Stopping MCP Server...")
            self.server.should_exit = True
            await self.server.shutdown()
            self.server = None
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app


# Global server instance
_server_instance = None


def get_mcp_server(config: MCPServerConfig = None) -> MCPServer:
    """Get or create MCP server instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = MCPServer(config)
    return _server_instance


async def start_mcp_server(config: MCPServerConfig = None):
    """Start MCP server (convenience function)"""
    server = get_mcp_server(config)
    await server.start()


async def stop_mcp_server():
    """Stop MCP server (convenience function)"""
    global _server_instance
    if _server_instance:
        await _server_instance.stop()
        _server_instance = None


def run_mcp_server(config: MCPServerConfig = None):
    """Run MCP server in sync mode (for CLI usage)"""
    server = get_mcp_server(config)
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    # Allow running server directly
    run_mcp_server()