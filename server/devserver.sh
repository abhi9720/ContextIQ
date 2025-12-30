#!/bin/sh
set -e # exit on error
set -x # print commands

# Get the directory where the script is located.
SCRIPT_DIR=$(dirname "$0")

# The path to the python executable in the virtual environment
PYTHON_EXEC="$SCRIPT_DIR/.venv/bin/python"

# Run the python application directly with the venv python executable
"$PYTHON_EXEC" -u -m src.main
