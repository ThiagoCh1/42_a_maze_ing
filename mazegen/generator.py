"""Maze generator module.

Provides MazeGenerator, a reusable class for generating 2D mazes using
multiple algorithms. The grid is stored as a 2D list of integers where
each integer encodes the closed walls of a cell as a bitmask:

    Bit 0 (LSB) = North wall closed
    Bit 1       = East  wall closed
    Bit 2       = South wall closed
    Bit 3       = West  wall closed

A value of 0xF (15) means all four walls are closed (isolated cell).
A value of 0x0 means all walls are open.

Example:
    >>> from mazegen.generator import MazeGenerator
    >>> gen = MazeGenerator(width=20, height=15, seed=42)
    >>> gen.generate()
    >>> print(gen.grid[0][0])        # wall bitmask of top-left cell
    >>> print("".join(gen.solution)) # shortest path as N/E/S/W string
"""

import random
from collections import deque
from typing import Callable, List, Optional, Tuple

# Wall bitmask constants
NORTH: int = 0b0001  # bit 0
EAST: int = 0b0010   # bit 1
SOUTH: int = 0b0100  # bit 2
WEST: int = 0b1000   # bit 3

# Opposite wall for each direction
OPPOSITE: dict[int, int] = {
    NORTH: SOUTH,
    EAST: WEST,
    SOUTH: NORTH,
    WEST: EAST,
}

# Movement deltas (dr, dc) for each direction
DELTA: dict[int, Tuple[int, int]] = {
    NORTH: (-1, 0),
    EAST: (0, 1),
    SOUTH: (1, 0),
    WEST: (0, -1),
}

# Direction to letter
DIR_LETTER: dict[int, str] = {
    NORTH: "N",
    EAST: "E",
    SOUTH: "S",
    WEST: "W",
}

# Pixel patterns for "4" and "2" (7 rows x 4 cols, 1 = closed cell)
PATTERN_4: List[List[int]] = [
    [1, 0, 1, 0],
    [1, 0, 1, 0],
    [1, 1, 1, 1],
    [0, 0, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 0],
]

PATTERN_2: List[List[int]] = [
    [1, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 0],
    [1, 1, 1, 0],
    [1, 0, 0, 0],
    [1, 0, 0, 0],
    [1, 1, 1, 0],
]

PATTERN_HEIGHT: int = 7
PATTERN_4_WIDTH: int = 4
PATTERN_2_WIDTH: int = 4
PATTERN_GAP: int = 1
PATTERN_TOTAL_WIDTH: int = PATTERN_4_WIDTH + PATTERN_GAP + PATTERN_2_WIDTH  # 9


