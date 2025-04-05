@echo off
echo ===== 启动STEP/DWG到G代码转换器Web界面 =====
call gcode_env\Scripts\activate.bat && python web_interface.py
