# Deployment Guide

This guide explains how to deploy the AI Educational Content Generator in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Environment Variables](#environment-variables)
3. [Adapter Configuration](#adapter-configuration)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Troubleshooting](#troubleshooting)

## Local Development

### Backend Setup

1. **Create virtual environment:**

```bash
cd backend
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Run development server:**

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API docs at: http://localhost:8000/docs
```

### Frontend Setup

1. **Install dependencies:**

```bash
cd vue-project
npm install
```

2. **Configure environment:**

```bash
# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env
```

3. **Run development server:**

```bash
npm run dev
# Access at: http://localhost:5173
```

## Environment Variables

### Backend Configuration

Create `backend/.env` with the following variables:

```bash
# ============================================
# APPLICATION SETTINGS
# ============================================
APP_ENV=development          # development, staging, production
DEBUG=true                   # Enable debug mode
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL

# ============================================
# AI ADAPTER CONFIGURATION
# ============================================
AI_ADAPTER=mock             # Options: mock, custom, openai, anthropic

# ============================================
# CUSTOM AI PROVIDER (if using custom adapter)
# ============================================
CUSTOM_AI_API_URL=https://api.example.com/v1
CUSTOM_AI_API_KEY=your_api_key_here
CUSTOM_AI_MODEL=your_model_name
CUSTOM_AI_TIMEOUT=60

# ============================================
# API SETTINGS
# ============================================
API_TIMEOUT=60              # Request timeout in seconds
MAX_RETRIES=3               # Max retry attempts for failed requests
RATE_LIMIT_PER_MINUTE=60   # Requests per minute per user

# ============================================
# CORS SETTINGS
# ============================================
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# ============================================
# LOGGING
# ============================================
LOG_FILE=logs/app.log
LOG_MAX_BYTES=10485760      # 10MB
LOG_BACKUP_COUNT=5
```

### Frontend Configuration

Create `vue-project/.env`:

```bash
# API endpoint
VITE_API_URL=http://localhost:8000

# Optional: Enable debug mode
VITE_DEBUG=true

# Optional: Analytics (if you add it)
VITE_ANALYTICS_ID=
```

## Adapter Configuration

### Using Mock Adapter (Default)

No configuration needed. Perfect for demos and testing.

```bash
AI_ADAPTER=mock
```

The mock adapter returns realistic sample data without external API calls.

### Using Custom Adapter

1. **Set adapter type:**

```bash
AI_ADAPTER=custom
```

2. **Configure your API:**

```bash
CUSTOM_AI_API_URL=https://api.yourprovider.com/v1
CUSTOM_AI_API_KEY=sk-your-api-key-here
CUSTOM_AI_MODEL=your-model-name
CUSTOM_AI_TIMEOUT=60
```

3. **Implement adapter** (if needed):

Edit `backend/app/adapters/custom.py` to match your API's format.

### Using OpenAI

```bash
AI_ADAPTER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4
OPENAI_ORG_ID=org-your-org-id  # Optional
```

### Using Anthropic

```bash
AI_ADAPTER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL=claude-3-opus-20240229
```

### Using Self-Hosted Models (Ollama)

```bash
AI_ADAPTER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

## Production Deployment

### Option 1: Traditional Server (VPS/VM)

#### Backend Deployment

1. **Install system dependencies:**

```bash
sudo apt update
sudo apt install python3.9 python3-pip python3-venv nginx
```

2. **Setup application:**

```bash
cd /var/www/ai-content-generator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure systemd service:**

Create `/etc/systemd/system/ai-content-api.service`:

```ini
[Unit]
Description=AI Content Generator API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/ai-content-generator/backend
Environment="PATH=/var/www/ai-content-generator/venv/bin"
EnvironmentFile=/var/www/ai-content-generator/backend/.env
ExecStart=/var/www/ai-content-generator/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile /var/log/ai-content-api/access.log \
    --error-logfile /var/log/ai-content-api/error.log

[Install]
WantedBy=multi-user.target
```

4. **Start service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-content-api
sudo systemctl start ai-content-api
```

5. **Configure Nginx:**

Create `/etc/nginx/sites-available/ai-content-generator`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running AI requests
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/ai-content-generator /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Frontend Deployment

1. **Build production bundle:**

```bash
cd vue-project
npm run build
```

2. **Deploy to static hosting:**

```bash
# Copy dist/ folder to web server
sudo cp -r dist/* /var/www/html/
```

Or use static hosting services:
- **Netlify**: `netlify deploy --prod --dir=dist`
- **Vercel**: `vercel --prod`
- **AWS S3**: `aws s3 sync dist/ s3://your-bucket/`

### Option 2: Docker Deployment

#### Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY prompt_templates/ ./prompt_templates/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

Create `vue-project/Dockerfile`:

```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - AI_ADAPTER=${AI_ADAPTER}
      - CUSTOM_AI_API_KEY=${CUSTOM_AI_API_KEY}
    env_file:
      - ./backend/.env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./vue-project
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  logs:
```

**Deploy:**

```bash
docker-compose up -d
```

### Option 3: Cloud Platform Deployment

#### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
cd backend
eb init -p python-3.9 ai-content-generator

# Create environment
eb create production-env

# Deploy
eb deploy
```

#### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-content-api

# Deploy
gcloud run deploy ai-content-api \
  --image gcr.io/PROJECT_ID/ai-content-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Heroku

```bash
# Login
heroku login

# Create app
heroku create ai-content-generator

# Set environment variables
heroku config:set AI_ADAPTER=custom
heroku config:set CUSTOM_AI_API_KEY=your_key

# Deploy
git push heroku main
```

## Troubleshooting

### Backend Issues

**Problem**: Module not found errors

```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Problem**: Port already in use

```bash
# Solution: Change port or kill process
lsof -ti:8000 | xargs kill -9
# Or use different port
uvicorn app.main:app --port 8001
```

**Problem**: CORS errors

```bash
# Solution: Check CORS_ORIGINS in .env
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com
```

### Frontend Issues

**Problem**: API connection refused

```bash
# Solution: Check VITE_API_URL in .env
VITE_API_URL=http://localhost:8000
```

**Problem**: Build fails

```bash
# Solution: Clear cache and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Adapter Issues

**Problem**: Mock adapter not working

```bash
# Solution: Verify adapter setting
AI_ADAPTER=mock  # Must be lowercase
```

**Problem**: Custom adapter timeout

```bash
# Solution: Increase timeout
CUSTOM_AI_TIMEOUT=120
API_TIMEOUT=120
```

### Performance Issues

**Problem**: Slow response times

```bash
# Solution 1: Increase workers
gunicorn --workers 8 app.main:app

# Solution 2: Enable caching (implement Redis)
# Solution 3: Use faster AI model
```

**Problem**: High memory usage

```bash
# Solution: Limit worker memory
gunicorn --max-requests 1000 --max-requests-jitter 50
```

## Health Checks

### Backend Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "adapter": "mock",
  "version": "1.0.0"
}
```

### Frontend Health Check

```bash
curl http://localhost:5173
# Should return 200 OK
```

## Monitoring

### Logging

Backend logs location:
- Development: `backend/logs/app.log`
- Production: `/var/log/ai-content-api/`

View logs:
```bash
# Development
tail -f backend/logs/app.log

# Production (systemd)
sudo journalctl -u ai-content-api -f
```

### Metrics (Future Enhancement)

Consider adding:
- Prometheus for metrics collection
- Grafana for visualization
- Sentry for error tracking
- DataDog for APM

## Security Checklist

- [ ] Change all default passwords/keys
- [ ] Enable HTTPS (use Let's Encrypt)
- [ ] Set secure CORS origins
- [ ] Implement rate limiting
- [ ] Enable firewall rules
- [ ] Regular security updates
- [ ] Backup environment variables
- [ ] Use secrets manager (AWS Secrets Manager, etc.)
- [ ] Enable audit logging
- [ ] Implement authentication (if needed)

## Backup and Recovery

### Backup Configuration

```bash
# Backup environment files
tar -czf config-backup-$(date +%Y%m%d).tar.gz backend/.env vue-project/.env

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz backend/logs/
```

### Recovery

```bash
# Restore configuration
tar -xzf config-backup-20240101.tar.gz

# Restart services
sudo systemctl restart ai-content-api
```

## Scaling Strategies

### Horizontal Scaling

1. **Load Balancer**: Nginx, HAProxy, or cloud LB
2. **Multiple Backend Instances**: Run on different ports/servers
3. **Session Management**: Use Redis for shared state (if needed)

### Vertical Scaling

1. **Increase Resources**: More CPU/RAM for server
2. **Optimize Code**: Profile and optimize bottlenecks
3. **Database Optimization**: If database is added

## Support

For issues or questions:
1. Check logs for error messages
2. Review environment variable configuration
3. Verify adapter implementation
4. Test with mock adapter first
5. Check network connectivity to AI provider

---

**Note**: This is a portfolio project. Adapt deployment strategies to your specific infrastructure and requirements.
