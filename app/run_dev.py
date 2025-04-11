#!/usr/bin/env python3
"""
Development script to run the SBO application for local development.
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
logger = logging.getLogger("run_dev")

def ensure_directories():
    """Ensure required directories exist"""
    directories = [
        "mock_data",
        "routes",
        "utils"
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        # Ensure __init__.py exists
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            with open(init_file, "w") as f:
                f.write(f'"""\nPackage containing {directory} for the SBO application.\n"""\n')

def setup_env_vars(db_path=None, port=None, debug=False):
    """Set up environment variables for the application"""
    env = os.environ.copy()

    # Set database path if provided
    if db_path:
        env["DATABASE_URL"] = f"sqlite:///{db_path}"

    # Set port if provided
    if port:
        env["SERVICE_PORT"] = str(port)

    # Set debug mode
    env["DEBUG"] = "true" if debug else "false"

    # Set default JWT secret for development
    if "JWT_SECRET_KEY" not in env:
        env["JWT_SECRET_KEY"] = "dev_secret_key"

    return env

def run_app(args):
    """Run the application"""
    # Ensure directories exist
    ensure_directories()

    # Set up environment variables
    env = setup_env_vars(
        db_path=args.db,
        port=args.port,
        debug=args.debug
    )

    # Determine which file to run
    main_file = "main.py"

    # Prepare command
    cmd = [
        sys.executable, "-m", "uvicorn",
        f"{main_file.split('.')[0]}:app",
        "--host", "0.0.0.0",
        "--port", str(args.port)
    ]

    # Add reload flag if in debug mode
    if args.debug:
        cmd.append("--reload")

    # Log command
    logger.info(f"Starting application with command: {' '.join(cmd)}")

    # Run the application
    try:
        process = subprocess.run(cmd, env=env)
        return process.returncode
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error running application: {str(e)}")
        return 1

def init_db(args):
    """Initialize the database with schema"""
    # Set up environment variables
    env = setup_env_vars(
        db_path=args.db,
        debug=args.debug
    )

    # Set environment variables before imports
    for key, value in env.items():
        os.environ[key] = value

    try:
        # Step 1: Import and initialize database schema only
        logger.info("Initializing database schema...")
        from database import init_db
        init_db()
        logger.info("Database schema initialized")

        # Step 2: Now load mock data
        logger.info("Loading mock data...")
        from init_mock_data import init_mock_data_if_needed
        from database import get_db

        db = next(get_db())
        try:
            init_mock_data_if_needed(db)
            logger.info("Mock data loaded successfully")
            db.close()
            return 0
        except Exception as e:
            db.close()
            logger.error(f"Error loading mock data: {str(e)}")
            return 1

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return 1

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run SBO application for development")

    # Define subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the application")
    run_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    run_parser.add_argument(
        "--port",
        type=int,
        default=8800,
        help="Port to run the application on (default: 8800)"
    )
    run_parser.add_argument(
        "--db",
        default="./sbo_dev.db",
        help="Database path (default: ./sbo_dev.db)"
    )

    # Init-db command
    init_db_parser = subparsers.add_parser("init-db", help="Initialize database schema")
    init_db_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    init_db_parser.add_argument(
        "--db",
        default="./sbo_dev.db",
        help="Database path (default: ./sbo_dev.db)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Handle commands
    if args.command == "run":
        return run_app(args)
    elif args.command == "init-db":
        return init_db(args)
    else:
        # Default to run if no command specified
        args.command = "run"
        args.debug = False
        args.port = 8800
        args.db = "./sbo_dev.db"
        return run_app(args)

if __name__ == "__main__":
    sys.exit(main())
