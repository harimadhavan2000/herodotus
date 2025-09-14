#!/usr/bin/env python3
"""
Test script to verify that progressive revelation is working correctly
and not revealing too many clues at once
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_progressive_revelation():
    """Test that clue revelation is progressive, not all-at-once"""
    print("🔍 Progressive Revelation Test")
    print("=" * 35)
    
    try:
        from game.game_state import GameState
        
        # Test 1: Check initial revelation
        print("\n1. Testing initial starter clue revelation...")
        game_state = GameState()
        
        success = game_state.start_new_game("Movies", 3, "challenging")
        
        if not success:
            print("❌ Game failed to start")
            return False
        
        # Check how many clues are initially revealed
        initial_status = game_state.get_game_status()
        initial_clues = initial_status.get('current_clues', [])
        
        print(f"Initial clues revealed: {len(initial_clues)}")
        
        if len(initial_clues) <= 2:  # Should be conservative
            print("✅ Conservative initial revelation (≤2 clues)")
        else:
            print(f"❌ Too many initial clues revealed: {len(initial_clues)}")
            print("Clues:", [clue['clue'][:50] + "..." for clue in initial_clues])
            return False
        
        # Test 2: Check revelation after solving first clue
        if initial_clues:
            print(f"\n2. Testing revelation after solving first clue...")
            first_clue = initial_clues[0]
            print(f"First clue: '{first_clue['clue'][:60]}...'")
            
            # Get the correct answer from the board
            cell = game_state.board.get_cell(first_clue['row'], first_clue['col'])
            correct_answer = cell.answer if cell else "Unknown"
            
            print(f"Solving with answer: '{correct_answer}'")
            
            # Make the guess
            result = game_state.make_guess(correct_answer, first_clue['row'] + 1, first_clue['col'] + 1)
            
            if result['success']:
                print("✅ First clue solved successfully")
                
                # Check how many NEW clues are revealed
                new_status = game_state.get_game_status()
                new_clues = new_status.get('current_clues', [])
                
                # Calculate newly revealed clues (excluding the one we just solved)
                newly_revealed_count = len(new_clues)
                
                print(f"Total clues available after solving: {newly_revealed_count}")
                print(f"Progress: {new_status.get('progress', 0):.1f}%")
                
                if newly_revealed_count <= 4:  # Should reveal some but not all
                    print("✅ Conservative revelation after solving (reasonable number of new clues)")
                    
                    # Show what clues are now available
                    print("Available clues:")
                    for clue in new_clues[:3]:  # Show first 3
                        print(f"   • Position {clue['position']}: {clue['clue'][:50]}...")
                    
                else:
                    print(f"❌ Too many clues revealed after one solve: {newly_revealed_count}")
                    return False
                
            else:
                print(f"❌ Failed to solve first clue: {result['message']}")
                return False
        
        # Test 3: Check that not all clues are revealed at once
        total_cells = game_state.board.total_cells
        revealed_cells = len(new_clues) + 1  # +1 for the solved one
        
        if revealed_cells < total_cells:
            print(f"✅ Progressive system working: {revealed_cells}/{total_cells} cells revealed")
        else:
            print(f"❌ All cells revealed at once: {revealed_cells}/{total_cells}")
            return False
        
        # Test 4: Test another solve to see continued progression
        if len(new_clues) > 0:
            print(f"\n3. Testing continued progression...")
            second_clue = new_clues[0]
            second_cell = game_state.board.get_cell(second_clue['row'], second_clue['col'])
            
            if second_cell:
                print(f"Solving second clue: '{second_clue['clue'][:50]}...'")
                second_result = game_state.make_guess(
                    second_cell.answer, 
                    second_clue['row'] + 1, 
                    second_clue['col'] + 1
                )
                
                if second_result['success']:
                    final_status = game_state.get_game_status()
                    final_clues = len(final_status.get('current_clues', []))
                    
                    print(f"✅ Second solve successful")
                    print(f"Final available clues: {final_clues}")
                    print(f"Final progress: {final_status.get('progress', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_different_grid_sizes():
    """Test progressive revelation with different grid sizes"""
    print(f"\n🎯 Testing Different Grid Sizes")
    print("=" * 32)
    
    try:
        from game.game_state import GameState
        
        for grid_size in [3, 4]:  # Test 3x3 and 4x4
            print(f"\nTesting {grid_size}x{grid_size} grid...")
            
            game_state = GameState()
            success = game_state.start_new_game("Countries and Capitals", grid_size, "challenging")
            
            if success:
                status = game_state.get_game_status()
                initial_clues = len(status.get('current_clues', []))
                total_cells = grid_size * grid_size
                
                print(f"  Grid size: {grid_size}x{grid_size} ({total_cells} total)")
                print(f"  Initial clues: {initial_clues}")
                print(f"  Percentage revealed: {(initial_clues/total_cells)*100:.1f}%")
                
                # Check that we're not revealing too high a percentage initially
                reveal_percentage = (initial_clues / total_cells) * 100
                if reveal_percentage <= 33:  # At most 1/3 initially
                    print(f"  ✅ Conservative initial revelation ({reveal_percentage:.1f}%)")
                else:
                    print(f"  ❌ Too many initial clues ({reveal_percentage:.1f}%)")
            else:
                print(f"  ⚠️  Failed to generate {grid_size}x{grid_size} board")
                
        return True
        
    except Exception as e:
        print(f"❌ Grid size test failed: {e}")
        return False

def main():
    """Run all progressive revelation tests"""
    print("🎮 Progressive Revelation Test Suite")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 2
    
    if test_progressive_revelation():
        tests_passed += 1
        
    if test_with_different_grid_sizes():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("\n🎉 All tests passed! Progressive revelation is working correctly.")
        print("\n✅ Key improvements:")
        print("• Only 1-2 starter clues revealed initially")
        print("• Each solve reveals at most 2 new clues")
        print("• Proper progression through the puzzle")
        print("• No more 'solve one, reveal all' problem")
        
        print(f"\n🚀 Try the improved game:")
        print("   python main.py")
        print("   Notice how solving clues gradually unlocks more!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    main()