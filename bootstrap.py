import os
import ssl
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Optional Twilio client
twilio_client = None
if os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN'):
    try:
        from twilio.rest import Client
        twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        logging.info('[Bootstrap] Twilio client initialized')
    except Exception as e:
        logging.warning(f'[Bootstrap] Twilio init failed: {e}')

# Optional MQTT client
mqtt_client = None
if os.getenv('MQTT_BROKER'):
    try:
        import paho.mqtt.client as mqtt
        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(os.getenv('MQTT_USER'), os.getenv('MQTT_PASS'))
        mqtt_client.connect(os.getenv('MQTT_BROKER'), int(os.getenv('MQTT_PORT', '1883')))
        mqtt_client.loop_start()
        logging.info('[Bootstrap] MQTT client connected')
    except Exception as e:
        logging.warning(f'[Bootstrap] MQTT init failed: {e}')

# Shared context passed to all agents
shared_context = {
    "HIGH_RISK_ACTIONS": {"delete_file", "shutdown", "reboot", "format", "wipe"},
    "smtp_credentials": {
        "host": os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        "port": int(os.getenv('SMTP_PORT', '465')),
        "address": os.getenv('SMTP_USER', ''),
        "password": os.getenv('SMTP_PASS', '')
    },
    "twilio_client": twilio_client,
    "twilio_number": os.getenv('TWILIO_FROM', ''),
    "mqtt_client": mqtt_client,
}
