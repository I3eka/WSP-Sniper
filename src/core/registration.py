"""Registration logic for the WSP sniper application.

This module provides:
- RegistrationLogic: class containing methods for parsing formulas,
  validating selections, and executing registration attempts.
"""

import asyncio
from typing import Any

from loguru import logger

from config.settings import settings
from src.api.client import WSPAsyncClient


class RegistrationLogic:
    """Handles registration logic for the WSP sniper application.

    Methods:
    -------
    parse_formula(formula: str) -> tuple[int, int, int]
        Parse a formula string into lesson type counts.
    validate_selection(selection_codes, stream_code_map, required_counts)
        -> tuple[bool, str]: Validate that selected lessons match required counts.
    execute_sniper_attack(client, registration_plan) -> None
        Execute registration attempts for all subjects in the plan.
    """

    @staticmethod
    def parse_formula(formula: str) -> tuple[int, int, int]:
        """Parse a formula string into lesson type counts.

        Parameters
        ----------
        formula : str
            A formula string in the format "L/Lab/Pr" (e.g., "2/1/1").

        Returns:
        -------
        tuple[int, int, int]
            A tuple of (lectures, labs, practicals) counts.
            Returns (-1, -1, -1) if parsing fails.
        """
        try:
            parts = formula.split("/")
            lec, lab, pr = map(int, parts)
            return lec, lab, pr
        except (ValueError, IndexError, AttributeError):
            return -1, -1, -1

    @staticmethod
    def validate_selection(
        selection_codes: list[str],
        stream_code_map: dict[str, Any],
        required_counts: tuple[int, int, int],
    ) -> tuple[bool, str]:
        """Validate that selected lessons match required counts.

        Parameters
        ----------
        selection_codes : list[str]
            List of selected stream codes.
        stream_code_map : dict[str, Any]
            Mapping from stream codes to lesson data.
        required_counts : tuple[int, int, int]
            Required counts as (lectures, labs, practicals).

        Returns:
        -------
        tuple[bool, str]
            A tuple of (is_valid, message) indicating validation result.
        """
        req_l, req_b, req_p = required_counts
        if req_l == -1:
            return True, "Formula unknown, skipping validation."
        selected_lessons = [stream_code_map[code] for code in selection_codes]
        act_l = sum(1 for s in selected_lessons if s.get("lessonTypeId") == 1)
        act_b = sum(1 for s in selected_lessons if s.get("lessonTypeId") == 2)
        act_p = sum(1 for s in selected_lessons if s.get("lessonTypeId") == 3)
        if act_l == req_l and act_b == req_b and act_p == req_p:
            return True, "OK"
        msg = (
            f"Requirement mismatch. "
            f"Needed: L:{req_l}, Lab:{req_b}, Pr:{req_p}. "
            f"Selected: L:{act_l}, Lab:{act_b}, Pr:{act_p}."
        )
        return False, msg

    @staticmethod
    async def _attempt_registration(
        client: WSPAsyncClient, subject_id: int, payload: list[int]
    ):
        """Attempt to register until successful.

        Ignores 504, 502, 500 and any network errors, retrying every 0.5 sec.
        """
        attempt = 1
        while True:
            logger.info(f"Subj {subject_id}: Requesting... (Attempt #{attempt})")
            status, text = await client.register_lessons(subject_id, payload)

            if status == 200:
                logger.success(f"Subj {subject_id}: ✅ SUCCESS! Response: {text}")
                return

            if status == 504:
                logger.warning(
                    f"Subj {subject_id}: ⚠️ 504 Gateway Time-out "
                    f"(Server Busy). Retrying in 0.5s..."
                )
                await asyncio.sleep(0.5)
                attempt += 1
                continue

            if status == 500 and "Регистрация не началась" in text:
                logger.warning(f"Subj {subject_id}: ⏳ Too early. Retry #{attempt}...")
                await asyncio.sleep(settings.retry_delay)
                attempt += 1
                continue

            clean_text = "HTML Page" if "<html" in text.lower() else text.strip()

            logger.error(
                f"Subj {subject_id}: ❌ Failed [{status}] {clean_text}. "
                f"Retrying in 0.5s..."
            )

            await asyncio.sleep(0.5)
            attempt += 1

    @staticmethod
    async def execute_sniper_attack(
        client: WSPAsyncClient, registration_plan: dict[int, list[int]]
    ) -> None:
        """Execute registration attempts for all subjects in the plan.

        Parameters
        ----------
        client : WSPAsyncClient
            The async client used to make registration requests.
        registration_plan : dict[int, list[int]]
            A mapping from subject IDs to lists of lesson IDs to register.
        """
        tasks = []
        for subject_id, payload in registration_plan.items():
            task = asyncio.create_task(
                RegistrationLogic._attempt_registration(client, subject_id, payload)
            )
            tasks.append(task)
            await asyncio.sleep(settings.request_delay)
        await asyncio.gather(*tasks)
