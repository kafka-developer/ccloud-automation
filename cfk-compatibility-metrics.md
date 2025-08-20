# Kafka/CFK — Version & Compatibility

**Namespace:** `cdm-kafka`
**Scope:** CFK operator + Kafka brokers + Schema Registry (no ZooKeeper)
**Purpose:** 1) Read actual versions. 
             2) Decide if CFK↔CP pairing is supported. 
             3) Check Schema Registry. 4) Minimal KRaft sanity.

> **Terminology:** CP versions look like **MAJOR.MINOR.PATCH** (e.g., **7.8.3**).
> **Major** = first number (**7**). **Minor** = first two numbers (**7.8**). **Patch** = last number (**3**).
> “**Kafka core**” is the Apache Kafka version packaged by that CP line (see the table below).

---

## 1) Read the versions

**Confluent Platform (CP) — from a broker image tag**

```bash
# CP full version (e.g., 7.8.3)
kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' \
  -o jsonpath='{.items[0].spec.containers[0].image}{"\n"}' | awk -F: '{print $2}'

# CP minor only (e.g., 7.8) — useful for Kafka core mapping
kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' \
  -o jsonpath='{.items[0].spec.containers[0].image}' | awk -F: '{print $2}' | cut -d. -f1-2
```

**CFK operator / bundle (use the init tag as CFK version)**

```bash
kubectl -n cdm-kafka get pods -l 'app.kubernetes.io/name=confluent-operator' \
  -o jsonpath='{.items[0].spec.containers[0].image}{"\n"}{.items[0].spec.initContainers[0].image}{"\n"}'
# Example: confluent-init-container:2.10.2  → CFK = 2.10.2
```

**Kafka core (CP → Kafka mapping)**

| CP minor | Kafka core |
| -------- | ---------- |
| 7.6      | 3.6        |
| 7.7      | 3.7        |
| 7.8      | 3.8        |
| 8.0      | 4.0        |

3. Why “Optional Sanity from Inside a Broker”?

>You can use the command below to verify the Kafka core version actually running inside your broker container. It's always good to very the running versions instead of 
>completely relying on the official confluent document.**


```bash
kubectl -n cdm-kafka exec -ti $(kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' -o name | head -n1 | cut -d/ -f2) \
  -- bash -lc 'kafka-topics --version || kafka-topics.sh --version'
```

---

## 2) Decide compatibility (operator ↔ platform)

**Rule to enforce (extend when new majors arrive):**

| CP major you run | Required CFK major | Why                                                |
| ---------------- | ------------------ | -------------------------------------------------- |
| **7.x**          | **2.x**            | Matches current operator/platform lines.           |
| **8.x**          | **3.x**            | 8.x is KRaft-only; CFK 3.x aligns with that model. |
| **9.x** (future) | **TBD**            | Add once vendor guidance is published.             |

**Grab the majors and compare to the table**

```bash
# CP major (prints 7 / 8 / 9...)
kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' \
  -o jsonpath='{.items[0].spec.containers[0].image}' | awk -F: '{print $2}' | cut -d. -f1

# CFK major (prints 2 / 3 / 4...)
kubectl -n cdm-kafka get pods -l 'app.kubernetes.io/name=confluent-operator' \
  -o jsonpath='{.items[0].spec.initContainers[0].image}' | awk -F: '{print $2}' | cut -d. -f1
```

**Interpretation**

* CP **7** with CFK **2** → compatible.
* CP **8** with CFK **3** → compatible (KRaft-only).
* CP **8** with CFK **2** → not compatible → upgrade CFK to **3.x** first.
* When a new CP or CFK major appears, **add a row** above and use the same quick compare.

---

## 3) Schema Registry (SR) — versions & checks

**SR version**

```bash
kubectl -n cdm-kafka exec -ti $(kubectl -n cdm-kafka get pods -l 'confluent.io/type=SchemaRegistry' -o name | head -n1 | cut -d/ -f2) \
  -- bash -lc 'curl -s localhost:8081/ | jq -r .version'
# Expect it to align with CP minor (e.g., CP 7.8 → SR 7.8.x)
```

**SR compatibility mode**

```bash
# Global mode (e.g., BACKWARD, FULL, FORWARD, NONE)
kubectl -n cdm-kafka exec -ti $(kubectl -n cdm-kafka get pods -l 'confluent.io/type=SchemaRegistry' -o name | head -n1 | cut -d/ -f2) \
  -- bash -lc 'curl -s localhost:8081/config | jq -r .compatibilityLevel'

# Per-subject (replace <subject>)
kubectl -n cdm-kafka exec -ti $(kubectl -n cdm-kafka get pods -l 'confluent.io/type=SchemaRegistry' -o name | head -n1 | cut -d/ -f2) \
  -- bash -lc 'curl -s localhost:8081/config/<subject> | jq -r .compatibilityLevel'
```

**SR quick practices**

* Keep **SR version aligned with CP minor** (e.g., 7.8.x with CP 7.8.x).
* Prefer **BACKWARD** or **FULL** unless you have a specific need.
* Confirm the `_schemas` topic exists and is healthy:

```bash
# from a broker pod (replace <broker-pod> with an actual broker pod)
kubectl -n cdm-kafka exec -ti <broker-pod> -- bash -lc \
'kafka-topics --bootstrap-server localhost:9092 --describe --topic _schemas || true'
```

---

## 4) KRaft sanity

You’re right to ask. There isn’t a separate, branded “**KRaft version**” string. In practice you prove KRaft’s “version” by two things:

