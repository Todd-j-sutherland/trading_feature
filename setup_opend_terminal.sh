#!/bin/bash
# OpenD Terminal Configuration Script

echo "🔧 OpenD Terminal Setup Helper"
echo "=================================="

# Kill any existing OpenD processes
echo "1. Stopping existing OpenD processes..."
pkill -f OpenD
sleep 2

# Find OpenD executable
OPEND_PATH=""
if [ -f "/Applications/OpenD.app/Contents/MacOS/OpenD" ]; then
    OPEND_PATH="/Applications/OpenD.app/Contents/MacOS/OpenD"
elif [ -f "/Applications/OpenD/OpenD" ]; then
    OPEND_PATH="/Applications/OpenD/OpenD"
else
    echo "❌ OpenD not found. Please install OpenD first."
    exit 1
fi

echo "✅ Found OpenD at: $OPEND_PATH"

# Create config directory
CONFIG_DIR="$HOME/Library/Application Support/cn.futu.FutuOpenDGUI"
mkdir -p "$CONFIG_DIR"

echo ""
echo "2. Setting up OpenD configuration..."
echo "You'll need your direct Moomoo credentials (not Google SSO)"
echo ""

# Get user credentials
read -p "Enter your Moomoo email/username: " LOGIN_ACCOUNT
read -s -p "Enter your Moomoo password: " LOGIN_PWD
echo ""
read -p "Enter your region (5=Australia, 1=Hong Kong, 2=US): " LOGIN_REGION

# Default to Australia if not specified
if [ -z "$LOGIN_REGION" ]; then
    LOGIN_REGION=5
fi

# Create basic config file
CONFIG_FILE="$CONFIG_DIR/FTOpenD.ini"
cat > "$CONFIG_FILE" << EOF
[General]
login_account=$LOGIN_ACCOUNT
login_pwd=$LOGIN_PWD
trade_env=1
login_region=$LOGIN_REGION
api_ip=127.0.0.1
api_port=11111
push_proto_type=1
qot_right=1

[Market]
au_enable=1
us_enable=1
hk_enable=1
EOF

echo "✅ Configuration file created at: $CONFIG_FILE"

echo ""
echo "3. Starting OpenD with configuration..."
echo "OpenD will start in paper trading mode (trade_env=1)"
echo ""

# Start OpenD with parameters
"$OPEND_PATH" \
    -login_account="$LOGIN_ACCOUNT" \
    -login_pwd="$LOGIN_PWD" \
    -trade_env=1 \
    -login_region=$LOGIN_REGION \
    -api_port=11111 &

OPEND_PID=$!
echo "✅ OpenD started with PID: $OPEND_PID"

# Wait a moment for startup
sleep 5

# Check if port is now available
echo ""
echo "4. Checking if OpenD API server is running..."
if nc -z 127.0.0.1 11111 2>/dev/null; then
    echo "✅ OpenD API server is running on port 11111!"
    echo ""
    echo "🎉 Setup complete! You can now run:"
    echo "   python test_connection.py"
else
    echo "❌ OpenD API server not running. Check the logs above for errors."
    echo ""
    echo "Common issues:"
    echo "- Incorrect credentials"
    echo "- Need to enable API access in your Moomoo account"
    echo "- Network connectivity issues"
fi

echo ""
echo "OpenD process ID: $OPEND_PID (use 'kill $OPEND_PID' to stop)"