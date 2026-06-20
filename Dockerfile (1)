# ══════════════════════════════════════════════════════════
# 云上归墅 · 微信公众号客服系统
# Python 3.10 + Gunicorn + Nginx
# ══════════════════════════════════════════════════════════
FROM python:3.10-slim

LABEL maintainer="云上归墅"
LABEL description="微信公众号AI客服系统"

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Shanghai

# 安装系统依赖（psycopg2 编译依赖 + 时区数据）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# 工作目录
WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir psycopg2-binary

# 复制项目代码
COPY . .

# 静态文件 / 上传目录
RUN mkdir -p /app/local_data/images /app/local_data/documents /app/reports

# 暴露端口（Gunicorn）
EXPOSE 8000

# 启动脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
