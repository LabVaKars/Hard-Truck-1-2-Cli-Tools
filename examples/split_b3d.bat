@echo off
REM === Split B3D === 
 
python3 .\b3d_cli.py b3d extract ^
    --i "D:\DB2\COMMON\TRUCKS.b3d" ^
    --node-refs --ref-materials --split ^
    --res "D:\DB2\COMMON\TRUCKS.res" ^
    --ref-texturefiles --ref-maskfiles

pause