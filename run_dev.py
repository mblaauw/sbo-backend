import subprocess
import time
import os
from concurrent.futures import ThreadPoolExecutor

# Service configurations
services = [
    {"name": "skills_service", "port": 8001, "module": "skills_service.main:app"},
    {"name": "matching_service", "port": 8002, "module": "matching_service.main:app"},
    {"name": "user_service", "port": 8003, "module": "user_service.main:app"},
    {"name": "assessment_service", "port": 8004, "module": "assessment_service.main:app"},
    {"name": "llm_service", "port": 8005, "module": "llm_service.main:app"},
    {"name": "api_gateway", "port": 8000, "module": "api_gateway.main:app"},
]

# Environment variables for inter-service communication
env_vars = {
    "SKILLS_SERVICE_URL": "http://localhost:8001",
    "MATCHING_SERVICE_URL": "http://localhost:8002",
    "USER_SERVICE_URL": "http://localhost:8003",
    "ASSESSMENT_SERVICE_URL": "http://localhost:8004",
    "LLM_SERVICE_URL": "http://localhost:8005",
    "API_GATEWAY_URL": "http://localhost:8000",
    "DATABASE_URL": "sqlite:///./test.db",  # For development
    "JWT_SECRET_KEY": "dev_secret_key",
}

def run_service(service):
    """Run a service using uvicorn"""
    cmd = [
        "uvicorn",
        service["module"],
        "--host", "0.0.0.0",
        "--port", str(service["port"]),
        "--reload"
    ]
    
    # Combine current environment with service-specific variables
    env = os.environ.copy()
    env.update(env_vars)
    
    print(f"Starting {service['name']} on port {service['port']}...")
    return subprocess.Popen(cmd, env=env)

def main():
    """Run all services in parallel"""
    processes = []
    
    with ThreadPoolExecutor(max_workers=len(services)) as executor:
        processes = list(executor.map(run_service, services))
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all services...")
        for p in processes:
            p.terminate()
        
        # Wait for all processes to terminate
        for p in processes:
            p.wait()
        
        print("All services stopped")

if __name__ == "__main__":
    main()