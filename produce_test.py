import os
import json
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
KAFKA_API_KEY = os.getenv("KAFKA_API_KEY")
KAFKA_API_SECRET = os.getenv("KAFKA_API_SECRET")
BOOTSTRAP_SERVER = os.getenv("KAFKA_REST_ENDPOINT").replace("https://", "").replace(":443", "")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")
SCHEMA_API_KEY = os.getenv("SCHEMA_API_KEY")
SCHEMA_API_SECRET = os.getenv("SCHEMA_API_SECRET")
TOPIC_NAME = "psdev-rbac_validation_topic"

# Load schema file
with open("schemas/schema.json", "r") as f:
    schema_str = f.read()

# Configure Schema Registry client
schema_registry_conf = {
    'url': SCHEMA_REGISTRY_URL,
    'basic.auth.user.info': f"{SCHEMA_API_KEY}:{SCHEMA_API_SECRET}"
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# JSON serializer
json_serializer = JSONSerializer(
    schema_str,
    schema_registry_client,
    lambda obj, ctx: obj
)

# Configure Kafka producer
producer_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': KAFKA_API_KEY,
    'sasl.password': KAFKA_API_SECRET,
    'key.serializer': StringSerializer('utf_8'),
    'value.serializer': json_serializer
}
producer = SerializingProducer(producer_conf)

# Delivery report callback
def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")

# Send 20 messages
for i in range(20):
    record = {"message": f"RBAC validation test #{i + 1}"}
    producer.produce(
        topic=TOPIC_NAME,
        key=str(i),
        value=record,
        on_delivery=delivery_report
    )

producer.flush()