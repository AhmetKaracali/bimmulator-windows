@echo off
rem bimmulator-windows: run the WSL2 helper scripts from Windows (cmd, PowerShell or double-click).
rem
rem   bimmulator.cmd setup C:\path\to\psdzdata   one-time setup (Nix, QEMU/ANGLE build, config)
rem   bimmulator.cmd snapshot                    first boot, saves a snapshot (~7 min)
rem   bimmulator.cmd start                       fast start from the snapshot
rem   bimmulator.cmd overlay [--language tr]     rebuild overlay.tar (language, coding, plug-ins)
rem   bimmulator.cmd key next press              controller keys
rem   bimmulator.cmd shot C:\temp\screen.png     screenshot
rem   bimmulator.cmd stop
rem
rem Settings: BIMMULATOR_DISTRO (default Ubuntu), BIMMULATOR_REPO (path INSIDE WSL, default
rem ~/bimmulator-windows). Clone the repository inside WSL, not on C:\ or D:\ (speed, line endings).
setlocal EnableDelayedExpansion
if "%BIMMULATOR_DISTRO%"=="" set BIMMULATOR_DISTRO=Ubuntu
if "%BIMMULATOR_REPO%"=="" set BIMMULATOR_REPO=~/bimmulator-windows
set ACTION=%1
if "%ACTION%"=="" goto usage
shift
set ARGS=
:collect
if "%~1"=="" goto run
set "ITEM=%~1"
rem Windows paths (C:\...) become /mnt/c/... for WSL
if "!ITEM:~1,2!"==":\" (
  for /f "delims=" %%P in ('wsl.exe -d %BIMMULATOR_DISTRO% -- wslpath -a "!ITEM!"') do set "ITEM=%%P"
)
set ARGS=!ARGS! "!ITEM!"
shift
goto collect
:run
if /i "%ACTION%"=="setup"    set SCRIPT=wsl/setup.sh
if /i "%ACTION%"=="snapshot" set SCRIPT=wsl/emulator.sh snapshot
if /i "%ACTION%"=="start"    set SCRIPT=wsl/emulator.sh fast
if /i "%ACTION%"=="full"     set SCRIPT=wsl/emulator.sh full
if /i "%ACTION%"=="prepare"  set SCRIPT=wsl/emulator.sh prepare
if /i "%ACTION%"=="overlay"  set SCRIPT=wsl/overlay.sh
if /i "%ACTION%"=="key"      set SCRIPT=wsl/control.sh key
if /i "%ACTION%"=="tap"      set SCRIPT=wsl/control.sh tap
if /i "%ACTION%"=="shot"     set SCRIPT=wsl/control.sh shot
if /i "%ACTION%"=="stop"     set SCRIPT=wsl/control.sh stop
if "%SCRIPT%"=="" goto usage
wsl.exe -d %BIMMULATOR_DISTRO% -- bash -lc "cd %BIMMULATOR_REPO% && bash %SCRIPT% !ARGS!"
exit /b %ERRORLEVEL%
:usage
findstr /b "rem  " "%~f0"
exit /b 2
