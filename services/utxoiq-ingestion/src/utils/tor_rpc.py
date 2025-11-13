"""
Bitcoin RPC client with Tor support using requests library.
"""

import json
import requests
from typing import Any, Optional
from urllib.parse import urlparse


class TorAuthServiceProxy:
    """Bitcoin RPC client that routes through Tor SOCKS proxy using requests."""
    
    def __init__(self, service_url: str, timeout: int = 30):
        """
        Initialize Tor-enabled RPC client.
        
        Args:
            service_url: Bitcoin RPC URL (format: http://user:pass@host:port)
            timeout: Request timeout in seconds
        """
        self.service_url = service_url
        self.timeout = timeout
        self.request_id = 0
        
        # Parse URL for auth
        parsed = urlparse(service_url)
        self.url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 8332}"
        self.auth = (parsed.username, parsed.password) if parsed.username else None
        
        # Create session with Tor SOCKS proxy
        self.session = requests.Session()
        self.session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        self.session.auth = self.auth
    
    def _call(self, method: str, params: Optional[list] = None) -> Any:
        """Make RPC call to Bitcoin Core."""
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or []
        }
        
        response = self.session.post(
            self.url,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        result = response.json()
        
        if 'error' in result and result['error']:
            raise Exception(f"RPC Error: {result['error']}")
        
        return result.get('result')
    
    def __getattr__(self, name: str):
        """Allow method calls like rpc.getblockcount()."""
        def method_proxy(*args):
            return self._call(name, list(args) if args else None)
        return method_proxy
