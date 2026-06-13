#!/bin/bash
# ══════════════════════════════════════════════════════════
# 云上归墅 · Docker 启动脚本
# 1. 等待 PostgreSQL 就绪
# 2. 初始化数据库表
# 3. 填充种子数据
# 4. 启动 Gunicorn
# ══════════════════════════════════════════════════════════
set -e

echo "🏔️  云上归墅 · 容器启动中..."

# ── 等待数据库 ───────────────────────────────────
if [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "⏳ 等待 PostgreSQL 就绪..."
    # 从 DATABASE_URL 解析主机（postgresql://user:pass@host:port/db）
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:/]*\).*|\1|p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_PORT=${DB_PORT:-5432}

    for i in $(seq 1 30); do
        if python3 -c "
import socket, sys
s = socket.socket()
try:
    s.settimeout(2)
    s.connect(('$DB_HOST', $DB_PORT))
    s.close()
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null; then
            echo "✅ PostgreSQL 已就绪"
            break
        fi
        echo "   等待数据库... ($i/30)"
        sleep 2
    done
else
    echo "📦 使用 SQLite（开发模式）"
fi

# ── 初始化数据库（建表 + 种子数据）───────────────
echo "📊 初始化数据库..."
python3 -c "
from app import app, init_app
with app.app_context():
    init_app()
    print('✅ 数据库表 + 种子数据就绪')
"

# ── 启动 Gunicorn ─────────────────────────────────
echo "🚀 启动 Gunicorn (4 workers)..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 30 \
    --graceful-timeout 15 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app
