@echo off
REM === Merge RES ===

python3 .\b3d_cli.py res merge ^
    --i-from "D:\DB2\COMMON\Bus.res" ^
    --i-to "D:\DB2\COMMON\Avensis.res" ^
    --o "D:\DB2\COMMON\AMerged.res" ^
    --replace

pause