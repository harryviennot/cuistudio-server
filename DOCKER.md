# Docker Deployment Guide

This guide explains how to run the cuistudio-server using Docker.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- `.env` file with required environment variables

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Build the image and start the container
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

The API will be available at `http://localhost:8000`

### 2. Stop the Application

```bash
docker-compose down
```

## Manual Docker Commands

### Build the Image

```bash
docker build -t cuistudio-server .
```

### Run the Container

```bash
docker run -d \
  --name cuistudio-server \
  -p 8000:8000 \
  --env-file .env \
  cuistudio-server
```

### View Logs

```bash
# Using docker-compose
docker-compose logs -f

# Using docker directly
docker logs -f cuistudio-server
```

### Stop and Remove Container

```bash
# Using docker-compose
docker-compose down

# Using docker directly
docker stop cuistudio-server
docker rm cuistudio-server
```

## Environment Variables

Make sure your `.env` file contains:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_publishable_key
SUPABASE_SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key

# Optional settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

## Health Check

The container includes a health check that pings the `/health` endpoint every 30 seconds.

Check container health:

```bash
docker ps
```

Look for the health status in the STATUS column.

## Development Mode

For development with hot-reload, you can mount your code as a volume:

```bash
docker run -d \
  --name cuistudio-server-dev \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd):/app \
  -e DEBUG=true \
  cuistudio-server
```

Or add to `docker-compose.yml`:

```yaml
services:
  cuistudio-server:
    # ... other config
    volumes:
      - .:/app
      - ./tmp:/tmp/recipe-app
    environment:
      - DEBUG=true
```

## Production Deployment

### Building for Production

```bash
# Build with a specific tag
docker build -t cuistudio-server:v1.0.0 .

# Tag for registry
docker tag cuistudio-server:v1.0.0 your-registry/cuistudio-server:v1.0.0

# Push to registry
docker push your-registry/cuistudio-server:v1.0.0
```

### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  cuistudio-server:
    # ... other config
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs
```

### Permission issues

Make sure the tmp directory exists and is writable:
```bash
mkdir -p tmp
chmod 755 tmp
```

### FFmpeg or Tesseract not found

These are included in the Docker image. If you see errors, rebuild the image:
```bash
docker-compose build --no-cache
```

### Memory issues

Increase Docker memory allocation in Docker Desktop settings (minimum 4GB recommended).

## Security Notes

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Use secrets management** in production (AWS Secrets Manager, Kubernetes secrets, etc.)
3. **Run as non-root user** - Consider adding this to Dockerfile for production:

```dockerfile
# Add before CMD
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
```

## Image Size

The current image is approximately 2-3GB due to:
- FFmpeg
- Tesseract OCR
- OpenCV
- Whisper model dependencies

To reduce size, consider multi-stage builds or removing unused dependencies.

## Kubernetes Deployment

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cuistudio-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cuistudio-server
  template:
    metadata:
      labels:
        app: cuistudio-server
    spec:
      containers:
      - name: cuistudio-server
        image: your-registry/cuistudio-server:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: cuistudio-secrets
              key: supabase-url
        # ... other env vars
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Support

For more information, see:
- [QUICKSTART.md](docs/QUICKSTART.md)
- [README.md](README.md)
