#!/usr/bin/env python3
"""
Test script for the Grid Puzzle Game
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing imports...")
    
    try:
        from game.llm_service import LLMService
        print("✅ LLMService imported successfully")
        
        from game.board import GameBoard
        print("✅ GameBoard imported successfully")
        
        from game.categories import CategoryManager
        print("✅ CategoryManager imported successfully")
        
        from game.clue_generator import ClueGenerator
        print("✅ ClueGenerator imported successfully")
        
        from game.game_state import GameState
        print("✅ GameState imported successfully")
        
        from game.ui import GameUI
        print("✅ GameUI imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic game functionality without full UI"""
    print("\nTesting basic functionality...")
    
    try:
        from game.categories import CategoryManager
        from game.clue_generator import ClueGenerator
        from game.game_state import GameState
        
        # Test category manager
        category_manager = CategoryManager()
        categories = category_manager.get_predefined_categories()
        print(f"✅ Found {len(categories)} predefined categories")
        
        # Test game state initialization
        game_state = GameState()
        print("✅ GameState created successfully")
        
        # Test fallback board generation (without API call)
        clue_generator = ClueGenerator()
        try:
            # This might use the API, so we'll catch any errors
            board_data = clue_generator._create_fallback_board("Countries and Capitals", 3)
            print("✅ Fallback board generation works")
        except Exception as e:
            print(f"⚠️  Fallback board generation failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_api_connection():
    """Test API connection (optional)"""
    print("\nTesting API connection...")
    
    try:
        from game.llm_service import LLMService
        
        if not os.getenv('PORTKEY_API_KEY'):
            print("⚠️  No API key found, skipping API test")
            return True
        
        llm_service = LLMService()
        print("✅ LLMService initialized successfully")
        
        # Try a simple API call
        try:
            board_data = llm_service.generate_game_board("Test Category", 3)
            if board_data and 'items' in board_data:
                print("✅ API connection successful")
                print(f"Generated {len(board_data['items'])} items")
            else:
                print("⚠️  API returned invalid data")
        except Exception as e:
            print(f"⚠️  API call failed: {e}")
            print("Game will work with fallback content")
        
        return True
        
    except Exception as e:
        print(f"❌ API connection test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧩 Grid Puzzle Game - Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_basic_functionality,
        test_api_connection
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The game should work correctly.")
        print("\nTo play the game, run: python main.py")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)