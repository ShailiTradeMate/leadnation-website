# VBIE Phase 3 — Doc 5/6: Nightly Orchestration + Queue Architecture + Scaling
## (Deliverable 6: Crawler Orchestration · Deliverable 7: Queue Architecture · Deliverable 8: Scaling Strategy · Section 7 · Section 9)

> Architecture only. NO code. The ingestion plane is **offline** — isolated from the web/app request path so it never affects user latency.

---

## SECTION 7 — NIGHTLY INTELLIGENCE ORCHESTRATION

### §7.1 Orchestrator model
A **DAG scheduler** (stage dependencies) driving the ingestion plane nightly, plus intraday micro-runs for time-sensitive sources (tenders, sanctions, news). Reads the `sources` registry to decide *what* runs, *when*, and *under what legal policy*.

### §7.2 Nightly DAG
```
00:00 DISCOVER   deltas: tenders(TED/SAM/UNGM), news RSS, new BoL consignees, new incorporations → candidates
01:00 INGEST     run due connectors (API/CSV/XML/RSS/PDF/OCR/HTML) per cadence
01:30 DOWNLOAD   bulk datasets (ABN XML, CID, ACRA, Comtrade) — change-detected
02:00 OCR+AI     scanned docs & unstructured pages → structured candidates (Section 4)
02:30 CHANGE     hash-diff; skip unchanged; version changed
03:00 RESOLVE    entity resolution / dedupe (Section 5); mid-band → QA queue
03:45 VERIFY     registry + trade + website/MX + email; SANCTIONS re-screen (hard gate)
04:15 TRUST      recompute Trust + decay; assign tiers; promote(Tier≥2)/demote
04:45 CLEANUP    dormant→hide, dissolved→archive, expire stale personal data
05:00 SUMMARIZE  Brain regenerates grounded AI summaries for changed entities
05:30 NOTIFY     intent alerts; admin digest (new buyers, errors, legal alerts)
06:00 REPORT     KPIs + calibration → admin dashboard
```

### §7.3 Orchestration properties
- **Idempotent & resumable** — checkpointed; safe re-run; auto-resume from last cursor.
- **Failure isolation** — one connector/stage failing doesn't halt the DAG; failures → retry queue + dead-letter + alert.
- **Priority** — high-value corridors + high buyer_yield + staleness first.
- **Cost guard** — nightly caps on paid verifications & LLM calls; overflow → next night.
- **Legal-aware** — every stage honors `sources` policy + suppression/opt-out registry.
- **Observability** — every run/stage/connector emits metrics + logs (`connector_runs`, `crawler_logs`, `brain_logs`).

---

## SECTION (Queue) — DELIVERABLE 7: QUEUE ARCHITECTURE

### §Q.1 Queue topology (broker-agnostic; e.g. Redis/SQS/RabbitMQ/Kafka-class)
```
discovery.queue → fetch.queue → parse.queue → extract.queue(AI) → resolve.queue
   → verify.queue → score.queue → promote.queue
+ retry.queue (backoff) + dead_letter.queue + per-domain politeness buckets
```
- **Per-domain politeness sub-queues** enforce crawl-delay/rate caps independent of global throughput.
- **Priority lanes** (high/normal/low) per queue.
- **Backpressure** — bounded queues; producers slow when consumers lag.
- **Exactly-once effect** via idempotent writes keyed on `source_id + content_hash` (at-least-once delivery tolerated).
- **Visibility/lease** timeouts → auto-requeue on worker crash (automatic resume).

### §Q.2 Workers
Stateless, horizontally scalable pools per queue (fetchers, extractors, resolvers, verifiers). Scale each pool independently by queue depth. Heavy stages (AI extract, resolution) scale separately from light stages (RSS fetch).

---

## SECTION 9 — DELIVERABLE 8: SCALING STRATEGY (10K → 10M buyers)

### §9.1 Scaling by tier
| Scale | Connectors | Queues | MongoDB | Brain/AI |
|-------|-----------|--------|---------|----------|
| **10K** | single worker per type; nightly batch | single broker, low volume | single Atlas cluster; basic indexes | rules-based resolution; LLM only for unstructured; cheap |
| **100K** | parallel workers per connector; corridor sharded jobs | priority lanes; per-domain buckets | indexes tuned; Atlas Search | ML matcher introduced; batch summaries |
| **1M** | distributed fetcher fleet; regional schedulers | partitioned queues by country/type; autoscale on depth | **shard by {country, hs_family}**; read replicas; archive cold entities | dedicated resolution service; embedding index for fuzzy/semantic; summary cache |
| **10M** | multi-region ingestion; provider adapters per corridor | Kafka-class partitioned streams; consumer groups | multi-shard, zone-aware; tiered storage (hot/warm/cold); time-series `signals` offloaded | GPU/batched inference; vector DB for matching; incremental re-score (only changed) |

### §9.2 How each layer scales
- **Connectors:** stateless + queue-driven → add workers linearly; heavy vs light pools scaled independently; provider adapters added by config.
- **Queues:** partition by country/source-type; consumer groups; autoscale on lag; dead-letter isolation.
- **MongoDB:** shard `entities` on `{country, hs_family}`; compound indexes (`registry_id`, `website`, `hs_codes.code`, `trust_band`, `status`); Atlas Search for discovery; move dormant/dissolved to cold archive; `signals` as time-series collection; read replicas for the read-heavy Buyer Card/search path.
- **Brain:** separate resolution + scoring + summary services; **incremental** recompute (only entities touched that night); embedding/vector index for fuzzy & semantic matching at scale; batch + cache AI summaries; cost guardrails.
- **Read path (web/app):** cache hot Buyer Cards + search results (short TTL); CDN for public AEO pages; fully decoupled from ingestion.

### §9.3 Startup-friendly staging
Begin single-cluster + single-broker + nightly batch (handles 10K–100K cheaply). Introduce sharding/streaming/vector only when metrics demand it. No premature infrastructure — architecture *allows* 10M but *runs lean* at 10K.
