#!/usr/bin/env python3
"""
Script to format all Python code in the project.
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("format-code")

# Default directories to format
DEFAULT_DIRS = ["services", "tests"]

def format_python_files(directories, check_only=False):
    """Format Python files in the specified directories"""
    logger.info(f"{'Checking' if check_only else 'Formatting'} Python files in: {', '.join(directories)}")
    
    # Make sure all directories exist
    for directory in directories:
        if not os.path.isdir(directory):
            logger.warning(f"Directory not found: {directory}")
            if not input(f"Continue without {directory}? (y/n): ").lower().startswith('y'):
                return 1
    
    # Get all Python files
    python_files = []
    for directory in directories:
        for path in Path(directory).rglob("*.py"):
            python_files.append(str(path))
    
    logger.info(f"Found {len(python_files)} Python files")
    
    if not python_files:
        logger.warning("No Python files found!")
        return 0
    
    # Run isort
    logger.info("Running isort...")
    isort_cmd = ["isort"]
    if check_only:
        isort_cmd.append("--check-only")
    isort_cmd.extend(python_files)
    
    isort_result = subprocess.run(isort_cmd)
    if isort_result.returncode != 0 and check_only:
        logger.error("isort check failed. Run without --check to fix.")
        return isort_result.returncode
    
    # Run black
    logger.info("Running black...")
    black_cmd = ["black"]
    if check_only:
        black_cmd.append("--check")
    black_cmd.extend(python_files)
    
    black_result = subprocess.run(black_cmd)
    if black_result.returncode != 0 and check_only:
        logger.error("black check failed. Run without --check to fix.")
        return black_result.returncode
    
    # Run flake8
    logger.info("Running flake8...")
    flake8_cmd = ["flake8"]
    flake8_cmd.extend(python_files)
    
    flake8_result = subprocess.run(flake8_cmd)
    if flake8_result.returncode != 0:
        logger.error("flake8 check failed. Please fix the issues manually.")
        return flake8_result.returncode
    
    logger.info("All formatting checks completed.")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format Python code in the project")
    parser.add_argument(
        "directories", 
        nargs="*", 
        default=DEFAULT_DIRS,
        help=f"Directories to format (default: {', '.join(DEFAULT_DIRS)})"
    )
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Check only, don't modify files"
    )
    
    args = parser.parse_args()
    
    exit_code = format_python_files(args.directories, args.check)
    sys.exit(exit_code)