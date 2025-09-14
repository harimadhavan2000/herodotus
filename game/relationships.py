from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

class RelationType(Enum):
    """Types of relationships between clues"""
    REQUIRES = "requires"           # A requires B,C to be solved first
    ENABLES = "enables"            # Solving A enables/reveals B,C
    HINTS_AT = "hints_at"          # A provides hints about B,C 
    COMPLEMENTS = "complements"    # A and B together solve C
    CONTRASTS = "contrasts"        # A and B provide contrasting info for C
    CHAINS_TO = "chains_to"        # A leads to B which leads to C (sequential)

@dataclass
class ClueRelationship:
    """Represents a relationship between clues"""
    relation_type: RelationType
    source_positions: List[Tuple[int, int]]      # Source cell positions
    target_positions: List[Tuple[int, int]]      # Target cell positions
    strength: float                              # Relationship strength (0.0-1.0)
    description: str                             # Human-readable description
    
    def involves_position(self, pos: Tuple[int, int]) -> bool:
        """Check if this relationship involves a specific position"""
        return pos in self.source_positions or pos in self.target_positions
    
    def is_source(self, pos: Tuple[int, int]) -> bool:
        """Check if position is a source in this relationship"""
        return pos in self.source_positions
    
    def is_target(self, pos: Tuple[int, int]) -> bool:
        """Check if position is a target in this relationship"""
        return pos in self.target_positions

