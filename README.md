# Linksy - Social Media Platform

A full-stack social media application built with FastAPI (backend) and React (frontend).

## 🏗️ Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite
- **Database**: PostgreSQL
- **Authentication**: Keycloak
- **Storage**: MinIO (S3-compatible)
- **Containerization**: Docker & Docker Compose

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Development

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

**Services:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Keycloak: http://localhost:8080
- MinIO Console: http://localhost:9001
- PgAdmin: http://localhost:5050

### Production

```bash
# Set up environment variables
cp backend/.env.example backend/.env.prod
# Edit backend/.env.prod with production values

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

## 📁 Project Structure

```
linksy/
├── backend/          # FastAPI backend
│   ├── src/         # Source code
│   ├── alembic/     # Database migrations
│   └── Dockerfile
├── frontend/         # React frontend
│   ├── src/         # Source code
│   └── Dockerfile
├── docker-compose.yml           # Default compose (dev)
├── docker-compose.dev.yml       # Development environment
├── docker-compose.prod.yml      # Production environment
└── README.md
```

## 🔧 Features

- ✅ User authentication (Keycloak)
- ✅ Posts with images
- ✅ Comments system
- ✅ Like functionality
- ✅ User profiles
- ✅ Image upload (MinIO)

## 🗄️ Database Migrations

Migrations run automatically on container startup in production via `entrypoint.sh`.

For manual migration:
```bash
docker exec linksy-backend-container-dev alembic upgrade head
```

## 🔐 Environment Variables

### Backend (.env.prod)
- `DATABASE_URL` - PostgreSQL connection string
- `KEYCLOAK_URL` - Keycloak server URL
- `KEYCLOAK_CLIENT_ID` - Keycloak client ID
- `KEYCLOAK_CLIENT_SECRET` - Keycloak client secret
- `MINIO_ENDPOINT` - MinIO endpoint
- `MINIO_ACCESS_KEY` - MinIO access key
- `MINIO_SECRET_KEY` - MinIO secret key
- `CORS_ORIGINS` - Allowed CORS origins

## 📝 Development

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

## 🐳 Docker Services

- **postgres**: PostgreSQL database
- **keycloak**: Authentication server
- **minio**: Object storage
- **backend**: FastAPI application
- **frontend**: React application
- **pgadmin**: Database administration (dev only)

## 📦 Volumes

- `postgres_data_*`: Database data
- `keycloak_data_*`: Keycloak configuration
- `minio_data_*`: Object storage data
- `pgadmin_data_*`: PgAdmin configuration

## 🔄 Production Deployment

1. Set environment variables in `backend/.env.prod`
2. Build and start: `docker-compose -f docker-compose.prod.yml up -d`
3. The entrypoint script will:
   - Wait for PostgreSQL
   - Initialize Keycloak database
   - Run Alembic migrations
   - Start the application

## 📚 API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 🛠️ Troubleshooting

### Database Connection Issues
- Check `DATABASE_URL` in `.env.prod`
- Ensure PostgreSQL container is healthy
- Check network connectivity

### Keycloak Issues
- Verify Keycloak database exists
- Check Keycloak logs: `docker logs linksy_keycloak_prod`

### MinIO Issues
- Check MinIO console: http://localhost:9001
- Verify bucket exists and CORS is configured

## 📄 License

[Your License Here]

