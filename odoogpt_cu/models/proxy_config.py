"""
Proxy Configuration Module
Provides utilities for configuring HTTP proxies for OpenAI SDK requests.
"""

import os
from typing import Optional, Dict
from urllib.parse import urlparse
import httpx
from dotenv import load_dotenv

load_dotenv()


class ProxyConfig:
    """Handles proxy configuration for HTTP clients."""

    def __init__(self, proxy_url: Optional[str] = None):
        """
        Initialize proxy configuration.

        Args:
            proxy_url: HTTP proxy URL in format: http://username:password@host:port
                      If None, will try to get from environment variables
        """
        self.proxy_url = proxy_url or self._get_proxy_from_env()
        self.is_valid = self._validate_proxy_url()

    def _get_proxy_from_env(self) -> Optional[str]:
        """Get proxy URL from environment variables."""
        # Check common proxy environment variables
        proxy_vars = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"]

        for var in proxy_vars:
            proxy = os.getenv(var)
            if proxy:
                return proxy

        return None

    def _validate_proxy_url(self) -> bool:
        """Validate the proxy URL format."""
        if not self.proxy_url:
            return False

        try:
            parsed = urlparse(self.proxy_url)
            return bool(parsed.scheme and parsed.hostname and parsed.port)
        except Exception:
            return False

    def get_httpx_client_config(self) -> Dict:
        """
        Get configuration for httpx client with proxy settings.

        Returns:
            Dictionary with httpx client configuration
        """
        config = {
            "timeout": 60.0,
            "verify": True,  # Enable SSL verification
        }

        if self.proxy_url and self.is_valid:
            # Use 'proxy' instead of 'proxies' for newer httpx versions
            config["proxy"] = self.proxy_url

        return config

    def create_sync_client(self) -> httpx.Client:
        """Create a synchronous httpx client with proxy configuration."""
        return httpx.Client(**self.get_httpx_client_config())

    def create_async_client(self) -> httpx.AsyncClient:
        """Create an asynchronous httpx client with proxy configuration."""
        return httpx.AsyncClient(**self.get_httpx_client_config())

    def get_proxy_info(self) -> Dict[str, str]:
        """Get proxy information for debugging."""
        if not self.proxy_url:
            return {"status": "No proxy configured"}

        if not self.is_valid:
            return {"status": "Invalid proxy URL", "url": self.proxy_url}

        try:
            parsed = urlparse(self.proxy_url)
            return {
                "status": "Proxy configured",
                "scheme": parsed.scheme,
                "hostname": parsed.hostname,
                "port": str(parsed.port),
                "username": parsed.username if parsed.username else "Not provided",
            }
        except Exception as e:
            return {"status": "Error parsing proxy URL", "error": str(e)}


def get_default_proxy_config() -> ProxyConfig:
    """Get default proxy configuration from environment."""
    return ProxyConfig()


def create_proxy_client_sync(proxy_url: Optional[str] = None) -> httpx.Client:
    """
    Create a synchronous HTTP client with proxy configuration.

    Args:
        proxy_url: Optional proxy URL. If None, uses environment variables.

    Returns:
        Configured httpx.Client
    """
    config = ProxyConfig(proxy_url)
    return config.create_sync_client()


def create_proxy_client_async(proxy_url: Optional[str] = None) -> httpx.AsyncClient:
    """
    Create an asynchronous HTTP client with proxy configuration.

    Args:
        proxy_url: Optional proxy URL. If None, uses environment variables.

    Returns:
        Configured httpx.AsyncClient
    """
    config = ProxyConfig(proxy_url)
    return config.create_async_client()


if __name__ == "__main__":
    proxy_config = get_default_proxy_config()
    print("Proxy Configuration Info:")
    print(proxy_config.get_proxy_info())

    test_config = ProxyConfig()
    print("\nTest Proxy Configuration:")
    print(test_config.get_proxy_info())
