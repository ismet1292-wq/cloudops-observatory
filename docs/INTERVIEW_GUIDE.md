# CloudOps Observatory interview guide

Use this after running the project and making your own changes. This guide explains the implementation; it does not establish that you personally completed a deployment.

## Demonstration in three minutes

1. Run the tests and explain one incident transition test.
2. Start the app and open the dashboard. Show the healthy endpoint and the deliberate failed endpoint.
3. Show `/api/status` and `/metrics` to demonstrate data can be consumed by other tools.
4. Stop the app, change the failed service URL to `/healthz` without changing its name, and restart. Show the resolved incident.
5. Explain one limitation and your next design improvement.

## Technical questions

**How do incidents work?** A check is always recorded. Consecutive failures at the configured threshold insert an incident if one is not already open. A partial unique index permits only one open incident per service. Consecutive successful checks at the recovery threshold resolve the active incident in the same transaction as writing the check.

**How is availability calculated?** The success percentage across the latest 120 checks per service. It is sample-based, not a contractual SLA or elapsed-time uptime calculation. Monitoring outages create missing samples, which this version does not count as failures.

**How is p95 calculated?** Sort latency values across that window and use the nearest-rank 95th percentile. It includes failed checks, so discuss whether a separate successful-request percentile would be more useful.

**Why SQLite?** It makes a small single-process prototype easy to run and supports transactionally consistent incident transitions. Before scaling to multiple workers, migrate storage and redesign task ownership to avoid duplicate probes.

**Why one Kubernetes replica and Recreate?** The app includes its own scheduler and uses a single SQLite database volume. Multiple replicas could duplicate monitoring or conflict over storage. Recreate avoids an overlapping update at the cost of downtime. This version does not demonstrate zero-downtime rolling deployment.

**What does `/healthz` prove?** Only that the HTTP server responds. It does not establish scheduler freshness or database writability. A worker-aware readiness check is a future improvement.

**What would you improve first?** Stale-data detection, retention, authentication, and restricted outbound requests. Then deploy, observe, and test the improved system.

## Evidence checklist

- [ ] You ran the app locally and verified healthy/failing checks.
- [ ] You demonstrated persistent incident recovery.
- [ ] You ran the tests yourself.
- [ ] You changed code and added a meaningful test.
- [ ] You built and ran the Docker image.
- [ ] GitHub CI passed on your repository.
- [ ] You deployed to Minikube and captured actual rollout/restart behavior.
- [ ] You can describe AI assistance and your own contribution accurately.

## Resume bullet after local verification

Developed an AI-assisted Python monitoring prototype with HTTP checks, SQLite incident tracking, a status dashboard, and automated tests; demonstrated outage detection and recovery locally.

Add Docker, CI publication, or Kubernetes deployment only after checking that evidence. Do not list AWS deployment or paid client experience for this project yet.

## Version 0.3 decisions

The worker uses ThreadPoolExecutor with eight threads to overlap network waits. The main monitor thread stores completed results sequentially. A BEGIN IMMEDIATE transaction keeps the check, consecutive-result counters, and incident transition atomic. The health_state table preserves counters across restarts. Opposite outcomes reset each consecutive streak. A barrier-based test verifies three probes can start concurrently without relying on fragile timing assertions.
