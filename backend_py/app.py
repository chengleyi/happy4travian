"""应用入口模块

此模块仅负责从工厂方法创建 Flask 应用实例。
"""
from factory import create_app

# 创建并导出 Flask 应用对象（供 gunicorn / flask 使用）
app = create_app()