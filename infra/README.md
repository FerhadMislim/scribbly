# Infrastructure

Docker configurations, Kubernetes manifests, and deployment configs for Scribbly.

## Getting Started

### Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Project Structure

```
infra/
├── docker/
│   ├── Dockerfile.backend-cpu
│   ├── Dockerfile.backend-gpu
│   └── Dockerfile.web
├── kubernetes/
│   ├── backend/
│   ├── gpu-worker/
│   └── postgres/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── Makefile
```

## Docker Images

| Image | Description | GPU |
|-------|------------|-----|
| `scribbly/backend-cpu` | FastAPI app, no GPU | No |
| `scribbly/backend-gpu` | FastAPI + CUDA + PyTorch | Yes |
| `scribbly/web` | Node build + nginx | No |

## Environment Variables

Create `backend/.env`:

```
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/scribbly
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT=http://minio:9000
S3_BUCKET=scribbly
S3_KEY=minioadmin
S3_SECRET=minioadmin
JWT_SECRET=your-secret-key
MODEL_PATH=/app/models
```

## Production Deployment

See [docs/deployment/](../docs/deployment/) for detailed deployment guides.

### Quick Deploy

```bash
# Backend to Fly.io
fly deploy --app scribbly-backend

# GPU worker
docker build -f infra/docker/Dockerfile.backend-gpu -t scribbly/gpu-worker .
docker push scribbly/gpu-worker
```

## Monitoring

- Health checks: `GET /health`
- Metrics: Prometheus endpoint at `/metrics`
- Logs: Shipped to CloudWatch/Loki via Fluent Bit
