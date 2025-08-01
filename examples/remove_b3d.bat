@echo off
REM === Remove from B3D ===

python3 .\b3d_cli.py b3d remove ^
    --i "D:\DB2\COMMON\Bus.b3d" ^
    --o "D:\DB2\COMMON\RemBus.b3d" ^
    --rem-nodes "LNKTRK*"

pause