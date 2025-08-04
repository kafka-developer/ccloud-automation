import os
from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import StringDeserializer
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Hardcoded Consumer Service Account credentials
CONSUMER_API_KEY = "5GX7JERHKKATX4MW"
CONSUMER_API_SECRET = "cfltn1xEwtzP1dPgZUlrjqPPqj692EOLgctRb1h88VaKw/DjH2vKwdTYCBFyN+9g"

# Load other config from .env
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")
SCHEMA_API_KEY = os.getenv("SCHEMA_API_KEY")
SCHEMA_API_SECRET = os.getenv("SCHEMA_API_SECRET")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
TOPIC_NAME = os.getenv("TOPIC_NAME", "psdev-rbac_validation_topic")
GROUP_ID = os.getenv("GROUP_ID", "rbac-validation-group")

# Schema registry config and client
schema_registry_conf = {
    'url': SCHEMA_REGISTRY_URL,
    'basic.auth.user.info': f'{SCHEMA_API_KEY}:{SCHEMA_API_SECRET}'
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Fetch the schema dynamically
subject = f"{TOPIC_NAME}-value"
schema_response = schema_registry_client.get_latest_version(subject)
schema_str = schema_response.schema.schema_str

# Kafka Consumer config
consumer_conf = {
    'bootstrap.servers': 'pkc-p11xm.us-east-1.aws.confluent.cloud:9092',
    'sasl.mechanisms': 'PLAIN',
    'security.protocol': 'SASL_SSL',
    'sasl.username': CONSUMER_API_KEY,
    'sasl.password': CONSUMER_API_SECRET,
    'key.deserializer': StringDeserializer('utf_8'),
    'value.deserializer': JSONDeserializer(schema_str),
    'group.id': GROUP_ID,
    'auto.offset.reset': 'earliest'
}

consumer = DeserializingConsumer(consumer_conf)
consumer.subscribe([TOPIC_NAME])

print(f"Consuming messages from topic: {TOPIC_NAME}")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        print(f"Key: {msg.key()}, Value: {msg.value()}")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()
