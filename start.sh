#!/bin/bash

# SkillHub Development Environment Startup Script

echo "========================================"
echo "SkillHub Development Environment"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "backend/main.py" ]; then
    echo -e "${RED}Error: Please run from project root${NC}"
    echo "Usage: cd /Users/guisheng.guo/Documents/workspace/skillhub && ./start.sh"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

if ! command_exists python3; then
    echo -e "${YELLOW}Warning: python3 not found${NC}"
fi

if ! command_exists npm; then
    echo -e "${YELLOW}Warning: npm not found${NC}"
fi

if ! command_exists uvicorn; then
    echo -e "${YELLOW}Installing uvicorn...${NC}"
    pip install uvicorn
fi

echo ""

# Ask what to start
echo "What would you like to start?"
echo "1) Backend only"
echo "2) Frontend only"
echo "3) Both (Backend in background, Frontend in foreground)"
echo "4) Run API tests"
echo "5) Initialize/Seed Database"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo -e "${GREEN}Starting backend...${NC}"
        python -m uvicorn backend.main:app --reload --port 8000
        ;;
    2)
        echo -e "${GREEN}Starting frontend...${NC}"
        cd frontend
        npm run dev
        ;;
    3)
        echo -e "${GREEN}Starting backend in background...${NC}"
        python -m uvicorn backend.main:app --reload --port 8000 &
        BACKEND_PID=$!
        echo "Backend PID: $BACKEND_PID"

        sleep 2

        echo -e "${GREEN}Starting frontend...${NC}"
        cd frontend
        npm run dev

        # Cleanup on exit
        kill $BACKEND_PID 2>/dev/null
        ;;
    4)
        echo -e "${GREEN}Running API tests...${NC}"
        ./backend/test_api_quick.sh
        ;;
    5)
        echo -e "${YELLOW}Initializing database...${NC}"
        cd backend
        python scripts/init_db.py

        echo -e "${YELLOW}Seeding database...${NC}"
        python scripts/seed_db.py

        echo -e "${GREEN}Database ready!${NC}"
        echo -e "Default user: ${BLUE}admin / admin123${NC}"
        ;;
    *)
        echo -e "${YELLOW}Invalid choice${NC}"
        exit 1
        ;;
esac
