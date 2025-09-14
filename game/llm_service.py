import os
import json
from typing import Dict, List, Optional
from portkey_ai import Portkey
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        api_key = os.getenv('PORTKEY_API_KEY')
        if not api_key:
            raise ValueError("PORTKEY_API_KEY not found in environment variables")
        
        self.portkey = Portkey(api_key=api_key)
    
    def generate_game_board(self, category: str, grid_size: int) -> Dict:
        """Generate a complete game board with interconnected clues"""
        num_items = grid_size * grid_size
        
        prompt = f"""Generate a {grid_size}x{grid_size} puzzle grid for the category "{category}".
        
Requirements:
1. Create exactly {num_items} items related to "{category}"
2. Each item needs a clue that references at least one other item in the grid
3. Ensure at least one clue can be solved without knowing other answers (starter clue)
4. Make clues progressively reveal information about other items
5. Vary difficulty levels (1=easy, 2=medium, 3=hard)

Return ONLY a valid JSON object with this exact structure:
{{
    "category": "{category}",
    "grid_size": {grid_size},
    "items": [
        {{
            "answer": "item_name",
            "clue": "descriptive clue that may reference other items",
            "references": ["other_item_names"],
            "difficulty": 1,
            "position": {{"row": 0, "col": 0}}
        }}
    ]
}}

Make sure clues are interconnected and solvable. Example references:
- "Capital of the country that borders [other answer]"
- "Same continent as [other answer]"
- "Director of the movie starring [other answer]"
"""

        try:
            response = self.portkey.chat.completions.create(
                model="@openai-1/gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a puzzle game designer. Return only valid JSON without any additional text or formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up any markdown formatting
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            board_data = json.loads(content)
            
            # Assign positions if not provided
            self._assign_positions(board_data, grid_size)
            
            return board_data
            
        except Exception as e:
            print(f"Error generating board: {e}")
            return self._fallback_board(category, grid_size)
    
    def _assign_positions(self, board_data: Dict, grid_size: int):
        """Assign grid positions to items if not already assigned"""
        for i, item in enumerate(board_data.get('items', [])):
            if 'position' not in item:
                row = i // grid_size
                col = i % grid_size
                item['position'] = {'row': row, 'col': col}
    
    def _fallback_board(self, category: str, grid_size: int) -> Dict:
        """Fallback board generation when LLM fails"""
        items = []
        num_items = grid_size * grid_size
        
        for i in range(num_items):
            row = i // grid_size
            col = i % grid_size
            items.append({
                "answer": f"{category} Item {i+1}",
                "clue": f"This is item {i+1} in the {category} category",
                "references": [],
                "difficulty": 1,
                "position": {"row": row, "col": col}
            })
        
        return {
            "category": category,
            "grid_size": grid_size,
            "items": items
        }
    
    def get_hint(self, item_name: str, context: str) -> str:
        """Generate a hint for a specific item"""
        prompt = f"""Give a helpful hint for the answer "{item_name}" in the context of: {context}
        
        The hint should:
        - Not directly give away the answer
        - Provide useful information that narrows down possibilities
        - Be 1-2 sentences maximum
        
        Return only the hint text."""
        
        try:
            response = self.portkey.chat.completions.create(
                model="@openai-1/gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful puzzle hint generator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Hint unavailable (Error: {str(e)})"