# Architecture

## Overview

This document describes the software architecture for a big distributed system. The system is designed for high throughput, scalability, and reliability, leveraging microservices, asynchronous event-driven messaging, MySQL for persistent storage, and Kafka for high-throughput data writing.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API Gateway                                  │
│              (Rate Limiting, Auth, Routing)                         │
└──────┬────────────────────┬──────────────────────┬──────────────────┘
       │                    │                      │
       ▼                    ▼                      ▼
┌──────────────┐   ┌──────────────┐      ┌──────────────┐
│ Microservice │   │ Microservice │ ...  │ Microservice │
│     A        │   │     B        │      │     N        │
└──────┬───────┘   └──────┬───────┘      └──────┬───────┘
       │                  │                      │
       ▼                  ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Message Queue (Kafka)                           │
│            Event Bus / Async Event-Driven Communication             │
└──────┬───────────────────┬───────────────────┬──────────────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
│  MySQL       │   │  MySQL       │   │  Kafka-Connect   │
│  (Primary DB)│   │  (Read Rep)  │   │  (Stream Process)│
└──────────────┘   └──────────────┘   └──────────────────┘
```

## Guiding Principles

- **Stateless microservices** — every instance is interchangeable. No session affinity, no local disk state, no in-memory caches that cannot be rebuilt. This design enables **horizontal scaling**: adding instances linearly increases throughput, and removing failed instances causes zero data loss.
- **Eventual consistency** across bounded contexts; strong consistency only within a single service's DB.
- **Async communication** between services via events; synchronous calls (gRPC/REST) reserved for queries and commands that require immediate response.
- **Observability by default** — every service emits structured logs, metrics, and traces.
- **Fail-fast and graceful degradation** — every outbound call is wrapped with a circuit breaker. When a dependency fails, the local service degrades (stale data, queued writes, 503) instead of cascading the failure. Bulkheads ensure one failing dependency cannot exhaust the entire service's resources.
- **Resilience is validated experimentally** — chaos engineering is a first-class practice, not an afterthought.
- **Test-Driven Development (TDD)** — all code is written test-first. Red → Green → Refactor is the default workflow.

## Architecture Style: Microservices

### Service Boundaries

Each microservice owns a single **bounded context** (Domain-Driven Design). Services communicate via:

| Communication Type | Protocol | Use Case |
|---|---|---|
| Synchronous | gRPC / REST | Queries, commands with immediate response |
| Asynchronous | Kafka Events | State changes, notifications, long-running workflows |
| Scheduled | Cron / Scheduler | Batch jobs, periodic reconciliation |

### Service Template

Every microservice follows the same internal layering:

```
┌─────────────────────────────────┐
│         API Layer                │  ← gRPC/REST handlers, rate limiting
├─────────────────────────────────┤
│      Application Layer           │  ← use cases, orchestration
├─────────────────────────────────┤
│       Domain Layer               │  ← business logic, domain events
├─────────────────────────────────┤
│     Resilience Layer             │  ← circuit breakers, bulkheads, retries
├─────────────────────────────────┤
│    Infrastructure Layer          │  ← DB, MQ clients, external IO
└─────────────────────────────────┘
```

- API layer validates input and maps to internal DTOs.
- Application layer contains use-case orchestration (commands/queries) and publishes domain events.
- Domain layer is pure business logic with zero external dependencies.
- **Resilience layer** wraps every outbound call (DB, Kafka, downstream service) with circuit breakers, bulkheads, and retry policies. This layer is **mandatory** — no microservice may call an external dependency without protection.
- Infrastructure layer implements repositories, event publishers, and external service clients.

### Circuit Breaker (Built-In, Every Service)

Every microservice **must** protect every outbound call (REST, gRPC, DB, Kafka, Redis) with a circuit breaker. This ensures the system degrades gracefully when dependencies fail.

```
  ┌──────────┐     healthy      ┌──────────┐
  │  CLOSED  │ ──────────────→ │   OPEN   │
  │ (normal) │ ←────────────── │ (failing)│
  └──────────┘   failure        └──────────┘
       ↑                              │
       │     timeout elapses          │
       │                              ▼
       │                     ┌──────────────┐
       └─────────────────────│   HALF-OPEN  │
            success (probe)  │  (probing)   │
                             └──────────────┘
