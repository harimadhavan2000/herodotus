import os
import json
from typing import Dict, List, Optional
from portkey_ai import Portkey
from dotenv import load_dotenv
from .relationships import RelationshipManager, ClueRelationship, RelationType

load_dotenv()

class LLMService:
    def __init__(self):
        api_key = os.getenv('PORTKEY_API_KEY')
        if not api_key:
            raise ValueError("PORTKEY_API_KEY not found in environment variables")
        
        self.portkey = Portkey(api_key=api_key)
    
    def generate_game_board(self, category: str, grid_size: int, difficulty_level: str = "challenging") -> Dict:
        """Generate a complete game board with sophisticated interconnected clues"""
        num_items = grid_size * grid_size
        
        # Define complexity based on difficulty level
        complexity_settings = {
            "casual": {
                "max_references_per_clue": 1,
                "multi_step_reasoning": False,
                "indirect_clues": False,
                "relationship_types": ["enables", "hints_at"]
            },
            "challenging": {
                "max_references_per_clue": 2,
                "multi_step_reasoning": True,
                "indirect_clues": True,
                "relationship_types": ["enables", "hints_at", "requires", "complements"]
            },
            "expert": {
                "max_references_per_clue": 3,
                "multi_step_reasoning": True,
                "indirect_clues": True,
                "relationship_types": ["enables", "hints_at", "requires", "complements", "contrasts"]
            },
            "mastermind": {
                "max_references_per_clue": 4,
                "multi_step_reasoning": True,
                "indirect_clues": True,
                "relationship_types": ["enables", "hints_at", "requires", "complements", "contrasts", "chains_to"]
            }
        }
        
        settings = complexity_settings.get(difficulty_level, complexity_settings["challenging"])
        
        prompt = f"""Generate a {grid_size}x{grid_size} puzzle grid for the category "{category}" with {difficulty_level} difficulty.

COMPLEXITY REQUIREMENTS FOR {difficulty_level.upper()}:
- Maximum references per clue: {settings["max_references_per_clue"]}
- Multi-step reasoning required: {settings["multi_step_reasoning"]}
- Use indirect/cryptic clues: {settings["indirect_clues"]}
- Relationship types to use: {', '.join(settings["relationship_types"])}

CORE REQUIREMENTS:
1. Create exactly {num_items} items related to "{category}"
2. Generate sophisticated interconnected clues with complex relationships
3. Include multiple relationship types (one-to-many, many-to-one, many-to-many)
4. Ensure at least 2-3 starter clues that can be solved independently
5. Create difficulty progression (1=easy starter, 2=medium, 3=hard, 4=expert)
6. Make solving one clue reveal multiple new clues through different relationship types

Return ONLY a valid JSON object with this exact structure:
{{
    "category": "{category}",
    "grid_size": {grid_size},
    "difficulty_level": "{difficulty_level}",
    "items": [
        {{
            "answer": "item_name",
            "clue": "sophisticated clue with complex references",
            "references": ["other_item_names"],
            "difficulty": 1,
            "position": {{"row": 0, "col": 0}}
        }}
    ],
    "relationships": [
        {{
            "type": "enables",
            "source_positions": [{{row: 0, col: 0}}],
            "target_positions": [{{row: 0, col: 1}}, {{row: 1, col: 0}}],
            "strength": 0.8,
            "description": "Solving this reveals two connected clues"
        }}
    ]
}}

RELATIONSHIP TYPES TO GENERATE:
- "enables": Solving source reveals targets
- "requires": Target needs sources solved first  
- "hints_at": Source provides hints about targets
- "complements": Sources work together to solve target
- "contrasts": Sources provide contrasting information
- "chains_to": Sequential solving chain

EXAMPLE COMPLEXITY FOR {difficulty_level.upper()}:
{self._get_difficulty_examples(difficulty_level)}

Make the puzzle appropriately complex for {difficulty_level} difficulty with rich interconnections.
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
            
            # Parse and validate relationships
            if 'relationships' in board_data:
                board_data['relationship_manager'] = self._create_relationship_manager(
                    board_data.get('relationships', []), 
                    difficulty_level
                )
            
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
    
    def _create_relationship_manager(self, relationships_data: List[Dict], difficulty_level: str) -> RelationshipManager:
        """Create a RelationshipManager from LLM-generated relationship data"""
        manager = RelationshipManager(difficulty_level)
        
        for rel_data in relationships_data:
            try:
                # Parse relationship type
                rel_type_str = rel_data.get('type', 'enables').lower()
                rel_type = None
                
                for rt in RelationType:
                    if rt.value == rel_type_str:
                        rel_type = rt
                        break
                
                if rel_type is None:
                    rel_type = RelationType.ENABLES  # Default fallback
                
                # Parse positions
                source_positions = []
                for pos_data in rel_data.get('source_positions', []):
                    if 'row' in pos_data and 'col' in pos_data:
                        source_positions.append((pos_data['row'], pos_data['col']))
                
                target_positions = []
                for pos_data in rel_data.get('target_positions', []):
                    if 'row' in pos_data and 'col' in pos_data:
                        target_positions.append((pos_data['row'], pos_data['col']))
                
                # Create and add relationship
                if source_positions and target_positions:
                    relationship = ClueRelationship(
                        relation_type=rel_type,
                        source_positions=source_positions,
                        target_positions=target_positions,
                        strength=float(rel_data.get('strength', 0.5)),
                        description=rel_data.get('description', f"{rel_type.value} relationship")
                    )
                    manager.add_relationship(relationship)
                    
            except Exception as e:
                print(f"Warning: Failed to parse relationship {rel_data}: {e}")
                continue
        
        return manager
    
    def _get_difficulty_examples(self, difficulty_level: str) -> str:
        """Get difficulty-specific examples for prompts"""
        examples = {
            "casual": "Direct clues with simple 1-to-1 references",
            "challenging": "Mix of direct and indirect clues with some multi-step reasoning",
            "expert": "Highly interconnected clues requiring deep logical reasoning", 
            "mastermind": "Cryptic, multilayered clues with maximum interconnectivity and mental gymnastics"
        }
        return examples.get(difficulty_level, examples["challenging"])
    
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