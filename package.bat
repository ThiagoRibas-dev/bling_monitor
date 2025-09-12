@echo off
echo Cleaning up old build files...
rmdir /s /q build
rmdir /s /q dist
echo Packaging the application...
python -m PyInstaller --onefile inativa_produtos_estoque_zero.py
echo Packaging complete! The executable can be found in the 'dist' folder.
pause