1. the **Kafka core level** you’re running (from CP → Kafka map), and
2. the **finalized features**—especially **`metadata.version`**—that the cluster advertises.

Here’s a **drop-in replacement** for your Section 4 that adds a real, minimal **KRaft “version” check** and a simple **PASS/FAIL**:

---

## 4) KRaft compatibility & “version” (minimal)

**What this checks**

* You’re actually running KRaft (required settings are present).
* The cluster’s **finalized metadata level** (aka “KRaft version”) is appropriate for your **Kafka core**.

### 4.1 Required KRaft settings (present = good)

```bash
# Expect non-empty values for all three
kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' -o jsonpath='{.items[0].spec.containers[0].env[?(@.name=="KAFKA_CFG_PROCESS_ROLES")].value}{"\n"}{.items[0].spec.containers[0].env[?(@.name=="KAFKA_CFG_CONTROLLER_LISTENER_NAMES")].value}{"\n"}{.items[0].spec.containers[0].env[?(@.name=="KAFKA_CFG_CONTROLLER_QUORUM_VOTERS")].value}{"\n"}'
```

**PASS** if you see values for `PROCESS_ROLES`, `CONTROLLER_LISTENER_NAMES`, and `CONTROLLER_QUORUM_VOTERS`.

### 4.2 KRaft “version” = Kafka core level + finalized **metadata.version**

1. We have already mapped **CP → Kafka core** earlier (e.g., CP **7.8 → Kafka 3.8**).
2. Now lets read the finalized features and locate **`metadata.version`**:

```bash
# From any broker pod; shows finalized features including metadata.version
kubectl -n cdm-kafka exec -ti $(kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' -o name | head -n1 | cut -d/ -f2) \
  -- bash -lc 'kafka-features --bootstrap-server localhost:9092 describe || true'
```

**Read it:** In the output, find `metadata.version`. It should be at or below your **Kafka core** level (e.g., for Kafka **3.8**, expect a 3.8-level metadata version).

**PASS / FAIL**

* **PASS:** `metadata.version` ≤ your Kafka core level (e.g., metadata 3.8 with Kafka 3.8).
* **FAIL:** `metadata.version` above your Kafka core (fix by setting it back / completing the upgrade).
* **Note:** During a rolling upgrade it can be **intentionally lower** than core; that’s fine until the roll completes.

*(Important: In KRaft, `metadata.version` is the cluster’s finalized metadata feature level—this is what people often mean by “KRaft version.”)*

---

## 5) Future-proof compatibility

Add rows here as you adopt newer lines whenever a newer version of CFK is available:

| CP major          | CFK major | Notes                                               |
| ----------------- | --------- | --------------------------------------------------- |
| 7.x               | 2.x       | Current pairing.                                    |
| 8.x               | 3.x       | KRaft-only platform; aligned operator.              |
| **9.x** (future)  | **?.x**   | Add once confirmed in release notes/support matrix. |
| **10.x** (future) | **?.x**   | Add once confirmed.                                 |

---

## 6) Gotchas

**6.1 Rolling upgrades show mixed versions briefly**
During a broker rollout, some pods run `7.8.2` while others already run `7.8.3`. That’s normal mid-upgrade.
**Do this:** finish the roll, then re-run your version/compat checks.

```bash
# Show each broker’s image tag (expect them to match when the roll is done)
kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' \
  -o jsonpath='{range .items[*]}{.metadata.name}{": "}{.spec.containers[0].image}{"\n"}{end}'
```

**6.2 Private/air-gapped registries can hide tags**
If images are pulled by **digest** (`sha256:...`), you won’t see a readable tag like `7.8.3`.
**Do this:** map the digest to a CP version using your internal registry/map, or add a simple annotation (e.g., `cpVersion: "7.8.3"`) on your StatefulSet.

```bash
# See the digest of a running broker image
kubectl -n cdm-kafka get pod $(kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' -o name | head -n1 | cut -d/ -f2) \
  -o jsonpath='{.status.containerStatuses[0].imageID}{"\n"}'
```

**6.3 IBP during upgrades (keep it simple)**
**Rule:** During a rolling upgrade, keep `inter.broker.protocol.version` (**IBP**) at the **current Kafka core level**.
After all brokers are on the new binaries and healthy, set IBP to the **new** core level.

Quick map we are using:

* CP 7.6 → Kafka core 3.6 → **IBP = 3.6**
* CP 7.7 → 3.7 → **IBP = 3.7**
* CP 7.8 → 3.8 → **IBP = 3.8**
* CP 8.0 → 4.0 → **IBP = 4.0**

Check what IBP is right now:

```bash
BROKER=$(kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' -o name | head -n1 | cut -d/ -f2)
kubectl -n cdm-kafka exec -ti "$BROKER" -- bash -lc \
'grep -E "^inter.broker.protocol.version" /etc/kafka/server.properties || echo "IBP not set (uses binary default)"'
```

**Rollback IBP in case of an issue:**
Set IBP back to the last working core level (e.g., `3.8`), let CFK roll brokers, then try again later.

```bash
# Example: set IBP back to 3.8 via patch (adjust <cluster-name>)
kubectl -n cdm-kafka patch kafka <cluster-name> --type='json' \
  -p='[{"op":"add","path":"/spec/kafka/configOverrides/server/-","value":"inter.broker.protocol.version=3.8"}]'
# Watch the roll:
kubectl -n cdm-kafka get pods -l 'confluent.io/type=Kafka' -w
```

---
