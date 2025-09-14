#!/usr/bin/env python3
"""Quick test to verify progressive revelation and completability fixes"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def quick_test():
    """Quick test of the completability system"""
    print("🔧 Quick Completability Test")
    print("=" * 30)
    
    try:
        from game.game_state import GameState
        
        # Test 1: Start a simple game
        print("\n1. Starting 3x3 game...")
        game_state = GameState()
        success = game_state.start_new_game("Movies", 3, "challenging")
        
        if not success:
            print("❌ Game failed to start")
            return False
        
        # Check initial state
        status = game_state.get_game_status()
        initial_clues = status.get('current_clues', [])
        print(f"✅ Game started with {len(initial_clues)} initial clues")
        
        # Test completability check
        completability = game_state.check_game_completability()
        print(f"✅ Completability check: {completability.get('completable', False)}")
        
        # Test 2: Simulate solving first clue
        if initial_clues:
            first_clue = initial_clues[0]
            cell = game_state.board.get_cell(first_clue['row'], first_clue['col'])
            if cell:
                print(f"\n2. Solving first clue: '{first_clue['clue'][:40]}...'")
                result = game_state.make_guess(cell.answer, first_clue['row'] + 1, first_clue['col'] + 1)
                
                if result['success']:
                    # Check revelation after solve
                    new_status = game_state.get_game_status()
                    new_clues = new_status.get('current_clues', [])
                    print(f"✅ After solving: {len(new_clues)} clues available")
                    print(f"✅ Progress: {new_status.get('progress', 0):.1f}%")
                    
                    # Check for stuck state
                    if game_state.board.is_stuck():
                        print("🚨 Game detected stuck state")
                    else:
                        print("✅ Game not stuck - can continue")
                else:
                    print(f"❌ Failed to solve: {result['message']}")
        
        # Test 3: Check reachability
        reachability = game_state.board.check_reachability()
        print(f"\n3. Reachability Analysis:")
        print(f"   All reachable: {reachability.get('all_reachable', False)}")
        print(f"   Reachability: {reachability.get('reachability_percentage', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 Quick test passed - completability system working!")
    else:
        print("\n❌ Quick test failed")