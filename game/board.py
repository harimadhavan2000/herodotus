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
        """Reveal the initial clues to start the game"""
        if self.relationship_manager:
            # Use relationship manager to determine starter clues
            solved_positions: Set[Tuple[int, int]] = set()
            
            # Find clues that can be revealed without any dependencies
            for pos, cell in self.cells.items():
                if self.relationship_manager.can_reveal_position(pos, solved_positions):
                    cell.revealed = True
            
            # If no clues were revealed, fallback to simple difficulty-based selection
            if not any(cell.revealed for cell in self.cells.values()):
                self._simple_starter_reveal()
        else:
            # Fallback to simple method
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
        """Simple fallback method for revealing connected clues"""
        solved_answer = cell.answer.lower()
        for other_cell in self.cells.values():
            if not other_cell.revealed and not other_cell.solved:
                # Check if this cell references the solved answer
                for ref in other_cell.references:
                    if fuzz.ratio(ref.lower(), solved_answer) >= 85:
                        other_cell.revealed = True
                        break
                
                # Also reveal cells with lower difficulty that don't have unresolved references
                if other_cell.difficulty <= 2 and self._can_reveal_cell(other_cell):
                    other_cell.revealed = True
    
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