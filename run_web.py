import os
import sys

# 确保Flask已安装
try:
    from flask import Flask
except ImportError:
    print("Flask未安装，正在安装...")
    os.system(f"{sys.executable} -m pip install flask")
    print("Flask安装完成")

from app.web_app import run_web_app

if __name__ == "__main__":
    print("启动Web应用...")
    print("请访问 http://localhost:5000 查看Web界面")
    run_web_app()
