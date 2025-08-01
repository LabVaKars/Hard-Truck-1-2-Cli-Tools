@echo off
REM === Remove from RES ===

python3 .\b3d_cli.py res remove ^
    --i "D:\DB2\COMMON\Bus.res" ^
    --o "D:\DB2\COMMON\RemBus.res" ^
    --rem-materials "bus_all*" ^
    --ref-texturefiles --ref-maskfiles

pause