```

#### States

| State | Behaviour |
|---|---|
| **CLOSED** | Requests pass through. Failure count resets on success. |
| **OPEN** | Requests fail **fast** (immediate exception, no network call). A timer starts. No wasted resources on a dead dependency. |
| **HALF-OPEN** | After the timeout, a probe request is allowed. Success → CLOSED; Failure → OPEN again. |

#### Configuration (per dependency)

| Parameter | Default | Description |
|---|---|---|
| Failure threshold | 5 consecutive failures | Opens the circuit. |
| Reset timeout | 10 s | Time before transitioning to HALF-OPEN. |
| Half-open probe limit | 1 | Number of probe requests allowed in HALF-OPEN. |
| Recording timeout as failure | yes | Calls that exceed a threshold are counted as failures. |

#### Fallback Behaviour

When the circuit is OPEN, the service must respond with a **meaningful fallback**:

- **Read path:** Return stale/cached data if available, otherwise a `503 Service Unavailable`.
- **Write path:** Queue to an outbox table or a local dead-letter for later retry.
- **Idempotent operations:** Can safely retry later; return 202 Accepted + a tracking ID.

#### Bulkhead

In addition to circuit breakers, each dependency pool gets a **fixed thread pool or semaphore** (bulkhead). If one dependency exhausts its pool, the rest of the service continues unaffected.

```
┌──────────────── Service ─────────────────┐
│                                          │
│  Thread pool A  ───→ Downstream X        │
│  (max 10)                                │
│                                          │
│  Thread pool B  ───→ Downstream Y        │
│  (max 10)         ───→ Kafka             │
│                                          │
│  Thread pool C  ───→ MySQL              │
│  (max 10)                                │
│                                          │
│  If pool A is full, calls to X fail fast │
│  but Y and MySQL are unaffected.         │
└──────────────────────────────────────────┘
```

#### Required Observability

Every circuit breaker must expose:

- Current state (CLOSED / OPEN / HALF-OPEN) as a Prometheus Gauge.
- Call count, success count, failure count, timeout count.
- Bulkhead pool utilization and queue depth.

All wired into a standard dashboard per service.

### Service Discovery

- All services register with a service registry (e.g., Consul, Kubernetes DNS).
- Clients use client-side load balancing (e.g., gRPC round-robin) or a sidecar proxy (e.g., Envoy).

## Asynchronous Event-Driven Communication (Message Queue)

### Event Bus (Kafka)

Kafka serves as the central event backbone. Every state change of importance is published as an event.

| Topic Naming Convention | Example |
|---|---|
| `<domain>.<event-name>` | `order.created`, `payment.settled` |

### Event Schema

Events are serialized as Avro or Protobuf with a Schema Registry for evolution:

```protobuf
message OrderCreated {
  string order_id = 1;
  string customer_id = 2;
  double total_amount = 3;
  int64 timestamp = 4;
}
```

### Producing and Consuming

- **Producers:** Services publish events **after** their local DB transaction commits (outbox pattern).
- **Consumers:** Services consume events idempotently (by `event_id` dedup) and process asynchronously.
- **Error handling:** Failed events go to a dead-letter topic (DLT) with offset + error metadata; a reconciliation job replays after manual fix.

### Outbox Pattern

To guarantee at-least-once delivery without distributed transactions:

1. Service writes the business entity + outbox record in the **same local DB transaction**.
2. A background poller (or Debezium CDC connector) reads the outbox table and publishes to Kafka.
3. Consumer deduplicates via `event_id`.

## MySQL Database

### Per-Service Database

Each microservice gets its own logical database (or schema). No service accesses another service's DB directly — all communication is via the API or event bus.

### Schema Design

- Well-normalized for transactional workloads (OLTP).
- Soft deletes (`deleted_at`) where applicable.
- Indexing strategy: cover query patterns with composite indexes; avoid over-indexing on write-heavy tables.

### Connection Pooling

Every service uses a connection pool (e.g., HikariCP for Java, `sqlalchemy.pool` for Python) with:

- Minimum idle connections: 2
- Maximum pool size: calculated as `(core_count * 2) + effective_spindle_count`
- Connection timeout: 5s
- Idle timeout: 10 min

### Migrations

All schema changes are managed via versioned migration files (e.g., Flyway, Liquibase, Alembic). Migrations are applied as part of the deployment pipeline, before the new service version starts.

### Read Replicas

- Read-only queries (reports, dashboards) are routed to read replicas.
- Writes always go to the primary.

### Encryption at Rest

- MySQL data volumes use **AES-256** encryption via Transparent Data Encryption (TDE) — InnoDB tablespace encryption (MySQL 8.0.13+).
- Binary logs, relay logs, and temp files are also encrypted.
- Encryption keys managed by KMS (AWS KMS / HashiCorp Vault) with 90-day rotation.
- Encrypted connections **required** between service and database (TLS 1.3).

## Kafka for High-Throughput Data Writing

Kafka is the primary sink for all **high-volume write streams** (logs, events, metrics, CDC). It decouples data producers from storage.

### Data Flow

```
Producer → Kafka → Kafka Streams / Kafka Connect → Sink (S3 / HDFS / ClickHouse / Elasticsearch / MySQL)
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **Partition count:** 3× the number of consumers per topic | Allows rebalancing headroom and parallel consumption. |
| **Replication factor:** 3 | Fault tolerance across brokers. |
| **Retention:** 7 days for raw events, compacted for keyed tables. | Balances replay capability with storage cost. |
| **Encryption at rest:** AES-256 on broker volumes (LUKS) + optional topic-level encryption. | GDPR compliance for stored events. |
| **Acks:** `acks=all` for critical events, `acks=1` for throughput-sensitive streams. | Trade-off durability vs. latency. |
| **Compression:** `lz4` or `zstd` on the producer. | Reduces network and storage. |
| **Message key:** Use a domain key (e.g., `order_id`) to preserve ordering per entity. | Enables ordered processing per partition. |

