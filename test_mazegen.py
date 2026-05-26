"""Manual test script for mazegen.generator.MazeGenerator.

Run with:
    python3 test_mazegen.py

Does NOT require pytest. Prints a summary of every check.
"""

from collections import deque
from typing import List, Set, Tuple

from mazegen.generator import MazeGenerator

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
DELTA = {NORTH: (-1, 0), EAST: (0, 1), SOUTH: (1, 0), WEST: (0, -1)}

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

results: List[Tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    label = PASS if condition else FAIL
    print(f"  [{label}] {name}" + (f" — {detail}" if detail else ""))
    results.append((name, condition, detail))


# ── helpers ──────────────────────────────────────────────────────────────────

def wall_coherence_errors(gen: MazeGenerator) -> int:
    """Count cells whose wall encoding disagrees with their neighbours."""
    errors = 0
    g, h, w = gen.grid, gen.height, gen.width
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if r > 0 and (v & NORTH) != ((g[r - 1][c] >> 2) & 1):
                errors += 1
            if c < w - 1 and ((v >> 1) & 1) != ((g[r][c + 1] >> 3) & 1):
                errors += 1
            if r < h - 1 and ((v >> 2) & 1) != (g[r + 1][c] & 1):
                errors += 1
            if c > 0 and ((v >> 3) & 1) != ((g[r][c - 1] >> 1) & 1):
                errors += 1
    return errors


def reachable_cells(gen: MazeGenerator) -> Set[Tuple[int, int]]:
    """BFS from entry; return all reachable (row, col) cells."""
    g, h, w = gen.grid, gen.height, gen.width
    start = (gen.entry[1], gen.entry[0])
    visited: Set[Tuple[int, int]] = {start}
    queue: deque[Tuple[int, int]] = deque([start])
    while queue:
        r, c = queue.popleft()
        for d, (dr, dc) in DELTA.items():
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and (nr, nc) not in visited
                and not (g[r][c] & d)
            ):
                visited.add((nr, nc))
                queue.append((nr, nc))
    return visited


def count_open_3x3(gen: MazeGenerator) -> int:
    """Count 3x3 windows where all internal walls are open."""
    g, h, w = gen.grid, gen.height, gen.width
    count = 0
    for r in range(h - 2):
        for c in range(w - 2):
            ok = True
            for br in range(r, r + 3):
                for bc in range(c, c + 2):
                    if g[br][bc] & EAST:
                        ok = False
            for br in range(r, r + 2):
                for bc in range(c, c + 3):
                    if g[br][bc] & SOUTH:
                        ok = False
            if ok:
                count += 1
    return count


def count_carved_edges(gen: MazeGenerator) -> int:
    g, h, w = gen.grid, gen.height, gen.width
    edges = 0
    for r in range(h):
        for c in range(w):
            if c < w - 1 and not (g[r][c] & EAST):
                edges += 1
            if r < h - 1 and not (g[r][c] & SOUTH):
                edges += 1
    return edges


def run_standard_checks(gen: MazeGenerator, label: str) -> None:
    """Run the full suite of checks on a generated maze."""
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")

    # 1. Wall coherence
    errors = wall_coherence_errors(gen)
    check("Wall coherence (neighbour agreement)",
          errors == 0, f"{errors} errors")

    # 2. Full connectivity (all non-42 cells reachable from entry)
    reached = reachable_cells(gen)
    non_42 = {
        (r, c)
        for r in range(gen.height)
        for c in range(gen.width)
        if (r, c) not in gen.forty_two_cells
    }
    unreachable = non_42 - reached
    check("Full connectivity", len(unreachable) == 0,
          f"{len(unreachable)} unreachable cells")

    # 3. Exit is reachable
    exit_cell = (gen.exit_[1], gen.exit_[0])
    check("Exit is reachable", exit_cell in reached)

    # 4. Solution path exists and is non-empty
    check("Solution path non-empty",
          len(gen.solution) > 0, f"{len(gen.solution)} steps")

    # 5. Solution path is valid (walk it and verify no wall crossed)
    g = gen.grid
    r, c = gen.entry[1], gen.entry[0]
    valid_path = True
    dir_map = {"N": NORTH, "E": EAST, "S": SOUTH, "W": WEST}
    for step in gen.solution:
        d = dir_map[step]
        if g[r][c] & d:
            valid_path = False
            break
        dr, dc = DELTA[d]
        r, c = r + dr, c + dc
    reached_exit = (r, c) == (gen.exit_[1], gen.exit_[0])
    check("Solution path walks through open walls", valid_path)
    check("Solution path ends at exit", reached_exit)

    # 6. No 3x3 open areas
    open3 = count_open_3x3(gen)
    check("No 3x3 open areas", open3 == 0, f"{open3} found")

    # 7. Outer border sealed (except entry/exit outer walls)
    border_ok = True
    h, w = gen.height, gen.width
    for c2 in range(w):
        if c2 != gen.entry[0] and c2 != gen.exit_[0]:
            if not (g[0][c2] & NORTH):
                border_ok = False
            if not (g[h - 1][c2] & SOUTH):
                border_ok = False
    for r2 in range(h):
        if r2 != gen.entry[1] and r2 != gen.exit_[1]:
            if not (g[r2][0] & WEST):
                border_ok = False
            if not (g[r2][w - 1] & EAST):
                border_ok = False
    check("Outer border sealed", border_ok)

    # 8. "42" cells are fully closed
    all_closed = all(
        g[r2][c2] == (NORTH | EAST | SOUTH | WEST)
        for r2, c2 in gen.forty_two_cells
    )
    check(
        "42 pattern cells are fully walled",
        all_closed,
        f"{len(gen.forty_two_cells)} cells",
    )

    # 9. Perfect maze check (spanning tree: edges == reachable - 1)
    if gen.perfect:
        edges = count_carved_edges(gen)
        n = len(non_42)
        check(
            "Perfect maze (spanning tree)",
            edges == n - 1,
            f"edges={edges}, non-42 cells={n}",
        )
    else:
        edges = count_carved_edges(gen)
        n = len(non_42)
        check(
            "Imperfect maze has extra edges",
            edges > n - 1,
            f"edges={edges}, non-42 cells={n}",
        )

    # 10. Reproducibility: same seed → same grid
    gen2 = MazeGenerator(
        width=gen.width,
        height=gen.height,
        entry=gen.entry,
        exit_=gen.exit_,
        perfect=gen.perfect,
        seed=gen.seed,
        algorithm=gen.algorithm,
    )
    gen2.generate()
    same = gen.grid == gen2.grid
    check("Reproducibility (same seed → same grid)", same)


