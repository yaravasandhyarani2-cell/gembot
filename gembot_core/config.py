"""gembot_core.config - Central configuration management for gembot.
Manages %USERPROFILE%\\agent\\config.json and environment fallbacks.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict

GLOBAL_AGENT_DIR = Path(os.path.expandvars(r"%USERPROFILE%\agent"))
CONFIG_FILE = GLOBAL_AGENT_DIR / "config.json"
GLOBAL_ENV = GLOBAL_AGENT_DIR / ".env"

DEFAULT_CONFIG: Dict[str, Any] = {
    "model": "qwen2.5-coder:7b",
    "fallback_model": "qwen2.5-coder:3b",
    "max_steps": 16,
    "max_output": 2500,
    "max_history": 24,
    "command_timeout": 60,
    "auto_confirm": False,
    "blocked_commands": [
        "format",
        "rmdir /s /q c:\\",
        "rmdir /s /q c:/",
        "del /f /s /q c:\\",
        "del /f /s /q c:/",
        "diskpart",
        "shutdown",
        "taskkill /f /im explorer.exe",
        "bcdedit",
        "reg delete hk",
    ],
}


def load_config() -> Dict[str, Any]:
    """Load configuration from %USERPROFILE%\\agent\\config.json, falling back to defaults."""
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    cfg.update(data)
        except Exception:
            pass

    # Environment variables override config
    env_model = os.getenv("MODEL")
    if env_model:
        cfg["model"] = env_model
    if os.getenv("MAX_STEPS"):
        try:
            cfg["max_steps"] = int(os.getenv("MAX_STEPS"))
        except ValueError:
            pass
    if os.getenv("MAX_OUTPUT"):
        try:
            cfg["max_output"] = int(os.getenv("MAX_OUTPUT"))
        except ValueError:
            pass

    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    """Save configuration to %USERPROFILE%\\agent\\config.json."""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def get_active_model() -> str:
    cfg = load_config()
    return cfg.get("model", "qwen2.5-coder:7b")


def set_active_model(model_name: str) -> None:
    cfg = load_config()
    cfg["model"] = model_name
    save_config(cfg)
    os.environ["MODEL"] = model_name
    # Keep .env in sync
    try:
        GLOBAL_ENV.parent.mkdir(parents=True, exist_ok=True)
        GLOBAL_ENV.write_text(f"MODEL={model_name}\n", encoding="utf-8")
    except Exception:
        pass
