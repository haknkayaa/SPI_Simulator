#!/bin/bash

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Hata durumunda çıkış fonksiyonu
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

echo -e "${GREEN}Starting SPI Simulator...${NC}"

# Python bağımlılıklarını kontrol et ve yükle
echo -e "${GREEN}Checking Python dependencies...${NC}"
cd backend || error_exit "Backend directory not found"
pip3 install -r requirements.txt || error_exit "Failed to install Python dependencies"

# Backend'i başlat
echo -e "${GREEN}Starting Backend...${NC}"
PYTHONPATH=$(pwd) python3 main.py &
BACKEND_PID=$!
cd ..

# Frontend bağımlılıklarını yükle ve başlat
echo -e "${GREEN}Installing Frontend dependencies...${NC}"
cd frontend || error_exit "Frontend directory not found"
npm install || error_exit "Failed to install Frontend dependencies"

echo -e "${GREEN}Starting Frontend...${NC}"
npm run dev &
FRONTEND_PID=$!

# Script sonlandırıldığında çalışacak cleanup fonksiyonu
cleanup() {
    echo -e "${YELLOW}Shutting down...${NC}"
    
    # Backend'i sonlandır
    if [ -n "$BACKEND_PID" ]; then
        echo -e "${YELLOW}Stopping Backend...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Frontend'i sonlandır
    if [ -n "$FRONTEND_PID" ]; then
        echo -e "${YELLOW}Stopping Frontend...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Tüm Python süreçlerini temizle
    echo -e "${YELLOW}Cleaning up Python processes...${NC}"
    pkill -f "python3 main.py" 2>/dev/null || true
    
    echo -e "${GREEN}Cleanup completed${NC}"
    exit 0
}

# SIGINT (Ctrl+C) ve SIGTERM sinyallerini yakala
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}SPI Simulator is running!${NC}"
echo -e "${GREEN}Backend: http://localhost:5001${NC}"
echo -e "${GREEN}Frontend: http://localhost:5173${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"

# Script'in sonlanmasını bekle
wait 