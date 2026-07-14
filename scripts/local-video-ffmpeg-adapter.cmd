@echo off
set ROOT=%~dp0..
"%ROOT%\backend\.venv\Scripts\python.exe" "%ROOT%\scripts\local_video_ffmpeg_adapter.py" "%~1" "%~2"
