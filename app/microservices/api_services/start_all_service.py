import multiprocessing
import uvicorn
import sys
import os

# ✅ Ensures Python can locate microservice modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ✅ This function starts an individual FastAPI service via Uvicorn
def start_services(app_module: str, port: int, service_name: str, reload: bool = False):
    print(f"Attempting to start {service_name} on port {port}...")
    try:
        uvicorn.run(
            app_module,
            host="0.0.0.0",
            port=port,
            reload=reload, # ✅ Change 1: Make reload dynamic via CLI flag
            timeout_keep_alive=10,         # ✅ Change 2: fixed syntax for keep-alive timeout
            log_level="info"
        )
    except Exception as e:
        print(f"ERROR: Unable to start {service_name} on port {port}: {e}", file=sys.stderr)


if __name__ == "__main__":
    # ✅ Change 2: Explicitly set start method to 'spawn'
    # Reason: Required on Windows to avoid RuntimeError when using multiprocessing

    if sys.platform == "win32":
        multiprocessing.set_start_method("spawn", force=True)


    # ✅ Ensures Windows can safely spawn subprocesses
    multiprocessing.freeze_support()

    # ✅ Change 3: Allow optional --reload flag via command line
    # Usage: `python main.py --reload`
    RELOAD_MODE = "--reload" in sys.argv

    services = [
        {
            "app_module": "app.microservices.users.users_routes:app",
            "port": 9000,
            "service_name": "Users Service"
        },
    ]

    processes = []
    print("Starting all microservices...")
    for service_info in services:
        p = multiprocessing.Process(
            target=start_services,
            args=(
                service_info["app_module"],
                service_info["port"],
                service_info["service_name"],
                RELOAD_MODE  # ✅ Pass reload mode to subprocesses
            ),
            name=service_info["service_name"]
        )
        processes.append(p)
        p.start()

    print("\nAll services initiated. Check console for logs from each service.")
    print("Press Ctrl+C to gracefully stop all services.")

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Stopping all services...")
        for p in processes:
            if p.is_alive():
                print(f"Terminating {p.name} (PID: {p.pid})...")
                p.terminate()
                p.join(timeout=5)
                if p.is_alive():
                    print(f"WARNING: {p.name} (PID: {p.pid}) did not terminate gracefully. Killing now.")
                    p.kill()
        print("All services stopped.")
