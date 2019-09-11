@echo off
title Youtube-DL 2019.09.12 (music format)
set /p url=URL video:
youtube-dl.exe -x --audio-format mp3 %url%
pause