### Exactly-Once Semantics (EOS)

- Enable `enable.idempotence=true` on producers.
- For exactly-once processing in Streams, use `processing.guarantee=exactly_once_v2`.
- Idempotent consumers are the primary strategy; EOS is applied where exactly-once sinks are required.

### Kafka Connect (CDC)

- **Debezium** captures MySQL binlog changes and streams them as Kafka events.
- Used for:
  - Outbox event relay (without poller).
  - Sync to search indices (Elasticsearch).
  - Sync to cache (Redis).
  - Sync to analytics stores (ClickHouse, S3).

## Deployment & Infrastructure

### Container Orchestration (Kubernetes)

- Each microservice runs as a Kubernetes Deployment with horizontal pod autoscaling (HPA) based on CPU/memory/custom metrics.
- StatefulSets for Kafka brokers, MySQL, and Zookeeper.
- Istio / Linkerd service mesh for mTLS, traffic splitting, and observability.

### CI/CD Pipeline

```
Build → Unit Test → Integration Test → Container Build → Staging Deploy → E2E → Production Deploy
```

- Blue-green or canary deployments.
- Health checks (liveness + readiness) must pass before traffic is routed.

## Observability

| Pillar | Tooling | Purpose |
|---|---|---|
| Logging | Structured JSON (stdout) → Fluentd → Elasticsearch | Centralized log search |
| Metrics | Prometheus + Grafana | Dashboards, alerting |
| Tracing | OpenTelemetry → Jaeger / Tempo | Distributed trace visualization |
| Health Checks | `/health` (liveness), `/ready` (readiness) | K8s probe endpoints |

