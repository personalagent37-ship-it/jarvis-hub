import json
import os

class IoTController:
    """
    Direct MQTT-based IoT Controller for ESP32/Arduino integration.
    Allows Jarvis to send precise physical commands directly to microcontrollers.
    """
    def __init__(self):
        try:
            from config import MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASS
            self.broker = MQTT_BROKER
            self.port = MQTT_PORT
            self.user = MQTT_USER
            self.password = MQTT_PASS
            self.enabled = True
        except ImportError:
            self.enabled = False

    def publish_command(self, topic: str, command: str, value: any = None) -> str:
        """
        Send a direct command to an ESP32 or Arduino on the network.
        Example: topic="jarvis/bedroom/light", command="ON"
        """
        if not self.enabled:
            return "IoT MQTT settings not configured."
            
        try:
            import paho.mqtt.client as mqtt
            import time
            
            client = mqtt.Client()
            if self.user and self.password:
                client.username_pw_set(self.user, self.password)
                
            client.connect(self.broker, self.port, 60)
            client.loop_start()
            
            payload = {"command": command}
            if value is not None:
                payload["value"] = value
                
            info = client.publish(topic, json.dumps(payload), qos=1)
            info.wait_for_publish()
            
            client.loop_stop()
            client.disconnect()
            
            return f"Successfully sent [{command}] to {topic}."
            
        except ImportError:
            return "Please run: pip install paho-mqtt"
        except Exception as e:
            return f"Failed to reach IoT device: {e}"

iot_controller = IoTController()
