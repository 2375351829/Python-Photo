#!/bin/bash

echo "Stopping Crawler Web Platform..."

if command -v docker-compose &> /dev/null; then
    docker-compose down
    echo "Services stopped with Docker Compose"
else
    echo "Stopping services manually..."
    
    pkill -f "uvicorn app.main:app"
    pkill -f "celery.*worker"
    pkill -f "celery.*beat"
    pkill -f "npm run dev"
    pkill -f "vite"
    
    echo "All services stopped"
fi
