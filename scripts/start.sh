#!/bin/bash

echo "Starting Crawler Web Platform..."

if command -v docker-compose &> /dev/null; then
    docker-compose up -d
    echo "Services started with Docker Compose"
    echo "Frontend: http://localhost"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
else
    echo "Docker Compose not found. Starting services manually..."
    
    echo "Starting Redis..."
    redis-server --daemonize yes
    
    echo "Starting Backend..."
    cd backend
    source .venv/bin/activate 2>/dev/null || true
    pip install -r ../requirements.txt
    alembic upgrade head
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    
    echo "Starting Celery Worker..."
    celery -A app.core.celery_app worker --loglevel=info &
    
    echo "Starting Celery Beat..."
    celery -A app.core.celery_app beat --loglevel=info &
    
    cd ..
    
    echo "Starting Frontend..."
    cd frontend
    npm install
    npm run dev &
    
    cd ..
    
    echo "All services started!"
    echo "Frontend: http://localhost:3000"
    echo "Backend API: http://localhost:8000"
fi
