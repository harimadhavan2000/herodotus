# 🧩 Grid Puzzle Game

A Sporcle-style grid puzzle game where you solve interconnected clues to reveal more clues in the grid. Powered by AI for dynamic content generation.

## 🎮 How to Play

1. **Choose a Category**: Select from predefined categories or create your own
2. **Select Grid Size**: Choose 3x3 (Easy), 4x4 (Medium), or 5x5 (Hard)
3. **Solve Clues**: Start with one revealed clue and solve it to unlock more
4. **Chain Solutions**: Each correct answer reveals new clues that reference solved items
5. **Complete the Grid**: Solve all clues to win!

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Portkey API key (for AI-generated content)

### Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key** (optional but recommended):
   ```bash
   cp .env.example .env
   # Edit .env and add your Portkey API key
   ```

4. **Run the game**:
   ```bash
   python main.py
   ```

## 🎯 Game Features

### Core Gameplay
- **Interconnected Clues**: Each clue references other items in the grid
- **Progressive Revelation**: Solving clues unlocks new ones
- **Multiple Difficulty Levels**: 3x3, 4x4, and 5x5 grids
- **Smart Scoring**: Points based on difficulty, time, and efficiency

### AI-Powered Content
- **Dynamic Categories**: AI generates unique puzzles for any category
- **Contextual Clues**: Clues that reference each other meaningfully
- **Adaptive Hints**: Get AI-generated hints when stuck

### User Interface
- **Rich Terminal UI**: Colorful, interactive command-line interface
- **Clear Visual Grid**: See your progress at a glance
- **Real-time Stats**: Track score, time, hints used, and accuracy

## 🎲 Available Categories

### Predefined Categories
- **Countries and Capitals**: World geography and capitals
- **Famous People**: Historical figures and celebrities
- **Movies and Directors**: Cinema and filmmakers
- **Animals and Habitats**: Wildlife and their environments
- **Books and Authors**: Literature and writers
- **Sports and Athletes**: Sports figures and achievements
- **Foods and Countries**: Traditional dishes and origins
- **Inventions and Inventors**: Famous inventions and creators
- **Landmarks and Locations**: World landmarks and their locations
- **Elements and Symbols**: Chemical elements and symbols

### Custom Categories
Create your own categories! The AI will generate appropriate interconnected clues for any topic you provide.

## 🎮 Commands

During gameplay, use these commands:

- `guess <row> <col> <answer>` - Make a guess (e.g., "guess 1 2 Paris")
- `hint <row> <col>` - Get a hint for a specific position
- `restart` - Restart the current game
- `quit` - Exit the game

## 📊 Scoring System

- **Base Points**: 10/20/30 points for easy/medium/hard clues
- **Difficulty Multiplier**: Higher for larger grids
- **Time Bonus**: Faster completion = more points
- **Accuracy Bonus**: Fewer wrong guesses = more points
- **Efficiency Bonus**: Fewer hints used = more points

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
PORTKEY_API_KEY=your_portkey_api_key_here
```

### Without API Key

The game works without an API key using fallback content, but you'll get:
- Limited predefined puzzles
- No custom category generation
- Basic hints instead of AI-generated ones

## 🚨 Troubleshooting

### Common Issues

1. **"PORTKEY_API_KEY not found"**
   - Copy `.env.example` to `.env` and add your API key
   - Or run with fallback content (limited features)

2. **"Game files not found"**
   - Make sure you're running `python main.py` from the project directory

3. **Import errors**
   - Run `pip install -r requirements.txt` to install dependencies

4. **AI generation fails**
   - Check your internet connection
   - Verify your Portkey API key is valid
   - The game will fall back to predefined content

### Dependencies

- `portkey-ai`: AI integration for content generation
- `rich`: Beautiful terminal user interface
- `fuzzywuzzy`: Fuzzy string matching for answers
- `python-dotenv`: Environment variable management

## 🎨 Customization

The game is designed to be extensible:

- **Add Categories**: Edit `data/categories.json` to add fallback content
- **Modify UI**: Customize colors and layouts in `game/ui.py`
- **Adjust Scoring**: Modify scoring logic in `game/game_state.py`
- **Grid Sizes**: Add new grid sizes in the UI selection

## 🤖 AI Integration

This game uses Portkey AI to generate:
- Dynamic puzzle content for any category
- Interconnected clues that reference each other
- Contextual hints based on current game state
- Difficulty-appropriate content for different grid sizes

The AI ensures puzzles are:
- Solvable with a clear progression
- Appropriately challenging for the selected difficulty
- Thematically consistent within categories

---

**Enjoy your puzzle adventure! 🧩✨**