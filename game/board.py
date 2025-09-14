from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from fuzzywuzzy import fuzz

@dataclass
class Cell:
    answer: str
    clue: str
    references: List[str]
    difficulty: int
    position: Dict[str, int]
    solved: bool = False
    revealed: bool = False

class GameBoard:
    def __init__(self, board_data: Dict):
        self.category = board_data['category']
        self.grid_size = board_data['grid_size']
        self.cells: Dict[Tuple[int, int], Cell] = {}
        self.solved_count = 0
        self.total_cells = self.grid_size * self.grid_size
        self.starter_revealed = False
        
        # Initialize cells from board data
        for item in board_data['items']:
            pos = (item['position']['row'], item['position']['col'])
            self.cells[pos] = Cell(
                answer=item['answer'],
                clue=item['clue'],
                references=item.get('references', []),
                difficulty=item.get('difficulty', 1),
                position=item['position']
            )
        
        # Reveal the first starter clue (lowest difficulty)
        self._reveal_starter_clue()
    
    def _reveal_starter_clue(self):
        """Reveal the easiest clue to start the game"""
        starter_cells = [cell for cell in self.cells.values() if cell.difficulty == 1]
        if starter_cells:
            starter_cell = min(starter_cells, key=lambda c: len(c.references))
            starter_cell.revealed = True
            self.starter_revealed = True
    
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
        
        # Find and reveal cells that reference this solved answer
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
        """Get all currently available clues"""
        clues = []
        for pos, cell in self.cells.items():
            if cell.revealed and not cell.solved:
                clues.append({
                    'position': f"({pos[0]+1},{pos[1]+1})",
                    'clue': cell.clue,
                    'difficulty': cell.difficulty,
                    'row': pos[0],
                    'col': pos[1]
                })
        return sorted(clues, key=lambda x: x['difficulty'])