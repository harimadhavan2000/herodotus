from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from fuzzywuzzy import fuzz
from .relationships import RelationshipManager, ClueRelationship

@dataclass
class Cell:
    answer: str
    clue: str
    references: List[str]  # Keep for backward compatibility
    difficulty: int
    position: Dict[str, int]
    solved: bool = False
    revealed: bool = False
    relationship_description: str = ""  # Description of this cell's relationships

class GameBoard:
    def __init__(self, board_data: Dict, relationship_manager: Optional[RelationshipManager] = None):
        self.category = board_data['category']
        self.grid_size = board_data['grid_size']
        self.cells: Dict[Tuple[int, int], Cell] = {}
        self.solved_count = 0
        self.total_cells = self.grid_size * self.grid_size
        self.starter_revealed = False
        self.relationship_manager = relationship_manager
        
        # Initialize cells from board data
        for item in board_data['items']:
            pos = (item['position']['row'], item['position']['col'])
            cell = Cell(
                answer=item['answer'],
                clue=item['clue'],
                references=item.get('references', []),
                difficulty=item.get('difficulty', 1),
                position=item['position']
            )
            
            # Add relationship description if relationship manager exists
            if self.relationship_manager:
                cell.relationship_description = self.relationship_manager.generate_relationship_description(pos)
            
            self.cells[pos] = cell
        
        # Reveal the first starter clue (lowest difficulty)
        self._reveal_starter_clues()
    
    def _reveal_starter_clues(self):
        """Reveal the initial clues to start the game - conservative approach"""
        if self.relationship_manager:
            # Conservative approach: Only reveal 1-2 starter clues, not all independent ones
            solved_positions: Set[Tuple[int, int]] = set()
            revealed_count = 0
            max_starters = min(2, self.total_cells // 3)  # At most 1-2 starters depending on grid size
            
            # Find and reveal only a few independent starter clues
            for pos, cell in self.cells.items():
                if revealed_count >= max_starters:
                    break
                    
                if (cell.difficulty == 1 and 
                    self.relationship_manager.can_reveal_position(pos, solved_positions) and
                    len(cell.references) == 0):
                    cell.revealed = True
                    revealed_count += 1
            
            # If still no clues revealed, use fallback
            if revealed_count == 0:
                self._simple_starter_reveal()
        else:
            # Fallback to simple method - also conservative
            self._simple_starter_reveal()
        
        self.starter_revealed = True
    
    def _simple_starter_reveal(self):
        """Simple fallback method to reveal starter clues"""
        starter_cells = [cell for cell in self.cells.values() if cell.difficulty == 1]
        if starter_cells:
            starter_cell = min(starter_cells, key=lambda c: len(c.references))
            starter_cell.revealed = True
    
    def get_cell(self, row: int, col: int) -> Optional[Cell]:
        """Get cell at specific position"""
        return self.cells.get((row, col))
    
    def get_revealed_cells(self) -> List[Cell]:
        """Get all currently revealed cells"""
        return [cell for cell in self.cells.values() if cell.revealed and not cell.solved]
    
    def get_solved_cells(self) -> List[Cell]:
        """Get all solved cells"""
        return [cell for cell in self.cells.values() if cell.solved]
    
    def check_answer(self, guess: str, row: int, col: int) -> bool:
        """Check if guess matches the answer at position"""
        cell = self.get_cell(row, col)
        if not cell or not cell.revealed:
            return False
        
        # Use fuzzy matching to allow for typos
        similarity = fuzz.ratio(guess.lower().strip(), cell.answer.lower())
        if similarity >= 85:  # 85% similarity threshold
            self._mark_solved(cell)
            return True
        
        return False
    
    def _mark_solved(self, cell: Cell):
        """Mark cell as solved and reveal connected clues"""
        cell.solved = True
        self.solved_count += 1
        
        # Get position of solved cell
        solved_pos = (cell.position['row'], cell.position['col'])
        
        if self.relationship_manager:
            # Use relationship manager to determine newly revealed positions
            all_solved_positions = {(c.position['row'], c.position['col']) 
                                  for c in self.cells.values() if c.solved}
            
            newly_revealed_positions = self.relationship_manager.get_newly_revealed_positions(
                solved_pos, all_solved_positions
            )
            
            # Reveal the newly available positions
            for pos in newly_revealed_positions:
                if pos in self.cells:
                    self.cells[pos].revealed = True
        else:
            # Fallback to simple reference-based revelation
            self._simple_mark_solved(cell)
    
    def _simple_mark_solved(self, cell: Cell):
        """Simple fallback method for revealing connected clues - conservative approach"""
        solved_answer = cell.answer.lower()
        revealed_count = 0
        max_reveals_per_solve = 2  # Limit how many clues get revealed per solve
        
        for other_cell in self.cells.values():
            if not other_cell.revealed and not other_cell.solved and revealed_count < max_reveals_per_solve:
                # Only reveal cells that directly reference this solved answer
                for ref in other_cell.references:
                    if fuzz.ratio(ref.lower(), solved_answer) >= 85:
                        other_cell.revealed = True
                        revealed_count += 1
                        break
        
        # If no direct references found and we haven't revealed anything,
        # reveal just ONE low-difficulty cell as a fallback
        if revealed_count == 0:
            for other_cell in self.cells.values():
                if (not other_cell.revealed and not other_cell.solved and 
                    other_cell.difficulty == 1 and len(other_cell.references) <= 1):
                    other_cell.revealed = True
                    break
    
    def _can_reveal_cell(self, cell: Cell) -> bool:
        """Check if cell can be revealed based on solved references"""
        if not cell.references:
            return True
        
        solved_answers = [c.answer.lower() for c in self.get_solved_cells()]
        
        # Check if at least one reference is solved
        for ref in cell.references:
            for solved in solved_answers:
                if fuzz.ratio(ref.lower(), solved) >= 85:
                    return True
        
        return False
    
    def get_available_positions(self) -> List[Tuple[int, int]]:
        """Get positions of revealed but unsolved cells"""
        positions = []
        for pos, cell in self.cells.items():
            if cell.revealed and not cell.solved:
                positions.append(pos)
        return positions
    
    def is_complete(self) -> bool:
        """Check if all cells are solved"""
        return self.solved_count == self.total_cells
    
    def get_progress(self) -> float:
        """Get completion percentage"""
        return (self.solved_count / self.total_cells) * 100
    
    def get_grid_display(self) -> List[List[str]]:
        """Get grid representation for display"""
        grid = []
        for row in range(self.grid_size):
            grid_row = []
            for col in range(self.grid_size):
                cell = self.get_cell(row, col)
                if cell.solved:
                    grid_row.append(cell.answer[:8])  # Truncate long answers
                elif cell.revealed:
                    grid_row.append("❓")
                else:
                    grid_row.append("■")
            grid.append(grid_row)
        return grid
    
    def get_current_clues(self) -> List[Dict]:
        """Get all currently available clues with relationship information"""
        clues = []
        for pos, cell in self.cells.items():
            if cell.revealed and not cell.solved:
                clue_data = {
                    'position': f"({pos[0]+1},{pos[1]+1})",
                    'clue': cell.clue,
                    'difficulty': cell.difficulty,
                    'row': pos[0],
                    'col': pos[1],
                    'relationship_description': cell.relationship_description
                }
                clues.append(clue_data)
        return sorted(clues, key=lambda x: x['difficulty'])
    
    def is_stuck(self) -> bool:
        """Check if the game is in a stuck state (no available clues and not complete)"""
        if self.is_complete():
            return False
        
        available_clues = self.get_current_clues()
        return len(available_clues) == 0
    
    def get_unrevealed_cells(self) -> List[Dict]:
        """Get all unrevealed cells for emergency revelation"""
        unrevealed = []
        for pos, cell in self.cells.items():
            if not cell.revealed and not cell.solved:
                unrevealed.append({
                    'position': pos,
                    'cell': cell,
                    'difficulty': cell.difficulty,
                    'references_count': len(cell.references)
                })
        
        # Sort by difficulty and reference count (easier, fewer deps first)
        unrevealed.sort(key=lambda x: (x['difficulty'], x['references_count']))
        return unrevealed
    
    def emergency_reveal_clue(self) -> bool:
        """Emergency reveal of a strategic clue when stuck"""
        unrevealed = self.get_unrevealed_cells()
        
        if not unrevealed:
            return False
        
        # Find the best candidate for emergency revelation
        # Priority: low difficulty, few references, or completely independent
        best_candidate = None
        
        # First try: find completely independent clues (no references)
        for item in unrevealed:
            if item['references_count'] == 0 and item['difficulty'] <= 2:
                best_candidate = item
                break
        
        # Second try: find low-dependency clues
        if not best_candidate:
            for item in unrevealed:
                if item['references_count'] <= 1 and item['difficulty'] <= 3:
                    best_candidate = item
                    break
        
        # Last resort: just pick the easiest one
        if not best_candidate and unrevealed:
            best_candidate = unrevealed[0]
        
        if best_candidate:
            pos = best_candidate['position']
            cell = best_candidate['cell']
            cell.revealed = True
            
            print(f"🚨 Emergency revelation: Position ({pos[0]+1},{pos[1]+1}) - {cell.clue[:50]}...")
            return True
        
        return False
    
    def check_reachability(self) -> Dict[str, any]:
        """Check if all cells are theoretically reachable from starters"""
        if not self.relationship_manager:
            return {"all_reachable": True, "analysis": "No relationship manager - assuming reachable"}
        
        # Start with currently revealed cells
        reachable = set()
        for pos, cell in self.cells.items():
            if cell.revealed:
                reachable.add(pos)
        
        # Simulate revelation process to see what's reachable
        max_iterations = self.total_cells * 2  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            initial_reachable_count = len(reachable)
            
            # For each reachable position, see what it can unlock
            new_reachable = set()
            for pos in reachable:
                if self.relationship_manager:
                    newly_revealed = self.relationship_manager.get_newly_revealed_positions(pos, reachable)
                    new_reachable.update(newly_revealed)
            
            reachable.update(new_reachable)
            
            # If no new positions became reachable, we're done
            if len(reachable) == initial_reachable_count:
                break
            
            iteration += 1
        
        all_positions = set(self.cells.keys())
        unreachable_positions = all_positions - reachable
        
        return {
            "all_reachable": len(unreachable_positions) == 0,
            "reachable_count": len(reachable),
            "total_count": len(all_positions),
            "unreachable_positions": list(unreachable_positions),
            "reachability_percentage": (len(reachable) / len(all_positions)) * 100
        }