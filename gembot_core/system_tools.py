"""gembot_core.system_tools - Desktop control, screenshot capture, process inspection, system info."""
import base64
import datetime
import io
import os
import subprocess
from pathlib import Path
from typing import Dict, List


def take_screenshot(save_path: str = "") -> str:
    """Capture a screenshot of the primary Windows screen, saving to file and returning details.

    Args:
        save_path: Optional path to save image (e.g. screenshot.png). Defaults to .gembot/screenshots/.
    """
    try:
        from PIL import ImageGrab
        im = ImageGrab.grab()

        if not save_path:
            out_dir = Path(".gembot/screenshots")
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            target = out_dir / f"screenshot_{ts}.png"
        else:
            target = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(save_path))))
            target.parent.mkdir(parents=True, exist_ok=True)

        im.save(str(target), format="PNG")
        return f"Screenshot successfully captured and saved to {target}"
    except Exception as e:
        return f"Error taking screenshot: {e}"


def clipboard_read() -> str:
    """Read the current text from Windows clipboard."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        txt = root.clipboard_get()
        root.destroy()
        return txt or "(Clipboard is empty)"
    except Exception:
        # Fallback to PowerShell
        try:
            r = subprocess.run("powershell Get-Clipboard", shell=True, capture_output=True, text=True)
            return r.stdout.strip() or "(Clipboard is empty or contains non-text data)"
        except Exception as e:
            return f"Error reading clipboard: {e}"


def clipboard_write(text: str) -> str:
    """Copy given text into the Windows clipboard."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return f"Successfully copied {len(text)} characters to clipboard."
    except Exception:
        # Fallback to clip.exe
        try:
            p = subprocess.Popen("clip", stdin=subprocess.PIPE, shell=True)
            p.communicate(input=text.encode("utf-8"))
            return f"Successfully copied to clipboard using clip utility."
        except Exception as e:
            return f"Error writing to clipboard: {e}"


def system_info() -> str:
    """Get system hardware and status (CPU, RAM, Disks, Battery, OS)."""
    try:
        import psutil
        import platform

        cpu_pct = psutil.cpu_percent(interval=0.2)
        mem = psutil.virtual_memory()
        mem_used_gb = mem.used / (1024**3)
        mem_tot_gb = mem.total / (1024**3)

        disk = psutil.disk_usage("C:\\")
        disk_used_gb = disk.used / (1024**3)
        disk_tot_gb = disk.total / (1024**3)

        battery_str = "No battery detected / Desktop AC"
        battery = psutil.sensors_battery()
        if battery:
            battery_str = f"{battery.percent}% ({'Plugged In' if battery.power_plugged else 'On Battery'})"

        lines = [
            f"OS: {platform.system()} {platform.release()} (Build {platform.version()})",
            f"Machine: {platform.machine()} | Architecture: {platform.architecture()[0]}",
            f"CPU Usage: {cpu_pct}%",
            f"RAM Usage: {mem_used_gb:.1f} GB / {mem_tot_gb:.1f} GB ({mem.percent}%)",
            f"Drive C: Free {disk.free / (1024**3):.1f} GB / Total {disk_tot_gb:.1f} GB ({disk.percent}% used)",
            f"Power / Battery: {battery_str}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching system info: {e}"


def list_processes(limit: int = 15) -> str:
    """List top running processes sorted by memory usage."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                mem = p.info['memory_info'].rss / (1024 * 1024) if p.info['memory_info'] else 0
                procs.append((p.info['pid'], p.info['name'], mem, p.info.get('cpu_percent', 0)))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        procs.sort(key=lambda x: x[2], reverse=True)
        lines = [f"{'PID':<8} {'NAME':<28} {'MEMORY (MB)':<14} {'CPU %':<8}"]
        lines.append("-" * 60)
        for pid, name, mem, cpu in procs[:limit]:
            lines.append(f"{pid:<8} {name[:26]:<28} {mem:<14.1f} {cpu:<8}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing processes: {e}"


def kill_process(pid_or_name: str) -> str:
    """Terminate a process by its PID or executable name (e.g. 1234 or notepad.exe)."""
    try:
        import psutil
        target = pid_or_name.strip()
        killed = []
        if target.isdigit():
            pid = int(target)
            p = psutil.Process(pid)
            p_name = p.name()
            p.terminate()
            return f"Terminated process {p_name} (PID: {pid})."
        else:
            for p in psutil.process_iter(['pid', 'name']):
                if p.info['name'] and p.info['name'].lower() == target.lower():
                    p.terminate()
                    killed.append(f"{p.info['name']} (PID: {p.info['pid']})")
            if killed:
                return f"Terminated {len(killed)} processes: " + ", ".join(killed)
            return f"No process found with name '{target}'."
    except Exception as e:
        return f"Error terminating process: {e}"


def download_file(url: str, destination_path: str) -> str:
    """Download a file directly from a URL to a local destination."""
    try:
        import urllib.request
        dst = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(destination_path))))
        dst.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, str(dst))
        return f"Successfully downloaded file to {dst} ({dst.stat().st_size} bytes)."
    except Exception as e:
        return f"Error downloading from '{url}': {e}"


def http_request(method: str, url: str, headers: str = "", body: str = "") -> str:
    """Perform a custom HTTP request (GET, POST, PUT, DELETE, PATCH)."""
    try:
        import json
        import requests
        m = method.upper().strip()
        h_dict = {}
        if headers:
            try:
                h_dict = json.loads(headers)
            except Exception:
                for line in headers.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        h_dict[k.strip()] = v.strip()

        resp = requests.request(m, url, headers=h_dict, data=body if body else None, timeout=20)
        return (
            f"HTTP {resp.status_code} {resp.reason}\n"
            f"Headers: {dict(resp.headers)}\n\n"
            f"Body:\n{resp.text[:2000]}"
        )
    except Exception as e:
        return f"HTTP request failed: {e}"