class RelationshipManager:
    """Manages complex relationships between clues"""
    
    def __init__(self, difficulty_level: str = "challenging"):
        self.relationships: List[ClueRelationship] = []
        self.difficulty_level = difficulty_level
        self.position_to_relationships: Dict[Tuple[int, int], List[ClueRelationship]] = {}
    
    def add_relationship(self, relationship: ClueRelationship):
        """Add a new relationship"""
        self.relationships.append(relationship)
        
        # Index by positions for fast lookup
        all_positions = relationship.source_positions + relationship.target_positions
        for pos in all_positions:
            if pos not in self.position_to_relationships:
                self.position_to_relationships[pos] = []
            self.position_to_relationships[pos].append(relationship)
    
    def get_relationships_for_position(self, pos: Tuple[int, int]) -> List[ClueRelationship]:
        """Get all relationships involving a specific position"""
        return self.position_to_relationships.get(pos, [])
    
    def get_requires_relationships(self, pos: Tuple[int, int]) -> List[ClueRelationship]:
        """Get relationships where this position requires others"""
        return [r for r in self.get_relationships_for_position(pos) 
                if r.relation_type == RelationType.REQUIRES and r.is_source(pos)]
    
    def get_enabled_by_relationships(self, pos: Tuple[int, int]) -> List[ClueRelationship]:
        """Get relationships where this position is enabled by others"""
        return [r for r in self.get_relationships_for_position(pos)
                if r.relation_type == RelationType.ENABLES and r.is_target(pos)]
    
    def get_hint_relationships(self, pos: Tuple[int, int]) -> List[ClueRelationship]:
        """Get relationships where this position provides or receives hints"""
        return [r for r in self.get_relationships_for_position(pos)
                if r.relation_type == RelationType.HINTS_AT]
    
    def can_reveal_position(self, pos: Tuple[int, int], solved_positions: Set[Tuple[int, int]]) -> bool:
        """Check if a position can be revealed based on solved positions"""
        
        # Check REQUIRES relationships - all required positions must be solved
        requires_rels = self.get_requires_relationships(pos)
        for rel in requires_rels:
            required_sources = set(rel.source_positions) - {pos}  # Exclude self
            if not required_sources.issubset(solved_positions):
                return False
        
        # Check ENABLES relationships - at least one enabling position must be solved
        enabled_by_rels = self.get_enabled_by_relationships(pos)
        if enabled_by_rels:
            has_enabling_source = False
            for rel in enabled_by_rels:
                if any(src_pos in solved_positions for src_pos in rel.source_positions):
                    has_enabling_source = True
                    break
            if not has_enabling_source:
                return False
        
        # Check COMPLEMENTS relationships - need at least one complement solved
        complement_rels = [r for r in self.get_relationships_for_position(pos)
                          if r.relation_type == RelationType.COMPLEMENTS]
        for rel in complement_rels:
            other_positions = (set(rel.source_positions) | set(rel.target_positions)) - {pos}
            if not any(other_pos in solved_positions for other_pos in other_positions):
                return False
        
        return True
    
    def get_newly_revealed_positions(self, just_solved_pos: Tuple[int, int], 
                                   all_solved_positions: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Get positions that should be newly revealed after solving a position"""
        newly_revealed = []
        
        # Check all relationships involving the just-solved position
        related_relationships = self.get_relationships_for_position(just_solved_pos)
        
        # Collect all positions that might be affected
        potentially_affected = set()
        for rel in related_relationships:
            potentially_affected.update(rel.source_positions)
            potentially_affected.update(rel.target_positions)
        
        # Remove already solved positions
        potentially_affected -= all_solved_positions
        
        # Check each potentially affected position
        for pos in potentially_affected:
            if self.can_reveal_position(pos, all_solved_positions):
                newly_revealed.append(pos)
        
        return newly_revealed
    
    def get_complexity_level(self) -> Dict[str, int]:
        """Get complexity metrics for the current relationship set"""
        total_relationships = len(self.relationships)
        
        # Count by type
        type_counts = {}
        for rel_type in RelationType:
            type_counts[rel_type.value] = len([r for r in self.relationships 
                                              if r.relation_type == rel_type])
        
        # Calculate complexity metrics
        many_to_many_count = len([r for r in self.relationships 
                                 if len(r.source_positions) > 1 and len(r.target_positions) > 1])
        
        max_dependencies = max([len(r.source_positions) + len(r.target_positions) 
                               for r in self.relationships] or [0])
        
        return {
            "total_relationships": total_relationships,
            "many_to_many_relationships": many_to_many_count,
            "max_dependencies_per_relationship": max_dependencies,
            **type_counts
        }
    
    def generate_relationship_description(self, pos: Tuple[int, int]) -> str:
        """Generate a human-readable description of relationships for a position"""
        relationships = self.get_relationships_for_position(pos)
        
        if not relationships:
            return "Independent clue"
        
        descriptions = []
        for rel in relationships:
            if rel.is_source(pos):
                target_positions_str = ", ".join([f"({p[0]+1},{p[1]+1})" for p in rel.target_positions])
                if rel.relation_type == RelationType.REQUIRES:
                    descriptions.append(f"Requires {target_positions_str}")
                elif rel.relation_type == RelationType.ENABLES:
                    descriptions.append(f"Enables {target_positions_str}")
                elif rel.relation_type == RelationType.HINTS_AT:
                    descriptions.append(f"Hints at {target_positions_str}")
            
            if rel.is_target(pos):
                source_positions_str = ", ".join([f"({p[0]+1},{p[1]+1})" for p in rel.source_positions])
                if rel.relation_type == RelationType.REQUIRES:
                    descriptions.append(f"Required by {source_positions_str}")
                elif rel.relation_type == RelationType.ENABLES:
                    descriptions.append(f"Enabled by {source_positions_str}")
                elif rel.relation_type == RelationType.HINTS_AT:
                    descriptions.append(f"Hinted by {source_positions_str}")
        
        return " | ".join(descriptions) if descriptions else "Complex relationships"

def generate_difficulty_appropriate_relationships(grid_size: int, difficulty_level: str) -> RelationshipManager:
    """Generate relationships appropriate for the given difficulty level"""
    manager = RelationshipManager(difficulty_level)
    
    # Define difficulty parameters
    difficulty_params = {
        "casual": {
            "max_relationships_per_cell": 2,
            "prefer_simple": True,
            "complex_relationship_chance": 0.1
        },
        "challenging": {
            "max_relationships_per_cell": 3,
            "prefer_simple": False,
            "complex_relationship_chance": 0.3
        },
        "expert": {
            "max_relationships_per_cell": 4,
            "prefer_simple": False,
            "complex_relationship_chance": 0.5
        },
        "mastermind": {
            "max_relationships_per_cell": 6,
            "prefer_simple": False,
            "complex_relationship_chance": 0.7
        }
    }
    
    params = difficulty_params.get(difficulty_level, difficulty_params["challenging"])
    
    # This will be populated by the LLM service based on generated content
    # For now, return the manager structure
    return manager