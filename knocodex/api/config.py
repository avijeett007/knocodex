"""Configuration management API endpoints"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends
from ..models.mcp_task import MCPServerConfig
from ..config import get_config, update_config

router = APIRouter(prefix="/config", tags=["config"])


def get_current_config():
    """Dependency to get current configuration"""
    return get_config()


@router.get("", response_model=MCPServerConfig)
async def get_mcp_config(config: dict = Depends(get_current_config)):
    """Get current MCP server configuration"""
    try:
        mcp_config = config.get("mcp_server", {})
        return MCPServerConfig(**mcp_config)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.get("/all")
async def get_full_config(config: dict = Depends(get_current_config)):
    """Get full system configuration"""
    try:
        return config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.put("", response_model=MCPServerConfig)
async def update_mcp_config(
    updated_config: MCPServerConfig,
    config: dict = Depends(get_current_config)
):
    """Update MCP server configuration"""
    try:
        # Update the MCP server section of the configuration
        config["mcp_server"] = updated_config.model_dump()
        
        # Save updated configuration
        update_config(config)
        
        return updated_config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.patch("")
async def patch_mcp_config(
    config_updates: Dict[str, Any],
    config: dict = Depends(get_current_config)
):
    """Partially update MCP server configuration"""
    try:
        # Get current MCP config
        mcp_config = config.get("mcp_server", {})
        
        # Apply updates
        mcp_config.update(config_updates)
        
        # Validate updated config
        updated_config = MCPServerConfig(**mcp_config)
        
        # Save to main config
        config["mcp_server"] = updated_config.model_dump()
        update_config(config)
        
        return updated_config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to patch configuration: {str(e)}")


@router.get("/validate")
async def validate_config(config: dict = Depends(get_current_config)):
    """Validate current configuration"""
    try:
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate MCP server config
        try:
            mcp_config = config.get("mcp_server", {})
            MCPServerConfig(**mcp_config)
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"MCP server config invalid: {str(e)}")
        
        # Check for common configuration issues
        mcp_config = config.get("mcp_server", {})
        
        # Check if auth is enabled but no secret is provided
        if mcp_config.get("auth_enabled", False) and not mcp_config.get("auth_secret"):
            validation_results["warnings"].append("Authentication enabled but no auth_secret provided")
        
        # Check port availability (basic validation)
        port = mcp_config.get("port", 8080)
        if port < 1024 and port != 80 and port != 443:
            validation_results["warnings"].append(f"Port {port} requires elevated privileges")
        
        return validation_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate configuration: {str(e)}")


@router.post("/reset")
async def reset_mcp_config():
    """Reset MCP server configuration to defaults"""
    try:
        default_config = MCPServerConfig()
        
        # Get current full config
        config = get_current_config()
        config["mcp_server"] = default_config.model_dump()
        
        # Save updated configuration
        update_config(config)
        
        return default_config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset configuration: {str(e)}")


@router.get("/schema")
async def get_config_schema():
    """Get MCP server configuration JSON schema"""
    try:
        return MCPServerConfig.model_json_schema()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config schema: {str(e)}")