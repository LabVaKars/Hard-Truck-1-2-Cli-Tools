@echo off
REM === Split RES ===

python3 .\b3d_cli.py res extract ^
    --i "D:\DB2\COMMON\TRUCKS.res" ^
    --sections PALETTEFILES TEXTUREFILES MATERIALS ^
    --ref-texturefiles --ref-maskfiles

echo All tasks completed.
pause