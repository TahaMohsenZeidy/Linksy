# Linksy

A modern social media platform built with FastAPI and React, featuring user authentication, posts, comments, likes, and image uploads.

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **Alembic** - Database migrations
- **Keycloak** - Authentication and user management
- **MinIO** - Object storage for images
- **SQLAlchemy** - ORM for database operations

### Frontend
- **React** - UI framework
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Styling

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## Features

- User authentication via Keycloak
- User profiles with profile pictures
- Create, edit, and delete posts
- Post images support
- Comments system with threaded discussions
- Like/unlike posts
- Real-time like and comment counts
- Responsive UI

## Project Structure

```
linksy/
├── backend/           # FastAPI backend
│   ├── src/          # Application source code
│   ├── alembic/      # Database migrations
│   └── Dockerfile    # Backend container definition
├── frontend/         # React frontend
│   ├── src/          # React components and pages
│   └── Dockerfile    # Frontend container definition
├── docker-compose.yml           # Main compose file
├── docker-compose.dev.yml        # Development environment
└── docker-compose.prod.yml      # Production environment
```

## Prerequisites

- Docker and Docker Compose
- Git

## Quick Start

### Development

1. Clone the repository:
```bash
git clone <repository-url>
cd linksy
```

2. Set up environment variables:
```bash
# Backend environment
cp backend/.env.example backend/.env.dev
# Edit backend/.env.dev with your configuration
```

3. Start development environment:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Keycloak Admin: http://localhost:8080 (admin/admin)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

### Production

1. Set up environment variables:
```bash
# Backend environment
cp backend/.env.example backend/.env.prod
# Edit backend/.env.prod with production values
```

2. Start production environment:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

The backend will automatically:
- Wait for PostgreSQL to be ready
- Initialize Keycloak database
- Run database migrations
- Start the FastAPI application

## Environment Variables

### Backend (.env.prod)

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/linksy
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_CLIENT_ID=linksy-backend
KEYCLOAK_CLIENT_SECRET=your-secret
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=profile-pics
CORS_ORIGINS=http://localhost:3000
```

## Database Migrations

Migrations are handled automatically in production via the entrypoint script. For manual migration:

```bash
# Development
docker exec linksy-backend-container-dev alembic upgrade head

# Production
docker exec linksy-backend-container-prod alembic upgrade head
```

## API Documentation

Once the backend is running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Workflow

### Backend

1. Make changes to Python code in `backend/src/`
2. Create migration for schema changes:
```bash
docker exec linksy-backend-container-dev alembic revision --autogenerate -m "description"
```
3. Apply migration:
```bash
docker exec linksy-backend-container-dev alembic upgrade head
```

### Frontend

1. Make changes to React code in `frontend/src/`
2. Changes are hot-reloaded automatically in development mode

## Keycloak Setup

1. Access Keycloak Admin Console: http://localhost:8080
2. Login with admin credentials
3. Create a realm named `linksy`
4. Create a client `linksy-backend` with:
   - Client protocol: `openid-connect`
   - Access Type: `confidential`
   - Valid Redirect URIs: `*`
5. Note the client secret and add it to `.env.prod`

## MinIO Setup

MinIO is automatically configured. The bucket is created on first use. Access the console at http://localhost:9001 to manage buckets and policies.

## Volumes

The application uses Docker volumes for persistent data:
- `postgres_data` - Database files
- `keycloak_data` - Keycloak configuration and data
- `minio_data` - Object storage files
- `pgadmin_data` - PgAdmin configuration

## Troubleshooting

### Backend won't start
- Check PostgreSQL is healthy: `docker-compose ps`
- Verify environment variables in `.env.prod`
- Check logs: `docker logs linksy-backend-container-prod`

### Migrations fail
- Ensure PostgreSQL is running and accessible
- Check DATABASE_URL is correct
- Verify database exists

### Images not displaying
- Check MinIO is running: `docker logs linksy_minio_prod`
- Verify bucket exists and has correct policies
- Check presigned URL generation in backend logs

## License

[Your License Here]

