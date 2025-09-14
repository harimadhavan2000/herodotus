from typing import List, Dict

class CategoryManager:
    def __init__(self):
        self.predefined_categories = {
            "Countries and Capitals": {
                "description": "World countries and their capital cities",
                "examples": ["France -> Paris", "Japan -> Tokyo"]
            },
            "Famous People": {
                "description": "Historical figures, celebrities, and notable personalities",
                "examples": ["Scientists", "Actors", "Politicians"]
            },
            "Movies and Directors": {
                "description": "Popular movies and their directors",
                "examples": ["Inception -> Christopher Nolan"]
            },
            "Animals and Habitats": {
                "description": "Animals and where they live",
                "examples": ["Penguin -> Antarctica", "Lion -> Savanna"]
            },
            "Books and Authors": {
                "description": "Famous books and their authors",
                "examples": ["1984 -> George Orwell"]
            },
            "Sports and Athletes": {
                "description": "Sports figures and their achievements",
                "examples": ["Basketball players", "Olympic champions"]
            },
            "Foods and Countries": {
                "description": "Traditional dishes and their countries of origin",
                "examples": ["Pizza -> Italy", "Sushi -> Japan"]
            },
            "Inventions and Inventors": {
                "description": "Famous inventions and who created them",
                "examples": ["Light bulb -> Edison"]
            },
            "Landmarks and Locations": {
                "description": "Famous landmarks and where they're located",
                "examples": ["Eiffel Tower -> Paris"]
            },
            "Elements and Symbols": {
                "description": "Chemical elements and their symbols",
                "examples": ["Gold -> Au", "Iron -> Fe"]
            }
        }
    
    def get_predefined_categories(self) -> List[str]:
        """Get list of predefined category names"""
        return list(self.predefined_categories.keys())
    
    def get_category_info(self, category: str) -> Dict[str, str]:
        """Get information about a specific category"""
        return self.predefined_categories.get(category, {})
    
    def display_categories(self) -> str:
        """Format predefined categories for display"""
        display_text = "Available Categories:\n"
        for i, (name, info) in enumerate(self.predefined_categories.items(), 1):
            display_text += f"\n{i:2d}. {name}"
            display_text += f"\n    {info['description']}"
            display_text += f"\n    Examples: {', '.join(info['examples'])}\n"
        
        return display_text
    
    def validate_custom_category(self, category: str) -> bool:
        """Basic validation for custom categories"""
        if not category or len(category.strip()) < 3:
            return False
        
        # Check for inappropriate content (basic filter)
        inappropriate_words = ['hate', 'violence', 'explicit']
        category_lower = category.lower()
        
        return not any(word in category_lower for word in inappropriate_words)
    
    def get_category_by_number(self, number: int) -> str:
        """Get category name by its display number"""
        categories = list(self.predefined_categories.keys())
        if 1 <= number <= len(categories):
            return categories[number - 1]
        return ""
    
    def suggest_related_categories(self, custom_category: str) -> List[str]:
        """Suggest related predefined categories based on custom input"""
        suggestions = []
        custom_lower = custom_category.lower()
        
        # Simple keyword matching for suggestions
        keywords_map = {
            'country': ['Countries and Capitals', 'Foods and Countries'],
            'movie': ['Movies and Directors'],
            'book': ['Books and Authors'],
            'sport': ['Sports and Athletes'],
            'animal': ['Animals and Habitats'],
            'food': ['Foods and Countries'],
            'science': ['Inventions and Inventors', 'Elements and Symbols'],
            'person': ['Famous People'],
            'place': ['Landmarks and Locations']
        }
        
        for keyword, categories in keywords_map.items():
            if keyword in custom_lower:
                suggestions.extend(categories)
        
        return list(set(suggestions))  # Remove duplicates