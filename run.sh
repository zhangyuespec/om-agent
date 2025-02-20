#!/bin/bash

# 设置环境变量
export FLASK_APP=app.py
export FLASK_ENV=development

# 安装依赖
pip install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 启动应用
flask run --host=0.0.0.0 --port=8080