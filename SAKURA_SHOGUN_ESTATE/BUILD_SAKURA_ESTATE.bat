@echo off
setlocal
title Sakura Shogun Estate - Complete Build
cd /d "%~dp0"

REM ============================================================================
REM   SAKURA SHOGUN ESTATE - one run builds everything.
REM
REM   CENTER        The estate centre. Change it here and ONLY here.
REM                 (Keep the .5 on X and Z so everything lands on block centres.)
REM   SPEED         SAFE / NORMAL / FAST   - use SAFE if you see skipped commands.
REM   END_GAMEMODE  Gamemode you are put in when the build finishes.
REM   SUNSET        YES sets the time to dusk at the end so you arrive at golden hour.
REM   CHAT_KEY      The key that opens chat in your Minecraft controls.
REM ============================================================================
set "CENTER=408.5 69 -230.5"
set "SPEED=NORMAL"
set "END_GAMEMODE=survival"
set "SUNSET=YES"
set "CHAT_KEY=t"

powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Run_Estate_Automation.ps1" ^
  -CommandFile "%~dp0commands\sakura_estate_full.txt" ^
  -Center "%CENTER%" -Speed %SPEED% -EndMode %END_GAMEMODE% -Sunset %SUNSET% -ChatKey %CHAT_KEY%
endlocal
