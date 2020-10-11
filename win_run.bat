title 订阅微博并同步至电报 - [运行中]
@echo off
color 0a
cls
:start
python ./weibo.py
ping localhost -n 60 > nul
goto :start