"""gembot_core.coding_tools - Precision code editing, searching, testing, and file operations."""
import fnmatch
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List
from gembot_core.process_runner import run_process


def edit_file(path: str, old_str: str, new_str: str) -> str:
    """Perform a precise patch edit on an existing file by replacing old_str with new_str.

    Critical for large files: preserves the rest of the file without rewriting everything.
    """
    try:
        p = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(path))))
        if not p.is_file():
            return f"Error: File '{p}' does not exist."

        content = p.read_text(encoding="utf-8", errors="replace")
        if old_str not in content:
            # Try relaxing newline differences
            content_norm = content.replace("\r\n", "\n")
            old_norm = old_str.replace("\r\n", "\n")
            if old_norm in content_norm:
                new_norm = new_str.replace("\r\n", "\n")
                updated = content_norm.replace(old_norm, new_norm, 1)
                p.write_text(updated, encoding="utf-8")
                return f"Successfully updated '{p.name}' using normalized newlines."
            return f"Error: old_str was not found in '{p.name}'. Please verify the exact text to replace."

        count = content.count(old_str)
        updated = content.replace(old_str, new_str, 1)
        p.write_text(updated, encoding="utf-8")
        note = f" (Warning: {count} matches found, replaced the first one)" if count > 1 else ""
        return f"Successfully edited '{p.name}'{note}."
    except Exception as e:
        return f"Error editing file: {e}"


def search_files(pattern: str, path: str = ".", glob: str = "*") -> str:
    """Grep-style regex or text search across files in a directory.

    Args:
        pattern: String or keyword to search for inside files
        path: Base directory to search (default '.')
        glob: File glob pattern (e.g. *.py, *.js, *.ts, or *)
    """
    try:
        base = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(path))))
        if not base.exists():
            return f"Error: Path '{base}' does not exist."

        matches = []
        pattern_lower = pattern.lower()
        ignore_dirs = {".git", "node_modules", ".next", "__pycache__", "venv", ".gembot", "dist", "build"}

        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                if fnmatch.fnmatch(file, glob):
                    fpath = Path(root) / file
                    try:
                        # Skip large or binary files
                        if fpath.stat().st_size > 500 * 1024:
                            continue
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            for lineno, line in enumerate(f, 1):
                                if pattern_lower in line.lower():
                                    rel = os.path.relpath(fpath, base)
                                    matches.append(f"{rel}:{lineno}: {line.strip()[:150]}")
                                    if len(matches) >= 50:
                                        break
                    except Exception:
                        continue
            if len(matches) >= 50:
                break

        if not matches:
            return f"No matches found for '{pattern}' in {path} (glob: {glob})."
        return f"Found {len(matches)} matches:\n" + "\n".join(matches[:50])
    except Exception as e:
        return f"Error searching files: {e}"


def delete_file(path: str) -> str:
    """Delete a file from the filesystem."""
    try:
        p = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(path))))
        if not p.exists():
            return f"Error: '{p}' does not exist."
        if p.is_dir():
            shutil.rmtree(p)
            return f"Deleted directory '{p}'."
        else:
            p.unlink()
            return f"Deleted file '{p}'."
    except Exception as e:
        return f"Error deleting: {e}"


def copy_file(source: str, destination: str) -> str:
    """Copy a file or directory to a new destination."""
    try:
        src = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(source))))
        dst = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(destination))))
        if not src.exists():
            return f"Error: Source '{src}' not found."

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return f"Copied directory from {src} to {dst}"
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return f"Copied file to {dst}"
    except Exception as e:
        return f"Error copying: {e}"


def make_dir(path: str) -> str:
    """Create a new directory and all necessary parent directories."""
    try:
        p = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(path))))
        p.mkdir(parents=True, exist_ok=True)
        return f"Created directory '{p}'"
    except Exception as e:
        return f"Error creating directory: {e}"


def file_info(path: str) -> str:
    """Get metadata for a file or directory (size, modified time, permissions, lines of code)."""
    try:
        p = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(path))))
        if not p.exists():
            return f"Error: '{p}' not found."

        st = p.stat()
        size = st.st_size
        if size > 1024 * 1024:
            size_str = f"{size / (1024*1024):.2f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.2f} KB"
        else:
            size_str = f"{size} bytes"

        info = [
            f"Path: {p}",
            f"Type: {'Directory' if p.is_dir() else 'File'}",
            f"Size: {size_str}",
            f"Extension: {p.suffix or '(none)'}",
        ]

        if p.is_file() and size < 2 * 1024 * 1024:
            try:
                line_count = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
                info.append(f"Lines: {line_count}")
            except Exception:
                pass

        return "\n".join(info)
    except Exception as e:
        return f"Error reading file info: {e}"


def run_tests(cwd: str = ".") -> str:
    """Auto-detect and run unit tests (pytest for Python, npm test for Node/React) and report output."""
    base = Path(os.path.abspath(os.path.expanduser(os.path.expandvars(cwd))))
    if not base.exists():
        base = Path.cwd()

    # Detect test runner
    cmd = None
    if (base / "package.json").is_file():
        cmd = "npm test"
    elif any(base.glob("test_*.py")) or any(base.glob("*_test.py")) or (base / "tests").is_dir():
        cmd = "pytest -v"
    elif (base / "manage.py").is_file():
        cmd = "python manage.py test"
    else:
        cmd = "pytest -v"

    try:
        r = run_process(cmd, cwd=str(base), shell=True, timeout=90)
        out = (r.stdout + "\n" + r.stderr).strip()
        status = "PASSED" if r.returncode == 0 else f"FAILED (Exit Code {r.returncode})"
        return f"Test Runner: {cmd}\nStatus: {status}\n\nOutput:\n{out[:2500]}"
    except subprocess.TimeoutExpired:
        return f"Tests timed out after 90 seconds ({cmd})."
    except Exception as e:
        return f"Error executing tests: {e}"
