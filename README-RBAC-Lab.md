# Confluent Cloud RBAC POC Exercise

## Objective
To manually configure and validate **fine-grained access control** using **Role-Based Access Control (RBAC)** in **Confluent Cloud**, ensuring that different service accounts can perform **only their authorized actions** on Kafka resources (e.g., producing or consuming messages).

---

## Background

In a real-world enterprise setting, separating producer and consumer access ensures **security**, **traceability**, and **compliance**. With RBAC, you can enforce:

- **Producer-only access** to publish messages
- **Consumer-only access** to read messages from specified consumer groups
- **Least-privilege principle** by binding minimal roles

This lab simulates that by:

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
sa-xxxxxxx (producer)
sa-yyyyyyy (consumer)
```

---

## Step 1: Create Kafka Topic

>  Goal: Ensure there's a test topic to operate on

```bash
confluent kafka topic create psdev-rbac_validation_topic   --environment <ENV_ID>   --cluster <KAFKA_CLUSTER_ID>
```

---

## Step 2: Create Service Accounts

>  Goal: Simulate separate identities with different roles

```bash
# Producer
confluent iam service-account create psdev-svc-producer --description "Producer SA"

# Consumer
confluent iam service-account create psdev-svc-consumer --description "Consumer SA"
```

Note the generated service account IDs.

---

## Step 3: Generate API Keys

> Goal: Create credentials that represent each service account

```bash
# For producer
confluent api-key create   --resource <KAFKA_CLUSTER_ID>   --service-account <PRODUCER_SA_ID>   --description "Producer key"

# For consumer
confluent api-key create   --resource <KAFKA_CLUSTER_ID>   --service-account <CONSUMER_SA_ID>   --description "Consumer key"
```

Store both API key/secret pairs.

---

## Step 4: Assign RBAC Role Bindings

>  Goal: Grant each SA the minimal required role

### Producer: Write Access
```bash
confluent iam rbac role-binding create   --principal User:<PRODUCER_SA_ID>   --role DeveloperWrite   --resource Topic:psdev-rbac_validation_topic   --environment <ENV_ID>
```

### Consumer: Read Access for Consumer Group
```bash
confluent iam rbac role-binding create   --principal User:<CONSUMER_SA_ID>   --role DeveloperRead   --resource Topic:psdev-rbac_validation_topic   --environment <ENV_ID>

confluent iam rbac role-binding create   --principal User:<CONSUMER_SA_ID>   --role DeveloperRead   --resource Group:rbac-validation-group   --environment <ENV_ID>
```

---

## Step 5: Validate Access

### Producer Test (Python or REST)
Use the **producer API key** to send messages to `psdev-rbac_validation_topic`.

Expected: Success

### Consumer Test (Python or REST)
Use the **consumer API key** to consume from `psdev-rbac_validation_topic` with group `rbac-validation-group`.

Expected:  Success

###  Negative Test
Try using the **consumer service account** to produce — it should fail.

Expected: Access Denied

---

## Key Learnings

- You can enforce Kafka RBAC using service accounts
- Producer and consumer roles are **cleanly separated**
- You can **validate access** via real message operations
- Great for demos, audits, and compliance reviews

---

## Cleanup (Optional)

```bash
confluent kafka topic delete psdev-rbac_validation_topic --cluster <KAFKA_CLUSTER_ID>
confluent iam service-account delete <PRODUCER_SA_ID>
confluent iam service-account delete <CONSUMER_SA_ID>
```
