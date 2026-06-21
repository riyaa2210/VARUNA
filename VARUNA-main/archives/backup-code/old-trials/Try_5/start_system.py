import os
import time
import webbrowser
import sys
import subprocess
import urllib.request

# --- CONFIGURATION (MATCHING YOUR FOLDER STRUCTURE) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = BASE_DIR
MAIN_PY_PATH = os.path.join(BACKEND_DIR, "main.py")
FRONTEND_DIR = os.path.join(BASE_DIR, "dashboard")
VENV_ACTIVATE = os.path.join(BASE_DIR, ".venv", "Scripts", "activate.bat")

def start_system():
    print("=" * 60)
    print("      *** CODING_NEXUS LAUNCH PROTOCOL (SIH 2025) ***")
    print("=" * 60)

    # --- VALIDATION ---
    if not os.path.exists(MAIN_PY_PATH):
        print(f"[ERROR] Backend script not found at: {MAIN_PY_PATH}")
        input("Press Enter to exit...")
        return
    if not os.path.exists(FRONTEND_DIR):
        print(f"[ERROR] Frontend folder not found at: {FRONTEND_DIR}")
        input("Press Enter to exit...")
        return

    processes = []
    try:
        # --- STEP 1: START BACKEND ---
        print("\n[1/3] Initializing AI Core...")
        
        backend_core_cmd = f'cd /d "{BACKEND_DIR}" && '
        if os.path.exists(VENV_ACTIVATE):
            print("      (Activating Virtual Env and running script)")
            backend_core_cmd += f'"{VENV_ACTIVATE}" && python "{os.path.basename(MAIN_PY_PATH)}"'
        else:
            print("      (Virtual Env not found. Falling back to System Python)")
            python_exec = sys.executable or "python"
            backend_core_cmd += f'"{python_exec}" "{os.path.basename(MAIN_PY_PATH)}"'

        backend_process = subprocess.Popen(backend_core_cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        processes.append(backend_process)

        # --- STEP 2: HEALTH CHECK BACKEND ---
        print("\n[2/3] Waiting for AI Core to respond...")
        backend_ready = False
        for i in range(20): # Max wait 20 seconds
            try:
                # We check the /docs endpoint which is available by default in FastAPI
                with urllib.request.urlopen("http://localhost:8000/docs", timeout=1) as response:
                    if response.status == 200:
                        print("      (AI Core is online!)")
                        backend_ready = True
                        break
            except Exception:
                time.sleep(1)
            print(f"      (Attempt {i+1}/20...)")

        if not backend_ready:
            print("\n[ERROR] AI Core failed to start or respond in time.")
            raise RuntimeError("Backend failed to start")

        # --- STEP 3: START FRONTEND ---
        print("\n[3/3] Launching Command Dashboard...")
        frontend_cmd = f'cd /d "{FRONTEND_DIR}" && npm start'
        frontend_process = subprocess.Popen(frontend_cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        processes.append(frontend_process)

        # --- STEP 4: OPEN BROWSER ---
        print("\n[+] Opening browser...")
        time.sleep(5) # Give React time to compile
        webbrowser.open("http://localhost:3000")

        print("\n" + "=" * 60)
        print("    SYSTEM IS LIVE. Press Enter here to shut down all services.")
        print("=" * 60)
        input() # Wait for user to press Enter

    except Exception as e:
        print(f"\n[CRITICAL ERROR] An error occurred during startup: {e}")
        print("   (Check the console windows for more details)")
        input("Press Enter to acknowledge and shut down...")

    finally:
        # --- UNIFIED SHUTDOWN ---
        print("\n[+] Shutting down all services...")
        for p in reversed(processes):
            try:
                print(f"      (Terminating process tree with PID: {p.pid})")
                # Use taskkill on Windows to ensure the entire process tree is terminated
                subprocess.run(f"taskkill /F /T /PID {p.pid}", check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                # This can happen if the process is already closed
                print(f"      (Could not terminate process PID {p.pid}. It may have already closed. Error: {e.output.strip()})")
            except Exception as e:
                print(f"      (An unexpected error occurred while terminating PID {p.pid}: {e})")

        print("\n[+] System shutdown complete.")
        time.sleep(2)

if __name__ == "__main__":
    start_system()