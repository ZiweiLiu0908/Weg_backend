# 使用官方 Python 运行环境作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将依赖文件复制到容器中
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录下的代码复制到容器的工作目录中
COPY . .

# 设置对外暴露的端口号，与 uvicorn 运行端口一致
EXPOSE 8000

# 启动 FastAPI 应用，使用 uvicorn 作为 ASGI 服务器
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
