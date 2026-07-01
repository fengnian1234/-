#!/bin/bash
# 云上·归墅 — 数据库备份脚本
# 自适应 PostgreSQL / SQLite 双数据库
# 用法: bash scripts/backup.sh
# 输出: backups/backup_YYYY-MM-DD_HHMMSS.sql.gz

set -euo pipefail

# 加载环境变量
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
DB_URL="${DATABASE_URL:-sqlite:///yunshang_bnb.db}"

echo "=== 云上·归墅 数据库备份 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"

if [[ "$DB_URL" == postgresql* ]]; then
    # PostgreSQL: 使用 pg_dump
    echo "检测到 PostgreSQL 数据库"
    BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"

    # 解析 DATABASE_URL: postgresql://user:pass@host:port/dbname
    pg_dump "$DB_URL" | gzip > "$BACKUP_FILE"

    echo "备份完成: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

elif [[ "$DB_URL" == sqlite* ]]; then
    # SQLite: 使用 sqlite3 .dump
    echo "检测到 SQLite 数据库"

    # 从 sqlite:///path 中提取路径
    DB_PATH="${DB_URL#sqlite:///}"
    DB_PATH="${DB_PATH#sqlite://}"

    if [ ! -f "$DB_PATH" ]; then
        echo "错误: 数据库文件不存在: $DB_PATH"
        exit 1
    fi

    BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"
    sqlite3 "$DB_PATH" .dump | gzip > "$BACKUP_FILE"

    echo "备份完成: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

else
    echo "错误: 无法识别的 DATABASE_URL 格式: $DB_URL"
    exit 1
fi

# 清理 30 天前的旧备份
echo "清理 30 天前的旧备份..."
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +30 -delete -print

echo "=== 备份完成 ==="
