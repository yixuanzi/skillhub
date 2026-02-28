# SkillHub 部署指南 (MVP)

## 1. 部署概述

本文档提供 SkillHub MVP 的部署指南。MVP 采用简化的部署方式，适合开发和测试环境。

### MVP 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                      单机部署                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Nginx (可选)                       │  │
│  │         SSL 终止 + 静态文件服务 + 反向代理          │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                       │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │              FastAPI 应用 (端口 8000)                │  │
│  │         后端服务 + SQLite 数据库                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  文件存储: backend/artifacts/                                │
│  数据库: data/skillhub.db                                     │
└─────────────────────────────────────────────────────────────┘
```

### 环境说明

| 环境 | 配置 | 数据库 |
|------|------|--------|
| development | 单进程 | SQLite 本地文件 |
| production | 多进程 + Nginx | SQLite 本地文件 |

---

## 2. 开发环境部署

### 2.1 启动应用

```bash
# 方式一：使用 run.py
python run.py

# 方式二：分别启动
# 终端 1
cd backend && python -m uvicorn main:app --reload --port 8000

# 终端 2
cd frontend && npm run dev
```

### 2.2 访问应用

- **后端**: http://localhost:8000
- **前端**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs

---

## 3. 生产环境部署

### 3.1 构建应用

#### 后端构建

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 初始化数据库
python init_db.py
```

#### 前端构建

```bash
cd frontend
npm install
npm run build

# 构建产物在 frontend/dist/ 目录
```

### 3.2 使用 systemd 部署

#### 创建服务文件

```ini
# /etc/systemd/system/skillhub.service
[Unit]
Description=SkillHub API Server
After=network.target

[Service]
Type=notify
User=skillhub
Group=skillhub
WorkingDirectory=/opt/skillhub
Environment="PATH=/opt/skillhub/venv/bin"
EnvironmentFile=/opt/skillhub/.env
ExecStart=/opt/skillhub/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 启动服务

```bash
# 创建用户
sudo useradd -r -s /bin/false skillhub

# 创建目录
sudo mkdir -p /opt/skillhub
sudo chown skillhub:skillhub /opt/skillhub

# 复制文件
sudo cp -r backend/* /opt/skillhub/
sudo cp .env /opt/skillhub/

# 设置权限
sudo chown -R skillhub:skillhub /opt/skillhub

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable skillhub
sudo systemctl start skillhub

# 查看状态
sudo systemctl status skillhub
```

### 3.3 使用 Docker Compose 部署

#### Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建目录
RUN mkdir -p /app/data /app/artifacts

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  skillhub:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./artifacts:/app/artifacts
    environment:
      - DATABASE_URL=sqlite:///data/skillhub.db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - skillhub
    restart: unless-stopped
```

#### 部署

```bash
# 构建前端
cd frontend
npm run build

# 启动服务
cd ..
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 4. 使用 Nginx 反向代理

### 4.1 Nginx 配置

```nginx
# /etc/nginx/sites-available/skillhub
server {
    listen 80;
    server_name skillhub.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name skillhub.example.com;

    ssl_certificate /etc/nginx/ssl/skillhub.crt;
    ssl_certificate_key /etc/nginx/ssl/skillhub.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    # 前端静态文件
    location / {
        root /opt/skillhub/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4.2 启用配置

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/skillhub /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 5. SSL 证书配置

### 5.1 使用 Let's Encrypt

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d skillhub.example.com

# 自动续期
sudo certbot renew --dry-run
```

### 5.2 自签名证书（开发环境）

```bash
# 创建证书目录
sudo mkdir -p /etc/nginx/ssl

# 生成自签名证书
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/skillhub.key \
    -out /etc/nginx/ssl/skillhub.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=skillhub.example.com"
```

---

## 6. 环境变量配置

### 6.1 生产环境 .env

```bash
# backend/.env
DATABASE_URL=sqlite:///data/skillhub.db
JWT_SECRET_KEY=<使用 openssl rand -base64 32 生成>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ARTIFACTS_DIR=/app/artifacts

# CORS 配置
CORS_ORIGINS=["https://skillhub.example.com"]

# 日志级别
LOG_LEVEL=INFO
```

### 6.2 生成 JWT 密钥

```bash
# 生成强随机密钥
openssl rand -base64 32
```

---

## 7. 数据备份

### 7.1 备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/skillhub"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/opt/skillhub/data/skillhub.db"
ARTIFACTS_PATH="/opt/skillhub/artifacts"

# 创建备份目录
mkdir -p "$BACKUP_DIR/$DATE"

# 备份数据库
cp "$DB_PATH" "$BACKUP_DIR/$DATE/skillhub.db"

# 备份构建产物
tar -czf "$BACKUP_DIR/$DATE/artifacts.tar.gz" -C "$ARTIFACTS_PATH" .

# 删除 30 天前的备份
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR/$DATE"
```

### 7.2 定时备份

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /opt/skillhub/scripts/backup.sh
```

---

## 8. 监控和日志

### 8.1 日志配置

```python
# backend/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/skillhub/app.log'),
        logging.StreamHandler()
    ]
)
```

### 8.2 日志轮转

```bash
# /etc/logrotate.d/skillhub
/var/log/skillhub/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 skillhub skillhub
    sharedscripts
    postrotate
        systemctl reload skillhub > /dev/null 2>&1 || true
    endscript
}
```

---

## 9. 性能优化

### 9.1 多进程部署

```bash
# 使用 gunicorn 启动多进程
pip install gunicorn

gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/skillhub/access.log \
    --error-logfile /var/log/skillhub/error.log
```

### 9.2 Nginx 缓存配置

```nginx
# 缓存静态文件
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# 缓存 API 响应
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=skillhub_cache:10m max_size=100m inactive=60m;

location /api/ {
    proxy_cache skillhub_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
}
```

---

## 10. 故障排查

### 10.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 502 Bad Gateway | 后端服务未启动 | 检查服务状态 |
| 404 Not Found | 静态文件路径错误 | 检查 nginx root 配置 |
| CORS 错误 | 前端域名未配置 | 更新 CORS_ORIGINS |
| Token 无效 | JWT_SECRET_KEY 不一致 | 确保前后端使用相同密钥 |

### 10.2 查看日志

```bash
# 后端日志
sudo journalctl -u skillhub -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 应用日志
sudo tail -f /var/log/skillhub/app.log
```

---

## 11. 更新部署

### 11.1 更新流程

```bash
# 1. 备份数据
sudo /opt/skillhub/scripts/backup.sh

# 2. 拉取最新代码
cd /opt/skillhub
git pull origin main

# 3. 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 4. 执行数据库迁移
alembic upgrade head

# 5. 重新构建前端
cd frontend
npm install
npm run build

# 6. 重启服务
sudo systemctl restart skillhub
sudo systemctl reload nginx
```

---

## 12. 安全加固

### 12.1 防火墙配置

```bash
# 使用 ufw
sudo apt install ufw

# 允许 SSH
sudo ufw allow 22/tcp

# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

### 12.2 文件权限

```bash
# 设置正确的文件权限
sudo chown -R skillhub:skillhub /opt/skillhub
sudo chmod 750 /opt/skillhub
sudo chmod 640 /opt/skillhub/.env
sudo chmod 600 /opt/skillhub/data/skillhub.db
```

---

**文档版本**: v2.0 (MVP)
**最后更新**: 2025-02-28
