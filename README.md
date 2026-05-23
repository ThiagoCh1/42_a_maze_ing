*This project has been created as part of the 42 curriculum by thribeir, taalmeid.*

# A-Maze-ing

## Description

A-Maze-ing is a Python maze generator that creates 2D mazes from a configuration file and displays them interactively in the terminal. Mazes can be **perfect** (exactly one path between entry and exit) or **imperfect** (with loops). Every maze contains a hidden **"42"** pattern formed by blocked corridors at the centre.

The generation logic is packaged as a standalone, reusable Python library (`mazegen`) that can be installed via `pip`.

---

## Instructions

### Requirements

- Python 3.10+
- pip

### Installation

```bash
pip install ".[dev]" --user
```

Or with Make:

```bash
make install
```

### Running

```bash
make run
# or directly:
python3 a_maze_ing.py config.txt
```

### Linting

```bash
make lint          # flake8 + mypy standard
make lint-strict   # flake8 + mypy --strict
```

### Building the mazegen package

```bash
make build
# generates: dist/mazegen-1.0.0-py3-none-any.whl
```

### Running tests

```bash
python3 test_mazegen.py
```

---

## Configuration file format

One `KEY=VALUE` pair per line. Lines starting with `#` are comments.

| Key | Type | Required | Description | Example |
|---|---|---|---|---|
| `WIDTH` | int | yes | Number of columns | `WIDTH=20` |
| `HEIGHT` | int | yes | Number of rows | `HEIGHT=15` |
| `ENTRY` | x,y | yes | Entry coordinates | `ENTRY=0,0` |
| `EXIT` | x,y | yes | Exit coordinates | `EXIT=19,14` |
| `OUTPUT_FILE` | str | yes | Output file path | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | bool | yes | Perfect maze? | `PERFECT=True` |
| `SEED` | int | no | RNG seed for reproducibility | `SEED=42` |
| `ALGORITHM` | str | no | Generation algorithm | `ALGORITHM=prims` |

Valid algorithms: `recursive_backtracker`, `prims`, `kruskals`

---

## Maze generation algorithm

### Primary: Recursive Backtracker (iterative DFS)

The default algorithm. Performs a depth-first search starting from the entry cell, randomly carving passages into unvisited neighbours. When it hits a dead end it backtracks until a cell with unvisited neighbours is found.

**Why this algorithm?** It produces mazes with long winding corridors and few dead ends, giving a classic maze feel. It is straightforward to implement iteratively (avoiding Python recursion limits) and naturally produces perfect mazes (spanning trees).

### Bonus: Randomised Prim's

Grows the maze from a frontier list, picking edges at random. Produces mazes with more branching and shorter corridors.

### Bonus: Randomised Kruskal's

Uses a union-find structure to merge disjoint sets. Shuffles all internal walls and opens them if they connect two different components. Produces highly uniform, unbiased mazes.

---

## Reusable module (mazegen)

The `mazegen` package can be installed independently and used in any Python project.

### Install

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

### Basic usage

```python
from mazegen.generator import MazeGenerator

gen = MazeGenerator(width=20, height=15, seed=42)
gen.generate()

# grid[row][col] = wall bitmask (int 0-15)
# Bit 0=North, Bit 1=East, Bit 2=South, Bit 3=West
for row in gen.grid:
    print([hex(cell) for cell in row])

# Solution path as list of 'N','E','S','W'
print("Solution:", "".join(gen.solution))
```

### Custom parameters

```python
gen = MazeGenerator(
    width=30,
    height=20,
    entry=(0, 0),
    exit_=(29, 19),
    perfect=True,
    seed=1337,
    algorithm="prims",   # or "kruskals", "recursive_backtracker"
)
gen.generate()
```

### Step callback (animation hook)

```python
def on_step(grid):
    # called after each wall removal during generation
    pass

gen = MazeGenerator(width=20, height=15, step_callback=on_step)
gen.generate()
```

---

## Resources

- [Maze generation algorithms — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Buckblog: Maze Generation (Jamis Buck)](http://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap)
- [Think Labyrinth — Walter D. Pullen](http://www.astrolog.org/labyrnth/algrithm.htm)
- Python docs: [random](https://docs.python.org/3/library/random.html), [collections.deque](https://docs.python.org/3/library/collections.html#collections.deque)
- [flake8](https://flake8.pycqa.org/), [mypy](https://mypy.readthedocs.io/)

### AI usage

Claude (Anthropic) was used to: scaffold the initial project architecture, suggest the multi-algorithm strategy, review docstring and type hint conventions, help reason through the union-find implementation for Kruskal's, and assist with the terminal renderer colour logic. All generated code was reviewed, understood, and adapted by the project authors before submission.

---

## Team and project management

### Roles

| Member | Responsibilities |
|---|---|
| **thribeir** | Project architecture, maze generation algorithms (recursive backtracker, Prim's), BFS solver, output writer, config parser, packaging (`mazegen` library), test suite |
| **taalmeid** | Terminal renderer (ASCII display, colour system, interactive menu), Kruskal's algorithm, "42" pattern logic, README, Makefile |

### Planning

- **Week 1:** Config parser, MazeGenerator skeleton, recursive backtracker, output writer, validator testing.
- **Week 2:** BFS solver, Prim's and Kruskal's algorithms, "42" pattern, terminal renderer with colour system.
- **Week 3:** mazegen packaging, test suite, README, linting pass, final review.

### What worked well

- Separating the reusable `mazegen` module from the app-specific I/O from the start avoided painful refactoring later.
- Using a bitmask per cell kept the grid representation compact and made wall operations straightforward.
- The `step_callback` hook in `MazeGenerator` made the renderer decoupled from the generation logic.

### What could be improved

- The corridor-width constraint (no 3×3 open areas) could use a more robust post-processing pass.
- The "42" pattern placement could auto-scale with maze size for better visual impact on larger mazes.

### Tools used

- VS Code, Python 3.10+, venv
- flake8, mypy, pytest
- Claude (Anthropic) — see AI usage above
