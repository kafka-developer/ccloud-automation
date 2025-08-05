# Confluent Cloud RBAC POC Exercise

## Objective
To manually configure and validate **fine-grained access control** using **Role-Based Access Control (RBAC)** in **Confluent Cloud**, ensuring that different service accounts can perform **only their authorized actions** on Kafka resources (e.g., producing or consuming messages).

---

## Background

In a real-world enterprise setting, separating producer and consumer access ensures **security**, **traceability**, and **compliance**. With RBAC, you can enforce:

- **Producer-only access** to publish messages
- **Consumer-only access** to read messages from specified consumer groups
- **Least-privilege principle** by binding minimal roles

We accomplish that by:

1. Creating two service accounts (one producer, one consumer)
2. Assigning them appropriate roles
3. Validating access using the **Confluent CLI**

---

## Pre-requisites

- Confluent Cloud account
- Environment ID and Kafka Cluster ID
- `confluent` CLI installed (`v3.38.0+` recommended)
- `.env` file containing your base credentials
- Two service accounts created:

```bash
# Example names
sa-7ypzkko (producer)
sa-6kozzpq (consumer)
```

---

## Step 1: Create Kafka Topic

>  Goal: Ensure there's a test topic to operate on

```bash
confluent kafka topic create psdev-rbac_validation_topic   --environment env-xy7xpg   --cluster lkc-2nx3n2
```

---

## Step 2: Create Service Accounts

>  Goal: To have separate identities with different roles

```bash
# Producer
confluent iam service-account create psdev-svc  --description "Producer SA"

# Consumer
confluent iam service-account create psdev-svc-consumer --description "Consumer SA"
```

Note the generated service account IDs.

---

## Step 3: Generate API Keys

> Goal: Create credentials that represent each service account

```bash
# For producer
confluent api-key create   --resource lkc-2nx3n2   --service-account sa-7ypzkko   --description "Producer key"

# For consumer
confluent api-key create   --resource lkc-2nx3n2   --service-account sa-6kozzpq   --description "Consumer key"
```

Store both API key/secret pairs.

---

## Step 4: Assign RBAC Role Bindings

>  Goal: Grant each SA the minimal required role

### Producer: Write Access
```bash
confluent iam rbac role-binding create   --principal User:lkc-2nx3n2   --role DeveloperWrite   --resource Topic:psdev-rbac_validation_topic   --environment env-xy7xpg
```

### Consumer: Read Access for Consumer Group
```bash
confluent iam rbac role-binding create   --principal User:sa-6kozzpq   --role DeveloperRead   --resource Topic:psdev-rbac_validation_topic   --environment env-xy7xpg

confluent iam rbac role-binding create   --principal User:sa-6kozzpq   --role DeveloperRead   --resource Group:rbac-validation-group   --environment env-xy7xpg
```

---

## Step 5: Validate RBAC – Produce & Consume Messages

###  Goal:
Verify that only authorized service accounts can produce or consume data from the topic.

---

### Option A: Confluent Cloud UI

1. **Produce Message:**
   - Go to **Topics** → Click `psdev-rbac_validation_topic` → **Messages** tab
   - Click **Produce a message** from the **Actions** dropdown menu.
   - Paste:
     ```json
     {
       "message": "RBAC validation test"
     }
     ```
   - Click **Produce message**

2. **Consume Message:**
   - On the same screen, scroll to **Consume from beginning**
   - Consumer group: `rbac-validation-group`
   - Use API key for the `psdev-consumer-svc`
   - Click **Start consuming**

---

### Option B: Confluent CLI

Make sure you're authenticated:

```bash
confluent login
confluent environment use env-xy7xpg
confluent kafka cluster use lkc-2nx3n2
```

**1. Produce Message:**

```bash
echo '{"message":"RBAC validation test"}' | confluent kafka topic produce psdev-rbac_validation_topic   --value-format json   --api-key <PRODUCER_API_KEY>   --api-secret <PRODUCER_API_SECRET>
```

**2. Consume Message:**

```bash
confluent kafka topic consume psdev-rbac_validation_topic   --group rbac-validation-group   --from-beginning   --value-format json   --api-key <CONSUMER_API_KEY>   --api-secret <CONSUMER_API_SECRET>
```

If everything is correctly configured, the consumer should print:
```bash
{"message":"RBAC validation test"}
```

Otherwise, you’ll get `GROUP_AUTHORIZATION_FAILED`.

---
###  Negative Test
Try using the **consumer service account** to produce — it should fail.

Expected: Access Denied

---

## Key Learnings

- You can enforce Kafka RBAC using service accounts
- Producer and consumer roles are **cleanly separated**
- You can **validate access** via real message operations

---

## Cleanup (Optional)

```bash
confluent kafka topic delete psdev-rbac_validation_topic --cluster <KAFKA_CLUSTER_ID>
confluent iam service-account delete sa-7ypzkko
confluent iam service-account delete sa-6kozzpq
```
