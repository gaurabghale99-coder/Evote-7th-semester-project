#!/bin/bash

# Get the directory where the script is located to ensuring it runs from root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting E-Vote System..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Attempting to create..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Kill usage of ports 8000 and 5500 to avoid conflicts
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5500 | xargs kill -9 2>/dev/null

# Start Backend
echo "🔹 Starting Backend..."
./venv/bin/uvicorn backend:app --reload --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend running (PID: $BACKEND_PID)"

# Start Frontend
echo "🔹 Starting Frontend..."
cd EvoteKABIN
python3 -m http.server 5500 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend running (PID: $FRONTEND_PID)"

echo "✅ System is UP!"
echo "-----------------------------------------------------"
echo "   👉 Access App: http://localhost:5500"
echo "   👉 Backend API: http://127.0.0.1:8000/docs"
echo "-----------------------------------------------------"
echo "📝 Logs are being written to backend.log and frontend.log"
echo "❌ Press Ctrl+C to stop all servers."

# Trap Ctrl+C to kill background processes
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Wait forever until Ctrl+C
wait
