import asyncio
from typing import Any

import pandas as pd
import streamlit as st

from src.api.client import WSPAsyncClient
from src.utils.helpers import format_time, get_lesson_type_name
from src.utils.storage import load_saved_plan, save_plan_to_disk


def _parse_subject_identity(subject_data: dict) -> tuple[str, str]:
    """Robustly extracts (Name, Code) from a subject dictionary."""
    if "SEMESTER_SUBJECT" in subject_data:
        nested = subject_data["SEMESTER_SUBJECT"]
        name = nested.get("name") or nested.get("disciplineName")
        code = nested.get("code") or nested.get("disciplineCode")
        if name:
            return name, str(code or "")

    name = (
        subject_data.get("discipline")
        or subject_data.get("subjectName")
        or subject_data.get("name")
        or subject_data.get("title")
        or "Unknown Subject"
    )
    code = (
        subject_data.get("disciplineCode")
        or subject_data.get("code")
        or str(subject_data.get("id", ""))
    )
    return name, code


def render_web_scheduler():
    user_id = st.session_state.get("user_id")
    subjects = st.session_state.get("raw_subjects", [])

    if "plan" not in st.session_state:
        st.session_state.plan = load_saved_plan()

    plan = st.session_state.plan

    st.info(f"User ID: {user_id} | Planned Subjects: {len(plan)}")

    with st.expander("📚 Subject Selection & Scheduling", expanded=True):
        if not subjects:
            st.warning("No subjects found. Please login via Sidebar.")
            return

        for subject in subjects:
            s_name, s_code = _parse_subject_identity(subject)
            s_id = int(subject.get("id"))

            is_planned = s_id in plan
            icon = "✅" if is_planned else "⬜"

            if st.checkbox(f"{icon} {s_name} ({s_code})", key=f"chk_{s_id}"):
                _render_subject_details(user_id, s_id, s_name, s_code, plan)


def _render_subject_details(user_id, s_id, s_name, s_code, plan):
    cache_key = f"schedule_{s_id}"

    if cache_key not in st.session_state:
        try:
            with st.spinner(f"Loading schedule for {s_name}..."):

                async def fetch():
                    async with WSPAsyncClient() as client:
                        client.user_id = user_id
                        await client.login()
                        return await client.get_schedule(s_id)

                st.session_state[cache_key] = asyncio.run(fetch())
        except Exception as e:
            st.error(f"Failed to load: {e}")
            return

    schedule_data = st.session_state[cache_key]
    schedules = schedule_data.get("SCHEDULES", [])

    if not schedules:
        st.warning("No schedule available.")
        return

    streams: dict[str, list[dict[str, Any]]] = {}
    for s in schedules:
        streams.setdefault(str(s.get("stream", "N/A")), []).append(s)

    with st.form(f"form_{s_id}"):
        all_dfs = {}
        current_selection = plan.get(s_id, [])

        for stream_id, lessons in streams.items():
            st.markdown(f"**Stream {stream_id}**")
            rows = []
            for lesson in lessons:
                l_id = lesson["id"]
                begin = format_time(lesson.get("beginTime"))
                end = format_time(lesson.get("endTime"))
                count = lesson.get("studentCount")
                max_count = lesson.get("studentCountMax")
                rows.append(
                    {
                        "id": l_id,
                        "Select": l_id in current_selection,
                        "Code": s_code,
                        "Type": get_lesson_type_name(lesson.get("lessonTypeId")),
                        "Day": lesson.get("weekDay"),
                        "Time": f"{begin}-{end}",
                        "Teacher": lesson.get("teacher"),
                        "Seats": f"{count}/{max_count}",
                    }
                )

            df = pd.DataFrame(rows)
            all_dfs[stream_id] = st.data_editor(
                df,
                key=f"ed_{s_id}_{stream_id}",
                hide_index=True,
                disabled=["id", "Code", "Type", "Day", "Time", "Teacher", "Seats"],
                column_config={"id": None},
            )

        if st.form_submit_button("💾 Save Selection", type="primary"):
            final_ids = []
            for df in all_dfs.values():
                final_ids.extend(df[df["Select"]]["id"].tolist())

            if final_ids:
                plan[s_id] = final_ids
                st.session_state.plan = plan

                save_plan_to_disk(plan)
                st.toast(f"Saved {s_name}")
                st.rerun()
            else:
                if s_id in plan:
                    del plan[s_id]
                    st.session_state.plan = plan
                    save_plan_to_disk(plan)
                    st.toast(f"Removed {s_name} from plan")
                    st.rerun()
                else:
                    st.warning("No lessons selected.")
