import os
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich.layout import Layout
from rich.align import Align

class GameUI:
    def __init__(self):
        self.console = Console()
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_welcome(self):
        """Display welcome screen"""
        self.clear_screen()
        welcome_text = """
╔══════════════════════════════════════════════════════════════╗
║                     🧩 GRID PUZZLE GAME 🧩                    ║
║                                                              ║
║    Solve interconnected clues in a grid-based puzzle!       ║
║    Each clue you solve reveals new clues in the grid.       ║
║                                                              ║
║    🎯 How to Play:                                           ║
║    • Choose a category (or create your own)                 ║
║    • Start with one revealed clue                           ║
║    • Solve clues to unlock more clues                       ║
║    • Complete the entire grid to win!                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        self.console.print(welcome_text, style="bold cyan")
        self.console.print("\nPress Enter to continue...", style="dim")
        input()
    
    def display_category_selection(self, categories: List[str]) -> str:
        """Display category selection menu"""
        self.clear_screen()
        self.console.print("🎲 [bold]Choose a Category[/bold]\n")
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Number", style="bold blue")
        table.add_column("Category", style="bold")
        table.add_column("Description", style="dim")
        
        for i, category in enumerate(categories, 1):
            table.add_row(f"{i}.", category, "AI-generated content")
        
        self.console.print(table)
        
        self.console.print(f"\n{len(categories) + 1}. [bold yellow]Create Custom Category[/bold yellow]")
        
        while True:
            try:
                choice = IntPrompt.ask(
                    f"\nEnter your choice (1-{len(categories) + 1})",
                    default=1
                )
                
                if 1 <= choice <= len(categories):
                    return categories[choice - 1]
                elif choice == len(categories) + 1:
                    return self._get_custom_category()
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
            except Exception:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
    
    def _get_custom_category(self) -> str:
        """Get custom category from user"""
        while True:
            category = Prompt.ask("\n🎨 Enter your custom category")
            
            if len(category.strip()) >= 3:
                confirm = Prompt.ask(
                    f"Use '{category}' as your category? (y/n)", 
                    choices=["y", "n"], 
                    default="y"
                )
                if confirm.lower() == 'y':
                    return category.strip()
            else:
                self.console.print("[red]Category must be at least 3 characters long.[/red]")
    
    def select_grid_size(self) -> int:
        """Let user select grid size"""
        self.console.print("\n🎯 [bold]Choose Grid Size[/bold]")
        
        sizes = {
            1: {"size": 3, "desc": "3x3 - Beginner (9 clues)", "difficulty": "Easy"},
            2: {"size": 4, "desc": "4x4 - Intermediate (16 clues)", "difficulty": "Medium"}, 
            3: {"size": 5, "desc": "5x5 - Expert (25 clues)", "difficulty": "Hard"}
        }
        
        for num, info in sizes.items():
            difficulty_color = {"Easy": "green", "Medium": "yellow", "Hard": "red"}[info["difficulty"]]
            self.console.print(f"{num}. {info['desc']} - [{difficulty_color}]{info['difficulty']}[/{difficulty_color}]")
        
        while True:
            try:
                choice = IntPrompt.ask("\nSelect grid size (1-3)", default=1)
                if choice in sizes:
                    return sizes[choice]["size"]
                else:
                    self.console.print("[red]Invalid choice. Please select 1, 2, or 3.[/red]")
            except Exception:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
    
    def display_game_board(self, game_status: Dict):
        """Display the current game board and status"""
        self.clear_screen()
        
        # Game header
        self.console.print(f"🧩 [bold]{game_status['category']}[/bold] - {game_status['grid_size']}x{game_status['grid_size']} Grid\n")
        
        # Create board display
        board_display = game_status.get('board_display', [])
        if not board_display and 'current_clues' in game_status:
            # Generate board display from game state
            board_display = self._create_board_display(game_status)
        
        # Display grid
        table = Table(show_header=False, box=None, padding=(1, 2))
        for _ in range(game_status['grid_size']):
            table.add_column(justify="center", min_width=10)
        
        for i, row in enumerate(board_display):
            formatted_row = []
            for j, cell in enumerate(row):
                if cell == "■":
                    formatted_row.append("[dim]■[/dim]")
                elif cell == "❓":
                    formatted_row.append(f"[yellow]({i+1},{j+1})[/yellow]")
                else:
                    formatted_row.append(f"[green]{cell}[/green]")
            table.add_row(*formatted_row)
        
        self.console.print(table)
        
        # Status bar
        progress = game_status.get('progress', 0)
        self.console.print(f"\n📊 Progress: {progress:.1f}% | 🎯 Score: {game_status.get('score', 0)} | ⏱️  Time: {self._format_time(game_status.get('elapsed_time', 0))}")
        self.console.print(f"💡 Hints Used: {game_status.get('hints_used', 0)} | ❌ Wrong Guesses: {game_status.get('wrong_guesses', 0)}")
    
    def _create_board_display(self, game_status: Dict) -> List[List[str]]:
        """Create board display from game status"""
        grid_size = game_status['grid_size']
        display = [["■" for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Mark revealed positions
        for clue in game_status.get('current_clues', []):
            row, col = clue['row'], clue['col']
            display[row][col] = "❓"
        
        return display
    
    def display_current_clues(self, clues: List[Dict]):
        """Display available clues"""
        if not clues:
            self.console.print("\n[yellow]No clues available yet![/yellow]")
            return
        
        self.console.print("\n🔍 [bold]Available Clues:[/bold]")
        
        for clue in clues:
            difficulty_colors = {1: "green", 2: "yellow", 3: "red"}
            difficulty_color = difficulty_colors.get(clue['difficulty'], "white")
            
            clue_panel = Panel(
                f"[{difficulty_color}]{clue['clue']}[/{difficulty_color}]",
                title=f"Position {clue['position']} (Difficulty: {clue['difficulty']})",
                border_style=difficulty_color
            )
            self.console.print(clue_panel)
    
    def get_user_guess(self) -> Dict[str, any]:
        """Get user's guess input"""
        self.console.print("\n🎯 [bold]Make Your Move:[/bold]")
        self.console.print("Commands: 'guess <row> <col> <answer>', 'hint <row> <col>', 'quit', 'restart'")
        
        while True:
            user_input = Prompt.ask("Enter command").strip().lower()
            
            if user_input == 'quit':
                return {"action": "quit"}
            elif user_input == 'restart':
                return {"action": "restart"}
            elif user_input.startswith('guess '):
                parts = user_input.split(' ', 3)
                if len(parts) >= 4:
                    try:
                        row, col = int(parts[1]), int(parts[2])
                        guess = ' '.join(parts[3:])
                        return {"action": "guess", "row": row, "col": col, "guess": guess}
                    except ValueError:
                        self.console.print("[red]Invalid format. Use: guess <row> <col> <answer>[/red]")
                else:
                    self.console.print("[red]Invalid format. Use: guess <row> <col> <answer>[/red]")
            elif user_input.startswith('hint '):
                parts = user_input.split(' ')
                if len(parts) == 3:
                    try:
                        row, col = int(parts[1]), int(parts[2])
                        return {"action": "hint", "row": row, "col": col}
                    except ValueError:
                        self.console.print("[red]Invalid format. Use: hint <row> <col>[/red]")
                else:
                    self.console.print("[red]Invalid format. Use: hint <row> <col>[/red]")
            else:
                self.console.print("[red]Unknown command. Use 'guess', 'hint', 'restart', or 'quit'[/red]")
    
    def display_guess_result(self, result: Dict[str, any]):
        """Display result of a guess"""
        if result['success']:
            self.console.print(f"\n✅ [bold green]{result['message']}[/bold green]")
            if result.get('new_clues_revealed', 0) > 0:
                self.console.print(f"🎉 {result['new_clues_revealed']} new clue(s) revealed!")
        else:
            self.console.print(f"\n❌ [bold red]{result['message']}[/bold red]")
        
        input("\nPress Enter to continue...")
    
    def display_hint(self, hint_result: Dict[str, any]):
        """Display hint result"""
        if hint_result['success']:
            hint_panel = Panel(
                f"[yellow]{hint_result['hint']}[/yellow]",
                title="💡 Hint",
                border_style="yellow"
            )
            self.console.print(f"\n{hint_panel}")
            self.console.print(f"Hints used: {hint_result['hints_used']}")
        else:
            self.console.print(f"\n❌ [red]{hint_result['message']}[/red]")
        
        input("\nPress Enter to continue...")
    
    def display_game_complete(self, final_stats: Dict[str, any]):
        """Display game completion screen"""
        self.clear_screen()
        
        completion_text = """
🎉🎉🎉 CONGRATULATIONS! 🎉🎉🎉

You've completed the puzzle!
        """
        
        self.console.print(completion_text, style="bold green", justify="center")
        
        # Final stats table
        stats_table = Table(title="📊 Final Statistics", show_header=False)
        stats_table.add_column("Stat", style="bold")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("🎯 Final Score", str(final_stats.get('final_score', 0)))
        stats_table.add_row("⏱️  Completion Time", self._format_time(final_stats.get('completion_time', 0)))
        stats_table.add_row("💡 Hints Used", str(final_stats.get('hints_used', 0)))
        stats_table.add_row("❌ Wrong Guesses", str(final_stats.get('wrong_guesses', 0)))
        if 'completion_bonus' in final_stats:
            stats_table.add_row("🎁 Completion Bonus", str(final_stats['completion_bonus']))
        
        self.console.print(stats_table, justify="center")
        
        self.console.print("\n🎮 Play again? (y/n)", style="bold")
    
    def _format_time(self, seconds: float) -> str:
        """Format time in a readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def display_loading(self, message: str):
        """Display loading screen"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=message, total=None)
            return progress
    
    def display_error(self, error_message: str):
        """Display error message"""
        error_panel = Panel(
            f"[red]{error_message}[/red]",
            title="❌ Error",
            border_style="red"
        )
        self.console.print(error_panel)
        input("\nPress Enter to continue...")
    
    def confirm_quit(self) -> bool:
        """Confirm if user wants to quit"""
        return Prompt.ask("Are you sure you want to quit? (y/n)", choices=["y", "n"], default="n") == "y"