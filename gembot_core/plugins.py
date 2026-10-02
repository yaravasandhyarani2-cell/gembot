"""gembot_core.plugins - Dynamic plugin loader from %USERPROFILE%\\agent\\plugins\\."""
import importlib.util
import os
from pathlib import Path
from typing import Callable, Dict

PLUGINS_DIR = Path(os.path.expandvars(r"%USERPROFILE%\agent\plugins"))


def load_plugins() -> Dict[str, Callable]:
    """Scan %USERPROFILE%\\agent\\plugins\\ for Python files exposing tool functions."""
    loaded_tools: Dict[str, Callable] = {}
    if not PLUGINS_DIR.is_dir():
        try:
            PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            return loaded_tools

    for py_file in PLUGINS_DIR.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                # Check for exported tool or functions
                if hasattr(mod, "TOOL_NAME") and hasattr(mod, "run"):
                    loaded_tools[mod.TOOL_NAME] = mod.run
                elif hasattr(mod, "register_tools"):
                    tools = mod.register_tools()
                    if isinstance(tools, dict):
                        loaded_tools.update(tools)
        except Exception:
            pass

    return loaded_tools
