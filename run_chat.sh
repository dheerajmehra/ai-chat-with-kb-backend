#!/bin/bash
# Helper script to run only the Chat Service

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting Chat Service on port 8002..."
echo "Chat Service: http://localhost:8002"
echo "Health Check: http://localhost:8002/health"
echo ""

uvicorn chat-service.api.main:app --reload --host 0.0.0.0 --port 8002

