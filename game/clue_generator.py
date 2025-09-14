import json
import os
from typing import Dict, List
from .llm_service import LLMService
from .categories import CategoryManager

class ClueGenerator:
    def __init__(self):
        self.llm_service = LLMService()
        self.category_manager = CategoryManager()
        self.fallback_data = self._load_fallback_data()
    
    def _load_fallback_data(self) -> Dict:
        """Load fallback data from JSON file"""
        try:
            fallback_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'categories.json')
            with open(fallback_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def generate_board(self, category: str, grid_size: int = 3, difficulty_level: str = "challenging") -> Dict:
        """Generate a complete game board with sophisticated interconnected clues"""
        try:
            # Try LLM generation first
            print(f"🤖 Generating {grid_size}x{grid_size} board for '{category}' at {difficulty_level} difficulty...")
            board_data = self.llm_service.generate_game_board(category, grid_size, difficulty_level)
            
            # Validate the generated board
            if self._validate_board(board_data, grid_size):
                print("✅ Board generated successfully!")
                return board_data
            else:
                print("⚠️  LLM generated invalid board, using fallback...")
                return self._create_fallback_board(category, grid_size)
                
        except Exception as e:
            print(f"❌ Error generating board: {e}")
            print("Using fallback board generation...")
            return self._create_fallback_board(category, grid_size)
    
    def _validate_board(self, board_data: Dict, expected_size: int) -> bool:
        """Validate that the generated board is properly structured"""
        if not isinstance(board_data, dict):
            return False
        
        if 'items' not in board_data or not isinstance(board_data['items'], list):
            return False
        
        expected_items = expected_size * expected_size
        if len(board_data['items']) != expected_items:
            return False
        
        # Check that each item has required fields
        required_fields = ['answer', 'clue', 'position']
        for item in board_data['items']:
            if not all(field in item for field in required_fields):
                return False
            
            if not isinstance(item['position'], dict):
                return False
            
            if 'row' not in item['position'] or 'col' not in item['position']:
                return False
        
        return True
    
    def _create_fallback_board(self, category: str, grid_size: int) -> Dict:
        """Create a fallback board when LLM generation fails"""
        # Check if we have fallback data for this category
        fallback_items = self.fallback_data.get(category, {}).get('fallback_items', [])
        
        if not fallback_items:
            # Create generic items if no specific fallback exists
            fallback_items = self._create_generic_items(category, grid_size * grid_size)
        
        # Take only what we need for the grid
        num_items = grid_size * grid_size
        items = fallback_items[:num_items]
        
        # If we don't have enough items, create more generic ones
        while len(items) < num_items:
            items.append({
                "answer": f"{category} Item {len(items) + 1}",
                "clue": f"Item {len(items) + 1} in the {category} category"
            })
        
        # Add positions and create interconnections
        board_items = []
        for i, item in enumerate(items):
            row = i // grid_size
            col = i % grid_size
            
            # Add basic interconnections for fallback
            references = []
            if i > 0:  # Reference previous item
                references.append(items[i-1]['answer'])
            
            board_items.append({
                "answer": item['answer'],
                "clue": item['clue'],
                "references": references,
                "difficulty": min(3, (i // 3) + 1),  # Progressive difficulty
                "position": {"row": row, "col": col}
            })
        
        # Make the first item a starter (no references)
        if board_items:
            board_items[0]['references'] = []
            board_items[0]['difficulty'] = 1
        
        return {
            "category": category,
            "grid_size": grid_size,
            "items": board_items
        }
    
    def _create_generic_items(self, category: str, num_items: int) -> List[Dict]:
        """Create generic items for unknown categories"""
        items = []
        for i in range(num_items):
            items.append({
                "answer": f"{category} Item {i + 1}",
                "clue": f"This is the {self._ordinal(i + 1)} item in the {category} category"
            })
        return items
    
    def _ordinal(self, n: int) -> str:
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        return f"{n}{suffix}"
    
    def get_hint(self, answer: str, context: str = "") -> str:
        """Generate a hint for a specific answer"""
        try:
            return self.llm_service.get_hint(answer, context)
        except Exception:
            return f"Think about what relates to '{context}' and this category."
    
    def enhance_clues_with_context(self, board_data: Dict, solved_items: List[str]) -> Dict:
        """Enhance clues with context from solved items"""
        if not solved_items:
            return board_data
        
        try:
            # Use LLM to enhance clues based on what's already solved
            enhanced_board = board_data.copy()
            context = f"Already solved: {', '.join(solved_items)}"
            
            for item in enhanced_board['items']:
                if not any(solved in item['answer'] for solved in solved_items):
                    # Generate contextual hint
                    enhanced_clue = self.get_hint(item['answer'], context)
                    if enhanced_clue != item['clue']:
                        item['enhanced_clue'] = enhanced_clue
            
            return enhanced_board
            
        except Exception:
            return board_data