class MazeGenerator:
    """Generate a 2D maze with configurable algorithms and options.

    Args:
        width: Number of columns (cells). Must be >= 2.
        height: Number of rows (cells). Must be >= 2.
        entry: (x, y) coordinates of the entry cell. Defaults to (0, 0).
        exit_: (x, y) coordinates of the exit cell.
               Defaults to (width-1, height-1).
        perfect: If True, generates a perfect maze (exactly one path between
                 any two cells). If False, adds extra passages (loops).
        seed: Optional integer seed for reproducibility.
        algorithm: One of 'recursive_backtracker', 'prims', 'kruskals'.
                   Defaults to 'recursive_backtracker'.
        step_callback: Optional callable invoked after each wall removal.
                       Receives the current grid as argument. Useful for
                       animation.

    Attributes:
        grid: 2D list[list[int]] of wall bitmasks, indexed [row][col].
        solution: List of direction strings ('N','E','S','W') representing
                  the shortest path from entry to exit after generate().
        entry: (x, y) entry coordinates.
        exit_: (x, y) exit coordinates.
        width: Maze width in cells.
        height: Maze height in cells.
        forty_two_cells: Set of (row, col) cells used by the "42" pattern.

    Raises:
        ValueError: If parameters are invalid (out of bounds, same entry/exit,
                    unknown algorithm, dimensions too small).
    """

    ALGORITHMS: Tuple[str, ...] = (
        "recursive_backtracker",
        "prims",
        "kruskals",
    )

    def __init__(
        self,
        width: int = 20,
        height: int = 15,
        entry: Tuple[int, int] = (0, 0),
        exit_: Optional[Tuple[int, int]] = None,
        perfect: bool = True,
        seed: Optional[int] = None,
        algorithm: str = "recursive_backtracker",
        step_callback: Optional[Callable[[List[List[int]]], None]] = None,
    ) -> None:
        """Initialise the maze generator and validate parameters."""
        if width < 2 or height < 2:
            raise ValueError("Width and height must be at least 2.")
        if algorithm not in self.ALGORITHMS:
            raise ValueError(
                f"Unknown algorithm '{algorithm}'. "
                f"Choose from: {', '.join(self.ALGORITHMS)}"
            )

        self.width: int = width
        self.height: int = height
        self.entry: Tuple[int, int] = entry
        self.exit_: Tuple[int, int] = exit_ if exit_ is not None else (width - 1, height - 1)
        self.perfect: bool = perfect
        self.seed: Optional[int] = seed
        self.algorithm: str = algorithm
        self.step_callback: Optional[Callable[[List[List[int]]], None]] = step_callback

        ex, ey = self.entry
        xx, xy = self.exit_
        if not (0 <= ey < height and 0 <= ex < width):
            raise ValueError(f"Entry {self.entry} is out of bounds.")
        if not (0 <= xy < height and 0 <= xx < width):
            raise ValueError(f"Exit {self.exit_} is out of bounds.")
        if self.entry == self.exit_:
            raise ValueError("Entry and exit must be different cells.")

        self.grid: List[List[int]] = []
        self.solution: List[str] = []
        self.forty_two_cells: set[Tuple[int, int]] = set()
        self._rng: random.Random = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> None:
        """Generate the maze.

        Initialises a fully-walled grid, carves passages using the chosen
        algorithm, embeds the "42" pattern, enforces the corridor-width
        constraint, seals the outer border (except entry/exit), and finally
        solves for the shortest path.

        Raises:
            ValueError: If maze generation fails (should not happen with
                        valid parameters).
        """
        self._init_grid()
        self._place_forty_two()

        if self.algorithm == "recursive_backtracker":
            self._recursive_backtracker()
        elif self.algorithm == "prims":
            self._prims()
        elif self.algorithm == "kruskals":
            self._kruskals()

        if not self.perfect:
            self._add_loops()

        self._enforce_corridor_width()
        self._seal_border()
        self._open_entry_exit()
        self.solution = self._solve_bfs()

    # ------------------------------------------------------------------
    # Grid helpers
    # ------------------------------------------------------------------

    def _init_grid(self) -> None:
        """Create a fully-walled grid (all bits set to 1)."""
        self.grid = [
            [NORTH | EAST | SOUTH | WEST] * self.width
            for _ in range(self.height)
        ]

    def _carve(self, r: int, c: int, direction: int) -> None:
        """Remove the wall between (r, c) and its neighbour in direction.

        Args:
            r: Row of the source cell.
            c: Column of the source cell.
            direction: One of NORTH, EAST, SOUTH, WEST.
        """
        dr, dc = DELTA[direction]
        nr, nc = r + dr, c + dc
        self.grid[r][c] &= ~direction
        self.grid[nr][nc] &= ~OPPOSITE[direction]
        if self.step_callback is not None:
            self.step_callback(self.grid)

    def _in_bounds(self, r: int, c: int) -> bool:
        """Return True if (r, c) is inside the grid."""
        return 0 <= r < self.height and 0 <= c < self.width

    def _unvisited_neighbours(
        self, r: int, c: int, visited: List[List[bool]]
    ) -> List[Tuple[int, int, int]]:
        """Return list of (nr, nc, direction) for unvisited in-bounds neighbours."""
        result: List[Tuple[int, int, int]] = []
        for direction, (dr, dc) in DELTA.items():
            nr, nc = r + dr, c + dc
            if self._in_bounds(nr, nc) and not visited[nr][nc]:
                result.append((nr, nc, direction))
        return result

    # ------------------------------------------------------------------
    # "42" pattern
    # ------------------------------------------------------------------

    def _place_forty_two(self) -> None:
        """Embed the "42" pattern into the grid as fully closed cells.

        The pattern is placed roughly in the centre of the maze. If the
        maze is too small to fit it, a message is printed and no pattern
        is placed.
        """
        min_w = PATTERN_TOTAL_WIDTH + 2
        min_h = PATTERN_HEIGHT + 2
        if self.width < min_w or self.height < min_h:
            print(
                "Warning: maze is too small to display the '42' pattern "
                f"(need at least {min_w}x{min_h})."
            )
            return

        start_r = (self.height - PATTERN_HEIGHT) // 2
        start_c = (self.width - PATTERN_TOTAL_WIDTH) // 2

        self.forty_two_cells = set()
        for pr in range(PATTERN_HEIGHT):
            for pc in range(PATTERN_4_WIDTH):
                if PATTERN_4[pr][pc]:
                    self.forty_two_cells.add((start_r + pr, start_c + pc))
            for pc in range(PATTERN_2_WIDTH):
                if PATTERN_2[pr][pc]:
                    col = start_c + PATTERN_4_WIDTH + PATTERN_GAP + pc
                    self.forty_two_cells.add((start_r + pr, col))

        # For each "42" cell: close walls that face outside the pattern,
        # open walls that face another "42" cell (solid continuous block).
        for r, c in self.forty_two_cells:
            mask = 0
            for direction, (dr, dc) in DELTA.items():
                nr, nc = r + dr, c + dc
                if (nr, nc) not in self.forty_two_cells:
                    mask |= direction
            self.grid[r][c] = mask

    # ------------------------------------------------------------------
    # Algorithm: Recursive Backtracker (iterative DFS)
    # ------------------------------------------------------------------

    def _recursive_backtracker(self) -> None:
        """Carve passages using iterative depth-first search.

        Produces mazes with long winding corridors and few dead ends.
        """
        visited: List[List[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        # Pre-mark "42" cells as visited so they are never carved into
        for r, c in self.forty_two_cells:
            visited[r][c] = True

        sr, sc = self.entry[1], self.entry[0]
        visited[sr][sc] = True
        stack: List[Tuple[int, int]] = [(sr, sc)]

        while stack:
            r, c = stack[-1]
            neighbours = self._unvisited_neighbours(r, c, visited)
            if neighbours:
                nr, nc, direction = self._rng.choice(neighbours)
                self._carve(r, c, direction)
                visited[nr][nc] = True
                stack.append((nr, nc))
            else:
                stack.pop()

        # Connect any remaining unvisited non-42 cells
        self._connect_isolated(visited)

    # ------------------------------------------------------------------
    # Algorithm: Randomised Prim's
    # ------------------------------------------------------------------

    def _prims(self) -> None:
        """Carve passages using randomised Prim's algorithm.

        Grows the maze from a random starting cell by maintaining a
        frontier list. Produces more branchy mazes than DFS.
        """
        visited: List[List[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        for r, c in self.forty_two_cells:
            visited[r][c] = True

        sr, sc = self.entry[1], self.entry[0]
        visited[sr][sc] = True

        # Frontier: list of (nr, nc, from_r, from_c, direction)
        frontier: List[Tuple[int, int, int, int, int]] = []

        def add_frontier(r: int, c: int) -> None:
            for direction, (dr, dc) in DELTA.items():
                nr, nc = r + dr, c + dc
                if self._in_bounds(nr, nc) and not visited[nr][nc]:
                    frontier.append((nr, nc, r, c, direction))

        add_frontier(sr, sc)

        while frontier:
            idx = self._rng.randrange(len(frontier))
            nr, nc, fr, fc, direction = frontier[idx]
            frontier[idx] = frontier[-1]
            frontier.pop()

            if visited[nr][nc]:
                continue

            self._carve(fr, fc, direction)
            visited[nr][nc] = True
            add_frontier(nr, nc)

        self._connect_isolated(visited)

    # ------------------------------------------------------------------
    # Algorithm: Randomised Kruskal's
    # ------------------------------------------------------------------

    def _kruskals(self) -> None:
        """Carve passages using randomised Kruskal's algorithm.

        Shuffles all internal edges and opens them if they connect two
        different components (union-find). Produces highly uniform mazes.
        """
        parent: List[int] = list(range(self.width * self.height))
        rank: List[int] = [0] * (self.width * self.height)

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> bool:
            ra, rb = find(a), find(b)
            if ra == rb:
                return False
            if rank[ra] < rank[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            if rank[ra] == rank[rb]:
                rank[ra] += 1
            return True

        # Mark "42" cells as a single super-component
        forty_two_ids = [r * self.width + c for r, c in self.forty_two_cells]
        if forty_two_ids:
            for cell_id in forty_two_ids[1:]:
                union(forty_two_ids[0], cell_id)

        # Build all internal edges (going only SOUTH and EAST to avoid duplication)
        edges: List[Tuple[int, int, int, int]] = []
        for r in range(self.height):
            for c in range(self.width):
                if (r, c) in self.forty_two_cells:
                    continue
                if r + 1 < self.height and (r + 1, c) not in self.forty_two_cells:
                    edges.append((r, c, r + 1, c))
                if c + 1 < self.width and (r, c + 1) not in self.forty_two_cells:
                    edges.append((r, c, r, c + 1))

        self._rng.shuffle(edges)

        for r, c, nr, nc in edges:
            a = r * self.width + c
            b = nr * self.width + nc
            if union(a, b):
                direction = SOUTH if nr == r + 1 else EAST
                self._carve(r, c, direction)

        # Connect remaining isolated cells
        visited: List[List[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        for r, c in self.forty_two_cells:
            visited[r][c] = True
        for r in range(self.height):
            for c in range(self.width):
                if (r, c) not in self.forty_two_cells:
                    # A cell is connected if it has at least one open wall
                    # to a non-42 neighbour
                    if self.grid[r][c] != (NORTH | EAST | SOUTH | WEST):
                        visited[r][c] = True
        self._connect_isolated(visited)

    # ------------------------------------------------------------------
    # Connectivity helpers
    # ------------------------------------------------------------------

    def _connect_isolated(self, visited: List[List[bool]]) -> None:
        """Connect any unvisited (isolated) non-42 cells to the maze.

        Iterates over all unvisited cells and carves a passage to the
        nearest visited neighbour, ensuring full connectivity.

        Args:
            visited: 2D boolean grid of already-visited cells.
        """
        for r in range(self.height):
            for c in range(self.width):
                if visited[r][c] or (r, c) in self.forty_two_cells:
                    continue
                # Find a visited neighbour to connect to
                neighbours = []
                for direction, (dr, dc) in DELTA.items():
                    nr, nc = r + dr, c + dc
                    if (
                        self._in_bounds(nr, nc)
                        and visited[nr][nc]
                        and (nr, nc) not in self.forty_two_cells
                    ):
                        neighbours.append((nr, nc, direction))
                if neighbours:
                    _, _, direction = self._rng.choice(neighbours)
                    self._carve(r, c, direction)
                    visited[r][c] = True

    # ------------------------------------------------------------------
    # Post-processing
    # ------------------------------------------------------------------

    def _add_loops(self) -> None:
        """Add random extra passages to create an imperfect (loopy) maze.

        Removes approximately 15% of remaining internal walls to create
        multiple paths between cells.
        """
        internal_walls: List[Tuple[int, int, int]] = []
        for r in range(self.height):
            for c in range(self.width):
                if (r, c) in self.forty_two_cells:
                    continue
                for direction in (SOUTH, EAST):
                    dr, dc = DELTA[direction]
                    nr, nc = r + dr, c + dc
                    if (
                        self._in_bounds(nr, nc)
                        and (nr, nc) not in self.forty_two_cells
                        and self.grid[r][c] & direction
                    ):
                        internal_walls.append((r, c, direction))

        n_extra = max(1, len(internal_walls) // 7)
        self._rng.shuffle(internal_walls)
        for r, c, direction in internal_walls[:n_extra]:
            self._carve(r, c, direction)

    def _enforce_corridor_width(self) -> None:
        """Ensure no 3x3 (or larger) open area exists in the maze.

        Scans all 3x3 windows. If all 9 cells in a window are mutually
        open (forming a fully open area), it re-walls the centre cell's
        internal passages to break the opening.
        """
        for r in range(self.height - 2):
            for c in range(self.width - 2):
                # Check if all cells in this 3x3 block are connected to each other
                if self._is_open_3x3(r, c):
                    # Close the passage between centre and its south/east neighbours
                    cr, cc = r + 1, c + 1
                    if (cr, cc) not in self.forty_two_cells:
                        self.grid[cr][cc] |= SOUTH
                        self.grid[cr + 1][cc] |= NORTH
                        self.grid[cr][cc] |= EAST
                        self.grid[cr][cc + 1] |= WEST

    def _is_open_3x3(self, r: int, c: int) -> bool:
        """Return True if the 3x3 block starting at (r, c) is fully open.

        A block is considered "fully open" if each cell in the block has
        open walls towards all its neighbours within the block.

        Args:
            r: Top row of the 3x3 block.
            c: Left column of the 3x3 block.
        """
        # Check horizontal connections (East walls) within block
        for br in range(r, r + 3):
            for bc in range(c, c + 2):
                if self.grid[br][bc] & EAST:
                    return False
        # Check vertical connections (South walls) within block
        for br in range(r, r + 2):
            for bc in range(c, c + 3):
                if self.grid[br][bc] & SOUTH:
                    return False
        return True

    def _seal_border(self) -> None:
        """Ensure all outer-border cells have their outer walls closed.

        This enforces that there are no accidental openings on the
        perimeter of the maze (entry/exit openings are added separately).
        """
        for c in range(self.width):
            self.grid[0][c] |= NORTH
            self.grid[self.height - 1][c] |= SOUTH
        for r in range(self.height):
            self.grid[r][0] |= WEST
            self.grid[r][self.width - 1] |= EAST

    def _open_entry_exit(self) -> None:
        """Open the outer walls at the entry and exit cells.

        Entry is on the North wall of its cell (top border assumed) if it
        is on the top row, otherwise the West wall. Exit uses the South
        or East wall similarly.
        """
        ex, ey = self.entry
        xx, xy = self.exit_

        # Entry: open the border wall facing outward
        if ey == 0:
            self.grid[ey][ex] &= ~NORTH
        elif ey == self.height - 1:
            self.grid[ey][ex] &= ~SOUTH
        elif ex == 0:
            self.grid[ey][ex] &= ~WEST
        else:
            self.grid[ey][ex] &= ~EAST

        # Exit: open the border wall facing outward
        if xy == self.height - 1:
            self.grid[xy][xx] &= ~SOUTH
        elif xy == 0:
            self.grid[xy][xx] &= ~NORTH
        elif xx == self.width - 1:
            self.grid[xy][xx] &= ~EAST
        else:
            self.grid[xy][xx] &= ~WEST

    # ------------------------------------------------------------------
    # Solver: BFS shortest path
    # ------------------------------------------------------------------

    def _solve_bfs(self) -> List[str]:
        """Find the shortest path from entry to exit using BFS.

        Returns:
            List of direction strings ('N', 'E', 'S', 'W') representing
            the shortest valid path from entry to exit.

        Raises:
            ValueError: If no path exists between entry and exit.
        """
        ex, ey = self.entry
        xx, xy = self.exit_

        start = (ey, ex)
        goal = (xy, xx)

        prev: dict[Tuple[int, int], Optional[Tuple[Tuple[int, int], int]]] = {
            start: None
        }
        queue: deque[Tuple[int, int]] = deque([start])

        while queue:
            r, c = queue.popleft()
            if (r, c) == goal:
                break
            for direction, (dr, dc) in DELTA.items():
                nr, nc = r + dr, c + dc
                if (
                    self._in_bounds(nr, nc)
                    and (nr, nc) not in prev
                    and not (self.grid[r][c] & direction)
                ):
                    prev[(nr, nc)] = ((r, c), direction)
                    queue.append((nr, nc))

        if goal not in prev:
            raise ValueError(
                f"No path found from entry {self.entry} to exit {self.exit_}."
            )

        # Reconstruct path
        path: List[str] = []
        current: Tuple[int, int] = goal
        while prev[current] is not None:
            parent_info = prev[current]
            assert parent_info is not None
            parent, direction = parent_info
            path.append(DIR_LETTER[direction])
            current = parent

        path.reverse()
        return path
