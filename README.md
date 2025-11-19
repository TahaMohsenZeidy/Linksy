# Linksy - Social Media Platform

A full-stack social media application built with FastAPI (backend) and React (frontend).

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite
- **Database**: PostgreSQL
- **Authentication**: Keycloak
- **Storage**: MinIO (S3-compatible)
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Setup

```bash
# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration values

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Keycloak: http://localhost:8080
- MinIO Console: http://localhost:9001
- PgAdmin: http://localhost:5050

## Project Structure

```
linksy/
├── backend/          # FastAPI backend
│   ├── src/         # Source code
│   ├── alembic/     # Database migrations
│   ├── .env         # Environment variables
│   └── Dockerfile
├── frontend/         # React frontend
│   ├── src/         # Source code
│   └── Dockerfile
├── docker-compose.yml  # Docker Compose configuration
└── README.md
```

## Features

- User authentication (Keycloak)
- Posts with images
- Comments system
- Like functionality
- User profiles
- Image upload (MinIO)

## Database Migrations

Migrations run automatically on container startup via `entrypoint.sh`.

For manual migration:
```bash
docker exec linksy-backend-container alembic upgrade head
```

## Environment Variables

### Backend (.env)
- `DATABASE_URL` - PostgreSQL connection string
- `KEYCLOAK_URL` - Keycloak server URL
- `KEYCLOAK_CLIENT_ID` - Keycloak client ID
- `KEYCLOAK_CLIENT_SECRET` - Keycloak client secret
- `MINIO_ENDPOINT` - MinIO endpoint
- `MINIO_ACCESS_KEY` - MinIO access key
- `MINIO_SECRET_KEY` - MinIO secret key
- `CORS_ORIGINS` - Allowed CORS origins

## Development

### Running Backend Locally
```bash
cd backend
source linksyvenv/bin/activate
uvicorn src.main:app --reload
```

### Running Frontend Locally
```bash
cd frontend
npm install
npm run dev
```

## Docker Services

- **postgres**: PostgreSQL database
- **keycloak**: Authentication server
- **minio**: Object storage
- **backend**: FastAPI application
- **frontend**: React application
- **pgadmin**: Database administration (dev only)

## Volumes

- `postgres_data`: Database data
- `keycloak_data`: Keycloak configuration
- `minio_data`: Object storage data
- `pgadmin_data`: PgAdmin configuration

## Deployment

1. Set environment variables in `backend/.env`
2. Build and start: `docker-compose up -d`
3. The entrypoint script will:
   - Wait for PostgreSQL
   - Initialize Keycloak database
   - Run Alembic migrations
   - Start the application

## API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Troubleshooting

### Database Connection Issues
- Check `DATABASE_URL` in `backend/.env`
- Ensure PostgreSQL container is healthy
- Check network connectivity

### Keycloak Issues
- Verify Keycloak database exists
- Check Keycloak logs: `docker logs linksy_keycloak`

### MinIO Issues
- Check MinIO console: http://localhost:9001
- Verify bucket exists and CORS is configured


