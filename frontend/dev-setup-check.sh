#!/bin/bash
# Frontend Dev Setup Check Script

echo "🔍 Checking frontend development setup..."
echo ""

# Check current directory
echo "📁 Current directory: $(pwd)"
echo ""

# Check .env file
echo "📄 Checking .env file..."
if [ -f "frontend/.env" ]; then
    echo "✅ frontend/.env exists"
    echo "Content:"
    cat frontend/.env
else
    echo "❌ frontend/.env not found!"
fi
echo ""

# Check if vite dev server is running
echo "🔌 Checking if Vite dev server is running..."
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 5173 is already in use"
    echo "📌 Please stop the current dev server and restart it to load new .env configuration"
    echo ""
    echo "Steps to fix:"
    echo "  1. Stop the dev server (Ctrl+C in terminal)"
    echo "  2. Clear browser cache and localStorage"
    echo "  3. Restart dev server: npm run dev"
    echo "  4. Clear browser cache: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)"
else
    echo "✅ Port 5173 is available"
    echo "🚀 You can start the dev server with: npm run dev"
fi
echo ""

# Check backend server
echo "🔌 Checking if backend server is running..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Backend server is running on port 8000"
else
    echo "❌ Backend server is NOT running on port 8000"
    echo "📌 Please start the backend server first:"
    echo "  cd backend && python main.py"
fi
echo ""

echo "📝 Summary:"
echo "  - If Vite dev server is running, RESTART IT to load the new .env configuration"
echo "  - Clear browser cache and localStorage after restart"
echo "  - Make sure you are logged in (check localStorage for 'access_token')"
echo ""
