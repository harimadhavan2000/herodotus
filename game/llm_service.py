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
        try:
            api_key = os.getenv('PORTKEY_API_KEY')
            if not api_key:
                self.llm_available = False
                raise ValueError("PORTKEY_API_KEY not found in environment variables")
            
            self.portkey = Portkey(api_key=api_key)
            self.llm_available = True
        except Exception:
            self.llm_available = False
            raise
        
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
                print(f"❌ Generation attempt {attempt + 1} failed with error:")
                print(f"   Error type: {type(e).__name__}")
                print(f"   Error message: {str(e)}")
                if attempt == max_attempts - 1:
                    print("🔄 Final attempt failed, will use manual input fallback...")
        
        # All attempts failed, show summary and wait for user input
        print("🚨 All generation attempts exhausted.")
        print("📋 Please review the error details above.")
        input("Press Enter to continue with enhanced fallback board generation...")
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
                    {"role": "system", "content": "You are a puzzle game designer. CRITICAL: Return ONLY valid JSON. No markdown, no explanations, no extra text. All strings must be properly quoted and escaped. Ensure JSON is complete and valid."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            if not response.choices or len(response.choices) == 0:
                raise ValueError("LLM returned no choices")
            
            message = response.choices[0].message
            if not message or not hasattr(message, 'content'):
                raise ValueError("LLM response has no message content")
                
            content = message.content
            if not content:
                raise ValueError("LLM returned empty response")
            content = content.strip()
            
            # Clean up any markdown formatting
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            # Additional cleanup for malformed JSON
            content = content.strip()
            
            # Try to fix common JSON issues
            content = self._fix_json_issues(content)
            
            # Debug: Save the content that's causing issues
            if attempt > 0:  # On retry attempts, show the JSON for debugging
                print(f"🔍 DEBUG: Attempting to parse JSON content (length: {len(content)}):")
                print(f"First 200 chars: {content[:200]}...")
                print(f"Last 200 chars: ...{content[-200:]}")
            
            try:
                board_data = json.loads(content)
            except json.JSONDecodeError as json_error:
                print(f"⚠️  JSON parsing failed: {json_error}")
                print(f"🔧 Attempting JSON repair...")
                
                # Try more aggressive JSON fixing
                repaired_content = self._repair_json_aggressively(content, str(json_error))
                
                try:
                    board_data = json.loads(repaired_content)
                    print(f"✅ JSON repair successful!")
                except json.JSONDecodeError as repair_error:
                    print(f"❌ Local JSON repair failed: {repair_error}")
                    print(f"🤖 Attempting LLM-based JSON repair...")
                    
                    # Try using LLM to fix the JSON
                    if self.llm_available:
                        llm_repaired = self._llm_fix_json(content, str(json_error))
                        
                        if llm_repaired:
                            try:
                                board_data = json.loads(llm_repaired)
                                print(f"✅ LLM JSON repair successful!")
                            except json.JSONDecodeError:
                                print(f"❌ LLM JSON repair also failed, will retry generation...")
                                raise json_error  # Re-raise original error
                        else:
                            print(f"❌ LLM JSON repair returned no result, will retry generation...")
                            raise json_error  # Re-raise original error
                    else:
                        print(f"⚠️  LLM not available for JSON repair, will retry generation...")
                        # Show some debug info to help understand the issue
                        print(f"🔍 Problematic JSON around error location:")
                        lines = content.split('\n')
                        if 'line' in str(repair_error):
                            import re
                            line_match = re.search(r'line (\d+)', str(repair_error))
                            if line_match:
                                error_line_num = int(line_match.group(1)) - 1
                                start_line = max(0, error_line_num - 2)
                                end_line = min(len(lines), error_line_num + 3)
                                for i in range(start_line, end_line):
                                    marker = " >>> " if i == error_line_num else "     "
                                    print(f"{marker}Line {i+1}: {lines[i]}")
                        raise json_error  # Re-raise original error
            
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
            print(f"❌ LLM board generation failed with detailed error:")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            import traceback
            print(f"   Full traceback:")
            traceback.print_exc()
            
            print(f"\n⚠️  All LLM generation attempts failed.")
            print(f"📋 Please review the error details above.")
            input("Press Enter to continue with fallback board generation...")
            
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
    
    def _fix_json_issues(self, content: str) -> str:
        """Fix common JSON formatting issues from LLM responses"""
        import re
        
        # Remove any trailing commas before closing brackets/braces
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Fix unescaped quotes in strings (basic attempt)
        # This is tricky because we need to distinguish between JSON structure quotes and content quotes
        
        # Try to find and fix unterminated strings by ensuring they're properly closed
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check for unterminated strings (odd number of quotes on a line)
            quote_count = line.count('"')
            
            # Skip lines that are likely part of JSON structure (keys, arrays, etc.)
            if ':' not in line and '[' not in line and '{' not in line:
                continue
                
            # If we have an odd number of quotes and this looks like a value line
            if quote_count % 2 == 1 and ':' in line:
                # Try to find where the unterminated string might be
                if line.strip().endswith(',') or i == len(lines) - 1:
                    # This line should end properly, try to add missing quote
                    if line.count('"') % 2 == 1:
                        # Find the last quote and see if we need to close the string
                        last_quote_pos = line.rfind('"')
                        if last_quote_pos > 0:
                            # Check if this is a value (not a key)
                            before_last_quote = line[:last_quote_pos]
                            if ':' in before_last_quote:
                                # This appears to be an unterminated value string
                                if line.strip().endswith(','):
                                    line = line.rstrip(',').rstrip() + '\",'
                                else:
                                    line = line.rstrip() + '\"'
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _repair_json_aggressively(self, content: str, error_msg: str) -> str:
        """More aggressive JSON repair based on specific error"""
        import re
        
        # If the error mentions a specific line/column, try to fix that area
        if "line" in error_msg and "column" in error_msg:
            # Extract line and column numbers
            line_match = re.search(r'line (\d+)', error_msg)
            col_match = re.search(r'column (\d+)', error_msg)
            
            if line_match and col_match:
                error_line = int(line_match.group(1)) - 1  # 0-indexed
                error_col = int(col_match.group(1)) - 1
                
                lines = content.split('\n')
                if 0 <= error_line < len(lines):
                    problem_line = lines[error_line]
                    
                    # Common fixes for different JSON errors
                    if "Unterminated string" in error_msg:
                        # Try to add a closing quote at the error position or end of line
                        if error_col < len(problem_line):
                            # Add quote at error position
                            fixed_line = problem_line[:error_col] + '"' + problem_line[error_col:]
                        else:
                            # Add quote at end of line
                            fixed_line = problem_line.rstrip() + '"'
                        
                        # If line doesn't end with comma and it's not the last item, add comma
                        if not fixed_line.strip().endswith(',') and error_line < len(lines) - 2:
                            fixed_line = fixed_line.rstrip() + ','
                        
                        lines[error_line] = fixed_line
                    
                    elif "Expecting ',' delimiter" in error_msg:
                        # Handle missing comma errors
                        # Usually this means the previous line is missing a comma
                        if error_line > 0:
                            prev_line = lines[error_line - 1].rstrip()
                            # Add comma to previous line if it doesn't already have one
                            if not prev_line.endswith(',') and not prev_line.endswith('{') and not prev_line.endswith('['):
                                lines[error_line - 1] = prev_line + ','
                        else:
                            # If error is on current line, try to fix it
                            if not problem_line.rstrip().endswith(','):
                                lines[error_line] = problem_line.rstrip() + ','
                    
                    elif "Expecting property name enclosed in double quotes" in error_msg:
                        # Handle unquoted property names
                        # Look for unquoted keys and quote them
                        import re
                        # Pattern to find unquoted property names (word followed by colon)
                        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:'
                        def quote_match(match):
                            return f'"{match.group(1)}":'
                        
                        fixed_line = re.sub(pattern, quote_match, problem_line)
                        lines[error_line] = fixed_line
                    
                    elif "Expecting" in error_msg and ":" in error_msg:
                        # Handle missing colon errors
                        if ':' not in problem_line and '"' in problem_line:
                            # Try to add colon after the first quoted string (likely a key)
                            quote_pos = problem_line.find('"', problem_line.find('"') + 1)
                            if quote_pos != -1 and quote_pos + 1 < len(problem_line):
                                fixed_line = problem_line[:quote_pos + 1] + ': ' + problem_line[quote_pos + 1:].lstrip()
                                lines[error_line] = fixed_line
        
        # Additional common fixes
        repaired = '\n'.join(lines)
        
        # Apply global fixes that might not have been caught by line-specific fixes
        import re
        
        # Fix any remaining unquoted property names globally
        repaired = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', repaired)
        
        # Remove any invalid escape sequences
        repaired = re.sub(r'\\[^"\\\/bfnrt]', '', repaired)
        
        # Fix multiple consecutive commas
        repaired = re.sub(r',\s*,', ',', repaired)
        
        # Fix duplicate quotes around already quoted properties
        repaired = re.sub(r'""([^"]+)"":', r'"\1":', repaired)
        
        # Ensure proper closing of JSON
        if not repaired.strip().endswith('}'):
            repaired = repaired.rstrip() + '\n}'
        
        return repaired
    
    def _llm_fix_json(self, malformed_json: str, error_msg: str) -> str:
        """Use LLM to fix malformed JSON"""
        try:
            if not self.llm_available:
                return None
                
            # Truncate very long JSON to avoid token limits
            if len(malformed_json) > 3000:
                malformed_json = malformed_json[:3000] + "... [truncated]"
            
            prompt = f"""Fix this malformed JSON. The error is: {error_msg}

MALFORMED JSON:
{malformed_json}

Requirements:
- Return ONLY the fixed JSON
- No explanations or markdown formatting
- Ensure all strings are properly quoted
- Ensure all commas and colons are correctly placed
- Ensure the JSON is complete and valid

FIXED JSON:"""

            response = self.portkey.chat.completions.create(
                model="@openai-1/gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a JSON repair specialist. Return only valid, fixed JSON with no additional text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for precision
                max_tokens=2500
            )
            
            if not response.choices or len(response.choices) == 0:
                return None
                
            message = response.choices[0].message
            if not message or not hasattr(message, 'content'):
                return None
                
            fixed_content = message.content
            if not fixed_content:
                return None
                
            # Clean up the response
            fixed_content = fixed_content.strip()
            
            # Remove any markdown formatting
            if fixed_content.startswith('```json'):
                fixed_content = fixed_content[7:]
            if fixed_content.startswith('```'):
                fixed_content = fixed_content[3:]
            if fixed_content.endswith('```'):
                fixed_content = fixed_content[:-3]
                
            return fixed_content.strip()
            
        except Exception as e:
            print(f"⚠️  LLM JSON repair failed: {e}")
            return None