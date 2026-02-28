"""
MQTT Client Application for Azure IoT Operations Testing
Based on Step 11: Testing with MQTTX
"""

import json
import time
import argparse
from datetime import datetime
from typing import Optional
import paho.mqtt.client as mqtt


class AIOTestClient:
    """Test MQTT client for Azure IoT Operations"""

    def __init__(
        self,
        broker_host: str,
        broker_port: int = 1883,
        client_id: str = "aio-test-client",
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False
    ):
        """
        Initialize MQTT client
        
        Args:
            broker_host: MQTT broker hostname/IP
            broker_port: MQTT broker port (1883 for MQTT, 8883 for MQTTS)
            client_id: MQTT client ID
            username: Optional username for authentication
            password: Optional password for authentication
            use_tls: Whether to use TLS/SSL
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.use_tls = use_tls
        
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        
        self.connected = False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when client connects"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.connected = True
        else:
            print(f"✗ Failed to connect, return code {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Callback when client disconnects"""
        if rc != 0:
            print(f"✗ Unexpected disconnection (code {rc})")
        else:
            print("Disconnected from broker")
        self.connected = False

    def _on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            payload = json.loads(msg.payload.decode())
            print(f"  ← Received on {msg.topic}: {json.dumps(payload, indent=2)}")
        except json.JSONDecodeError:
            print(f"  ← Received on {msg.topic}: {msg.payload.decode()}")

    def _on_publish(self, client, userdata, mid):
        """Callback when message is published"""
        print(f"  → Message published (mid: {mid})")

    def connect(self):
        """Connect to MQTT broker"""
        try:
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            if self.use_tls:
                self.client.tls_set()
            
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            max_retries = 5
            for i in range(max_retries):
                if self.connected:
                    return True
                time.sleep(1)
            
            print("✗ Connection timeout")
            return False
            
        except Exception as e:
            print(f"✗ Connection error: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from broker"""
        self.client.loop_stop()
        self.client.disconnect()

    def publish_sensor_data(
        self,
        topic: str = "sensors/temperature",
        sensor_id: str = "sensor-001",
        temperature: float = 22.5,
        humidity: float = 45.0,
        count: int = 1,
        interval: int = 5
    ):
        """
        Publish sensor data messages
        
        Args:
            topic: MQTT topic
            sensor_id: Sensor identifier
            temperature: Temperature in Celsius
            humidity: Humidity percentage
            count: Number of messages to publish
            interval: Interval between messages in seconds
        """
        if not self.connected:
            print("✗ Not connected to broker")
            return

        for i in range(count):
            payload = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "sensorId": sensor_id,
                "temperature": temperature + (i * 0.1),  # Slight increase
                "humidity": humidity + (i * 0.2),
                "status": "normal"
            }
            
            try:
                result = self.client.publish(
                    topic,
                    json.dumps(payload),
                    qos=1
                )
                
                if i == 0:
                    print(f"\nPublishing to topic: {topic}")
                
                print(f"[{i+1}/{count}] {json.dumps(payload)}")
                
                if i < count - 1:
                    time.sleep(interval)
                    
            except Exception as e:
                print(f"✗ Publish error: {str(e)}")
                break

    def subscribe_topic(self, topic: str = "#", qos: int = 1):
        """
        Subscribe to a topic and listen for messages
        
        Args:
            topic: Topic to subscribe (# = all topics)
            qos: Quality of Service level
        """
        if not self.connected:
            print("✗ Not connected to broker")
            return

        try:
            self.client.subscribe(topic, qos)
            print(f"\n✓ Subscribed to: {topic}")
            print("Listening for messages (Press Ctrl+C to stop)...\n")
            
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        except Exception as e:
            print(f"✗ Subscribe error: {str(e)}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Azure IoT Operations MQTT Test Client"
    )
    parser.add_argument("--host", required=True, help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--client-id", default="aio-test-client", help="MQTT client ID")
    parser.add_argument("--username", help="MQTT username")
    parser.add_argument("--password", help="MQTT password")
    parser.add_argument("--tls", action="store_true", help="Use TLS/SSL")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Publish command
    pub_parser = subparsers.add_parser("pub", help="Publish messages")
    pub_parser.add_argument("--topic", default="sensors/temperature", help="MQTT topic")
    pub_parser.add_argument("--sensor-id", default="sensor-001", help="Sensor ID")
    pub_parser.add_argument("--temperature", type=float, default=22.5, help="Temperature value")
    pub_parser.add_argument("--humidity", type=float, default=45.0, help="Humidity value")
    pub_parser.add_argument("--count", type=int, default=5, help="Number of messages")
    pub_parser.add_argument("--interval", type=int, default=5, help="Interval between messages")
    
    # Subscribe command
    sub_parser = subparsers.add_parser("sub", help="Subscribe to topics")
    sub_parser.add_argument("--topic", default="#", help="Topic to subscribe")
    sub_parser.add_argument("--qos", type=int, default=1, help="Quality of Service")
    
    args = parser.parse_args()

    # Create client
    client = AIOTestClient(
        broker_host=args.host,
        broker_port=args.port,
        client_id=args.client_id,
        username=args.username,
        password=args.password,
        use_tls=args.tls
    )

    # Connect
    if not client.connect():
        return 1

    try:
        if args.command == "pub":
            client.publish_sensor_data(
                topic=args.topic,
                sensor_id=args.sensor_id,
                temperature=args.temperature,
                humidity=args.humidity,
                count=args.count,
                interval=args.interval
            )
        elif args.command == "sub":
            client.subscribe_topic(topic=args.topic, qos=args.qos)
        else:
            parser.print_help()
            return 1
            
    finally:
        client.disconnect()

    return 0


if __name__ == "__main__":
    exit(main())
