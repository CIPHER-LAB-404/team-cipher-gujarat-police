# 🚀 SENTINEL Production Deployment Guide
### Enterprise-Grade Setup for State Police Command Infrastructure

---

## 1. System Requirements

### Hardware Requirements (Per Node / 5,000 Streams)
* **Processor**: 16-Core x86_64 CPU (Intel Xeon / AMD EPYC)
* **RAM**: 64 GB DDR4/DDR5 ECC RAM
* **Storage**: 1 TB NVMe SSD (OS + Buffers) + High-Throughput Network Attached Storage (NAS)
* **GPU**: NVIDIA RTX A4000 / T4 (TensorRT acceleration for edge ANPR)
* **Network**: 10 Gbps SFP+ Dedicated Leased Fiber to State Data Center (SDC)

### Software Prerequisites
* **Operating System**: Ubuntu 22.04 LTS / Red Hat Enterprise Linux 9 / Windows Server 2022
* **Python Runtime**: Python 3.10+
* **Reverse Proxy**: Nginx 1.24+ with WebSocket and HTTP/2 support
* **SSL/TLS**: Valid State Government SSL Certificate (`.gov.in`)

---

## 2. Standard Local & VM Deployment

### Step 1: Clone & Configure Workspace
```bash
git clone https://github.com/GujaratPolice/sentinel.git /opt/sentinel
cd /opt/sentinel
```

### Step 2: Create Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run FastAPI Production Server
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 3. Production Systemd Service Configuration

Create `/etc/systemd/system/sentinel.service`:

```ini
[Unit]
Description=Gujarat Police Sentinel Command & CCTV Intelligence Platform
After=network.target

[Service]
User=sentinel
Group=sentinel
WorkingDirectory=/opt/sentinel/backend
ExecStart=/opt/sentinel/.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5
Environment="PATH=/opt/sentinel/.venv/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sentinel
sudo systemctl start sentinel
sudo systemctl status sentinel
```

---

## 4. Nginx Reverse Proxy & SSL Configuration

Create `/etc/nginx/sites-available/sentinel.conf`:

```nginx
server {
    listen 80;
    server_name sentinel.police.gujarat.gov.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sentinel.police.gujarat.gov.in;

    ssl_certificate /etc/ssl/certs/sentinel.gujaratpolice.gov.in.crt;
    ssl_certificate_key /etc/ssl/private/sentinel.gujaratpolice.gov.in.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Static Assets & Frontends
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket Real-Time Alert Stream
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

---

## 5. Docker Container Deployment

### `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Build & Run Container:
```bash
docker build -t gujarat-police/sentinel:2026.1 .
docker run -d --name sentinel-command -p 8000:8000 --restart unless-stopped gujarat-police/sentinel:2026.1
```
