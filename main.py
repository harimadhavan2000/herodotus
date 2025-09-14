#!/usr/bin/env python3
"""
Grid Puzzle Game - Main Entry Point

A Sporcle-style grid puzzle game where players solve interconnected clues
generated using AI to reveal more clues in the grid.
"""

import os
import sys
from game.ui import GameUI
from game.game_state import GameState
from game.categories import CategoryManager

class GridPuzzleGame:
    def __init__(self):
        self.ui = GameUI()
        self.game_state = GameState()
        self.category_manager = CategoryManager()
        self.running = True
    
    def run(self):
        """Main game loop"""
        try:
            self.ui.display_welcome()
            
            while self.running:
                if not self.game_state.game_active:
                    # Start new game
                    if not self._setup_new_game():
                        break
                
                self._game_loop()
                
                if self.game_state.game_active:
                    continue
                
                # Game ended - ask if player wants to play again
                if not self._ask_play_again():
                    break
            
        except KeyboardInterrupt:
            self.ui.console.print("\n\n👋 Thanks for playing! Goodbye!")
        except Exception as e:
            self.ui.display_error(f"An unexpected error occurred: {str(e)}")
            self.ui.console.print("The game will now exit.")
    
    def _setup_new_game(self) -> bool:
        """Set up a new game - returns False if user wants to quit"""
        try:
            # Category selection
            categories = self.category_manager.get_predefined_categories()
            selected_category = self.ui.display_category_selection(categories)
            
            if not selected_category:
                return False
            
            # Grid size selection
            grid_size = self.ui.select_grid_size()
            
            # Clue difficulty selection
            clue_difficulty = self.ui.select_clue_difficulty()
            
            # Show loading screen while generating board
            self.ui.console.print(f"\n🤖 Generating puzzle for '{selected_category}' at {clue_difficulty} difficulty...")
            
            # Start the game
            success = self.game_state.start_new_game(selected_category, grid_size, clue_difficulty)
            
            if not success:
                self.ui.display_error("Failed to generate game board. Please try again.")
                return True  # Try again
            
            self.ui.console.print("✅ Puzzle generated successfully!")
            return True
            
        except Exception as e:
            self.ui.display_error(f"Error setting up game: {str(e)}")
            return True
    
    def _game_loop(self):
        """Main gameplay loop"""
        while self.game_state.game_active and self.running:
            try:
                # Get current game status
                game_status = self.game_state.get_game_status()
                
                # Add board display to status
                if self.game_state.board:
                    game_status['board_display'] = self.game_state.board.get_grid_display()
                
                # Display game state
                self.ui.display_game_board(game_status)
                
                # Display available clues
                current_clues = game_status.get('current_clues', [])
                self.ui.display_current_clues(current_clues)
                
                # Get user input
                user_action = self.ui.get_user_guess()
                
                # Process user action
                if user_action['action'] == 'quit':
                    if self.ui.confirm_quit():
                        self.game_state.quit_game()
                        self.running = False
                    continue
                
                elif user_action['action'] == 'restart':
                    self.game_state.restart_game()
                    continue
                
                elif user_action['action'] == 'guess':
                    result = self.game_state.make_guess(
                        user_action['guess'],
                        user_action['row'],
                        user_action['col']
                    )
                    self.ui.display_guess_result(result)
                    
                    # Check if game is complete
                    if result.get('game_complete', False):
                        self.ui.display_game_complete(result)
                        break
                
                elif user_action['action'] == 'hint':
                    hint_result = self.game_state.get_hint(
                        user_action['row'],
                        user_action['col']
                    )
                    self.ui.display_hint(hint_result)
                
            except KeyboardInterrupt:
                if self.ui.confirm_quit():
                    self.game_state.quit_game()
                    self.running = False
            except Exception as e:
                self.ui.display_error(f"Error during gameplay: {str(e)}")
                input("Press Enter to continue...")
    
    def _ask_play_again(self) -> bool:
        """Ask if player wants to play again"""
        try:
            from rich.prompt import Prompt
            response = Prompt.ask("🎮 Play again? (y/n)", choices=["y", "n"], default="n")
            return response.lower() == 'y'
        except Exception:
            return False

def check_environment():
    """Check if all required environment variables and dependencies are available"""
    # Check for API key
    if not os.getenv('PORTKEY_API_KEY'):
        print("⚠️  Warning: PORTKEY_API_KEY not found in environment variables.")
        print("The game will use fallback content instead of AI-generated content.")
        print("To enable AI features:")
        print("1. Copy .env.example to .env")
        print("2. Add your Portkey API key to .env")
        print("3. Run: export PORTKEY_API_KEY=your_key (Linux/Mac) or set PORTKEY_API_KEY=your_key (Windows)")
        print()
        
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            return False
    
    return True

def main():
    """Main entry point"""
    print("🧩 Grid Puzzle Game")
    print("===================")
    
    # Check environment
    if not check_environment():
        print("Exiting...")
        return
    
    # Check if we're in the right directory
    if not os.path.exists('game'):
        print("Error: Game files not found. Make sure you're running from the correct directory.")
        return
    
    # Start the game
    try:
        game = GridPuzzleGame()
        game.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        print("Please check your installation and try again.")

if __name__ == "__main__":
    main()