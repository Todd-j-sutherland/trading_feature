#!/bin/bash
echo "🚀 Uploading Remote Host Configuration Fixes"
echo "==========================================="

# Upload the modified files to remote server
echo "📤 Uploading updated startup scripts..."
scp start_complete_ml_system.sh root@170.64.199.151:test/
scp start_ml_backend.sh root@170.64.199.151:test/
scp start_ml_frontend.sh root@170.64.199.151:test/

echo "📤 Uploading updated API server..."
scp api_server.py root@170.64.199.151:test/

echo "📤 Uploading updated frontend configuration..."
scp frontend/vite.config.ts root@170.64.199.151:test/frontend/

echo "✅ Upload complete!"
echo ""
echo "🔧 Next steps on remote server:"
echo "1. ssh root@170.64.199.151"
echo "2. cd test"
echo "3. ./start_complete_ml_system.sh"
echo ""
echo "🌐 Then access in your browser:"
echo "   Frontend: http://170.64.199.151:3002"
echo "   ML API: http://170.64.199.151:8001/docs"
echo "   Main API: http://170.64.199.151:8000"
