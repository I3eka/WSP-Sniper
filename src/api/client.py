import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from loguru import logger
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings


class WSPAsyncClient:
    def __init__(self):
        self.base_url = settings.base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_id: Optional[int] = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False, limit=100)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((aiohttp.ClientError, TimeoutError)),
        reraise=True,
    )
    async def login(self) -> int:
        """Authenticates and returns the User ID."""
        url = f"{self.base_url}/login?remember-me=1"
        data = {
            "remember-me": "1",
            "username": settings.username,
            "password": settings.password,
        }

        logger.debug(f"Attempting login for user: {settings.username}")
        async with self.session.post(url, data=data) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Login failed: {response.status} | {text}")
                raise Exception(f"Login failed: {response.status}")

            resp_json = await response.json()
            self.user_id = resp_json.get("id")

            if not self.user_id:
                raise Exception("Failed to retrieve user ID from response.")

            logger.info(f"Login successful. User ID: {self.user_id}")
            return self.user_id

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=2)
    )
    async def get_accruals(self) -> List[int]:
        if not self.user_id:
            raise Exception("User ID not set. Call login() first.")

        url = f"{self.base_url}/finance/accruals/{self.user_id}"
        async with self.session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return [subject["id"] for subject in data.get("ACCRUALS", [])]

    @retry(stop=stop_after_attempt(3))
    async def get_schedule(self, subject_id: int) -> Dict[str, Any]:
        url = (
            f"{self.base_url}/registration/student/{self.user_id}/schedule/{subject_id}"
        )
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def register_lessons(
        self, subject_id: int, payload: List[int]
    ) -> Tuple[int, str]:
        """
        Sends the final registration payload.
        Returns: (HTTP_STATUS_CODE, RESPONSE_TEXT)
        """
        url = f"{self.base_url}/registration/student/{self.user_id}/schedule/{subject_id}/save"
        try:
            async with self.session.post(url, json=payload) as response:
                text = await response.text()
                return response.status, text.strip()
        except Exception as e:
            return 0, str(e)
