"""Publish synthetic sensor readings to a local or Compose MQTT broker."""
import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default=os.getenv('MQTT_HOST', 'localhost'))
    parser.add_argument('--port', type=int, default=int(os.getenv('MQTT_PORT', '1883')))
    parser.add_argument('--count', type=int, default=5)
    parser.add_argument('--interval', type=float, default=1.0)
    args = parser.parse_args()
    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id='medical-lab-simulator')
    client.connect(args.host, args.port, 45); client.loop_start()
    choices = [('demo-patient-001', 'demo-device-001'), ('demo-patient-002', 'demo-device-002'), ('demo-patient-003', 'demo-device-001')]
    values = {'heart_rate': (72, 'beats/min'), 'oxygen_saturation': (97, '%'), 'body_temperature': (36.8, '°C')}
    try:
        for index in range(args.count):
            patient_id, device_id = choices[index % len(choices)]
            vital_type = list(values)[index % len(values)]; center, unit = values[vital_type]
            payload = {'patient_id': patient_id, 'device_id': device_id, 'type': vital_type, 'value': round(random.gauss(center, 1.5), 1), 'unit': unit, 'effectiveDateTime': datetime.now(timezone.utc).isoformat()}
            client.publish(f'medical-lab/vitals/{device_id}/reading', json.dumps(payload), qos=1).wait_for_publish(timeout=5)
            print(f"Published synthetic {vital_type} reading #{index + 1}")
            time.sleep(args.interval)
    finally:
        client.loop_stop(); client.disconnect()

if __name__ == '__main__': main()