### Required Metrics per Service

- Request rate, error rate, duration (RED method).
- Database pool utilization, query latency.
- Kafka produce/consume lag.
- Goroutine / thread count.

## Authentication (JWT)

JWT (JSON Web Token) is the primary authentication mechanism for all user-facing requests. The API Gateway is the single enforcement point.

### Token Types

| Token | Lifetime | Storage | Purpose |
|---|---|---|---|
| Access Token | 15 minutes | In-memory (client) | Authorizes API requests. Sent as `Authorization: Bearer <token>`. |
| Refresh Token | 7 days | HTTP-only secure cookie (or client storage) | Obtains new access tokens without re-authentication. |
| ID Token | 15 minutes | Client | Identity claims; used by frontend for display, not for API auth. |

### Token Format

```
Header:  { "alg": "RS256", "typ": "JWT", "kid": "..." }
Payload: {
  "sub": "user_abc123",
  "iss": "https://auth.example.com",
  "aud": "order-service",
  "exp": 1700000000,
  "iat": 1699999100,
  "roles": ["admin", "operator"],
  "scope": "orders:read orders:write"
}
```

- Algorithm: **RS256** (asymmetric RSA) — private key signs, public keys verify.
- Services verify tokens using JWKS (JSON Web Key Set) fetched from the auth service; no need to call the auth service on every request.
- `scope` and `roles` claims are used for fine-grained authorization.

### Token Flow

```
┌────────┐  POST /login     ┌────────────┐  Issue JWT   ┌──────────┐
│ Client │ ───────────────→ │ Auth Service│ ────────────→ │   JWT    │
│        │ ←─────────────── │ (Issuer)    │              │ (Tokens) │
└────────┘  Access+Refresh  └────────────┘              └──────────┘
     │                                                        │
     │  Request with Access Token                             │
     │ ────────────────────────────────────────────────────→  │
     │ ←──────────────────────────────────────────────────── │
     │           200 OK / 401 Unauthorized                    │
     │                                                        │
     │  Refresh on 401                                       │
     │ ────────────────────────────────────────────────────→  │
     │ ←──────────────────────────────────────────────────── │
     │           New Access Token / Refresh token rotation    │
```

1. Client authenticates via the Auth Service (login form, OAuth2 provider).
2. Auth Service issues an access token + refresh token pair.
3. Client includes the access token in every API request.
4. API Gateway validates the token (signature, expiry, audience) before proxying to downstream services.
5. When the access token expires, the client uses the refresh token to obtain a new pair (refresh token rotation).

### Validation in API Gateway

- Verify RS256 signature against the JWKS endpoint (cached, TTL 1 hour).
- Check `exp` (expiration), `nbf` (not before), `iss` (issuer), `aud` (audience).
- Extract `sub` (user ID) and inject it as a trusted header (`X-User-ID`, `X-User-Roles`) to downstream services, so microservices do not need to parse JWTs themselves.

### Token Revocation

- Revocation is handled via a **deny-list** (Redis, TTL = access token expiry). API Gateway checks the deny-list before validating the signature.
- Refresh tokens are revoked on logout or password change by deleting them from the data store.
- Long-lived compromise: rotate the signing key pair and update JWKS.

### Security

- **Never** store access/refresh tokens in `localStorage` (XSS vulnerability). Use HTTP-only secure cookies for refresh tokens.
- Access tokens returned in the response body; frontend keeps them in memory only.
- All inter-service communication additionally protected with **mTLS** (mutual TLS).

## Encryption at Rest

All data stores **must encrypt data at rest** using **AES-256** as the baseline cipher. This is mandatory for GDPR compliance (Art. 32 — "security of processing") and general data protection best practice.

