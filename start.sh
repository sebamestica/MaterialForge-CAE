#!/bin/bash
# =========================================================================
# MATERIALFORGE - STARTUP SCRIPT (Bash / Git Bash)
# =========================================================================

clear
echo -e "\e[36m========================================================\e[0m"
echo -e "\e[36m  >>> INICIANDO ENTORNO DE TRABAJO MATERIALFORGE <<<\e[0m"
echo -e "\e[36m========================================================\e[0m"
echo ""

# 1. Validar entorno virtual
if [ ! -d ".venv" ]; then
    echo -e "\e[31m[-] ERROR: No se encontró el entorno virtual .venv.\e[0m"
    exit 1
fi

# 2. Iniciar Backend FastAPI en segundo plano
echo -e "\e[32m[+] Iniciando API del Backend en puerto 8000 (segundo plano)...\e[0m"
source .venv/Scripts/activate || source .venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Esperar un par de segundos
sleep 2

# Función para apagar el backend al cerrar el script
cleanup() {
    echo ""
    echo -e "\e[33m[+] Apagando servidor del backend (PID: $BACKEND_PID)...\e[0m"
    kill $BACKEND_PID
    exit
}
trap cleanup SIGINT SIGTERM

# 3. Iniciar Frontend Next.js
echo -e "\e[32m[+] Iniciando Frontend Next.js en puerto 3000...\e[0m"
cd frontend
npm run dev

# Al finalizar (si npm run dev se corta), apagar backend
cleanup
