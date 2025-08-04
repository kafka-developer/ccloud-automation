import os
import requests
from dotenv import load_dotenv

load_dotenv()

rest_endpoint = os.getenv("KAFKA_REST_ENDPOINT")
api_key = os.getenv("KAFKA_API_KEY")
api_secret = os.getenv("KAFKA_API_SECRET")
topic_names_raw = os.getenv("TOPIC_NAMES", "")
topic_prefixes = os.getenv("TOPIC_PREFIXES", "")
cluster_id = os.getenv("KAFKA_CLUSTER_ID")

auth = (api_key, api_secret)

if not topic_names_raw.strip():
    print("No topic names found. Check TOPIC_NAMES in your .env file.")
    exit(1)

topic_names = [t.strip() for t in topic_names_raw.split(",") if t.strip()]
prefixes = [p.strip() for p in topic_prefixes.split(",") if p.strip()]

for prefix in prefixes:
    for topic in topic_names:
        full_topic_name = f"{prefix}-{topic}"
        url = f"{rest_endpoint}/kafka/v3/clusters/{cluster_id}/topics/{full_topic_name}"

        response = requests.delete(url, auth=auth)
        if response.status_code == 204:
            print(f"Successfully deleted topic: {full_topic_name}")
        elif response.status_code == 404:
            print(f"Topic not found: {full_topic_name}")
        else:
            print(f"Failed to delete topic {full_topic_name}: {response.text}")