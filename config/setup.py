from rich.console import Console
from rich.prompt import Prompt

console = Console()


def run_first_launch_setup():
    """
    Interactively prompts the user for configuration data
    and saves it to a .env file.
    """
    console.print("[bold blue]═" * 50 + "[/bold blue]")
    console.print(
        "[bold green]✨ Welcome to WSP-Sniper First Launch Setup! ✨[/bold green]"
    )
    console.print("It seems you don't have a configuration file yet.")
    console.print("Please enter your KBTU WSP credentials below.\n")

    # 1. Set Default URL
    base_url = "https://wsp2.kbtu.kz/bachelor/api"

    # 2. Gather User Input
    username = Prompt.ask("[bold cyan]Username[/bold cyan]")

    password = Prompt.ask("[bold cyan]Password[/bold cyan]", password=True)

    console.print(
        "\n[yellow]Time Configuration:[/yellow] Enter the start time as you see it on your local clock."
    )
    time_local = Prompt.ask(
        "[bold cyan]Desired Start Time (Local)[/bold cyan]", default="09:00:00.000000"
    )

    # 3. Construct .env content
    env_content = f"""WSP_BASE_URL="{base_url}"
WSP_USERNAME="{username}"
WSP_PASSWORD="{password}"
# Format: HH:MM:SS or HH:MM:SS.000000 (Local Time)
WSP_DESIRED_TIME_LOCAL="{time_local}"

# Delay (in seconds) between sending requests for DIFFERENT subjects
# Increase if you get 500 Errors. Default is 0.2
WSP_REQUEST_DELAY="0.2"

# Delay (in seconds) to wait before retrying the SAME subject 
# if the server says "Registration not started". Default is 0.5
WSP_RETRY_DELAY="0.5"
"""

    # 4. Write file
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        console.print(
            "\n[bold green][✓] Configuration saved to .env successfully![/bold green]"
        )
        console.print("Starting the bot initialization...\n")
        console.print("[bold blue]═" * 50 + "[/bold blue]\n")
    except Exception as e:
        console.print(f"[bold red][!] Failed to write .env file: {e}[/bold red]")
        exit(1)
