import asyncio
from typing import List, Dict, Any, Tuple
from loguru import logger
from src.api.client import WSPAsyncClient
from config.settings import settings


class RegistrationLogic:
    @staticmethod
    def parse_formula(formula: str) -> Tuple[int, int, int]:
        try:
            return tuple(map(int, formula.split("/")))
        except (ValueError, IndexError, AttributeError):
            return -1, -1, -1

    @staticmethod
    def validate_selection(
        selection_codes: List[str],
        stream_code_map: Dict[str, Any],
        required_counts: Tuple[int, int, int],
    ) -> Tuple[bool, str]:
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
        client: WSPAsyncClient, subject_id: int, payload: List[int]
    ):
        """
        Пытается зарегистрироваться до победного конца.
        Игнорирует 504, 502, 500 и любые ошибки сети, повторяя запрос каждые 0.5 сек.
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
                    f"Subj {subject_id}: ⚠️ 504 Gateway Time-out (Server Busy). Retrying in 0.5s..."
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
                f"Subj {subject_id}: ❌ Failed [{status}] {clean_text}. Retrying in 0.5s..."
            )

            await asyncio.sleep(0.5)
            attempt += 1

    @staticmethod
    async def execute_sniper_attack(
        client: WSPAsyncClient, registration_plan: Dict[int, List[int]]
    ) -> None:
        tasks = []
        for subject_id, payload in registration_plan.items():
            task = asyncio.create_task(
                RegistrationLogic._attempt_registration(client, subject_id, payload)
            )
            tasks.append(task)
            await asyncio.sleep(settings.request_delay)
        await asyncio.gather(*tasks)
