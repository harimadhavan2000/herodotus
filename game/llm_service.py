import os
import json
from typing import Dict, List, Optional
from portkey_ai import Portkey
from dotenv import load_dotenv
from .relationships import RelationshipManager, ClueRelationship, RelationType
from .board_validator import BoardQualityValidator

load_dotenv()

class LLMService:
    def __init__(self):
        api_key = os.getenv('PORTKEY_API_KEY')
        if not api_key:
            raise ValueError("PORTKEY_API_KEY not found in environment variables")
        
        self.portkey = Portkey(api_key=api_key)
        self.validator = BoardQualityValidator()
    
    def generate_game_board(self, category: str, grid_size: int, difficulty_level: str = "challenging", enable_validation: bool = True) -> Dict:
        """Generate a complete game board with sophisticated interconnected clues"""
        # More attempts for harder difficulties to avoid fallback
        max_attempts = {
            "casual": 3,
            "challenging": 4,
            "expert": 5,
            "mastermind": 5
        }.get(difficulty_level, 4)
        
        for attempt in range(max_attempts):
            try:
                print(f"🤖 Generating board (attempt {attempt + 1}/{max_attempts})...")
                board_data = self._generate_single_board(category, grid_size, difficulty_level, attempt, max_attempts)
                
                if not enable_validation:
                    return board_data
                
                # Validate board quality
                is_valid, issues = self.validator.validate_board_quality(board_data, enable_llm_validation=True)
                
                if is_valid:
                    print("✅ Board passed quality validation!")
                    return board_data
                else:
                    print(f"❌ Quality issues found (attempt {attempt + 1}):")
                    for issue in issues[:3]:  # Show first 3 issues
                        print(f"   • {issue}")
                    
                    if attempt < max_attempts - 1:
                        print("🔄 Regenerating with improvements...")
                    else:
                        print("⚠️  Max attempts reached, using enhanced fallback...")
                        
            except Exception as e:
                print(f"❌ Generation attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    print("🔄 Using fallback generation...")
        
        # All attempts failed, use enhanced fallback
        return self._enhanced_fallback_board(category, grid_size, difficulty_level)
    
    def _generate_single_board(self, category: str, grid_size: int, difficulty_level: str, attempt: int = 0, max_attempts: int = 4) -> Dict:
        """Generate a single board attempt"""
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
        
        # Increase complexity on later attempts to avoid fallback
        if attempt >= 2:  # From 3rd attempt onwards, make it more aggressive
            settings = dict(settings)  # Copy to avoid modifying original
            if difficulty_level in ["expert", "mastermind"]:
                settings["max_references_per_clue"] = min(settings["max_references_per_clue"] + 1, 5)
                settings["relationship_types"].extend(["chains_to", "contrasts"])
                settings["relationship_types"] = list(set(settings["relationship_types"]))  # Remove duplicates
        
        # Add quality improvement feedback based on attempt
        quality_reminder = ""
        if attempt > 0:
            final_attempt_warning = ""
            if attempt >= max_attempts - 2:
                final_attempt_warning = "🚨 FINAL ATTEMPT - Generate high-quality clues to avoid simple fallback!"
            
            quality_reminder = f"""

⚠️  CRITICAL QUALITY IMPROVEMENT (Attempt {attempt + 1}):
The previous generation had quality issues. This time:
❌ ABSOLUTELY NO placeholder clues like "This is item 1 in the {category} category"
❌ NEVER use "Item 1", "Item 2", "Entry number X", etc.
✅ EVERY clue must contain REAL, SPECIFIC information about the answer
✅ Starter clues must be solvable with general knowledge
✅ Use actual facts, descriptions, characteristics, or relationships

{final_attempt_warning}"""

        # Add attempt-specific guidance
        attempt_guidance = ""
        if attempt >= 1:
            attempt_guidance = f"""
🔥 HIGH PRIORITY - Attempt {attempt + 1}/{max_attempts}:
This is a retry after quality issues. Focus on {difficulty_level.upper()} difficulty with sophisticated clues!
"""

        prompt = f"""Generate a {grid_size}x{grid_size} puzzle grid for the category "{category}" with {difficulty_level} difficulty.{attempt_guidance}

🚫 ABSOLUTE QUALITY RULES - NEVER VIOLATE:
❌ NO placeholder clues: "This is item X", "Item number Y", "The Xth item"
❌ NO meta-grid references: "position", "row", "column", "grid location" 
❌ NO meaningless descriptions: "something in this category", "an item here"
✅ ONLY specific, factual, solvable clues based on real knowledge

COMPLEXITY REQUIREMENTS FOR {difficulty_level.upper()}:
- Maximum references per clue: {settings["max_references_per_clue"]}
- Multi-step reasoning required: {settings["multi_step_reasoning"]}
- Use indirect/cryptic clues: {settings["indirect_clues"]}
- Relationship types to use: {', '.join(settings["relationship_types"])}{quality_reminder}

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
            return self._enhanced_fallback_board(category, grid_size, difficulty_level)
    
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
    
    def _enhanced_fallback_board(self, category: str, grid_size: int, difficulty_level: str) -> Dict:
        """Enhanced fallback board generation with meaningful clues"""
        items = []
        num_items = grid_size * grid_size
        
        # Check if it's a custom category that needs special handling
        is_custom = self.validator.is_custom_category_likely(category)
        
        if is_custom:
            # For custom categories, create plausible generic clues
            for i in range(num_items):
                row = i // grid_size
                col = i % grid_size
                
                # Create meaningful fallback clues instead of "Item 1"
                clue_templates = [
                    f"A well-known example from {category}",
                    f"Popular item in the {category} category",
                    f"Classic {category.lower().rstrip('s')} that many would recognize",
                    f"Famous {category.lower().rstrip('s')} worth knowing",
                    f"Notable entry in {category}",
                    f"Recognized {category.lower().rstrip('s')} from this category",
                    f"Important {category.lower().rstrip('s')} in this field",
                    f"Memorable {category.lower().rstrip('s')} that stands out",
                    f"Significant {category.lower().rstrip('s')} in {category.lower()}"
                ]
                
                clue = clue_templates[i % len(clue_templates)]
                
                items.append({
                    "answer": f"Example {i+1}",
                    "clue": clue,
                    "references": [],
                    "difficulty": 1 if i < 3 else 2,  # First few are easier
                    "position": {"row": row, "col": col}
                })
        else:
            # For known categories, use category-specific fallbacks
            category_fallbacks = self._get_category_fallbacks(category, num_items)
            
            for i, fallback_item in enumerate(category_fallbacks):
                row = i // grid_size
                col = i % grid_size
                
                items.append({
                    "answer": fallback_item["answer"],
                    "clue": fallback_item["clue"],
                    "references": fallback_item.get("references", []),
                    "difficulty": fallback_item.get("difficulty", 1),
                    "position": {"row": row, "col": col}
                })
        
        print("✅ Enhanced fallback board generated with meaningful clues!")
        return {
            "category": category,
            "grid_size": grid_size,
            "difficulty_level": difficulty_level,
            "items": items
        }
    
    def _get_category_fallbacks(self, category: str, num_items: int) -> List[Dict]:
        """Get meaningful fallback items for known categories"""
        category_lower = category.lower()
        
        fallbacks = {
            "countries": [
                {"answer": "France", "clue": "European country famous for the Eiffel Tower"},
                {"answer": "Japan", "clue": "Island nation known as the Land of the Rising Sun"},
                {"answer": "Brazil", "clue": "Largest country in South America"},
                {"answer": "Australia", "clue": "Island continent down under"},
                {"answer": "Egypt", "clue": "North African country home to the pyramids"},
                {"answer": "Canada", "clue": "North American country known for maple syrup"},
                {"answer": "India", "clue": "South Asian country with the Taj Mahal"},
                {"answer": "Russia", "clue": "Largest country by land area"},
                {"answer": "Germany", "clue": "European country known for Oktoberfest"}
            ],
            "movies": [
                {"answer": "Titanic", "clue": "1997 disaster romance film about a doomed ship"},
                {"answer": "Avatar", "clue": "James Cameron's blue alien world epic"},
                {"answer": "Star Wars", "clue": "Space saga with Jedi and the Force"},
                {"answer": "Jaws", "clue": "Spielberg's thriller about a great white shark"},
                {"answer": "E.T.", "clue": "Spielberg film about a friendly alien"},
                {"answer": "Rocky", "clue": "Boxing underdog story set in Philadelphia"},
                {"answer": "Casablanca", "clue": "Classic 1942 film set in wartime Morocco"},
                {"answer": "The Godfather", "clue": "Coppola's mafia family saga"},
                {"answer": "Psycho", "clue": "Hitchcock's motel horror masterpiece"}
            ],
            "animals": [
                {"answer": "Lion", "clue": "King of the jungle with a mighty roar"},
                {"answer": "Elephant", "clue": "Largest land mammal with a trunk"},
                {"answer": "Penguin", "clue": "Flightless bird that waddles on ice"},
                {"answer": "Dolphin", "clue": "Intelligent marine mammal that clicks"},
                {"answer": "Tiger", "clue": "Striped big cat from Asia"},
                {"answer": "Giraffe", "clue": "Tallest animal with a long neck"},
                {"answer": "Whale", "clue": "Largest animal on Earth, lives in oceans"},
                {"answer": "Eagle", "clue": "Majestic bird of prey with sharp talons"},
                {"answer": "Panda", "clue": "Black and white bear that eats bamboo"}
            ]
        }
        
        # Find matching fallback category
        for key, items in fallbacks.items():
            if key in category_lower or category_lower in key:
                # Extend list if needed
                while len(items) < num_items:
                    items.extend(items[:min(len(items), num_items - len(items))])
                return items[:num_items]
        
        # Generic fallback if no specific category found
        generic_items = []
        for i in range(num_items):
            generic_items.append({
                "answer": f"Item {i+1}",
                "clue": f"A notable example from {category}",
                "difficulty": 1
            })
        
        return generic_items
    
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