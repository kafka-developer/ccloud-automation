# Kafka/CFK — Version & Compatibility

**Namespace:** `cdm-kafka`  
**Scope:** CFK operator + Kafka brokers + Schema Registry (no ZooKeeper)  
**Purpose:** 
             
 - 1) See **compatibility** at a glance. 
 - 2) Read actual versions. 
 - 3) Decide if CFK↔CP pairing is supported. 
 - 4) Check Schema Registry. 
 - 5) Minimal KRaft sanity.

> **Terminology:** CP versions look like **MAJOR.MINOR.PATCH** (e.g., **7.8.3**).  
> **Major** = first number (**7**). **Minor** = first two numbers (**7.8**). **Patch** = last number (**3**).  
> “**Kafka core**” is the Apache Kafka version packaged by that CP line.

---

## 0) Compatibility at a glance (Kubernetes ↔ CFK ↔ CP/Kafka ↔ Schema Registry)

| Confluent Platform (CP) | Kafka core (bundled) | Compatible **CFK** lines | **Supported Kubernetes** (by CFK line) | Schema Registry (SR) |
|---|---|---|---|---|
| **7.6.x** | **3.6.x** | **2.8.x – 3.0.x** | 2.8.x: 1.25–1.29 · 2.9.x: 1.25–1.30 · 2.10.x: 1.25–1.31 · 2.11.x: 1.25–1.32 · 3.0.x: 1.25–1.33 | **7.6.x** |
| **7.7.x** | **3.7.x** | **2.9.x – 3.0.x** | 2.9.x: 1.25–1.30 · 2.10.x: 1.25–1.31 · 2.11.x: 1.25–1.32 · 3.0.x: 1.25–1.33 | **7.7.x** |
| **7.8.x** | **3.8.x** | **2.10.x – 3.0.x** | 2.10.x: 1.25–1.31 · 2.11.x: 1.25–1.32 · 3.0.x: 1.25–1.33 | **7.8.x** |
| **7.9.x** | **3.9.x** | **2.11.x – 3.0.x** | 2.11.x: 1.25–1.32 · 3.0.x: 1.25–1.33 | **7.9.x** |
| **8.0.x** *(KRaft-only)* | **4.0.x** | **3.0.x** | 3.0.x: 1.25–1.33 | **8.0.x** |

**How to use find versions**: find  **CP** row, make sure **CFK** is within the compatible lines, confirm  **Kubernetes server** version is in range for that CFK line, and keep **SR** on the **same CP minor**

---

## 1) Check the versions

**Confluent Platform (CP) — from broker image tags**
```bash
kubectl -n cdm-kafka get pods -o json \
| jq -r '.items[] | select(.metadata.name|test("^kafka-")) | .spec.containers[].image' \
| awk -F: '{print $2}' | sort -u
```

**CP minor only (e.g., `7.8`) — for Kafka-core mapping**
```bash
kubectl -n cdm-kafka get pods -o json \
| jq -r '.items[] | select(.metadata.name|test("^kafka-")) | .spec.containers[].image' \
| awk -F: '{print $2}' | cut -d. -f1-2 | sort -u
```

**CFK operator / bundle (init tag = CFK version)**
```bash
NS=cdm-kafka
OP=$(kubectl -n "$NS" get pods -o name | grep -E '^pod/confluent-operator-' | head -n1 | cut -d/ -f2)
( kubectl -n "$NS" get pods -o json | jq -r '.items[] | .spec.initContainers[]?.image' | grep -i 'confluent.*init-container' | awk -F: '{print $2}' | head -n1
  kubectl -n "$NS" get pod "$OP" -o json | jq -r '.metadata.labels["app.kubernetes.io/version"] // empty'
) | sed '/^$/d' | head -n1

```

**Schema Registry (SR) version (if SR is deployed)**
```bash
SR=$(kubectl -n cdm-kafka get pods -o name | grep -E '^pod/(schema-registry|sr)-' | head -n1 | cut -d/ -f2); if [ -n "$SR" ]; then kubectl -n cdm-kafka exec -ti "$SR" -- bash -lc 'curl -s localhost:8081/ | jq -r .version'; else echo "No Schema Registry pod found"; fi
```

**Kubernetes server version (portable)**
```bash
kubectl get --raw /version | jq -r '.major+"."+ (.minor|sub("\\+.*$";""))'

```

**Kafka core (CP → Kafka mapping)**

| CP minor | Kafka core |
|---|---|
| 7.6 | 3.6 |
| 7.7 | 3.7 |
| 7.8 | 3.8 |
| 7.9 | 3.9 |
| 8.0 | 4.0 |

**Optional sanity from inside a broker**
```bash
kubectl -n cdm-kafka exec -ti kafka-0 -c kafka -- bash -lc 'kafka-topics --version || kafka-topics.sh --version'
```

---

## 2) Decide compatibility (operator ↔ platform)

**Confluent Platform vs CFK Operator compatibility table**

