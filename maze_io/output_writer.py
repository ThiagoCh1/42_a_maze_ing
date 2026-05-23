"""Output file writer for A-Maze-ing.

Writes the maze grid and solution to a file in the required format:
- One hexadecimal digit per cell, row by row.
- An empty line separator.
- Entry coordinates (x,y).
- Exit coordinates (x,y).
- Shortest path as a string of N/E/S/W characters.
"""

from __future__ import annotations

from mazegen.generator import MazeGenerator


class OutputWriter:
    """Write a generated maze to a file in the subject-specified format.

    Args:
        generator: A MazeGenerator instance after generate() has been called.
    """

    def __init__(self, generator: MazeGenerator) -> None:
        """Initialise the writer with a generated maze.

        Args:
            generator: MazeGenerator with a completed grid and solution.
        """
        self._gen = generator

    def write(self, path: str) -> None:
        """Write the maze to a file.

        The file format is:
            <hex grid, one row per line>
            <empty line>
            <entry x,y>
            <exit x,y>
            <solution path>

        Args:
            path: Destination file path.

        Raises:
            OSError: If the file cannot be written.
        """
        gen = self._gen
        with open(path, "w", newline="\n") as f:
            for row in gen.grid:
                f.write("".join(format(cell, "X") for cell in row) + "\n")
            f.write("\n")
            f.write(f"{gen.entry[0]},{gen.entry[1]}\n")
            f.write(f"{gen.exit_[0]},{gen.exit_[1]}\n")
            f.write("".join(gen.solution) + "\n")
