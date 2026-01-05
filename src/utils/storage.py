import json
import os
from loguru import logger

SAVE_FILE = "saved_plan.json"


def load_saved_plan() -> dict:
    """
    Loads the saved plan from disk.
    Converts JSON string keys back to integers (Subject IDs).
    """
    if not os.path.exists(SAVE_FILE):
        return {}

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # JSON keys are always strings, we need int keys for subject IDs
            return {int(k): v for k, v in data.items()}
    except Exception as e:
        logger.error(f"Failed to load saved plan: {e}")
        return {}


def save_plan_to_disk(plan: dict) -> bool:
    """
    Saves the plan to disk. Returns True if successful.
    """
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Failed to save plan: {e}")
        return False
