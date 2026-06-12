#!/bin/bash
source jarvis-env/bin/activate

echo "Starting Jarvis WhatsApp Server..."
python3 whatsapp_server.py &
SERVER_PID=$!

sleep 2

echo "Starting ngrok on port 5000..."
pyngrok_bin=$(which ngrok)
if [ -z "$pyngrok_bin" ]; then
    # if ngrok isn't in path, use pyngrok wrapper
    python3 -c "from pyngrok import ngrok; url = ngrok.connect(5000).public_url; print('\n>>> NGROK URL:', url, '\n')" &
else
    ngrok http 5000 &
fi
NGROK_PID=$!

# Wait for a few seconds to let pyngrok print the URL
sleep 5

echo "=========================================================================="
echo "ACTION REQUIRED: "
echo "1. Go to Twilio Console -> Messaging -> Settings -> WhatsApp Sandbox Settings"
echo "2. Under 'Sandbox Configuration', find the 'WHEN A MESSAGE COMES IN' field"
echo "3. Paste the NGROK URL printed above, adding '/whatsapp' at the end."
echo "   Example: https://xxxx-xxxx.ngrok.app/whatsapp"
echo "4. Save the settings in Twilio."
echo "5. Send a WhatsApp message to Jarvis!"
echo "=========================================================================="

wait $SERVER_PID
