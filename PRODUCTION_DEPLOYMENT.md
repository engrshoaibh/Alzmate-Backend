# Production Deployment Guide

## Quick Start Commands

### Option 1: Using Uvicorn (Recommended for development/small production)

```bash
# Activate virtual environment
source env/bin/activate  # Linux/Mac
# OR
env\Scripts\activate  # Windows

# Start with production settings
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

### Option 2: Using Gunicorn with Uvicorn Workers (Recommended for production)

```bash
# Activate virtual environment
source env/bin/activate

# Start with Gunicorn
gunicorn main:app -c gunicorn_config.py
```

### Option 3: Using Docker (Recommended for containerized deployments)

```bash
docker build -t alzmate-backend .
docker run -p 8000:8000 --env-file .env alzmate-backend
```

## Production Start Scripts

### Linux/Mac
```bash
chmod +x start_production.sh
./start_production.sh
```

### Windows
```cmd
start_production.bat
```

## Environment Variables

Set these environment variables before starting:

```bash
# Required: Firebase Configuration
export FIREBASE_PROJECT_ID="your-project-id"
export FIREBASE_CREDENTIALS_PATH="/path/to/service-account-key.json"
# OR
export FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'

# Optional: Cloudinary (defaults are in config.py)
export CLOUDINARY_CLOUD_NAME="dkiqc4jru"
export CLOUDINARY_API_KEY="659932293576982"
export CLOUDINARY_API_SECRET="1f7M0nZpCLZ1F7ytj1CYwaV2xo8"
export CLOUDINARY_UPLOAD_PRESET="alzMate"
```

## Production Settings

### Uvicorn Production Command

```bash
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log \
    --no-use-colors
```

**Parameters:**
- `--host 0.0.0.0`: Listen on all network interfaces
- `--port 8000`: Port number
- `--workers 4`: Number of worker processes (adjust based on CPU cores)
- `--log-level info`: Logging level
- `--access-log`: Enable access logging
- `--no-use-colors`: Disable colors for production logs

### Gunicorn Production Command

```bash
gunicorn main:app -c gunicorn_config.py
```

**Configuration:**
- Workers: Automatically set to `CPU_COUNT * 2 + 1`
- Worker class: UvicornWorker (async support)
- Timeout: 30 seconds
- Logging: To stdout/stderr

## Systemd Service (Linux)

Create `/etc/systemd/system/alzmate-backend.service`:

```ini
[Unit]
Description=AlzMate Emotion Analysis Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/BackendModel
Environment="PATH=/path/to/BackendModel/env/bin"
Environment="FIREBASE_PROJECT_ID=your-project-id"
Environment="FIREBASE_CREDENTIALS_PATH=/path/to/service-account-key.json"
ExecStart=/path/to/BackendModel/env/bin/gunicorn main:app -c gunicorn_config.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable alzmate-backend
sudo systemctl start alzmate-backend
sudo systemctl status alzmate-backend
```

## Nginx Reverse Proxy (Recommended)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start command
CMD ["gunicorn", "main:app", "-c", "gunicorn_config.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}
      - FIREBASE_CREDENTIALS_PATH=/app/credentials.json
      - CLOUDINARY_CLOUD_NAME=${CLOUDINARY_CLOUD_NAME}
      - CLOUDINARY_API_KEY=${CLOUDINARY_API_KEY}
      - CLOUDINARY_API_SECRET=${CLOUDINARY_API_SECRET}
    volumes:
      - ./credentials.json:/app/credentials.json:ro
    restart: unless-stopped
```

## Performance Tuning

### Worker Count
- **Uvicorn**: `--workers 4` (adjust based on CPU cores)
- **Gunicorn**: Auto-calculated as `CPU_COUNT * 2 + 1`

### Memory Considerations
- Each worker loads the ML model (~500MB-1GB)
- Total memory needed: `workers * model_size + base_memory`
- Recommended: 4GB+ RAM for 4 workers

### Timeout Settings
- Increase timeout for large file uploads
- Default: 30 seconds
- For audio uploads: Consider 60-120 seconds

## Monitoring

### Health Check Endpoint
```bash
curl http://localhost:8000/
```

### Logs
- Access logs: stdout
- Error logs: stderr
- Application logs: Check uvicorn/gunicorn output

### Metrics
Consider adding:
- Prometheus metrics
- Application performance monitoring (APM)
- Error tracking (Sentry)

## Security Checklist

- [ ] Use HTTPS in production (Nginx/SSL)
- [ ] Set proper CORS origins
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Monitor for vulnerabilities

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>
```

### Memory Issues
- Reduce worker count
- Use model quantization
- Enable model caching

### Firebase Connection Issues
- Verify credentials path
- Check network connectivity
- Verify project ID

## Quick Reference

### Start Production Server
```bash
# Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Gunicorn
gunicorn main:app -c gunicorn_config.py

# Docker
docker-compose up -d
```

### Stop Server
```bash
# Find and kill process
pkill -f "uvicorn main:app"
# OR
pkill -f "gunicorn main:app"

# Docker
docker-compose down
```

### View Logs
```bash
# Systemd
sudo journalctl -u alzmate-backend -f

# Docker
docker-compose logs -f
```






