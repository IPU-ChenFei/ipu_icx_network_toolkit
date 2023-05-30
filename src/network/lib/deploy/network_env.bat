@echo off
set toolpath=C:\BKCPkg\domains\network

:: 1. Download tools
scp -r root@10.239.115.67:/localdisk/test_tools/network/windows/* %toolpath%

:: Install iperf3
if not exist %toolpath%\\iperf-3.1.3-win64\\iperf3.exe echo "Start to install iperf3..."
Expand-Archive -Force -Path %toolpath%\iperf-3.1.3-win64.zip -DestinationPath %toolpath%

:: Install iwvss
if not exist "C:\\iwvss" echo "Start to install iwvss..."
%toolpath%\iwvss\iwVSS 2.9.2.exe /S

:: Install Mellanox WinOF2
if not exist "C:\\Program Files\Mellanox\MLNX_WinOF2" echo "Start to install Mellanox WinOF tool..."
%toolpath%\MLNX_WinOF2-2_70_51000_All_x64.exe /S

:: Install WinMFT
if not exist "C:\\Program Files\Mellanox\MLNX_WinOF2" echo "Start to install WinMFT tool..."
%toolpath%\WinMFT_x64_4_15_1_9.exe /S
