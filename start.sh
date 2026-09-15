#!/usr/bin/env bash

# ==============================================================================
# NeedNow AI - Local Development Startup Script
# ==============================================================================
# This script starts both the FastAPI backend and Next.js frontend concurrently.
# Usage: ./start.sh or bash start.sh
# Press Ctrl+C to gracefully stop both servers.

# ANSI Color codes for formatted output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Determine root directory of the project
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}   🚀 Starting NeedNow AI Development Servers      ${NC}"
echo -e "${CYAN}====================================================${NC}"

# Function to handle graceful shutdown when Ctrl+C (SIGINT) or SIGTERM is triggered
cleanup() {
    echo -e "\n${YELLOW}⏹  Shutting down development servers...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    echo -e "${GREEN}✓ All services stopped successfully.${NC}"
    exit 0
}

# Register signal traps
trap cleanup SIGINT SIGTERM EXIT

# ------------------------------------------------------------------------------
# 1. Backend Startup
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[Backend] Setting up FastAPI environment...${NC}"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}[Backend] Error: Directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

# Locate virtual environment (supports macOS/Linux bin/activate and Windows Scripts/activate)
VENV_ACTIVATE=""
if [ -f "$BACKEND_DIR/venv/bin/activate" ]; then
    VENV_ACTIVATE="$BACKEND_DIR/venv/bin/activate"
elif [ -f "$BACKEND_DIR/venv/Scripts/activate" ]; then
    VENV_ACTIVATE="$BACKEND_DIR/venv/Scripts/activate"
elif [ -f "$BACKEND_DIR/.venv/bin/activate" ]; then
    VENV_ACTIVATE="$BACKEND_DIR/.venv/bin/activate"
elif [ -f "$BACKEND_DIR/.venv/Scripts/activate" ]; then
    VENV_ACTIVATE="$BACKEND_DIR/.venv/Scripts/activate"
fi

if [ -n "$VENV_ACTIVATE" ]; then
    echo -e "${GREEN}[Backend] Activating virtual environment: $VENV_ACTIVATE${NC}"
    source "$VENV_ACTIVATE"
else
    echo -e "${YELLOW}[Backend] Warning: No virtual environment found in backend/venv or backend/.venv.${NC}"
    echo -e "${YELLOW}[Backend] Using system Python environment...${NC}"
fi

# Check for backend .env file
if [ ! -f "$BACKEND_DIR/.env" ] && [ -f "$BACKEND_DIR/.env.example" ]; then
    echo -e "${YELLOW}[Backend] .env missing. Creating from .env.example...${NC}"
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

cd "$BACKEND_DIR" || exit 1
echo -e "${GREEN}[Backend] Starting Uvicorn server on http://localhost:8000 ...${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# ------------------------------------------------------------------------------
# 2. Frontend Startup
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[Frontend] Setting up Next.js environment...${NC}"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}[Frontend] Error: Directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

# Check for frontend .env.local file
if [ ! -f "$FRONTEND_DIR/.env.local" ]; then
    echo -e "${YELLOW}[Frontend] .env.local missing. Creating default .env.local...${NC}"
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > "$FRONTEND_DIR/.env.local"
fi

cd "$FRONTEND_DIR" || exit 1
echo -e "${GREEN}[Frontend] Starting Next.js server on http://localhost:3000 ...${NC}"
npm run dev &
FRONTEND_PID=$!

# ------------------------------------------------------------------------------
# 3. Status Summary
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}   ✨ NeedNow AI is up and running!                ${NC}"
echo -e "${GREEN}   • Frontend: http://localhost:3000              ${NC}"
echo -e "${GREEN}   • Backend:  http://localhost:8000              ${NC}"
echo -e "${GREEN}   • API Docs: http://localhost:8000/docs         ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "${CYAN}Press Ctrl+C to stop both backend and frontend.${NC}\n"

# Keep script active and waiting for background jobs
wait $BACKEND_PID $FRONTEND_PID
