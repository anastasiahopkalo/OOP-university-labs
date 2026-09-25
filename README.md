# CodeLearn Studio

Interactive platform for learning algorithms and data structures with real-time visualization and progress tracking.

## Overview

CodeLearn Studio is a desktop application that helps students understand how algorithms work through step-by-step visualization, practical exercises, and progress monitoring. Instead of just reading code or watching videos, students see algorithms executing in real-time, write their own implementations, and track their learning progress.

## The Problem We're Solving

Students struggle to understand algorithms because:
- They can't see how data changes step by step
- There's no way to practice and get immediate feedback
- Progress is hard to track across different topics
- They need a tool that works offline and locally

## Comparison with Existing Solutions

| Feature | Visualgo | AlgoVisualizer | HackerRank | CodeLearn Studio |
|---------|----------|----------------|-----------|-----------------|
| Offline usage | No | No | No | **Yes** |
| Local installation | No | No | No | **Yes** |
| Built-in exercises | No | Minimal | Yes | **Yes** |
| Progress tracking | No | No | Yes | **Yes** |
| Open source | No | Partial | No | **Yes** |
| Easy deployment | No | No | No | **Yes** |

Our solution is better because you can run it on any computer without internet, customize it, and most importantly, students can see the full learning journey in one integrated application.

## What It Does

### For Students
1. **Visualize Algorithms** - Watch QuickSort, BubbleSort, Dijkstra's algorithm execute step by step
2. **Do Exercises** - Write code directly in the app and test it against predefined test cases
3. **Track Progress** - See graphs showing learning progress, topics mastered, and achievements

### Technical Features
- Step-by-step animation of 5+ sorting algorithms
- 7+ data structures (linked lists, stacks, queues, trees, graphs)
- Code editor with built-in testing framework
- Local SQLite database to store user progress
- Dashboard with performance charts
- Support for running 100+ test cases simultaneously

## How to Run

### Requirements
- Python 3.8+
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/CodeLearnStudio.git
cd CodeLearnStudio

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Run tests
pytest tests/ -v --cov=src
```

The app will open a desktop window with three tabs: Visualization, Exercises, and Dashboard.

## Team Structure (2 People)

This project is designed for a 2-person team with clear responsibilities:

**Person 1: Backend Developer**
- Implements all 12+ classes and algorithms
- Creates exercise testing logic
- Manages the database for storing progress
- Writes unit tests for all components
- Covers: Sorting algorithms, Search algorithms, Data structures, Classes hierarchy

**Person 2: Frontend Developer**
- Builds the PyQt5 GUI with all three panels
- Integrates matplotlib for progress charts
- Creates the visualization system for animating algorithms
- Implements styling and user experience
- Connects backend logic to UI through signals/slots

Both work on Git together, making commits regularly. No conflicts - they work in separate modules.

## How This Covers Three Lab Assignments

### Lab 1: Object-Oriented Programming
The backend developer implements the OOP requirements:
- 12+ classes: Algorithm (abstract), SortingAlgorithm, QuickSort, MergeSort, BubbleSort, DataStructure, LinkedList, DynamicArray, Visualizer, Exercise, ProgressTracker, and more
- 2 inheritance hierarchies: Algorithm tree and DataStructure tree
- Polymorphism: Abstract methods, generic types with TypeVar, method overriding
- 25+ non-trivial methods across all classes
- Proper encapsulation with private/protected/public members
- Unit tests covering 70%+ of the code

### Lab 2: GUI Development
The frontend developer implements the PyQt5 requirements:
- Main window with three tabs (QTabWidget)
- VisualizationPanel: Choose algorithm, play/pause/step animations, adjust speed
- ExercisePanel: Code editor, run tests, view results in a table
- DashboardPanel: Progress bar, matplotlib charts, achievements list
- 3+ additional features: Dark theme, real-time statistics, code history
- Signals and slots connecting UI to backend logic
- Professional, clean interface

### Lab 3: Using External Libraries
Both developers use 6 external libraries across the project:
1. **PyQt5** - The entire GUI framework (frontend)
2. **matplotlib** - Graphs and charts in the dashboard (frontend)
3. **SQLAlchemy** - Database models and queries (backend)
4. **pytest** - Unit testing framework (backend)
5. **networkx** - Graph algorithms implementation (backend)
6. **numpy** - Numerical operations for advanced algorithms (backend)

These aren't random choices - each solves a real problem in the architecture.

## Technologies Used

### Frontend Stack
- **PyQt5**: Professional desktop GUI framework
- **matplotlib**: Scientific plotting library integrated into PyQt5
- **Python 3.8+**: Core language

### Backend Stack
- **SQLAlchemy ORM**: Maps Python classes to database tables
- **SQLite**: Lightweight, file-based database (no server needed)
- **NetworkX**: Library for graph algorithms
- **numpy**: Numerical operations

### Development Tools
- **pytest**: Unit testing with fixtures and parametrization
- **Git**: Version control with 25-30 meaningful commits
- **PEP8**: Code style guide followed throughout

## Project Statistics

```
Total Classes: 12+
Total Methods: 25+
Lines of Code: ~2000
  - Core logic: ~500
  - Algorithms: ~400
  - GUI: ~600
  - Database: ~150
  - Tests: ~300

