import re
import json
from typing import Dict, List, Tuple, Optional
from portkey_ai import Portkey
import os
from dotenv import load_dotenv

load_dotenv()

class BoardQualityValidator:
    """Validates board quality to ensure clues are solvable and meaningful"""
    
    def __init__(self):
        try:
            api_key = os.getenv('PORTKEY_API_KEY')
            if api_key:
                self.portkey = Portkey(api_key=api_key)
                self.llm_available = True
            else:
                self.llm_available = False
        except Exception:
            self.llm_available = False
    
    # Patterns for meaningless placeholder clues
    MEANINGLESS_PATTERNS = [
        r"this is item \d+",
        r"item \d+ in the .+ category",
        r".+ item \d+",
        r"the \d+(?:st|nd|rd|th) item",
        r"entry number \d+",
        r"answer \d+",
        r"clue \d+",
        r"position \(\d+,\d+\)",
        r"this is the .+ item",
        r"number \d+ in our list"
    ]
    
    # Additional meaningless phrases
    MEANINGLESS_PHRASES = [
        "in our puzzle",
        "in this grid",
        "in the current board",
        "according to our list",
        "as per our arrangement",
        "in this puzzle game"
    ]
    
    def validate_board_quality(self, board_data: Dict, enable_llm_validation: bool = True) -> Tuple[bool, List[str]]:
        """
        Validate board quality focusing on meaningful, solvable clues
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_issues)
        """
        issues = []
        
        if 'items' not in board_data:
            issues.append("Board has no items")
            return False, issues
        
        # Check each item for quality issues
        for i, item in enumerate(board_data['items']):
            item_issues = self._validate_single_item(item, i)
            issues.extend(item_issues)
        
        # Check starter clues specifically
        starter_issues = self._validate_starter_clues(board_data)
        issues.extend(starter_issues)
        
        # Use LLM validation if available and enabled
        if enable_llm_validation and self.llm_available and not issues:
            llm_valid, llm_issues = self._llm_validate_board(board_data)
            if not llm_valid:
                issues.extend(llm_issues)
        
        return len(issues) == 0, issues
    
    def _validate_single_item(self, item: Dict, index: int) -> List[str]:
        """Validate a single item for quality issues"""
        issues = []
        
        if 'clue' not in item or 'answer' not in item:
            issues.append(f"Item {index} missing clue or answer")
            return issues
        
        clue = item['clue'].lower()
        answer = item.get('answer', '')
        
        # Check for meaningless patterns
        for pattern in self.MEANINGLESS_PATTERNS:
            if re.search(pattern, clue, re.IGNORECASE):
                issues.append(f"Item {index} has meaningless placeholder clue: '{item['clue']}'")
                break
        
        # Check for meaningless phrases
        for phrase in self.MEANINGLESS_PHRASES:
            if phrase.lower() in clue:
                issues.append(f"Item {index} contains meta-puzzle reference: '{phrase}'")
                break
        
        # Check if clue is too short/generic
        if len(clue.split()) < 3:
            issues.append(f"Item {index} has overly short clue: '{item['clue']}'")
        
        # Check if clue just repeats the answer
        if answer.lower() in clue and len(clue.split()) < 5:
            issues.append(f"Item {index} clue is just the answer: '{item['clue']}'")
        
        return issues
    
    def _validate_starter_clues(self, board_data: Dict) -> List[str]:
        """Validate that starter clues are independently solvable"""
        issues = []
        
        # Find potential starter clues (difficulty 1, minimal references)
        starter_candidates = []
        
        for item in board_data.get('items', []):
            difficulty = item.get('difficulty', 1)
            references = item.get('references', [])
            
            if difficulty == 1 and len(references) == 0:
                starter_candidates.append(item)
        
        if not starter_candidates:
            # If no clear starters, check low-difficulty items
            for item in board_data.get('items', []):
                if item.get('difficulty', 1) <= 2:
                    starter_candidates.append(item)
        
        if not starter_candidates:
            issues.append("No identifiable starter clues found")
            return issues
        
        # Validate starter clues have meaningful content
        for item in starter_candidates[:3]:  # Check first few starters
            clue = item['clue'].lower()
            
            # Starters should be independently solvable
            if any(pattern in clue for pattern in ["solve first", "need other answers", "requires"]):
                issues.append(f"Starter clue has dependencies: '{item['clue']}'")
            
            # Check for generic content
            generic_words = ["something", "anything", "item", "thing", "element"]
            word_count = len(clue.split())
            generic_count = sum(1 for word in generic_words if word in clue)
            
            if generic_count > 1 or (generic_count == 1 and word_count < 6):
                issues.append(f"Starter clue too generic: '{item['clue']}'")
        
        return issues
    
    def _llm_validate_board(self, board_data: Dict) -> Tuple[bool, List[str]]:
        """Use LLM to validate board quality"""
        try:
            # Prepare clues for validation
            clues_text = "\n".join([
                f"{i+1}. Answer: {item['answer']} | Clue: {item['clue']}"
                for i, item in enumerate(board_data.get('items', [])[:5])  # Check first 5
            ])
            
            prompt = f"""Evaluate these puzzle clues for quality issues. Focus on whether they are SOLVABLE and MEANINGFUL.

CLUES TO CHECK:
{clues_text}

CRITICAL ISSUES TO FLAG:
❌ Placeholder clues like "This is item 1 in the [category] category"
❌ Clues that give no actual information about the answer
❌ Generic descriptions with no specific details
❌ Clues that require seeing the grid structure
❌ Starter clues that can't be solved independently

GOOD EXAMPLES:
✅ "Rajinikanth's robot movie from 2010" (specific, solvable)
✅ "Capital of France, home to the Eiffel Tower" (clear, informative)
✅ "Physicist who developed the theory of relativity" (factual, solvable)

Return ONLY a JSON object:
{{
    "is_valid": boolean,
    "issues": ["list of specific problems found"],
    "problematic_clues": [1, 2, 3]
}}

A clue MUST contain actual information that helps solve the answer!"""

            response = self.portkey.chat.completions.create(
                model="@openai-1/gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a puzzle quality validator. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up JSON formatting
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            result = json.loads(content)
            
            is_valid = result.get('is_valid', False)
            issues = result.get('issues', [])
            
            return is_valid, issues
            
        except Exception as e:
            # LLM validation failed, but don't block the game
            print(f"Warning: LLM validation failed: {e}")
            return True, []
    
    def suggest_improvements(self, board_data: Dict, category: str) -> str:
        """Generate suggestions for improving board quality"""
        suggestions = []
        
        # Count different types of issues
        placeholder_count = 0
        generic_count = 0
        
        for item in board_data.get('items', []):
            clue = item.get('clue', '').lower()
            
            for pattern in self.MEANINGLESS_PATTERNS:
                if re.search(pattern, clue, re.IGNORECASE):
                    placeholder_count += 1
                    break
            
            if len(clue.split()) < 4:
                generic_count += 1
        
        if placeholder_count > 0:
            suggestions.append(f"Replace {placeholder_count} placeholder clues with specific, factual information")
        
        if generic_count > 0:
            suggestions.append(f"Add more detail to {generic_count} overly short clues")
        
        suggestions.append(f"Ensure clues are based on real knowledge about {category}")
        suggestions.append("Make starter clues independently solvable without other answers")
        
        return " | ".join(suggestions)
    
    def is_custom_category_likely(self, category: str) -> bool:
        """Check if this is likely a custom category that might need special handling"""
        common_categories = {
            "countries", "capitals", "movies", "people", "famous people", 
            "animals", "books", "authors", "sports", "foods", "inventions",
            "elements", "landmarks", "actors", "directors", "musicians"
        }
        
        category_lower = category.lower()
        return not any(common in category_lower for common in common_categories)