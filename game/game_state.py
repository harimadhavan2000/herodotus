import time
from typing import Dict, List, Optional
from .board import GameBoard
from .clue_generator import ClueGenerator
from .categories import CategoryManager

class GameState:
    def __init__(self):
        self.board: Optional[GameBoard] = None
        self.clue_generator = ClueGenerator()
        self.category_manager = CategoryManager()
        self.start_time: Optional[float] = None
        self.hints_used = 0
        self.wrong_guesses = 0
        self.score = 0
        self.game_active = False
        self.current_category = ""
        self.grid_size = 3
        self.clue_difficulty_level = "challenging"
        self.difficulty_multiplier = 1.0
    
    def start_new_game(self, category: str, grid_size: int = 3, clue_difficulty_level: str = "challenging") -> bool:
        """Initialize a new game with given category, grid size, and clue difficulty"""
        try:
            self.current_category = category
            self.grid_size = grid_size
            self.clue_difficulty_level = clue_difficulty_level
            self.difficulty_multiplier = self._calculate_difficulty_multiplier(grid_size, clue_difficulty_level)
            
            # Generate board using LLM with difficulty level
            board_data = self.clue_generator.generate_board(category, grid_size, clue_difficulty_level)
            
            # Extract relationship manager if present
            relationship_manager = board_data.get('relationship_manager')
            
            # Create board with relationship manager
            self.board = GameBoard(board_data, relationship_manager)
            
            # Reset game state
            self.start_time = time.time()
            self.hints_used = 0
            self.wrong_guesses = 0
            self.score = 0
            self.game_active = True
            
            return True
            
        except Exception as e:
            print(f"Error starting game: {e}")
            return False
    
    def _calculate_difficulty_multiplier(self, grid_size: int, clue_difficulty_level: str = "challenging") -> float:
        """Calculate difficulty multiplier based on grid size and clue difficulty"""
        # Base multiplier for grid size
        grid_multipliers = {3: 1.0, 4: 1.5, 5: 2.0}
        grid_mult = grid_multipliers.get(grid_size, 1.0)
        
        # Additional multiplier for clue difficulty
        clue_multipliers = {
            "casual": 0.8,
            "challenging": 1.0, 
            "expert": 1.3,
            "mastermind": 1.6
        }
        clue_mult = clue_multipliers.get(clue_difficulty_level, 1.0)
        
        return grid_mult * clue_mult
    
    def make_guess(self, guess: str, row: int, col: int) -> Dict[str, any]:
        """Process a player's guess"""
        if not self.game_active or not self.board:
            return {"success": False, "message": "Game not active"}
        
        # Adjust for 1-based input to 0-based indexing
        row -= 1
        col -= 1
        
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return {"success": False, "message": "Position out of bounds"}
        
        cell = self.board.get_cell(row, col)
        if not cell:
            return {"success": False, "message": "No cell at this position"}
        
        if not cell.revealed:
            return {"success": False, "message": "This clue hasn't been revealed yet"}
        
        if cell.solved:
            return {"success": False, "message": "This cell is already solved"}
        
        # Check if guess is correct
        is_correct = self.board.check_answer(guess, row, col)
        
        if is_correct:
            # Calculate points for correct guess
            points = self._calculate_points(cell.difficulty)
            self.score += points
            
            result = {
                "success": True,
                "message": f"Correct! '{cell.answer}' (+{points} points)",
                "answer": cell.answer,
                "points_earned": points,
                "new_clues_revealed": self._get_newly_revealed_count()
            }
            
            # After solving, check if we're stuck and need emergency revelation
            if not self.board.is_complete():
                self._check_and_handle_stuck_state()
            
            # Check if game is complete
            if self.board.is_complete():
                self.game_active = False
                bonus_points = self._calculate_completion_bonus()
                self.score += bonus_points
                result["game_complete"] = True
                result["completion_bonus"] = bonus_points
                result["final_score"] = self.score
                result["completion_time"] = self.get_elapsed_time()
            
            return result
        else:
            self.wrong_guesses += 1
            return {
                "success": False,
                "message": f"Incorrect. The answer was not '{guess}'",
                "wrong_guesses": self.wrong_guesses
            }
    
    def _get_newly_revealed_count(self) -> int:
        """Get count of newly revealed clues after last correct answer"""
        if not self.board:
            return 0
        return len(self.board.get_revealed_cells())
    
    def _calculate_points(self, difficulty: int) -> int:
        """Calculate points based on difficulty and other factors"""
        base_points = {1: 10, 2: 20, 3: 30}.get(difficulty, 10)
        
        # Apply difficulty multiplier based on grid size
        points = int(base_points * self.difficulty_multiplier)
        
        # Reduce points for hints used (per hint used on this cell)
        hint_penalty = min(5, self.hints_used)
        points = max(5, points - hint_penalty)
        
        return points
    
    def _calculate_completion_bonus(self) -> int:
        """Calculate bonus points for completing the game"""
        if not self.start_time:
            return 0
        
        elapsed_time = time.time() - self.start_time
        time_bonus = max(0, 100 - int(elapsed_time / 10))  # Bonus decreases over time
        
        # Bonus for fewer wrong guesses
        accuracy_bonus = max(0, 50 - (self.wrong_guesses * 10))
        
        # Bonus for fewer hints used
        efficiency_bonus = max(0, 30 - (self.hints_used * 5))
        
        total_bonus = int((time_bonus + accuracy_bonus + efficiency_bonus) * self.difficulty_multiplier)
        return total_bonus
    
    def get_hint(self, row: int, col: int) -> Dict[str, any]:
        """Get a hint for a specific position"""
        if not self.game_active or not self.board:
            return {"success": False, "message": "Game not active"}
        
        # Adjust for 1-based input
        row -= 1
        col -= 1
        
        cell = self.board.get_cell(row, col)
        if not cell or not cell.revealed or cell.solved:
            return {"success": False, "message": "Cannot get hint for this position"}
        
        # Generate contextual hint
        solved_answers = [c.answer for c in self.board.get_solved_cells()]
        context = f"Category: {self.current_category}. Solved items: {', '.join(solved_answers[-3:])}"
        
        hint = self.clue_generator.get_hint(cell.answer, context)
        self.hints_used += 1
        
        return {
            "success": True,
            "hint": hint,
            "hints_used": self.hints_used
        }
    
    def get_game_status(self) -> Dict[str, any]:
        """Get current game status"""
        if not self.board:
            return {"game_active": False}
        
        return {
            "game_active": self.game_active,
            "category": self.current_category,
            "grid_size": self.grid_size,
            "clue_difficulty_level": self.clue_difficulty_level,
            "progress": self.board.get_progress(),
            "solved_count": self.board.solved_count,
            "total_cells": self.board.total_cells,
            "score": self.score,
            "hints_used": self.hints_used,
            "wrong_guesses": self.wrong_guesses,
            "elapsed_time": self.get_elapsed_time(),
            "current_clues": self.board.get_current_clues()
        }
    
    def get_elapsed_time(self) -> float:
        """Get elapsed game time in seconds"""
        if not self.start_time:
            return 0
        return time.time() - self.start_time
    
    def get_leaderboard_entry(self) -> Dict[str, any]:
        """Get entry for leaderboard/high scores"""
        return {
            "category": self.current_category,
            "grid_size": self.grid_size,
            "score": self.score,
            "completion_time": self.get_elapsed_time(),
            "hints_used": self.hints_used,
            "wrong_guesses": self.wrong_guesses,
            "completed": not self.game_active and self.board and self.board.is_complete()
        }
    
    def restart_game(self) -> bool:
        """Restart the current game with same category, grid size, and difficulty"""
        return self.start_new_game(self.current_category, self.grid_size, self.clue_difficulty_level)
    
    def quit_game(self):
        """End the current game"""
        self.game_active = False
    
    def _check_and_handle_stuck_state(self):
        """Check if the game is stuck and handle with emergency revelation"""
        if not self.board:
            return
        
        # Check if we're stuck (no available clues but game not complete)
        if self.board.is_stuck():
            print("🚨 Detected stuck state - no available clues!")
            
            # Try emergency revelation
            revealed = self.board.emergency_reveal_clue()
            
            if revealed:
                print("✅ Emergency clue revealed to continue progress")
            else:
                print("⚠️  No more clues available - this shouldn't happen!")
    
    def check_game_completability(self) -> Dict[str, any]:
        """Check if the current game state is completable"""
        if not self.board:
            return {"completable": False, "reason": "No board"}
        
        if self.board.is_complete():
            return {"completable": True, "reason": "Already complete"}
        
        # Check if we're currently stuck
        if self.board.is_stuck():
            return {
                "completable": False, 
                "reason": "Currently stuck - no available clues",
                "can_emergency_reveal": len(self.board.get_unrevealed_cells()) > 0
            }
        
        # Check overall reachability
        reachability = self.board.check_reachability()
        
        return {
            "completable": reachability.get("all_reachable", True),
            "reachable_percentage": reachability.get("reachability_percentage", 100.0),
            "unreachable_count": len(reachability.get("unreachable_positions", [])),
            "available_clues": len(self.board.get_current_clues())
        }