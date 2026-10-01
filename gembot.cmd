@echo off
setlocal

:: Check if Ollama is running, launch if not
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:11434/' -TimeoutSec 1; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [gembot] Starting Ollama server in background...
    start "" /B "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve >nul 2>&1
    timeout /t 3 /nobreak >nul 2>&1
)

:: Run gembot with the agent environment
"%USERPROFILE%\agent\venv\Scripts\python.exe" "%USERPROFILE%\agent\agent.py" %*

endlocal
