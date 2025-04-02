#!/usr/bin/env python3
"""
Development script to run all SBO services locally
"""

import subprocess
import time
import os
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

# Service configurations - updated for services/ directory structure
services = [
    {"name": "skills_service", "port": 8101, "module": "services.skills_service.main:app"},
    {"name": "matching_service", "port": 8102, "module": "services.matching_service.main:app"},
    {"name": "user_service", "port": 8103, "module": "services.user_service.main:app"},
    {"name": "assessment_service", "port": 8104, "module": "services.assessment_service.main:app"},
    {"name": "llm_service", "port": 8105, "module": "services.llm_service.main:app"},
    {"name": "api_gateway", "port": 8100, "module": "services.api_gateway.main:app"},
]

# Environment variables for inter-service communication
env_vars = {
    "SKILLS_SERVICE_URL": "http://localhost:8101",
    "MATCHING_SERVICE_URL": "http://localhost:8102",
    "USER_SERVICE_URL": "http://localhost:8103",
    "ASSESSMENT_SERVICE_URL": "http://localhost:8104",
    "LLM_SERVICE_URL": "http://localhost:8105",
    "API_GATEWAY_URL": "http://localhost:8100",
    "DATABASE_URL": "sqlite:///./data/sbo.db",  # Use a data directory
    "JWT_SECRET_KEY": "dev_secret_key",
    "PYTHONPATH": os.path.dirname(os.path.abspath(__file__))  # Add project root to PYTHONPATH
}

# Global list to track processes
processes = []

def handle_exit(signum, frame):
    """Handle exit signals by stopping all processes"""
    print("\nStopping all services...")
    for p in processes:
        p.terminate()
    
    # Wait for all processes to terminate
    for p in processes:
        p.wait()
    
    print("All services stopped")
    sys.exit(0)

def run_service(service):
    """Run a service using uvicorn"""
    # Extract service name from module path
    service_name = service["module"].split(".")[1]
    
    # Get service directory
    service_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "services")
    
    # Create module name relative to service directory
    module = f"{service_name}.main:app"
    
    cmd = [
        "uvicorn",
        module,
        "--host", "0.0.0.0",
        "--port", str(service["port"]),
        "--reload",
        "--app-dir", service_dir
    ]
    
    env = os.environ.copy()
    env.update(env_vars)
    
    print(f"Starting {service['name']} on port {service['port']}...")
    return subprocess.Popen(cmd, env=env)

def main():
    """Run all services in parallel"""
    global processes
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    print("Starting all SBO services in development mode...")
    print(f"Project root: {os.path.dirname(os.path.abspath(__file__))}")
    
    with ThreadPoolExecutor(max_workers=len(services)) as executor:
        processes = list(executor.map(run_service, services))
    
    # Give services time to start
    time.sleep(2)
    
    print("\nAll services started!")
    print("Access API Gateway at http://localhost:8100")
    print("Press Ctrl+C to stop all services")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_exit(None, None)

if __name__ == "__main__":
    main()