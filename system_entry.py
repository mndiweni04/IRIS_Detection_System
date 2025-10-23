import subprocess
import time
import sys
from pathlib import Path

# --- CONFIGURATION (Portable Paths) ---
ROOT_DIR = Path(__file__).resolve().parent 
SERVICE_DIR = ROOT_DIR / "service"
DASHBOARD_DIR = ROOT_DIR / "dashboard"

# Define VENV executables (using the inferred relative paths)
# NOTE: These paths MUST exist relative to the IRIS_Project root.
SERVICE_PYTHON_EXECUTABLE = SERVICE_DIR / ".venv" / "Scripts" / "python.exe"
DASHBOARD_PYTHON_EXECUTABLE = DASHBOARD_DIR / ".venv" / "Scripts" / "python.exe"

# FIX 1: Command for the Service - Use the explicit VENV executable and module flag
# The module resolution failed when CWD was IRIS_Project, so we keep CWD as SERVICE_DIR.
SERVICE_PY_CMD = [str(SERVICE_PYTHON_EXECUTABLE), "-m", "src.controller"]

# FIX 2: Command for the Dashboard (unchanged)
DASHBOARD_PY_CMD = [str(DASHBOARD_PYTHON_EXECUTABLE), "run_dashboard.py"]


def run_concurrently():
    print("--- Starting IRIS Project Components ---")
    
    processes = []
    
    try:
        # 1. Start the Python Service (WS Server)
        print("Starting Python Service (WS Server)...")
        service_process = subprocess.Popen(
            SERVICE_PY_CMD,
            # CRITICAL CWD FIX: Set CWD to the SERVICE directory where module resolution works.
            cwd=SERVICE_DIR, 
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            shell=True # For stability on Windows
        )
        processes.append(service_process)
        print("Python Service started.")

        time.sleep(3) 

        # 2. Start the Dashboard (PySimpleGUI Client)
        print("Starting Dashboard (PySimpleGUI Client)...")
        dashboard_process = subprocess.Popen(
            DASHBOARD_PY_CMD,
            cwd=DASHBOARD_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            shell=True 
        )
        processes.append(dashboard_process)
        print("Dashboard started. System fully launched.")

        for p in processes:
            p.wait()

    except FileNotFoundError as e:
        print(f"FATAL ERROR: Could not find executable: {e}")
        print("Ensure all VENV paths are correct.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
    finally:
        print("--- Initiating Project Shutdown ---")
        for p in processes:
            if p.poll() is None:
                p.terminate()
                print(f"Terminated process {p.pid}")
        
        time.sleep(1)
        for p in processes:
             if p.poll() is None:
                p.kill()
                print(f"Killed process {p.pid}")

        print("--- All IRIS Project Components Terminated ---")

if __name__ == "__main__":
    run_concurrently()