Test Coverage: 70%+
Git Commits: 25-30
Development Time: 40-50 hours
```

## File Structure

```
CodeLearnStudio/
├── src/
│   ├── core/              # OOP architecture (Lab 1)
│   │   ├── algorithm.py
│   │   ├── data_structure.py
│   │   ├── visualizer.py
│   │   └── exercise.py
│   ├── algorithms/        # Sorting, searching, graphs
│   │   ├── sorting/
│   │   ├── searching/
│   │   └── graphs/
│   ├── gui/               # PyQt5 interface (Lab 2)
│   │   ├── main_window.py
│   │   ├── visualization_panel.py
│   │   ├── exercise_panel.py
│   │   └── dashboard_panel.py
│   └── database/          # SQLAlchemy models (Lab 3)
│       ├── models.py
│       └── database.py
├── tests/                 # Unit tests
│   ├── test_algorithms.py
│   └── test_data_structures.py
└── main.py               # Entry point
```

## Key Features Explained

### Visualization Panel
Shows an algorithm executing step by step. Users can:
- Select which algorithm to watch (QuickSort, MergeSort, BubbleSort, etc.)
- Play the animation at normal or custom speed
- Step forward or backward through each operation
- See highlighted elements being compared or swapped
- View metrics like number of comparisons and swaps

### Exercise Panel
Lets students write and test code:
- Pre-written exercises for each data structure
- Code editor where students write their solution
- Click "Run" to execute against 10-20 test cases
- See results in a table (passed/failed, execution time)
- Can submit for scoring

### Dashboard Panel
Tracks overall progress:
- Visual progress bar showing course completion
- Line chart showing learning over days
- List of achievements unlocked
- Statistics: total exercises solved, average score, learning streak

## Why This Design Works

1. **Clear Separation**: Backend and frontend are independent. Backend implements business logic, frontend just displays it.
2. **Scalable**: Easy to add new algorithms (inherit from Algorithm class), new exercises (add to database), new charts (extend visualizer).
3. **Educational**: Students learn real software engineering: OOP patterns, database design, GUI development, testing.
4. **Practical**: The application actually works and teaches something useful.

## How to Use It

1. Open the application (`python main.py`)
2. Click "Visualization" tab to watch algorithms
3. Click "Exercises" tab to write code
4. Click "Dashboard" to see progress
5. Pick an algorithm, run the visualization
6. Solve exercises and watch your score increase
7. Check the dashboard to see improvement over time

## Dependencies

```
PyQt5>=5.15.0
matplotlib>=3.3.0
SQLAlchemy>=1.4.0
pytest>=6.2.0
networkx>=2.6.0
numpy>=1.19.0
```

## Testing

Run unit tests with coverage:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

This generates an HTML report showing exactly which parts of the code are tested.

## Development Notes

- The project follows PEP8 style guide
- All classes have docstrings explaining their purpose
- Each major change is committed to Git with a clear message
- Abstract base classes (ABC) enforce contracts for subclasses
- Database queries use ORM to prevent SQL injection
- Tests use pytest fixtures for clean, reusable test code

## Conclusion

CodeLearn Studio demonstrates solid understanding of:
- Object-oriented programming (inheritance, polymorphism, encapsulation)
- Desktop application development (PyQt5)
- Database management (SQLAlchemy ORM)
- Professional software practices (testing, version control, documentation)

The application solves a real problem (understanding algorithms) in a practical way that students can actually use.