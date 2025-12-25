"""
Security utilities for the PDF Generator service.

Provides URL validation to prevent SSRF attacks.
"""

import ipaddress
from typing import List
from urllib.parse import urlparse
from fastapi import HTTPException


def is_private_ip(host: str) -> bool:
    """
    Check if a host is a private/internal IP address.
    
    Args:
        host: Hostname or IP address
        
    Returns:
        True if host is a private IP, False otherwise
    """
    try:
        # Try to parse as IP address
        ip = ipaddress.ip_address(host)
        # Check if it's in private ranges
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        # Not an IP address, assume it's a hostname (public)
        # We'll validate against allowlist instead
        return False


def validate_frontend_url(url: str, allowed_origins: List[str]) -> str:
    """
    Validate frontend URL against allowlist to prevent SSRF attacks.
    
    Args:
        url: The frontend URL to validate
        allowed_origins: List of allowed origin strings (e.g., ["http://localhost:5173"])
        
    Returns:
        Validated origin string (scheme + host + port, no path/query)
        
    Raises:
        HTTPException: If URL is invalid or not in allowlist
    """
    if not url:
        raise HTTPException(status_code=400, detail="frontend_url is required")
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid frontend_url format: {str(e)}")
    
    # Validate scheme: must be http or https
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scheme: {parsed.scheme}. Only http and https are allowed."
        )
    
    # Validate host: must not be empty
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="Invalid frontend_url: missing hostname")
    
    # Block private IP addresses (SSRF protection)
    if is_private_ip(parsed.hostname):
        # Allow localhost only if explicitly in allowlist
        if parsed.hostname not in ("localhost", "127.0.0.1"):
            raise HTTPException(
                status_code=400,
                detail=f"Private IP addresses are not allowed: {parsed.hostname}"
            )
    
    # Construct origin (scheme + hostname + port)
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    
    origin = f"{parsed.scheme}://{parsed.hostname}"
    if (parsed.scheme == "http" and port != 80) or (parsed.scheme == "https" and port != 443):
        origin = f"{origin}:{port}"
    
    # Validate against allowlist
    if origin not in allowed_origins:
        raise HTTPException(
            status_code=400,
            detail=f"frontend_url origin '{origin}' is not in the allowed list. "
                   f"Allowed origins: {', '.join(allowed_origins)}"
        )
    
    return origin
