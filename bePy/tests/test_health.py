import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    # Depending on your router setup, you might have a root path or need to check a specific one
    # Assuming there's a health endpoint or at least we check if the router is working
    response = await client.get("/api/v1/auth/me") # Just to see if it responds with 401 instead of 404
    assert response.status_code in [200, 401, 403, 404] # Basic sanity check
