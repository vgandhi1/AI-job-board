# Deployment Guide

## Architecture Overview

### Current Setup: CORS-based Development

The application currently uses **CORS (Cross-Origin Resource Sharing)** for development. This means:

- **Backend** runs on `http://localhost:8000` (FastAPI)
- **Frontend** runs on `http://localhost:3000` (Next.js)
- **CORS middleware** in FastAPI allows the frontend to make API requests

This is suitable for:
- ✅ Local development
- ✅ Development environments
- ✅ Quick prototyping

### Production Setup: Nginx Reverse Proxy (Recommended)

For production, you should use **Nginx** as a reverse proxy to:

1. **Serve both frontend and backend** from a single domain
2. **Avoid CORS issues** (same origin)
3. **Handle SSL/TLS** termination
4. **Load balancing** and caching
5. **Better security** and performance

#### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (Next.js)
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://backend:8000/health;
    }
}
```

#### Docker Compose with Nginx

See `docker-compose.prod.yml` for a production-ready setup with Nginx.

## Running the Application

### Option 1: Docker Compose (Recommended)

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Run migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Add sample data (optional):**
   ```bash
   docker-compose exec backend python scripts/add_sample_jobs.py
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your settings
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
cp .env.example .env
# Edit .env with backend URL
npm install
npm run dev
```

## Why Separate requirements.txt?

**Keeping separate `requirements.txt` files is recommended** because:

1. **Different Technologies**: Backend uses Python, Frontend uses Node.js
2. **Different Dependencies**: They have completely different dependency ecosystems
3. **Separation of Concerns**: Each service manages its own dependencies
4. **Docker Best Practices**: Each service has its own Dockerfile and dependencies
5. **Scalability**: Services can be scaled independently

**However**, if you want a unified setup script, you can create a `setup.sh`:

```bash
#!/bin/bash
# Setup script for the entire project

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd ..

# Frontend setup
cd frontend
npm install
cp .env.example .env
cd ..
```

## Environment Variables

### Backend (.env)
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `DEBUG`: Enable debug mode (true/false)

### Frontend (.env)
- `NEXT_PUBLIC_API_URL`: Backend API URL

### Root (.env for docker-compose)
- `OPENAI_API_KEY`: Passed to backend container

## Production Considerations

1. **Use Nginx** for reverse proxy
2. **Set up SSL/TLS** certificates (Let's Encrypt)
3. **Use environment-specific configs** (dev/staging/prod)
4. **Enable database backups**
5. **Set up monitoring** and logging
6. **Use secrets management** (not .env files in production)
7. **Configure CORS** properly for production domains
