import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env from same directory
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Load variables
kafka_rest_endpoint = os.getenv("KAFKA_REST_ENDPOINT")
schema_registry_url = os.getenv("SCHEMA_REGISTRY_URL")
topic_names_raw = os.getenv("TOPIC_NAMES", "")
prefixes_raw = os.getenv("TOPIC_PREFIXES", "")
partitions = int(os.getenv("PARTITIONS", "3"))
retention_ms = int(os.getenv("RETENTION_MS", "172800000"))
schema_api_key = os.getenv("SCHEMA_API_KEY")
schema_api_secret = os.getenv("SCHEMA_API_SECRET")

# Load schema from file
with open("schemas/schema.json", "r") as schema_file:
    json_schema = schema_file.read()

# Debug logs
print(f"[DEBUG] Raw TOPIC_NAMES: '{topic_names_raw}'")
topic_names = [name.strip() for name in topic_names_raw.split(",") if name.strip()]
prefixes = [p.strip() for p in prefixes_raw.split(",") if p.strip()]
print(f"[DEBUG] Parsed topic_names: {topic_names}")
print(f"[DEBUG] Parsed prefixes: {prefixes}")

if not topic_names:
    print("[‼] No topic names found. Check TOPIC_NAMES in your .env file.")
    exit(1)

# Schema Registry headers
sr_headers = {
    "Content-Type": "application/vnd.schemaregistry.v1+json"
}
sr_auth = (schema_api_key, schema_api_secret)

for prefix in prefixes:
    for topic in topic_names:
        full_topic = f"{prefix}-{topic}"

        # Create topic
        topic_url = f"{kafka_rest_endpoint}/kafka/v3/clusters/{os.getenv('KAFKA_CLUSTER_ID')}/topics"
        payload = {
            "topic_name": full_topic,
            "partitions_count": partitions,
            "configs": [{"name": "retention.ms", "value": str(retention_ms)}]
        }

        response = requests.post(topic_url, auth=(os.getenv("KAFKA_API_KEY"), os.getenv("KAFKA_API_SECRET")),
                                 headers={"Content-Type": "application/json"}, json=payload)

        if response.status_code == 409:
            print(f"Topic already exists: {full_topic}")
        elif response.ok:
            print(f"Successfully created topic: {full_topic}")
        else:
            print(f"Failed to create topic {full_topic}: {response.text}")
            continue

        # Register schema for topic
        subject_name = f"{full_topic}-value"
        schema_payload = {
            "schemaType": "JSON",
            "schema": json_schema
        }

        schema_url = f"{schema_registry_url}/subjects/{subject_name}/versions"
        schema_resp = requests.post(schema_url, headers=sr_headers, auth=sr_auth, data=json.dumps(schema_payload))

        if schema_resp.ok:
            print(f"Registered schema for subject: {subject_name}")
        else:
            print(f"Failed to register schema for {subject_name}: {schema_resp.text}")