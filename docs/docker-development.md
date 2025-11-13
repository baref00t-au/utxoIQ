# Docker Development Environment

This guide explains how to run the entire utxoIQ stack in Docker for local development.

## Prerequisites

- Docker Desktop installed and running
- At least 4GB RAM allocated to Docker
- Ports 3000, 8000, 5432, 6379, 8085, 9050 available

## Quick Start

### Windows

```cmd
# Start all services
scripts\dev-docker.bat

# Stop all services
scripts\dev-docker-stop.bat
```

### Manual Start

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Services

The Docker environment includes:

| Service | Port | Description |
|---------|------|-------------|
| **frontend** | 3000 | Next.js web application |
| **web-api** | 8000 | FastAPI backend service |
| **postgres** | 5432 | PostgreSQL database |
| **redis** | 6379 | Redis cache |
| **bigquery-emulator** | 9050 | BigQuery emulator |
| **pubsub-emulator** | 8085 | Cloud Pub/Sub emulator |

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: `postgresql://utxoiq:utxoiq_dev_password@localhost:5432/utxoiq_db`
- **Redis**: `redis://localhost:6379`

## Development Workflow

### Hot Reload

Both frontend and backend support hot reload:

- **Frontend**: Edit files in `frontend/src/` - changes apply automatically
- **Backend**: Edit files in `services/web-api/src/` - server reloads automatically

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f web-api

# Last 100 lines
docker-compose logs --tail=100 web-api
```

### Restart a Service

```bash
# Restart frontend
docker-compose restart frontend

# Restart backend
docker-compose restart web-api

# Rebuild and restart
docker-compose up --build -d web-api
```

### Access Container Shell

```bash
# Frontend container
docker exec -it utxoiq-frontend sh

# Backend container
docker exec -it utxoiq-web-api bash

# Database
docker exec -it utxoiq-postgres psql -U utxoiq -d utxoiq_db
```

## Troubleshooting

### Port Already in Use

If you get port conflicts:

```bash
# Check what's using the port
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Stop the process or change the port in docker-compose.yml
```

### Services Not Starting

```bash
# Check service health
docker-compose ps

# View detailed logs
docker-compose logs web-api

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

### Database Connection Issues

```bash
# Check if PostgreSQL is healthy
docker-compose ps postgres

# Connect to database
docker exec -it utxoiq-postgres psql -U utxoiq -d utxoiq_db

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Frontend Not Loading

```bash
# Check if web-api is healthy
curl http://localhost:8000/health

# Rebuild frontend
docker-compose up --build -d frontend

# Check frontend logs
docker-compose logs -f frontend
```

## Environment Variables

Environment variables are configured in `docker-compose.yml`:

- **Frontend**: Uses `NEXT_PUBLIC_API_URL=http://web-api:8000` (internal Docker network)
- **Backend**: Connects to `postgres:5432` and `redis:6379` (internal Docker network)

To override, create a `.env` file in the root directory.

## Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (deletes database data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Production Build

To test production builds locally:

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Run production stack
docker-compose -f docker-compose.prod.yml up
```

## Network Architecture

All services run on the `utxoiq-network` Docker network:

```
┌─────────────────────────────────────────┐
│  Docker Network: utxoiq-network         │
│                                         │
│  ┌──────────┐      ┌──────────┐       │
│  │ frontend │─────▶│ web-api  │       │
│  │  :3000   │      │  :8000   │       │
│  └──────────┘      └────┬─────┘       │
│                          │              │
│       ┌──────────────────┼─────────┐   │
│       │                  │         │   │
│  ┌────▼────┐      ┌─────▼──┐  ┌──▼──┐│
│  │postgres │      │ redis  │  │ ... ││
│  │  :5432  │      │ :6379  │  │     ││
│  └─────────┘      └────────┘  └─────┘│
└─────────────────────────────────────────┘
```

## Tips

1. **Use Docker logs** instead of console.log for debugging
2. **Volume mounts** enable hot reload - no need to rebuild
3. **Health checks** ensure services start in correct order
4. **Named volumes** persist data between restarts
5. **Internal DNS** - services can reach each other by name (e.g., `web-api:8000`)