| Data Store | Encryption Method | Key Management |
|---|---|---|
| **MySQL** | Transparent Data Encryption (TDE) via MySQL Enterprise or Percona Server with AES-256 tablespace encryption. Alternatively, filesystem-level LUKS/dm-crypt on the data volume. | Keys stored in Vault or KMS (AWS KMS / GCP Cloud KMS); rotated every 90 days. |
| **Kafka** | Broker-side `log.message.encryption` or at-rest encryption via encrypted volumes (LUKS). Topic-level encryption for sensitive PII topics. | Per-topic keys in Vault; broker volume key via KMS. |
| **Redis** | Redis Enterprise on-disk encryption (AES-256-GCM) or filesystem-level encryption for persistence (RDB/AOF files). | Encryption key from KMS, cached in memory for the lifetime of the process. |
| **Elasticsearch / OpenSearch** | Encrypted at the filesystem level (LUKS), plus cluster-level encryption with the `opensearch-security` plugin (AES-256). | KMS-managed volume key; cluster key stored in the elasticsearch keystore. |
| **S3 / Object Store** | Server-Side Encryption (SSE-S3 or SSE-KMS) with AES-256. Enable bucket default encryption. | SSE-KMS uses a KMS-managed CMK with automatic key rotation. |
| **Backups (MySQL dump / S3 snapshots)** | GPG or `openssl enc -aes-256-cbc` before uploading to S3/offsite storage. | Backup passphrase stored in Vault. |

### Column-Level Encryption (PII)

For highly sensitive fields (passwords, email, phone, tax ID, payment card PAN):

```
┌──────────────────────────────────────────────────────┐
│  Application layer encrypts before writing to DB:    │
│                                                      │
│  ciphertext = AES-256-GCM(plaintext, derived_key)    │
│  ciphertext + nonce + tag are stored in a BLOB       │
│  column (e.g. `encrypted_email`).                    │
│                                                      │
│  Keys are derived per-user from a master key +       │
│  user_id (envelope encryption). Master key in KMS.   │
└──────────────────────────────────────────────────────┘
```

- Never store raw secrets in logs, error messages, or audit trails.
- Data masking at the application layer for read queries in non-production environments.

### Encryption Key Rotation

- **Volume / TDE keys:** rotate every 90 days (automated via KMS key rotation).
- **Application-level encryption keys:** re-wrap with a new master key (re-encrypt data lazily on read, or via a background re-key job).
- **Kafka topic keys:** rotate on topic compaction or log segment roll.

### GDPR Compliance Checklist

| Requirement | How Addressed |
|---|---|
| Data is encrypted at rest | AES-256 on all data stores (TDE / filesystem / SSE). |
| Encryption keys are managed securely | KMS / Vault with access audit logging, automatic rotation. |
| PII is protected beyond default encryption | Column-level AES-256-GCM for high-sensitivity fields. |
| Backups are also encrypted | AES-256-CBC before offsite storage. |
| Key rotation process exists | 90-day rotation for volume keys; per-master-key rotation for application-level. |
| Encryption is documented and auditable | This document + Infrastructure-as-Code + KMS audit logs. |

## Test-Driven Development (TDD)

All code is written test-first. The **Red → Green → Refactor** cycle is the default workflow for every feature and bug fix.

### Workflow

```
┌─────────────────────────────────────────────────────┐
│  1. RED    Write a failing test that describes the  │
│            desired behaviour (one assertion only).  │
├─────────────────────────────────────────────────────┤
│  2. GREEN  Write the minimal code to make the test  │
│            pass (no optimisation, no extra logic).   │
├─────────────────────────────────────────────────────┤
│  3. REFACTOR  Clean up both code and test. Remove   │
│               duplication, improve naming, ensure   │
│               the test still passes.                │
└─────────────────────────────────────────────────────┘
```

### Test Pyramid

