import asyncio
from typing import List, Dict, Any, Tuple
from loguru import logger
from src.api.client import WSPAsyncClient
from config.settings import settings


class RegistrationLogic:
    # ... (методы parse_formula и validate_selection без изменений) ...
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
        attempt = 1
        while True:
            # ЛОГ ПЕРЕД ОТПРАВКОЙ (Виден и в консоли, и в браузере)
            logger.info(f"Subj {subject_id}: Requesting... (Attempt #{attempt})")

            status, text = await client.register_lessons(subject_id, payload)

            if status == 200:
                logger.success(f"Subj {subject_id}: ✅ SUCCESS! Response: {text}")
                return

            # Проверка на "Рано"
            if status == 500 and "Регистрация не началась" in text:
                logger.warning(
                    f"Subj {subject_id}: ⏳ Too early. Retry #{attempt} in {settings.retry_delay}s..."
                )
                await asyncio.sleep(settings.retry_delay)
                attempt += 1
                continue

            # Ошибка
            logger.error(f"Subj {subject_id}: ❌ FAILED [{status}] {text}")
            return

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
