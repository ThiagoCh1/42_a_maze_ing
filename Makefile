PYTHON = python3
MAIN   = a_maze_ing.py
CONFIG = config.txt

.PHONY: install run debug clean lint lint-strict build

install:
	$(PYTHON) -m pip install ".[dev]" --user

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name "dist"        -exec rm -rf {} + 2>/dev/null; \
	find . -type d -name "*.egg-info"  -exec rm -rf {} + 2>/dev/null; \
	echo "Cleaned."

lint:
	flake8 .
	$(PYTHON) -m mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	flake8 .
	$(PYTHON) -m mypy . --strict

build:
	$(PYTHON) -m build
