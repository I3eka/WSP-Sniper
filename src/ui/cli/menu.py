from typing import Any

from rich.prompt import Confirm, Prompt

from src.core.registration import RegistrationLogic
from src.ui.cli.formatting import console, create_schedule_table, print_header
from src.utils.helpers import format_time, get_lesson_short_code, get_lesson_type_name
from src.utils.storage import SAVE_FILE, load_saved_plan, save_plan_to_disk


class CLI:
    def get_user_confirmation(self, plan: dict) -> bool:
        console.print_json(data=plan)
        return Confirm.ask("[bold yellow]Confirm registration blueprint?[/bold yellow]")

    def ask_to_load_plan(self) -> dict[int, list[int]]:
        """Interactively asks to load the plan if it exists."""
        loaded_plan = load_saved_plan()
        if not loaded_plan:
            return {}

        console.print(
            f"\n[bold cyan][?] Found a saved plan in '{SAVE_FILE}'.[/bold cyan]"
        )
        if Confirm.ask("Do you want to load the previous configuration?"):
            console.print("[green]Plan loaded successfully![/green]")
            return loaded_plan
        return {}

    def save_plan(self, plan: dict[int, list[int]]):
        """Saves plan with CLI feedback."""
        if save_plan_to_disk(plan):
            console.print(
                f"[green][✓] Plan saved to '{SAVE_FILE}' for next time.[/green]"
            )
        else:
            console.print("[red]Warning: Failed to save plan.[/red]")

    def interactive_subject_selection(self, subject_data: dict[str, Any]) -> list[int]:
        subject = subject_data.get("SEMESTER_SUBJECT", {})
        schedules = subject_data.get("SCHEDULES", [])

        print_header(f"Configuring: {subject.get('name')} ({subject.get('code')})")
        console.print(f"Formula: [yellow]{subject.get('formula')}[/yellow]")

        if not schedules:
            console.print("[red]No schedule available.[/red]")
            return []

        streams: dict[str, list[dict[str, Any]]] = {}
        for sch in schedules:
            sid = str(sch.get("stream", "N/A"))
            streams.setdefault(sid, []).append(sch)

        selection_code_map = {}
        sorted_stream_ids = sorted(
            streams.keys(), key=lambda x: int(x) if x.isdigit() else x
        )

        for stream_id in sorted_stream_ids:
            lessons = streams[stream_id]
            table = create_schedule_table()
            is_reg = any(lesson["studentRegistered"] for lesson in lessons)
            title_style = "bold green" if is_reg else "bold white"
            console.print(f"\n[{title_style}]→ Stream {stream_id}[/{title_style}]")

            for s in lessons:
                l_type = get_lesson_type_name(int(s.get("lessonTypeId", 0)))
                s_code = get_lesson_short_code(int(s.get("lessonTypeId", 0)))
                grp = s.get("group")
                sel_code = f"{s_code}{grp}"
                selection_code_map[sel_code] = s

                time_rng = f"{format_time(s['beginTime'])}-{format_time(s['endTime'])}"
                limit = f"{s['studentCount']}/{s['studentCountMax']}"

                table.add_row(
                    sel_code,
                    str(grp),
                    l_type,
                    s.get("teacher", "N/A"),
                    s.get("room", "N/A"),
                    s.get("weekDay", "N/A"),
                    time_rng,
                    limit,
                )
            console.print(table)

        selected_stream = Prompt.ask(
            "Select Stream ID", choices=sorted_stream_ids, show_choices=True
        )
        stream_lessons = streams[selected_stream]

        current_stream_map = {}
        for s in stream_lessons:
            short_code = get_lesson_short_code(int(s.get("lessonTypeId", 0)))
            code = f"{short_code}{s.get('group')}"
            current_stream_map[code] = s

        req_counts = RegistrationLogic.parse_formula(subject.get("formula"))

        while True:
            console.print(
                f"[bold]Selected Stream {selected_stream}. "
                f"Enter codes (e.g. L1 P1).[/bold]"
            )
            user_input = Prompt.ask("Codes")
            chosen_codes = list(set(c.upper() for c in user_input.split() if c))

            if not all(c in current_stream_map for c in chosen_codes):
                console.print("[red]Invalid code entered.[/red]")
                continue

            is_valid, msg = RegistrationLogic.validate_selection(
                chosen_codes, current_stream_map, req_counts
            )
            if is_valid:
                console.print("[green]Selection Validated.[/green]")
                break
            else:
                console.print(f"[red]Validation Error:[/red] {msg}")
                if not Confirm.ask("Retry selection? (no to abort subject)"):
                    return []

        return sorted([current_stream_map[c]["id"] for c in chosen_codes])
