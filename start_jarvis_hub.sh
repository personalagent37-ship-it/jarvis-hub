#!/bin/bash
source jarvis-env/bin/activate
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0
export XAUTHORITY=$HOME/.Xauthority
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"

# Load NVM and Node 20 for 9Router compatibility
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "=================================================="
echo " Starting JARVIS HUB & Python Brain"
echo "=================================================="

# Forcefully kill any lingering background processes holding our ports
fuser -k 20128/tcp 3000/tcp 5000/tcp 8080/tcp 2>/dev/null || true

# Start the Python Webhook Server
python3 whatsapp_server.py &
PYTHON_PID=$!

echo "=================================================="
echo " Starting Auto-Security Daemon"
echo "=================================================="
python3 auto_security.py &
SECURITY_PID=$!

sleep 2

echo "=================================================="
echo " Starting 9Router (Unlimited Claude API Proxy)"
echo "=================================================="
cd 9router
npm run dev &
ROUTER_PID=$!
cd ..

sleep 2

# Start the Node.js Jarvis Hub Client
cd jarvis_hub
node hub.js &
NODE_PID=$!

# Trap Ctrl+C (SIGINT) to cleanly exit background processes
trap "echo -e '\nStopping JARVIS Hub and 9Router...'; kill $PYTHON_PID $ROUTER_PID $NODE_PID $SECURITY_PID; exit" SIGINT SIGTERM

echo "=================================================="
echo " Both servers are running in the background."
echo " Check the output above for the QR code!"
echo "=================================================="

# Wait for any of the critical processes to exit
wait -n $PYTHON_PID $ROUTER_PID $NODE_PID

# If any process dies, kill the rest and exit so SystemD can restart the whole bundle cleanly
kill $PYTHON_PID $ROUTER_PID $NODE_PID $SECURITY_PID 2>/dev/null
exit 1
