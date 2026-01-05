from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def display_logo():
    logo = r"""
                                        ██╗    ██╗███████╗██████╗     ███████╗███╗   ██╗██╗██████╗ ███████╗██████╗                                                     
                                        ██║    ██║██╔════╝██╔══██╗    ██╔════╝████╗  ██║██║██╔══██╗██╔════╝██╔══██╗                                                    
                                        ██║ █╗ ██║███████╗██████╔╝    ███████╗██╔██╗ ██║██║██████╔╝█████╗  ██████╔╝                                                    
                                        ██║███╗██║╚════██║██╔═══╝     ╚════██║██║╚██╗██║██║██╔═══╝ ██╔══╝  ██╔══██╗                                                    
                                        ╚███╔███╔╝███████║██║         ███████║██║ ╚████║██║██║     ███████╗██║  ██║                                                    
                                        ╚══╝╚══╝ ╚══════╝╚═╝         ╚══════╝╚═╝  ╚════╝╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝                                                    
"""
    console.print(Panel(Text(logo, style="bold cyan"), title="v2.0"))


def print_header(text: str):
    console.print(f"\n[bold blue]{'═' * 50}[/bold blue]")
    console.print(f"[bold]{text}[/bold]")
    console.print(f"[bold blue]{'═' * 50}[/bold blue]")


def create_schedule_table() -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Code", style="cyan", width=8)
    table.add_column("Group", width=8)
    table.add_column("Type", width=8)
    table.add_column("Teacher", style="green")
    table.add_column("Room")
    table.add_column("Day")
    table.add_column("Time")
    table.add_column("Limit", justify="right")
    return table
