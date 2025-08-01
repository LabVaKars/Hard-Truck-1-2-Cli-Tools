@echo off
REM === Merge B3D ===

python3 .\b3d_cli.py b3d merge ^
    --i-from "D:\DB2\COMMON\Bus.b3d" ^
    --i-to "D:\DB2\COMMON\Avensis.b3d" ^
    --o "D:\DB2\COMMON\AMerged.b3d" ^
    --replace

pause