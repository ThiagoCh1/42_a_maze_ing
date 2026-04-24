*This project has been created as part of the 42 curriculum by thribeir and taalmeid.*

# A-Maze-ing

A maze generator written in Python 3. Reads a configuration file, generates a valid (optionally perfect) maze with a hidden **"42"** pattern embedded in it, writes the result to a hexadecimal output file, and renders it interactively in the terminal using ASCII.

---

## Description

This project implements a complete maze generation pipeline:

- **Generation:** Randomly generates a maze using the Recursive Backtracker (DFS) algorithm. Supports a `PERFECT` mode where exactly one path exists between entry and exit. Non-perfect mode adds extra wall removals for multiple paths.
- **"42" pattern:** A set of fully-walled cells forming the digits "4" and "2" is embedded in every generated maze. These cells are treated as obstacles during generation and remain intact.
- **Output:** Writes the maze to a file using one hexadecimal digit per cell, encoding which walls are closed via a 4-bit bitmask (N/E/S/W). Includes entry/exit coordinates and the shortest path as a direction string.
- **Visualization:** Interactive ASCII terminal display with options to re-generate, show/hide the solution path, and change wall colours.
- **Reusable module:** The generation logic is packaged as `mazegen` and can be installed via pip and imported in any Python project.

---

## Instructions

### Requirements

- Python 3.10 or later
- pip

### Install dependencies

```bash
make install
```

### Run

```bash
python3 a_maze_ing.py config.txt
```

### Debug mode

```bash
make debug
```

### Lint (flake8 + mypy)

```bash
make lint
```

### Clean

```bash
make clean
```

---

## Configuration File Format

The config file uses `KEY=VALUE` pairs, one per line. Lines starting with `#` are ignored.

| Key | Description | Example |
|-----|-------------|---------|
| `WIDTH` | Maze width in cells | `WIDTH=20` |
| `HEIGHT` | Maze height in cells | `HEIGHT=15` |
| `ENTRY` | Entry cell coordinates (x,y) | `ENTRY=0,0` |
| `EXIT` | Exit cell coordinates (x,y) | `EXIT=19,14` |
| `OUTPUT_FILE` | Path to the output hex file | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Generate a perfect maze (one path) | `PERFECT=True` |
| `SEED` | Random seed for reproducibility | `SEED=42` |

Example `config.txt`:

```
# A-Maze-ing default configuration
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
```

---

## Output File Format

The output file contains one hexadecimal character per cell (uppercase), stored row by row. Each hex digit encodes which walls are closed using a 4-bit bitmask:

| Bit | Direction |
|-----|-----------|
| 0 (LSB) | North |
| 1 | East |
| 2 | South |
| 3 | West |

A closed wall sets the bit to `1`. Example: `A` (binary `1010`) means East and West walls are closed.

After the grid, a blank line separates three footer lines:

```
<entry_x>,<entry_y>
<exit_x>,<exit_y>
<shortest_path_as_NESW_string>
```

All lines end with `\n`.

---

## Maze Generation Algorithm

**Algorithm used: Recursive Backtracker (Depth-First Search)**

The algorithm works as follows:
1. Start with a grid where all walls are closed (every cell = `0xF`).
2. Pick a starting cell, mark it visited.
3. While unvisited neighbors exist: pick a random unvisited neighbor, remove the wall between them, recurse into the neighbor.
4. Backtrack when no unvisited neighbors remain.

**Why this algorithm:**
- Naturally produces a perfect maze (spanning tree of the cell graph) — no extra logic needed for `PERFECT=True`.
- Simple to implement correctly and debug.
- Produces mazes with long winding corridors, which are visually interesting.
- Well-studied: easy to reason about correctness and connectivity guarantees.

For **non-perfect mode**, the algorithm runs first, then a configurable number of extra walls are randomly removed (checking that no 3×3 open area is created).

The **"42" pattern cells** are placed before generation and treated as obstacles — DFS skips them. Post-generation BFS validates that all non-42 cells remain reachable.

**Shortest path** is found with BFS, which guarantees the shortest path unlike DFS.

---

## Reusable Module (`mazegen`)

The generation logic is packaged as a standalone pip-installable module.

### Install from the built package

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

### Basic usage

```python
from mazegen import MazeGenerator

# Instantiate with parameters
mg = MazeGenerator(width=20, height=15, seed=42, perfect=True)

# Generate the maze
mg.generate()

# Access the grid (list[list[int]], indexed grid[row][col])
grid = mg.grid

# Access the solution
path_cells = mg.solution    # list[tuple[int, int]] — (x, y) coordinates
path_str = mg.path_str      # str — e.g. "SSWWNEENE..."
```

### Custom parameters

```python
# Non-perfect maze with a specific size and seed
mg = MazeGenerator(width=30, height=20, seed=1337, perfect=False)
mg.generate()
```

### Rebuild the package from source

```bash
python -m venv venv
source venv/bin/activate
pip install build
python -m build
# Output: dist/mazegen-1.0.0-py3-none-any.whl
```

---

## Interactive Menu

After generation, the terminal displays the maze and a menu:

```
==== A-Maze-ing ====
1. Re-generate a new maze
2. Show/Hide solution path
3. Change wall colour
4. Quit
Choice (1-4):
```

- **Re-generate:** Creates a new maze with a random seed (same config dimensions).
- **Show/Hide path:** Toggles the shortest path overlay (`·` characters).
- **Change wall colour:** Cycles through ANSI terminal colours for the wall character.

---

## Team & Project Management

### Roles

| Member | Responsibilities |
|--------|-----------------|
| taalmeid | `generator.py` (MazeGenerator + DFS), `solver.py` (BFS), `config_parser.py`, `test_generator.py` |
| thribeir | `writer.py` (hex output), `renderer.py` (ASCII + menu), `a_maze_ing.py` (main wiring), `pyproject.toml`, `Makefile`, `test_output.py` |
| Both | `README.md`, Phase 0 design contract, final integration |

### Planning

**Anticipated plan:**
- Day 1: Phase 0 — design contract session together (no code)
- Day 2: Phase 1 — setup + stubs
- Day 3–4: Phase 2 — core generation + main wiring in parallel
- Day 5–6: Phase 3 — output, renderer, review pass
- Day 7: Phase 4 — tests + validation script
- Day 8–9: Phase 5 — packaging, README, dry run

**How it evolved:**
- *TBD after project completion*

### What worked well
- *TBD*

### What could be improved
- *TBD*

### Tools used
- VS Code, Git/GitHub
- flake8 + mypy for code quality
- pytest for testing

---

## Resources

### Maze generation
- [Recursive Backtracker explanation — Jamis Buck](https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking)
- [Maze generation algorithms overview — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)

### Python packaging
- [Python Packaging User Guide — packaging.python.org](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [pyproject.toml reference](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

### Technical references
- [ANSI escape codes — Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [Python type hints — mypy docs](https://mypy.readthedocs.io/en/stable/)
- [flake8 documentation](https://flake8.pycqa.org/en/latest/)

All generated content was reviewed, tested, and understood by both team members before being used. No code was blindly copied — all logic was understood and validated.