# ── test cases ───────────────

def main() -> None:
    print("=" * 60)
    print("  mazegen test suite")
    print("=" * 60)

    # --- Standard 20x15, recursive backtracker, perfect ---
    gen = MazeGenerator(width=20, height=15,
                        entry=(0, 0), exit_=(19, 14), seed=42)
    gen.generate()
    run_standard_checks(
        gen, "20x15 | recursive_backtracker | perfect | seed=42"
    )

    # --- Prim's ---
    gen = MazeGenerator(
        width=20, height=15, entry=(0, 0), exit_=(19, 14),
        seed=7, algorithm="prims"
    )
    gen.generate()
    run_standard_checks(gen, "20x15 | prims | perfect | seed=7")

    # --- Kruskal's ---
    gen = MazeGenerator(
        width=20, height=15, entry=(0, 0), exit_=(19, 14),
        seed=7, algorithm="kruskals"
    )
    gen.generate()
    run_standard_checks(gen, "20x15 | kruskals | perfect | seed=7")

    # --- Imperfect maze ---
    gen = MazeGenerator(
        width=20, height=15, entry=(0, 0), exit_=(19, 14),
        seed=99, perfect=False
    )
    gen.generate()
    run_standard_checks(
        gen, "20x15 | recursive_backtracker | imperfect | seed=99"
    )

    # --- Large maze ---
    gen = MazeGenerator(
        width=50, height=40, entry=(0, 0), exit_=(49, 39), seed=123
    )
    gen.generate()
    run_standard_checks(
        gen, "50x40 | recursive_backtracker | perfect | seed=123"
    )

    # --- Small maze (too small for 42 pattern) ---
    print(f"\n{'─' * 60}")
    print("  5x5 | too small for 42 pattern (expect warning)")
    print(f"{'─' * 60}")
    gen_small = MazeGenerator(
        width=5, height=5, entry=(0, 0), exit_=(4, 4), seed=1
    )
    gen_small.generate()
    check("42 cells empty on small maze", len(gen_small.forty_two_cells) == 0)
    check("Still generates solution", len(gen_small.solution) > 0)
    # --- Error handling ---
    print(f"\n{'─' * 60}")
    print("  Error handling")
    print(f"{'─' * 60}")

    try:
        MazeGenerator(width=1, height=15)
        check("Rejects width < 2", False)
    except ValueError:
        check("Rejects width < 2", True)

    try:
        MazeGenerator(width=20, height=15, entry=(0, 0), exit_=(0, 0))
        check("Rejects same entry and exit", False)
    except ValueError:
        check("Rejects same entry and exit", True)

    try:
        MazeGenerator(width=20, height=15, entry=(99, 99))
        check("Rejects out-of-bounds entry", False)
    except ValueError:
        check("Rejects out-of-bounds entry", True)

    try:
        MazeGenerator(width=20, height=15, algorithm="dijkstra")
        check("Rejects unknown algorithm", False)
    except ValueError:
        check("Rejects unknown algorithm", True)

    # --- Summary ---
    print(f"\n{'=' * 60}")
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed
    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  |  \033[31m{failed} FAILED\033[0m")
        print("\n  Failed checks:")
        for name, ok, detail in results:
            if not ok:
                print(f"    - {name}" + (f" ({detail})" if detail else ""))
    else:
        print("  |  \033[32mAll good!\033[0m")
    print("=" * 60)


if __name__ == "__main__":
    main()
