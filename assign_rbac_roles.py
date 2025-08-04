import os
import requests
from dotenv import load_dotenv

load_dotenv()

org_id = os.getenv("ORG_ID")
env_id = os.getenv("ENV_ID")
cluster_id = os.getenv("KAFKA_CLUSTER_ID")
api_key = os.getenv("CCLOUD_API_KEY")
api_secret = os.getenv("CCLOUD_API_SECRET")
service_account_id = os.getenv("SERVICE_ACCOUNT_ID")
role = os.getenv("ROLE")
topic_names_raw = os.getenv("TOPIC_NAMES", "")
topic_prefixes = os.getenv("TOPIC_PREFIXES", "")

auth = (api_key, api_secret)

if not all([org_id, env_id, cluster_id, service_account_id, role]):
    print("Missing required environment variables. Check ORG_ID, ENV_ID, CLUSTER_ID, SERVICE_ACCOUNT_ID, ROLE.")
    exit(1)

if not topic_names_raw.strip():
    print("No topic names found. Check TOPIC_NAMES in your .env file.")
    exit(1)

topic_names = [t.strip() for t in topic_names_raw.split(",") if t.strip()]
prefixes = [p.strip() for p in topic_prefixes.split(",") if p.strip()]

for prefix in prefixes:
    for topic in topic_names:
        full_topic = f"{prefix}-{topic}"
        crn_pattern = (
            f"crn://confluent.cloud/organization={org_id}"
            f"/environment={env_id}/cloud-cluster={cluster_id}/topic={full_topic}"
        )

        payload = {
            "principal": f"User:{service_account_id}",
            "role_name": role,
            "crn_pattern": crn_pattern
        }

        response = requests.post(
            "https://api.confluent.cloud/iam/v2/role-bindings",
            auth=auth,
            json=payload
        )

        if response.status_code in [200, 201]:
            print(f"Successfully assigned {role} to topic: {full_topic}")
        else:
            print(f"Failed to assign RBAC to topic {full_topic}: {response.text}")