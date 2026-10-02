"""gembot_core package initialization."""
from gembot_core.config import load_config, save_config, get_active_model, set_active_model
from gembot_core.safety import backup_file, undo_last_change, is_dangerous_command, log_session_activity
from gembot_core.coding_tools import edit_file, search_files, delete_file, copy_file, make_dir, file_info, run_tests
from gembot_core.memory import remember_fact, recall_fact, save_session, load_session, list_sessions, auto_summarize_history
from gembot_core.system_tools import take_screenshot, clipboard_read, clipboard_write, system_info, list_processes, kill_process, download_file, http_request
from gembot_core.doc_tools import create_docx, read_docx, create_excel, read_excel
from gembot_core.plugins import load_plugins
