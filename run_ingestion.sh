#!/bin/bash
# Helper script to run only the Ingestion Service

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting Ingestion Service on port 8001..."
echo "Ingestion Service: http://localhost:8001"
echo "Health Check: http://localhost:8001/health"
echo ""

uvicorn ingestion-service.api.main:app --reload --host 0.0.0.0 --port 8001