```
         ╱╲
        ╱  ╲
       ╱ E2E╲            ←  Few  — smoke / critical user journeys
      ╱──────╲
     ╱Integration╲        ←  Some — service-level, DB, Kafka, contract
    ╱────────────╲
   ╱   Unit Tests  ╲      ← Many  — pure business logic, domain entities
  ╱────────────────╲
```

| Layer | Scope | Examples | Tools |
|---|---|---|---|
| **Unit** | Single class, function, or module. External dependencies are mocked/stubbed. | Validate order total, tax calculation, state machine transitions | JUnit (Java), `testing` package (Go), Vitest/Jest (Node), pytest (Python) |
| **Integration** | Service boundary — real DB, real Kafka (via Testcontainers), real HTTP client. One external dependency at a time. | Repository queries, Kafka produce/consume, REST handler response codes | Testcontainers, `testcontainers-go`, `testcontainers-java`, pytest-docker |
| **Contract** | Provider verifies its API matches the consumer's expectations (Pact / Spring Cloud Contract). | "Order service returns 200 with order body for GET /orders/:id" | Pact, Spring Cloud Contract |
| **E2E** | Full system deployed in a transient environment (ephemeral K8s namespace). | User places order → payment processed → inventory updated | Playwright, Cypress, k6, Argo Workflows |

### Testing Conventions

- **Test name describes the scenario:** `{method}_{given}_{expect}` — e.g. `calculateTotal_whenNoItems_returnsZero`.
- **Arrange → Act → Assert** structure enforced in every test body.
- **One logical assertion per test.** Multiple assertions on the same object are acceptable if they verify one behaviour.
- **Never share mutable state between tests.** Each test sets up its own fixtures.
- **Fake → Stub → Mock** preference order. Use fakes (in-memory implementations) unless the behaviour must be verified (mock).
- **Test data** is created via factory functions / builders, not static JSON files.

### Test Doubles Preference

| Type | When to Use |
|---|---|
| **Fake** | In-memory DB, in-memory Kafka, in-memory cache — full working implementation. First choice. |
| **Stub** | Returns fixed values for a specific call. Second choice. |
| **Mock** | Verifies interaction expectations (was `Send()` called exactly once?). Last resort. |

### Code Coverage Targets

| Metric | Target |
|---|---|
| Line coverage (unit) | ≥ 80% |
| Branch coverage (unit) | ≥ 75% |
| Integration coverage (critical paths) | 100% of all repository and message handler methods |

Coverage is a **lower bound indicator**, not a goal. Missing a test for an edge case is a design smell even at 100% coverage.

### CI Enforcement

- Unit + integration tests **must pass** before a PR can merge (blocking CI gate).
- Contract tests run on every PR; a contract break blocks the pipeline.
- E2E tests run nightly and on staging deploys; they are allowed to be flaky but flakiness must be fixed within 24 hours.
- Test execution time per service should stay under **5 minutes** (unit + integration). If longer, split the service or parallelise.

## Chaos Engineering

Chaos engineering is the practice of **intentionally injecting failures** into the system to uncover weaknesses before they cause production incidents. It is a core requirement, not an optional activity.

### Principles

- **Hypothesis-driven:** Every experiment starts with a hypothesis about steady-state behavior (e.g. "when one Kafka broker fails, produce/consume latency stays under 500ms").
- **Blast radius controlled:** Experiments start in staging, then progress to production in a small, contained scope (1% of traffic, one AZ, one partition).
- **Automated and continuous:** Experiments run on a schedule (e.g. daily game day), not as one-off manual drills.
- **Automated rollback:** If the system deviates beyond a defined threshold, the experiment aborts and remediation is triggered.

### Experiment Types

