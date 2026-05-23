"""Configuration file parser for A-Maze-ing.

Reads a KEY=VALUE configuration file and returns a validated MazeConfig.

Format:
    WIDTH=20
    HEIGHT=15
    ENTRY=0,0
    EXIT=19,14
    OUTPUT_FILE=maze.txt
    PERFECT=True
    # Optional
    SEED=42
    ALGORITHM=recursive_backtracker
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


VALID_ALGORITHMS = ("recursive_backtracker", "prims", "kruskals")


@dataclass
class MazeConfig:
    """Validated maze configuration.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        entry: (x, y) entry coordinates.
        exit_: (x, y) exit coordinates.
        output_file: Path to the output file.
        perfect: Whether to generate a perfect maze.
        seed: Optional RNG seed for reproducibility.
        algorithm: Generation algorithm name.
    """

    width: int
    height: int
    entry: Tuple[int, int]
    exit_: Tuple[int, int]
    output_file: str
    perfect: bool
    seed: Optional[int] = field(default=None)
    algorithm: str = field(default="recursive_backtracker")


class ConfigParser:
    """Parse and validate a maze configuration file."""

    REQUIRED_KEYS = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}

    @staticmethod
    def load(path: str) -> MazeConfig:
        """Load and validate a configuration file.

        Args:
            path: Path to the configuration file.

        Returns:
            A validated MazeConfig instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file contains invalid or missing keys.
        """
        raw: dict[str, str] = {}

        try:
            with open(path, "r") as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        raise ValueError(
                            f"Line {lineno}: expected KEY=VALUE, got: {line!r}"
                        )
                    key, _, value = line.partition("=")
                    key = key.strip().upper()
                    value = value.strip()
                    if not key:
                        raise ValueError(f"Line {lineno}: empty key.")
                    raw[key] = value
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {path!r}")

        missing = ConfigParser.REQUIRED_KEYS - raw.keys()
        if missing:
            raise ValueError(f"Missing required keys: {', '.join(sorted(missing))}")

        # Parse WIDTH / HEIGHT
        try:
            width = int(raw["WIDTH"])
            height = int(raw["HEIGHT"])
        except ValueError:
            raise ValueError("WIDTH and HEIGHT must be integers.")
        if width < 2 or height < 2:
            raise ValueError("WIDTH and HEIGHT must be at least 2.")

        # Parse ENTRY / EXIT
        entry = ConfigParser._parse_coord("ENTRY", raw["ENTRY"], width, height)
        exit_ = ConfigParser._parse_coord("EXIT", raw["EXIT"], width, height)
        if entry == exit_:
            raise ValueError("ENTRY and EXIT must be different cells.")

        # Parse OUTPUT_FILE
        output_file = raw["OUTPUT_FILE"]
        if not output_file:
            raise ValueError("OUTPUT_FILE must not be empty.")

        # Parse PERFECT
        perfect_raw = raw["PERFECT"].strip().lower()
        if perfect_raw not in ("true", "false"):
            raise ValueError("PERFECT must be 'True' or 'False'.")
        perfect = perfect_raw == "true"

        # Parse optional SEED
        seed: Optional[int] = None
        if "SEED" in raw:
            try:
                seed = int(raw["SEED"])
            except ValueError:
                raise ValueError("SEED must be an integer.")

        # Parse optional ALGORITHM
        algorithm = raw.get("ALGORITHM", "recursive_backtracker").strip().lower()
        if algorithm not in VALID_ALGORITHMS:
            raise ValueError(
                f"Unknown ALGORITHM '{algorithm}'. "
                f"Choose from: {', '.join(VALID_ALGORITHMS)}"
            )

        return MazeConfig(
            width=width,
            height=height,
            entry=entry,
            exit_=exit_,
            output_file=output_file,
            perfect=perfect,
            seed=seed,
            algorithm=algorithm,
        )

    @staticmethod
    def _parse_coord(
        key: str, value: str, width: int, height: int
    ) -> Tuple[int, int]:
        """Parse and validate a coordinate string 'x,y'.

        Args:
            key: Key name (for error messages).
            value: Raw string value to parse.
            width: Maze width for bounds check.
            height: Maze height for bounds check.

        Returns:
            Tuple (x, y).

        Raises:
            ValueError: If the coordinate is malformed or out of bounds.
        """
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError(f"{key} must be in format x,y — got: {value!r}")
        try:
            x, y = int(parts[0].strip()), int(parts[1].strip())
        except ValueError:
            raise ValueError(f"{key} coordinates must be integers — got: {value!r}")
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(
                f"{key} ({x},{y}) is out of bounds for maze {width}x{height}."
            )
        return (x, y)
