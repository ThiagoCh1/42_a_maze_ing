"""A-Maze-ing: maze generator entry point.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys

from maze_io.config_parser import ConfigParser, MazeConfig
from maze_io.output_writer import OutputWriter
from mazegen.generator import MazeGenerator
from renderer.terminal import TerminalRenderer


def main() -> None:
    """Run the maze generator from a config file.

    Reads configuration, generates the maze, writes output file,
    and launches the interactive terminal renderer.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py <config_file>")
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        config: MazeConfig = ConfigParser.load(config_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    try:
        generator = MazeGenerator(
            width=config.width,
            height=config.height,
            entry=config.entry,
            exit_=config.exit_,
            perfect=config.perfect,
            seed=config.seed,
            algorithm=config.algorithm,
        )
        generator.generate()
    except ValueError as e:
        print(f"Maze generation error: {e}")
        sys.exit(1)

    try:
        writer = OutputWriter(generator)
        writer.write(config.output_file)
    except OSError as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

    renderer = TerminalRenderer(generator)
    renderer.run()


if __name__ == "__main__":
    main()
