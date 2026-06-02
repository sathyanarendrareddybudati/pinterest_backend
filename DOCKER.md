# Docker Setup for Pinterest Backend

This project includes Docker and Docker Compose configuration for running the entire application stack locally.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 1.29+)

## Quick Start

### Build and Start All Services

```bash
docker-compose up --build
```

This command will:

- Build the FastAPI application image
- Start PostgreSQL database (port 5432)
- Start Redis cache (port 6379)
- Start Elasticsearch (port 9200)
- Start the FastAPI app (port 8000)

### Stop Services

```bash
docker-compose down
```

To also remove volumes (database data will be deleted):

```bash
docker-compose down -v
```

## Services

### PostgreSQL

- **Container**: pinterest_postgres
- **Port**: 5432
- **Username**: pinterest_user
- **Password**: pinterest_password
- **Database**: pinterest
- **Volume**: postgres_data

### Redis

- **Container**: pinterest_redis
- **Port**: 6379
- **Volume**: redis_data

### Elasticsearch

- **Container**: pinterest_elasticsearch
- **Port**: 9200
- **Volume**: elasticsearch_data
- **Single-node cluster** (security disabled for development)

### FastAPI Application

- **Container**: pinterest_backend
- **Port**: 8000
- **Base URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Configuration

Environment variables are set in `docker-compose.yml`. Key variables:

```yaml
DATABASE_URL: postgresql://pinterest_user:pinterest_password@postgres:5432/pinterest
REDIS_URL: redis://redis:6379/0
ELASTICSEARCH_URL: http://elasticsearch:9200
```

### Override Environment Variables

Create a `.env.local` file or `docker-compose.override.yml` to customize settings:

```yaml
# docker-compose.override.yml example
services:
  app:
    environment:
      CLOUDINARY_CLOUD_NAME: your_value
      CLOUDINARY_API_KEY: your_key
      CLOUDINARY_API_SECRET: your_secret
```

## Common Commands

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs app
docker-compose logs postgres
docker-compose logs redis
docker-compose logs elasticsearch

# Follow logs in real-time
docker-compose logs -f app
```

### Execute Commands in Container

```bash
# Run Python command
docker-compose exec app python -c "from app.main import app; print(app)"

# Access PostgreSQL
docker-compose exec postgres psql -U pinterest_user -d pinterest

# Access Redis CLI
docker-compose exec redis redis-cli

# Access Elasticsearch
docker-compose exec elasticsearch curl http://localhost:9200
```

### Database Migrations

```bash
# Create database tables
docker-compose exec app python -c "from app.main import app; from app.models.models import Base; from app.core.database import engine; Base.metadata.create_all(bind=engine)"
```

## Troubleshooting

### Port Already in Use

If a port is already in use, modify the port mapping in `docker-compose.yml`:

```yaml
services:
  app:
    ports:
      - "8001:8000" # Changed from 8000:8000
```

### Service Failing to Start

Check logs:

```bash
docker-compose logs service_name
```

### Permission Denied on Unix Sockets

Run with `sudo` or add your user to the docker group:

```bash
sudo usermod -aG docker $USER
```

### Clean Rebuild

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## Development

### Reload Code Changes

The app runs with `--reload` flag, so changes to code are automatically reloaded.

### Install New Dependencies

1. Update `requirements.txt`
2. Rebuild the image:

```bash
docker-compose build app
docker-compose up
```

## Production Deployment

For production, create a `docker-compose.prod.yml`:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Security Recommendations

- Disable `--reload` flag
- Set strong passwords for database and Redis
- Enable Elasticsearch security
- Use environment-specific `.env` files
- Set `CLOUDINARY_*` and other secrets via Docker secrets or environment variables
- Use a reverse proxy (Nginx) in front

## Performance Tuning

### Elasticsearch Memory

Edit `docker-compose.yml`:

```yaml
elasticsearch:
  environment:
    - ES_JAVA_OPTS=-Xms2g -Xmx2g # Increase as needed
```

### PostgreSQL Optimization

Add to `docker-compose.yml`:

```yaml
postgres:
  command:
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "effective_cache_size=1GB"
```

## Useful Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Redis Docker Image](https://hub.docker.com/_/redis)
- [Elasticsearch Docker Image](https://www.docker.elastic.co/)

## Next Steps

1. Start containers: `docker-compose up`
2. Check API health: `curl http://localhost:8000/`
3. Access API docs: `http://localhost:8000/docs`
4. Monitor logs: `docker-compose logs -f`
