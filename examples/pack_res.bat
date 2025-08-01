@echo off
REM === Pack RES ===

python3 .\b3d_cli.py res pack ^
    --i "D:\DB2\COMMON\COMMON_unpack" ^
    --o "D:\DB2\COMMON\COMMON_pack.res"

pause