| CP major you run | Required CFK major | Why |
|---|---|---|
| **7.x** | **2.x** | Matches current operator/platform lines. |
| **8.x** | **3.x** | 8.x is KRaft-only; CFK 3.x aligns with that model. |
| **9.x** (future) | **TBD** | Add once vendor guidance is published. |

**Grab the majors and compare to the table**
```bash
kubectl -n cdm-kafka exec -ti kafka-0 -c kafka -- bash -lc '
for f in /etc/kafka/server.properties /etc/kafka/kraft/server.properties; do
  [ -f "$f" ] && { echo "-- $f"; sed -n -e "s/^[[:space:]]*//" -e "/^#/d" \
    -e "/^\(node\.id\|broker\.id\)[[:space:]]*=/p" "$f"; }
done'

```

**Interpretation**  
- CP **7** with CFK **2** → compatible.  
- CP **8** with CFK **3** → compatible (KRaft-only).  
- CP **8** with CFK **2** → not compatible → upgrade CFK to **3.x** first.  
- When a new CP or CFK major appears, add a row and use the same quick compare.

---

## 3) Schema Registry (SR) — Version Compatibility for Install/Upgrade

SR should track **CP minor** (e.g., CP **7.8** → SR **7.8.x**). Keep SR aligned during installs/upgrades.

**Quick SR health checks (optional)**
```bash
SR=$(kubectl -n cdm-kafka get pods -o name | grep -E '^pod/(schema-registry|sr)-' | head -n1 | cut -d/ -f2); [ -n "$SR" ] && kubectl -n cdm-kafka exec -ti "$SR" -- bash -lc 'curl -s -o /dev/null -w "%{http_code}
" localhost:8081/' || echo "No Schema Registry pod found"

kubectl -n cdm-kafka exec -ti kafka-0 -c kafka -- bash -lc 'kafka-topics --bootstrap-server localhost:9092 --describe --topic _schemas || true'
```

---

## 4) KRaft compatibility & “version” 

**What this checks**  
- You’re running KRaft (required settings present).  
- The cluster’s **finalized metadata level** (`metadata.version`) is appropriate for your **Kafka core**.

**4.1 Required KRaft settings (present = good)**
```bash
NS=cdm-kafka
for p in $(kubectl -n "$NS" get pods -o name | sed 's#pod/##' | grep -E '^(kafka-|kraftcontroller-)'); do
  CFLAG=""; [[ "$p" == kafka-* ]] && CFLAG="-c kafka"
  echo "== $p ==";
  kubectl -n "$NS" exec -ti "$p" $CFLAG -- bash -lc '
    for f in /etc/kafka/server.properties /etc/kafka/kraft/server.properties; do
      if [ -f "$f" ]; then
        sed -n -e "/^[[:space:]]*#/d" -e "/^[[:space:]]*$/d"           -e "/^\(process\.roles\|controller\.listener\.names\|controller\.quorum\.voters\)\s*=/p" "$f"
      fi
    done'
done
```
**PASS** if `process.roles`, `controller.listener.names`, and `controller.quorum.voters` are non-empty (and voters use real DNS:port, not `localhost`).

**4.2 KRaft “version” = finalized `metadata.version`**
```bash
kubectl -n cdm-kafka exec -ti kafka-0 -c kafka -- bash -lc 'kafka-features --bootstrap-server localhost:9092 describe || true'
```
**PASS** if `metadata.version` is **≤** your Kafka core level (e.g., Kafka **3.8** ⇒ metadata.version **3.8** or lower during upgrade).

---

## 5) For future version compatibility of CP and CFK

Add rows here whenever a newer version of CFK is available:

| CP major | CFK major | Notes |
|---|---|---|
| 7.x | 2.x | Current pairing. |
| 8.x | 3.x | KRaft-only platform; aligned operator. |
| **9.x** (future) | **?.x** | Add once confirmed in release notes/support matrix. |

---

## 6) Gotchas

**6.1 Rolling upgrades show mixed versions briefly**
```bash
kubectl -n cdm-kafka get pods -o json \
| jq -r '.items[] | select(.metadata.name|test("^kafka-")) | "\(.metadata.name): \(.spec.containers[].image)"'

```

**6.2 Private/air-gapped registries can hide tags. For unique CP tags**
```bash
kubectl -n cdm-kafka get pods -o json \
| jq -r '.items[] | select(.metadata.name|test("^kafka-")) | .spec.containers[].image' \
| awk -F: '{print $2}' | sort -u

```

**6.3 IBP during upgrades **  
Rule: keep `inter.broker.protocol.version` (**IBP**) at the **current Kafka core level** during the roll; after all brokers are on the new binaries and healthy, set IBP to the **new** core level.

**Check IBP now **
```bash
kubectl -n cdm-kafka exec -ti kafka-0 -c kafka -- bash -lc 'grep -E "^inter.broker.protocol.version" /etc/kafka/server.properties || echo "IBP not set (uses binary default)"'
```

---
