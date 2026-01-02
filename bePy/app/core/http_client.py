# app/core/http_client.py
import httpx

_client: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(15),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            )
        )
    return _client

async def close_http_client():
    global _client
    if _client:
        await _client.aclose()
        _client = None
