# src/utils/helpers.py


def format_time(time_float: float | None) -> str:
    """Converts a float time (e.g., 14.5) to HH:MM string."""
    if time_float is None:
        return "N/A"
    hour = int(time_float)
    minute = int((time_float - hour) * 60)
    return f"{hour:02d}:{minute:02d}"


def get_lesson_type_name(lesson_type_id: int | None) -> str:
    mapping = {1: "Lecture", 2: "Lab", 3: "Practice"}
    if lesson_type_id is None:
        return "N/A"
    return mapping.get(lesson_type_id, "N/A")


def get_lesson_short_code(lesson_type_id: int) -> str:
    mapping = {1: "L", 2: "B", 3: "P"}
    return mapping.get(lesson_type_id, "")
