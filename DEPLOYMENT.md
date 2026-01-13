# Docker Deployment Guide

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Access at: `http://localhost:8501` or `http://127.0.0.1:8501`

### Using Make Commands

```bash
# Build and start
make start

# View logs
make logs

# Restart
make restart

# Stop and clean
make down
```

## Configuration

### Environment Variables

Create `.env` file in project root:

```env
OPENAI_API_KEY=sk-your-key-here
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
```

### Ollama Configuration

**Docker Deployment (default):**
The `config.yaml` is pre-configured for Docker with:
```yaml
ollama:
  base_url: "http://host.docker.internal:11434"
```

This allows the container to access Ollama running on your host machine.

**Local Development (non-Docker):**
When running locally with `streamlit run app.py`, use `config.local.yaml`:
```bash
cp config.local.yaml config.yaml
streamlit run app.py
```

Or manually update `config.yaml`:
```yaml
ollama:
  base_url: "http://localhost:11434"
```

### Verify Ollama Access

```bash
# Check Ollama is running on host
curl http://localhost:11434/api/tags

# Check from inside container
docker exec excel-ai-app curl http://host.docker.internal:11434/api/tags
```

## Production Deployment

### Behind Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  excel-ai:
    # ... other config
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Update Models

Edit `config.yaml` and restart:

```bash
docker-compose restart
# or
make restart
```

## Troubleshooting

**Issue: Can't connect to Ollama**
- Ensure Ollama is running: `ollama ps`
- Verify config uses `host.docker.internal:11434`
- Test access: `docker exec excel-ai-app curl http://host.docker.internal:11434/api/tags`

**Issue: API key not found**
- Verify `.env` file exists in project directory
- Check env vars in container: `docker exec excel-ai-app env | grep API_KEY`
- Restart container after updating `.env`: `docker-compose restart`

**Issue: Port already in use**
- Change port in `docker-compose.yml`: `"8502:8501"`
- Or stop conflicting service

**Issue: Container keeps restarting**
- Check logs: `docker logs excel-ai-app`
- Common causes: missing config files, invalid YAML syntax

**View detailed logs:**
```bash
docker-compose logs -f excel-ai
# or
make logs
```

## Alternative: Direct Docker Run

```bash
# Build image
docker build -t excel-ai .

# Run container
docker run -d \
  --name excel-ai \
  -p 8501:8501 \
  --add-host=host.docker.internal:host-gateway \
  --env-file .env \
  -v $(pwd)/config.yaml:/app/config.yaml \
  excel-ai

# View logs
docker logs -f excel-ai

# Stop and remove
docker stop excel-ai
docker rm excel-ai
```
