#!/usr/bin/env python3
"""
Script to run tests for all SBO microservices.
"""

import os
import sys
import argparse
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test-runner")

# Define services and their test paths
SERVICES = {
    "skills": "tests/test_skills_service.py",
    "matching": "tests/test_matching_service.py",
    "user": "tests/test_user_service.py",
    "assessment": "tests/test_assessment_service.py",
    "llm": "tests/test_llm_service.py",
    "api": "tests/test_api_gateway.py",
    "integration": "tests/test_integration.py"
}

def run_tests(service_names, coverage=False, verbose=False):
    """Run tests for the specified services"""
    
    # Set up command
    command = ["pytest"]
    
    # Add options
    if verbose:
        command.append("-v")
    
    if coverage:
        command.extend([
            "--cov=services",
            "--cov-report=term",
            "--cov-report=html:coverage_report"
        ])
    
    # Add test paths
    test_paths = []
    for service in service_names:
        if service in SERVICES:
            test_paths.append(SERVICES[service])
        else:
            logger.warning(f"Unknown service: {service}")
    
    if not test_paths:
        logger.error("No valid test paths found")
        return 1
    
    command.extend(test_paths)
    
    logger.info(f"Running tests with command: {' '.join(command)}")
    try:
        result = subprocess.run(command)
        return result.returncode
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests for SBO services")
    parser.add_argument(
        "services", 
        nargs="*", 
        default=list(SERVICES.keys()),
        help="Services to test (default: all)"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Generate coverage report"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate services
    invalid_services = [s for s in args.services if s not in SERVICES]
    if invalid_services:
        logger.error(f"Unknown services: {', '.join(invalid_services)}")
        logger.info(f"Available services: {', '.join(SERVICES.keys())}")
        sys.exit(1)
    
    # Run tests
    exit_code = run_tests(args.services, args.coverage, args.verbose)
    sys.exit(exit_code)