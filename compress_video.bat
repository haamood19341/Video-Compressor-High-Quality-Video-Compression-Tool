@echo off
echo Video Compressor
echo ===============

if "%~1"=="" (
    echo Error: No input file specified.
    echo Usage: compress_video.bat input_file [output_file]
    exit /b 1
)

set INPUT=%~1
set OUTPUT=compressed_%~nx1

if not "%~2"=="" (
    set OUTPUT=%~2
)

echo Input: %INPUT%
echo Output: %OUTPUT%
echo.
echo Starting compression...
python video_compressor.py "%INPUT%" -o "%OUTPUT%"

echo.
echo Done!
pause 