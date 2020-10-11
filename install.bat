echo off
cls
pip install .\lxml-4.5.2-cp39-cp39-win_amd64.whl
pip install .\lxml-4.5.2-cp39-cp39-win32.whl
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
cls
pip install -r requirements.txt
pause