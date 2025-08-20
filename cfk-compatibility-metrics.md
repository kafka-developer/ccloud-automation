# CFK 2.10.2 – Environment Compatibility Brief (no-pvs cluster, **KRaft-only**, namespace: `cdm-kafka`)

*Last updated: 2025-08-20*

Environment-specific note based on your screenshot. This version assumes **KRaft-only** and uses the Kubernetes namespace **`cdm-kafka`** in all commands.

---

## 1) Environment snapshot

| Item                           | Value                                          |
| ------------------------------ | ---------------------------------------------- |
| Cluster label                  | `no-pvs`                                       |
| **Namespace**                  | **`cdm-kafka`**                                |
| **CFK version**                | **2.10.2**                                     |
| Operator image                 | `confluentinc/confluent-operator:0.1145.50`    |
| Init container                 | `confluentinc/confluent-init-container:2.10.2` |
| CP component images            | `7.8.3` (Confluent Platform **7.8.x**)         |
| Kafka core (implied by CP 7.8) | **3.8.x**                                      |
| Metadata mode                  | **KRaft**                                      |

**Implication:** Platform components should align on **CP 7.8.x** (brokers, Schema Registry, Connect, ksqlDB).

---

## 2) Compatibility summary (CP 7.8.x, KRaft-only)

| Component        | Version in this env  | Notes                                                |
| ---------------- | -------------------- | ---------------------------------------------------- |
| CFK (operator)   | 2.10.2               | Manages CP 7.x deployments on Kubernetes.            |
| Kafka Broker     | 3.8.x (via CP 7.8.x) | KRaft roles required (`broker` and/or `controller`). |
| Schema Registry  | 7.8.x (expected)     | Keep SR on the same CP minor.                        |
| Connect / ksqlDB | 7.8.x (expected)     | Match CP; clients can vary within supported ranges.  |

---

## 3) Confirm **KRaft** configuration (namespace: `cdm-kafka`)

**3.1 Roles and quorum voters (from pod env)**

```bash
# Roles on each broker pod
kubectl -n cdm-kafka get pods -l confluent.io/type=Kafka \
  -o jsonpath='{range .items[*]}{.metadata.name}{": "}{.spec.containers[0].env[?(@.name=="KAFKA_CFG_PROCESS_ROLES")].value}{"\n"}{end}'

# Quorum voters
kubectl -n cdm-kafka get pods -l confluent.io/type=Kafka \
  -o jsonpath='{range .items[*]}{.metadata.name}{": "}{.spec.containers[0].env[?(@.name=="KAFKA_CFG_CONTROLLER_QUORUM_VOTERS")].value}{"\n"}{end}'
```

**3.2 Controller listener names (optional)**

```bash
kubectl -n cdm-kafka get pods -l confluent.io/type=Kafka \
  -o jsonpath='{range .items[*]}{.metadata.name}{": "}{.spec.containers[0].env[?(@.name=="KAFKA_CFG_CONTROLLER_LISTENER_NAMES")].value}{"\n"}{end}'
```

**3.3 Inspect `server.properties` (optional)**

```bash
# Replace <broker-pod>
kubectl -n cdm-kafka exec -ti <broker-pod> -- bash -lc \
'grep -E "^(process.roles|controller.quorum.voters|controller.listener.names)" /etc/kafka/server.properties || true'
```

**Expected:**

* `process.roles` set (`broker` and/or `broker,controller`)
* `controller.quorum.voters` set
* `controller.listener.names` set (e.g., `CONTROLLER`)

---

## 4) Version discovery (images/tags)

```bash
# CFK operator image
kubectl -n cdm-kafka get pods -l app.kubernetes.io/name=confluent-operator \
  -o jsonpath='{.items[0].spec.containers[0].image}{"\n"}'

# Kafka broker images (CP version in tag)
kubectl -n cdm-kafka get pods -l confluent.io/type=Kafka \
  -o jsonpath='{.items[*].spec.containers[0].image}{"\n"}'
# Expect: confluentinc/cp-kafka:7.8.3

# Schema Registry images (CP version in tag)
kubectl -n cdm-kafka get pods -l confluent.io/type=SchemaRegistry \
  -o jsonpath='{.items[*].spec.containers[0].image}{"\n"}'
# Expect: confluentinc/cp-schema-registry:7.8.3
```

---

## 5) Upgrade guidance (KRaft-only path)

* **Remain on CP 7.8.x:** Track latest **7.8.x** patch.
* **Target CP 8.0.x (Kafka 4.0, KRaft):**

  1. Ensure quorum health (`controller.quorum.voters` consistent; all controllers ready).
  2. Upgrade **CFK to 3.0.x** (recommended for CP 8.0).
  3. Perform a rolling upgrade of brokers and components to **CP 8.0.x**.
  4. Verify client compatibility against the CP interoperability matrix.

---

## 6) Next confirmations

* Kubernetes version and storage configuration for the `cdm-kafka` namespace’s cluster.
* Exact **Schema Registry** tag and current **compatibility mode** (e.g., Backward).
* Any component pins or custom images in Helm/kustomize overlays.

---

## 7) Reference links

* Confluent Platform Release Notes (version mapping): [https://docs.confluent.io/platform/current/release-notes/index.html](https://docs.confluent.io/platform/current/release-notes/index.html)
* Versions & Interoperability Matrix: [https://docs.confluent.io/platform/current/installation/versions-interoperability.html](https://docs.confluent.io/platform/current/installation/versions-interoperability.html)
* Confluent for Kubernetes Release Notes: [https://docs.confluent.io/operator/current/release-notes.html](https://docs.confluent.io/operator/current/release-notes.html)
