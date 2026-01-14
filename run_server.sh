#!/bin/bash
# Helper script to run the FastAPI services (split architecture)
# Usage:
#   ./run_server.sh              # Run both services
#   ./run_server.sh ingestion    # Run only ingestion service
#   ./run_server.sh chat         # Run only chat service
#   ./run_server.sh both         # Run both services (default)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Warning: venv directory not found. Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Get the service to run (default: both)
SERVICE=${1:-both}

# Function to run ingestion service
run_ingestion() {
    echo -e "${BLUE}Starting Ingestion Service on port 8001...${NC}"
    echo -e "${GREEN}Ingestion Service: http://localhost:8001${NC}"
    echo -e "${GREEN}Health Check: http://localhost:8001/health${NC}"
    echo ""
    uvicorn ingestion_service.api.main:app --reload --host 0.0.0.0 --port 8001
}

# Function to run chat service
run_chat() {
    echo -e "${BLUE}Starting Chat Service on port 8002...${NC}"
    echo -e "${GREEN}Chat Service: http://localhost:8002${NC}"
    echo -e "${GREEN}Health Check: http://localhost:8002/health${NC}"
    echo ""
    uvicorn chat_service.api.main:app --reload --host 0.0.0.0 --port 8002
}

# Function to run both services in background
run_both() {
    echo -e "${BLUE}Starting both services...${NC}"
    echo -e "${GREEN}Ingestion Service: http://localhost:8001${NC}"
    echo -e "${GREEN}Chat Service: http://localhost:8002${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
    echo ""
    
    # Run both services in background
    uvicorn ingestion_service.api.main:app --reload --host 0.0.0.0 --port 8001 &
    INGESTION_PID=$!
    
    uvicorn chat_service.api.main:app --reload --host 0.0.0.0 --port 8002 &
    CHAT_PID=$!
    
    # Wait for both processes
    trap "kill $INGESTION_PID $CHAT_PID; exit" INT TERM
    wait
}

# Run the appropriate service(s)
case $SERVICE in
    ingestion|ingest)
        run_ingestion
        ;;
    chat)
        run_chat
        ;;
    both|all|"")
        run_both
        ;;
    *)
        echo -e "${YELLOW}Unknown service: $SERVICE${NC}"
        echo "Usage: ./run_server.sh [ingestion|chat|both]"
        echo "  ingestion - Run only ingestion service (port 8001)"
        echo "  chat      - Run only chat service (port 8002)"
        echo "  both      - Run both services (default)"
        exit 1
        ;;
esac
