#!/usr/bin/env python3
"""
Quick demo of the Grid Puzzle Game functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.game_state import GameState
from game.categories import CategoryManager

def demo_game():
    """Demonstrate the game functionality"""
    print("🧩 Grid Puzzle Game - Quick Demo")
    print("=" * 40)
    
    # Initialize components
    game_state = GameState()
    category_manager = CategoryManager()
    
    # Show available categories
    print("\n📋 Available Categories:")
    categories = category_manager.get_predefined_categories()
    for i, category in enumerate(categories[:5], 1):  # Show first 5
        print(f"  {i}. {category}")
    print(f"  ... and {len(categories)-5} more")
    
    # Start a demo game
    print(f"\n🎮 Starting demo game with 'Countries and Capitals' (3x3 grid)")
    success = game_state.start_new_game("Countries and Capitals", 3)
    
    if success:
        print("✅ Game started successfully!")
        
        # Show initial game status
        status = game_state.get_game_status()
        print(f"\n📊 Game Status:")
        print(f"  Category: {status['category']}")
        print(f"  Grid Size: {status['grid_size']}x{status['grid_size']}")
        print(f"  Progress: {status['progress']:.1f}%")
        print(f"  Score: {status['score']}")
        
        # Show available clues
        clues = status['current_clues']
        print(f"\n🔍 Available Clues ({len(clues)}):")
        for clue in clues:
            print(f"  Position {clue['position']}: {clue['clue']}")
        
        # Show the grid
        if game_state.board:
            grid = game_state.board.get_grid_display()
            print(f"\n🎯 Current Grid:")
            for row in grid:
                print("  " + " | ".join(f"{cell:^8}" for cell in row))
        
        print(f"\n🎲 Demo completed! The game is ready to play.")
        print("Run 'python main.py' to play the full interactive version.")
    else:
        print("❌ Failed to start demo game")

if __name__ == "__main__":
    demo_game()