| Category | Experiment | Tooling |
|---|---|---|
| **Network** | Latency injection, packet loss, DNS failure, TLS termination | Chaos Mesh / Toxiproxy / Istio fault injection |
| **Compute** | Pod/kill, node failure, resource exhaustion (CPU/memory/disk) | Chaos Mesh / Litmus / Gremlin |
| **Database** | Connection pool exhaustion, slow queries, failover, replica lag | Chaos Mesh + custom SQL injectors |
| **Kafka** | Broker kill, partition leader re-election, produce/consume lag injection, topic deletion | Chaos Mesh / Kafka-specific fault probes |
| **Dependencies** | Downstream service timeout / 500 / circuit breaker trip | Istio fault injection / Hoverfly / WireMock |
| **State** | Clock skew, corrupted messages, duplicate events | Custom chaos agents |

### Game Day Cadence

```
┌──────────────────────────────────────────────────────────────┐
│  Monthly Game Day Schedule                                  │
│                                                              │
│  Week 1: Plan & hypothesis review                            │
│  Week 2: Staging experiment run + retro                     │
│  Week 3: Production experiment (low blast radius)            │
│  Week 4: Report, resilience backlog grooming                │
└──────────────────────────────────────────────────────────────┘
```

### Steady-State Metrics (measured before, during, and after experiment)

- p99 API latency
- Error rate (5xx / 4xx)
- Kafka consumer lag
- Database query latency and pool utilization
- Business KPIs (e.g. order completion rate, payment success rate)

### Tooling Recommendation

| Tool | Purpose |
|---|---|
| **Chaos Mesh** | Kubernetes-native fault injection (pod kill, network partition, IO delay). First choice for K8s-based deployments. |
| **Litmus** | Chaos orchestration with pre-defined experiment hubs and workflow scheduling. |
| **Toxiproxy** | TCP-level network chaos (latency, bandwidth, disconnects) for integration tests. |
| **Istio fault injection** | Service mesh level: HTTP delay, abort, timeout for specific routes. |
| **Gremlin** | SaaS chaos platform with managed experiments and reporting (alternative if no in-house K8s chaos tooling). |

### Success Criteria

The system is considered resilient when:

1. No experiment causes **user-facing impact** (all failures are masked by circuit breakers, retries, failover).
2. All steady-state metrics return to baseline **within 60 seconds** after the fault is removed.
3. Every service's degraded behaviour is **observable** (correct log levels, metric spikes, trace spans with error tags).
4. A regression caught in staging never reaches production twice.

## Failure Handling

| Failure Scenario | Mitigation |
|---|---|
| Downstream service unavailable | Circuit breaker (e.g., Resilience4j, Hystrix) with fallback |
| Kafka broker down | Replicas re-elect leader; producer retries with backoff |
| DB connection exhausted | Pool waits, rejects with 503; circuit breaker trips |
| Message processing failure | Retry topic (3 attempts) → Dead Letter Topic → Alert |
| Consumer crash | Kafka rebalances partitions to remaining consumers |
| Network partition | Idempotent consumers + outbox pattern ensure no data loss |

## Technology Stack (Recommended)

| Component | Technology |
|---|---|
| Language | Go / Kotlin / Java / Rust (choose per service) |
| API | gRPC (inter-service), REST (external-facing via Gateway) |
| Message Queue | Apache Kafka + Schema Registry |
| Database | MySQL 8+ (per-service), Vitess or ProxySQL for sharding |
| CDC | Debezium (Kafka Connect) |
| Cache | Redis (distributed cache, session store) |
| Search | Elasticsearch / OpenSearch |
| Container | Docker + Kubernetes |
| Service Mesh | Istio / Linkerd |
| Resilience (circuit breaker) | Resilience4j (Java), `hystrix-go` / `breaker` (Go), `opossum` (Node), `pybreaker` (Python) |
| Observability | OpenTelemetry, Prometheus, Grafana, Jaeger/Tempo |
| Chaos Engineering | Chaos Mesh, Litmus, Toxiproxy, Istio fault injection |
| CI/CD | GitLab CI / GitHub Actions / ArgoCD |
