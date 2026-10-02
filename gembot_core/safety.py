"""gembot_core.safety - Safety checks, confirmation gates, backups, and undo operations."""
import datetime
import os
import re
import shutil
from pathlib import Path
from typing import Optional, Tuple

BACKUP_DIR = Path(".gembot/backups")
LOGS_DIR = Path(".gembot/logs")
UNDO_STACK_FILE = Path(".gembot/backups/undo_stack.json")


def ensure_dirs() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def backup_file(filepath: str) -> Optional[str]:
    """Create a timestamped snapshot of a file in .gembot/backups/ before modifying or deleting."""
    try:
        p = Path(filepath).resolve()
        if not p.is_file():
            return None
        ensure_dirs()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{p.name}.{timestamp}.bak"
        dest = BACKUP_DIR / backup_name
        shutil.copy2(p, dest)

        # Record in undo history
        undo_log = BACKUP_DIR / "undo_log.txt"
        with open(undo_log, "a", encoding="utf-8") as f:
            f.write(f"{p}|{dest.resolve()}\n")

        return str(dest)
    except Exception:
        return None


def undo_last_change() -> Tuple[bool, str]:
    """Restore the last modified or deleted file from .gembot/backups/."""
    undo_log = BACKUP_DIR / "undo_log.txt"
    if not undo_log.is_file():
        return False, "No undo history available."

    try:
        lines = undo_log.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return False, "No undo records left."

        last_entry = lines.pop()
        target_path, backup_path = last_entry.split("|", 1)

        t_p = Path(target_path)
        b_p = Path(backup_path)

        if not b_p.is_file():
            return False, f"Backup file {b_p} was not found on disk."

        t_p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(b_p, t_p)

        # Write remaining entries back
        undo_log.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return True, f"Successfully restored {t_p.name} from backup {b_p.name}."
    except Exception as e:
        return False, f"Failed to undo: {e}"


def is_dangerous_command(command: str, blocked_list: list) -> Tuple[bool, str]:
    """Inspect shell command against blocked commands and dangerous patterns."""
    cmd_lower = command.lower().strip()
    for blocked in blocked_list:
        if blocked.lower() in cmd_lower:
            return True, f"Command contains blocked pattern '{blocked}'."

    # Dangerous commands pattern
    destructive_patterns = [
        (r"\bformat\s+[a-z]:", "Drive format command"),
        (r"\brmdir\s+/[sq]\s+[a-z]:\\", "System drive recursive deletion"),
        (r"\bdel\s+/[fs]\s+[a-z]:\\", "System drive file deletion"),
        (r"\bgit\s+push\s+.*--force", "Force push to git remote"),
        (r"\bshutdown\b", "System shutdown command"),
    ]
    for pat, desc in destructive_patterns:
        if re.search(pat, cmd_lower):
            return True, desc

    return False, ""


def log_session_activity(tool_name: str, args: dict, result: str) -> None:
    """Log tool invocations and results to .gembot/logs/session-<date>.log."""
    try:
        ensure_dirs()
        date_str = datetime.date.today().isoformat()
        log_file = LOGS_DIR / f"session-{date_str}.log"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] TOOL: {tool_name}\nARGS: {args}\nRESULT:\n{result}\n{'-'*60}\n")
    except Exception:
        pass
