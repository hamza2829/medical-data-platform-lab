import json
import logging
import paho.mqtt.client as mqtt
from django.conf import settings
from django.core.management.base import BaseCommand
from paho.mqtt.enums import CallbackAPIVersion
from core.ingest import ingest_message

logger = logging.getLogger('sensor.ingest')

class Command(BaseCommand):
    help = 'Subscribe to synthetic sensor readings and store validated FHIR Observations.'
    def handle(self, *args, **options):
        client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id='medical-lab-ingest')
        def on_connect(mqtt_client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                mqtt_client.subscribe('medical-lab/vitals/+/reading', qos=1)
                logger.info('MQTT subscriber connected and ready.')
                self.stdout.write(self.style.SUCCESS('MQTT subscriber connected and ready.'))
            else: logger.error('MQTT connection rejected; code=%s', reason_code)
        def on_message(mqtt_client, userdata, message):
            try:
                payload = json.loads(message.payload.decode('utf-8'))
                record = ingest_message(payload)
                logger.info('Stored FHIR Observation id=%s', record.resource_id)
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                logger.warning('Rejected sensor message; reason=%s', str(exc)[:80])
            except Exception:
                logger.exception('Sensor message processing failed; payload omitted.')
        client.on_connect = on_connect
        client.on_message = on_message
        self.stdout.write(f'Connecting to MQTT at {settings.MQTT_HOST}:{settings.MQTT_PORT}')
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=45)
        try: client.loop_forever()
        except KeyboardInterrupt: client.disconnect()
