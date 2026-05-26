"""Terminal ASCII renderer for A-Maze-ing.

Character cells in most terminals are ~2x taller than wide.
To get square-looking corridors and thin walls we use:
    - corridor: 2 chars wide, 1 line tall
    - wall:     1 char  wide, 1 line tall

Canvas grid: (2h+1) rows x (2w+1) cols — same as before,
but wall cols print as 1 char and corridor cols print as 2 chars.
All rows are 1 line tall (uniform height).
This gives corridors that are ~2 chars x ~2 char-heights = roughly square.
"""

from __future__ import annotations

import os
import sys
from typing import List, Tuple

from mazegen.generator import MazeGenerator, DELTA

RESET = "\033[0m"
NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8


def _bg(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


COLOUR_SETS: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = [
    ((220, 220, 220), (0, 0, 0)),
    ((180, 120, 40),  (0, 0, 0)),
    ((40, 160, 80),   (0, 0, 0)),
    ((60, 120, 200),  (0, 0, 0)),
    ((180, 50, 50),   (0, 0, 0)),
]

COLOUR_ENTRY = (200, 50, 200)
COLOUR_EXIT = (200, 50, 50)
COLOUR_PATH = (50, 180, 200)
COLOUR_42 = (100, 100, 100)  # dark grey — distinct from walls, looks blocked


class TerminalRenderer:
    def __init__(self, generator: MazeGenerator) -> None:
        self._gen = generator
        self._show_path = False
        self._colour_idx = 0
        self._path_cells: set[Tuple[int, int]] = set()
        self._path_passages: set[Tuple[int, int]] = set()
        self._compute_path()

    def run(self) -> None:
        self._render()
        while True:
            self._print_menu()
            choice = input("Choice (1-4): ").strip()
            if choice == "1":
                self._regenerate()
            elif choice == "2":
                self._show_path = not self._show_path
                self._render()
            elif choice == "3":
                self._colour_idx = (self._colour_idx + 1) % len(COLOUR_SETS)
                self._render()
            elif choice == "4":
                print("Bye!")
                sys.exit(0)
            else:
                print("  Invalid choice.")

    def _compute_path(self) -> None:
        gen = self._gen
        self._path_cells = set()
        self._path_passages = set()
        dir_map = {"N": NORTH, "E": EAST, "S": SOUTH, "W": WEST}
        r, c = gen.entry[1], gen.entry[0]
        self._path_cells.add((r, c))

        for step in gen.solution:
            d = dir_map[step]
            dr, dc = DELTA[d]

            # passage pixel in the (2h+1)x(2w+1) grid
            if d == NORTH:
                pp = (2 * r, 2 * c + 1)
            elif d == SOUTH:
                pp = (2 * r + 2, 2 * c + 1)
            elif d == EAST:
                pp = (2 * r + 1, 2 * c + 2)
            else:
                pp = (2 * r + 1, 2 * c)

            self._path_passages.add(pp)
            r, c = r + dr, c + dc
            self._path_cells.add((r, c))

    def _regenerate(self) -> None:
        import random
        gen = MazeGenerator(
            width=self._gen.width,
            height=self._gen.height,
            entry=self._gen.entry,
            exit_=self._gen.exit_,
            perfect=self._gen.perfect,
            seed=random.randint(0, 2**31),
            algorithm=self._gen.algorithm,
        )
        gen.generate()
        self._gen = gen
        self._show_path = False
        self._compute_path()
        self._render()

    def _render(self) -> None:
        _clear()
        gen = self._gen
        wall_rgb, floor_rgb = COLOUR_SETS[self._colour_idx]

        h, w = gen.height, gen.width
        g = gen.grid

        # Canvas: (2h+1) rows x (2w+1) cols
        # canvas[pr][pc] = RGB tuple
        rows = 2 * h + 1
        cols = 2 * w + 1
        canvas: List[List[Tuple[int, int, int]]] = [
            [wall_rgb] * cols for _ in range(rows)
        ]

        # Fill cell interiors (odd row, odd col) with floor
        for r in range(h):
            for c in range(w):
                canvas[2*r+1][2*c+1] = floor_rgb

        # Open passages
        for r in range(h):
            for c in range(w):
                cell = g[r][c]
                if r > 0 and not (cell & NORTH):
                    canvas[2 * r][2 * c + 1] = floor_rgb

                if r < h - 1 and not (cell & SOUTH):
                    canvas[2 * r + 2][2 * c + 1] = floor_rgb

                if c < w - 1 and not (cell & EAST):
                    canvas[2 * r + 1][2 * c + 2] = floor_rgb

                if c > 0 and not (cell & WEST):
                    canvas[2 * r + 1][2 * c] = floor_rgb
        # Outer openings
        ex, ey = gen.entry
        xx, xy = gen.exit_
        if ey == 0:
            canvas[0][2 * ex + 1] = floor_rgb
        elif ex == 0:
            canvas[2 * ey + 1][0] = floor_rgb
        if xy == h - 1:
            canvas[2 * h][2 * xx + 1] = floor_rgb
        elif xx == w - 1:
            canvas[2 * xy + 1][2 * w] = floor_rgb

        # "42" — fill interior with COLOUR_42 (distinct blocked corridor)
        for r, c in gen.forty_two_cells:
            canvas[2*r+1][2*c+1] = COLOUR_42
            # fill passage pixels to adjacent 42 cells
            for direction, (dr, dc) in DELTA.items():
                nr, nc = r+dr, c+dc
                if (nr, nc) in gen.forty_two_cells:
                    if direction == NORTH:
                        pr2, pc2 = 2 * r, 2 * c + 1
                    elif direction == SOUTH:
                        pr2, pc2 = 2 * r + 2, 2 * c + 1
                    elif direction == EAST:
                        pr2, pc2 = 2 * r + 1, 2 * c + 2
                    else:
                        pr2, pc2 = 2 * r + 1, 2 * c
                    canvas[pr2][pc2] = COLOUR_42
        # Solution path
        if self._show_path:
            for r, c in self._path_cells:
                if (r, c) not in gen.forty_two_cells:
                    canvas[2*r+1][2*c+1] = COLOUR_PATH
            for pr2, pc2 in self._path_passages:
                if canvas[pr2][pc2] == floor_rgb:
                    canvas[pr2][pc2] = COLOUR_PATH

        # Entry / Exit on top
        canvas[2*ey+1][2*ex+1] = COLOUR_ENTRY
        canvas[2*xy+1][2*xx+1] = COLOUR_EXIT

        # ── Print ────────────────────────────────────────────────────────────
        # col pc: even = wall col (1 char), odd = corridor col (2 chars)
        # all rows: 1 line tall
        lines: List[str] = []
        for pr in range(rows):
            line = ""
            for pc in range(cols):
                w2 = 1 if pc % 2 == 0 else 2
                line += _bg(*canvas[pr][pc]) + " " * w2 + RESET
            lines.append(line)

        print("\n".join(lines))

        wr, wg, wb = wall_rgb
        print()
        print(
            f"  {_bg(*COLOUR_ENTRY)}  {RESET} Entry  "
            f"{_bg(*COLOUR_EXIT)}  {RESET} Exit  "
            f"{_bg(*COLOUR_PATH)}  {RESET} Path  "
            f"{_bg(*COLOUR_42)}  {RESET} 42  "
            f"{_bg(wr,wg,wb)}  {RESET} Wall"
        )

    def _print_menu(self) -> None:
        path_label = "Hide" if self._show_path else "Show"
        print()
        print("=== A-Maze-ing ===")
        print("1. Re-generate a new maze")
        print(f"2. {path_label} path from entry to exit")
        print("3. Rotate maze wall colours")
        print("4. Quit")


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")
