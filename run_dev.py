#!/usr/bin/env python3
"""
Development script to run SBO microservices for local development.
"""

import os
import sys
import argparse
import subprocess
import signal
import logging
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_dev")

# Define services and their ports
SERVICES = {
    "skills": {
        "module": "services.skills_service",
        "port": 8801
    },
    "matching": {
        "module": "services.matching_service",
        "port": 8802
    },
    "user": {
        "module": "services.user_service",
        "port": 8803
    },
    "assessment": {
        "module": "services.assessment_service",
        "port": 8804
    },
    "llm": {
        "module": "services.llm_service",
        "port": 8805
    },
    "api": {
        "module": "services.api_gateway",
        "port": 8800
    }
}

# Default environment variables
DEFAULT_ENV = {
    "DATABASE_URL": "sqlite:///./sbo_dev.db",
    "JWT_SECRET_KEY": "dev_secret_key",
    "LLM_API_KEY": "dummy-key-for-development"
}

# Store process handles
processes = {}

def start_service(service_name, debug=False):
    """Start a single service with uvicorn"""
    service = SERVICES.get(service_name)
    if not service:
        logger.error(f"Unknown service: {service_name}")
        return

    port = service["port"]
    module = service["module"]
    
    # Prepare environment variables
    env = os.environ.copy()
    
    # Add default environment variables if not already set
    for key, value in DEFAULT_ENV.items():
        if key not in env:
            env[key] = value

    # Add service URLs based on ports
    for svc_name, svc_config in SERVICES.items():
        url_var = f"{svc_name.upper()}_SERVICE_URL"
        if url_var not in env:
            env[url_var] = f"http://localhost:{svc_config['port']}"

    # Command to run the service
    cmd = [
        "uvicorn",
        f"{module}:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ]
    
    if debug:
        cmd.append("--log-level=debug")
    
    logger.info(f"Starting {service_name} service on port {port}")
    
    # Start the process
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Store the process handle
    processes[service_name] = process
    
    # Read and log output
    for line in iter(process.stdout.readline, ''):
        print(f"[{service_name.upper()}] {line}", end='')
    
    process.stdout.close()
    return_code = process.wait()
    if return_code:
        logger.error(f"{service_name} service exited with return code {return_code}")
    else:
        logger.info(f"{service_name} service stopped")

def start_services(service_names, debug=False):
    """Start multiple services in parallel"""
    with ThreadPoolExecutor(max_workers=len(service_names)) as executor:
        for service_name in service_names:
            executor.submit(start_service, service_name, debug)

def stop_services():
    """Stop all running services"""
    for service_name, process in processes.items():
        logger.info(f"Stopping {service_name} service")
        process.send_signal(signal.SIGINT)
    
    # Wait for processes to terminate
    for service_name, process in processes.items():
        try:
            process.wait(timeout=5)
            logger.info(f"{service_name} service stopped")
        except subprocess.TimeoutExpired:
            logger.warning(f"{service_name} service did not stop gracefully, killing")
            process.kill()

def handle_interrupt(signum, frame):
    """Handle interrupt signal (Ctrl+C)"""
    logger.info("Interrupt received, stopping services")
    stop_services()
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SBO services for development")
    parser.add_argument(
        "services", 
        nargs="*", 
        default=list(SERVICES.keys()),
        help="Services to run (default: all)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    parser.add_argument(
        "--db", 
        help="Database URL (default: sqlite:///./sbo_dev.db)"
    )
    
    args = parser.parse_args()
    
    # Set database URL if provided
    if args.db:
        DEFAULT_ENV["DATABASE_URL"] = args.db
    
    # Validate services
    invalid_services = [s for s in args.services if s not in SERVICES]
    if invalid_services:
        logger.error(f"Unknown services: {', '.join(invalid_services)}")
        logger.info(f"Available services: {', '.join(SERVICES.keys())}")
        sys.exit(1)
    
    # Register signal handler
    signal.signal(signal.SIGINT, handle_interrupt)
    signal.signal(signal.SIGTERM, handle_interrupt)
    
    try:
        # Start requested services
        logger.info(f"Starting services: {', '.join(args.services)}")
        start_services(args.services, args.debug)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        stop_services()