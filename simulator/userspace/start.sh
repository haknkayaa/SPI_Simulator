#!/bin/bash

# Renk tanımlamaları
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting SPI Simulator...${NC}"

# Python bağımlılıklarını kontrol et ve yükle
echo -e "${GREEN}Checking Python dependencies...${NC}"
pip3 install -r requirements.txt

# Backend'i başlat
echo -e "${GREEN}Starting Backend...${NC}"
cd backend
sudo -n python3 app.py &
BACKEND_PID=$!
cd ..

# Frontend bağımlılıklarını yükle ve başlat
echo -e "${GREEN}Installing Frontend dependencies...${NC}"
cd frontend
npm install

echo -e "${GREEN}Starting Frontend...${NC}"
npm run dev &
FRONTEND_PID=$!

# Script sonlandırıldığında çalışacak cleanup fonksiyonu
cleanup() {
    echo -e "${RED}Shutting down...${NC}"
    # Backend'i sudo ile sonlandır
    sudo kill $BACKEND_PID 2>/dev/null
    # Frontend'i sonlandır
    kill $FRONTEND_PID 2>/dev/null
    # Tüm Python süreçlerini temizle
    sudo pkill -f "python3 app.py" 2>/dev/null
    exit 0
}

# SIGINT (Ctrl+C) ve SIGTERM sinyallerini yakala
trap cleanup SIGINT SIGTERM

# Script'in sonlanmasını bekle
wait 