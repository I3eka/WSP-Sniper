import os
import json
from typing import List, Dict, Any
from rich.prompt import Prompt, Confirm
from src.ui.formatting import console, create_schedule_table, print_header
from src.utils.helpers import format_time, get_lesson_type_name, get_lesson_short_code
from src.core.registration import RegistrationLogic

SAVE_FILE = "saved_plan.json"


class CLI:
    def get_user_confirmation(self, plan: Dict) -> bool:
        console.print_json(data=plan)
        return Confirm.ask("[bold yellow]Confirm registration blueprint?[/bold yellow]")

    def ask_to_load_plan(self) -> Dict[int, List[int]]:
        """
        Checks for a saved plan file and asks user if they want to use it.
        """
        if not os.path.exists(SAVE_FILE):
            return {}

        console.print(
            f"\n[bold cyan][?] Found a saved plan in '{SAVE_FILE}'.[/bold cyan]"
        )
        if Confirm.ask("Do you want to load the previous configuration?"):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    plan = {int(k): v for k, v in data.items()}
                console.print("[green]Plan loaded successfully![/green]")
                return plan
            except Exception as e:
                console.print(f"[red]Failed to load plan: {e}[/red]")
        return {}

    def save_plan(self, plan: Dict[int, List[int]]):
        """
        Saves the current registration plan to disk.
        """
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=4)
            console.print(
                f"[green][✓] Plan saved to '{SAVE_FILE}' for next time.[/green]"
            )
        except Exception as e:
            console.print(f"[red]Warning: Failed to save plan: {e}[/red]")

    def interactive_subject_selection(self, subject_data: Dict[str, Any]) -> List[int]:
        subject = subject_data.get("SEMESTER_SUBJECT", {})
        schedules = subject_data.get("SCHEDULES", [])

        print_header(f"Configuring: {subject.get('name')} ({subject.get('code')})")
        console.print(f"Formula: [yellow]{subject.get('formula')}[/yellow]")

        if not schedules:
            console.print("[red]No schedule available.[/red]")
            return []

        streams = {}
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
                l_type = get_lesson_type_name(s.get("lessonTypeId"))
                s_code = get_lesson_short_code(s.get("lessonTypeId"))
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
            code = f"{get_lesson_short_code(s.get('lessonTypeId'))}{s.get('group')}"
            current_stream_map[code] = s

        req_counts = RegistrationLogic.parse_formula(subject.get("formula"))

        while True:
            console.print(
                f"[bold]Selected Stream {selected_stream}. Enter codes (e.g. L1 P1).[/bold]"
            )
            user_input = Prompt.ask("Codes")
            chosen_codes = list(set(c.upper() for c in user_input.split() if c))

            if not all(c in current_stream_map for c in chosen_codes):
                console.print("[red]Invalid code entered. Check table above.[/red]")
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
