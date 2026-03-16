"""Jobs resource — /v1/jobs

Check the status of async jobs (PDF generation, FEC export, etc.).
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Jobs:
    """Synchronous jobs resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def get(self, job_id: str) -> dict[str, Any]:
        """Returns the job dict with status, progress, result, and error fields."""
        resp = self._client.get(f"/v1/jobs/{job_id}")
        return resp.json()  # type: ignore[no-any-return]


class AsyncJobs:
    """Asynchronous jobs resource.

    Check the status of async jobs (PDF generation, FEC export, etc.).
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def get(self, job_id: str) -> dict[str, Any]:
        """Returns the job dict with status, progress, result, and error fields."""
        resp = await self._client.get(f"/v1/jobs/{job_id}")
        return resp.json()  # type: ignore[no-any-return]
