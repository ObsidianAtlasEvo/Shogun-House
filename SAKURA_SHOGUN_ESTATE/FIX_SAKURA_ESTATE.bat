@echo off
setlocal
title Sakura Shogun Estate - Repair Pass (v2)
cd /d "%~dp0"

REM ============================================================================
REM   SAKURA SHOGUN ESTATE - REPAIR PASS
REM   For an estate you ALREADY built with BUILD_SAKURA_ESTATE.bat (first release).
REM   Only changed blocks are placed (about 2-3 minutes). Nothing else is cleared.
REM
REM   Use the SAME CENTER you built with. (Default below is the original.)
REM ============================================================================
set "CENTER=408.5 69 -230.5"
set "SPEED=NORMAL"
set "END_GAMEMODE=survival"
set "CHAT_KEY=t"

powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Run_Estate_Automation.ps1" ^
  -CommandFile "%~dp0commands\sakura_estate_fix_v2.txt" ^
  -Center "%CENTER%" -Speed %SPEED% -EndMode %END_GAMEMODE% -Sunset NO -ChatKey %CHAT_KEY% ^
  -ConfirmWord REPAIR -Mode REPAIR -Title "SAKURA SHOGUN ESTATE  -  repair pass v2"
endlocal
