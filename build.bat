@echo off
REM 任务清单应用打包脚本

echo 正在打包任务清单应用...
pyinstaller --noconfirm --onefile --windowed --name="任务清单" ^
  --icon=icon.ico ^
  --add-data="data;data" ^
  main.py

echo 打包完成！
echo 可执行文件位于 dist/任务清单.exe
pause