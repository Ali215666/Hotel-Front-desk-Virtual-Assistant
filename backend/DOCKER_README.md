# Hotel Front Desk AI Backend - Docker Guide

## Quick Start

### Build and Run with Docker

```bash
# Build the Docker image
docker build -t hotel-ai-backend .

# Run the container
docker run -p 8000:8000 hotel-ai-backend

# Run with Ollama connection (if Ollama is on host)
docker run -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  hotel-ai-backend
```

### Build and Run with Docker Compose

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Dockerfile Features

✅ **Python 3.11 slim** - Minimal base image for smaller size
✅ **Non-root user** - Security best practice (runs as `appuser`)
✅ **Layer caching** - Optimized build with requirements first
✅ **Health checks** - Built-in container health monitoring
✅ **Production-ready** - Environment variables and optimizations
✅ **Small image size** - Cleaned apt cache and minimal dependencies

## Environment Variables

- `PYTHONDONTWRITEBYTECODE=1` - Prevents Python from writing pyc files
- `PYTHONUNBUFFERED=1` - Forces stdout/stderr to be unbuffered
- `OLLAMA_BASE_URL` - URL for Ollama API (default: http://localhost:11434)

## Endpoints

- **Health Check**: `http://localhost:8000/health`
- **REST API**: `http://localhost:8000/api/chat`
- **WebSocket**: `ws://localhost:8000/ws/chat`
- **API Docs**: `http://localhost:8000/docs`

## Building for Production

```bash
# Build with specific tag
docker build -t hotel-ai-backend:v1.0.0 .

# Build with multi-stage (if needed for even smaller images)
docker build --target production -t hotel-ai-backend:prod .

# Push to registry
docker tag hotel-ai-backend:v1.0.0 your-registry/hotel-ai-backend:v1.0.0
docker push your-registry/hotel-ai-backend:v1.0.0
```

## Development Mode

For development with hot-reload, use docker-compose with volume mounts:

```bash
docker-compose up
```

This mounts local code into the container for live updates.

## Troubleshooting

### Cannot connect to Ollama

If backend can't reach Ollama on host:

**Linux**: Use `--network host`
```bash
docker run --network host hotel-ai-backend
```

**Windows/Mac**: Use `host.docker.internal`
```bash
docker run -e OLLAMA_BASE_URL=http://host.docker.internal:11434 -p 8000:8000 hotel-ai-backend
```

### Permission Issues

Container runs as non-root user (`appuser`, UID 1000). If you have permission issues with volumes, ensure files are readable by UID 1000.

## Image Size Optimization

Current optimizations:
- Slim Python base image (~120MB vs ~900MB for full image)
- Minimal system dependencies
- No cached pip packages
- Cleaned apt cache
- `.dockerignore` excludes unnecessary files

Expected final image size: ~200-300MB
