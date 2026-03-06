# 使用Python官方镜像作为基础
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将requirements.txt复制到容器
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将应用源代码复制到容器
COPY src/ ./src/

# 暴露8080端口
EXPOSE 8080

# 运行模拟WMS API
CMD ["python", "src/mock_wms_api.py"]
