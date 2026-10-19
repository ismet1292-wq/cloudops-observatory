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

**What do `/healthz` and `/readyz` prove?** `/healthz` shows that the HTTP server responds. `/readyz` returns 200 only after the monitoring worker completes a cycle and while progress remains fresh. Startup, stale progress, worker failure, and shutdown return 503. Failed target checks still count as completed monitoring work. The readiness check proves recent progress, not immediate database writability or production availability.

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

Docker publication, Minikube persistence, and the temporary AWS deployment have recorded project evidence. Review that evidence and explain which actions you performed and where AI assistance was used. This project does not establish paid client experience.

## Verified AWS portfolio example

Deployed and validated an AI-assisted Python monitoring application on AWS using
Terraform, a digest-pinned Docker image, encrypted EBS storage, and private
Systems Manager access; verified incident recovery and persistence after
container replacement and host reboot, then removed the temporary compute and disks.

Use this wording only after you can explain the implementation and your own
contribution. The demo was temporary, used internal test endpoints, and is no
longer running. It did not demonstrate high availability or production operations.
See [AWS results and evidence](AWS_DEMO_RESULTS.md).

Be prepared to explain:

- Why the application listens on loopback and needs no inbound security-group rules.
- Why the host still needed outbound connectivity and a public IPv4 address.
- How the mounted data disk preserved SQLite history across container replacement and reboot.
- Why one host and SQLite imply downtime and limit scaling.
- How cleanup was verified, and why an agreed allowance was not an enforced billing cap.


## Version 0.3 decisions

The worker uses ThreadPoolExecutor with eight threads to overlap network waits. The main monitor thread stores completed results sequentially. A BEGIN IMMEDIATE transaction keeps the check, consecutive-result counters, and incident transition atomic. The health_state table preserves counters across restarts. Opposite outcomes reset each consecutive streak. A barrier-based test verifies three probes can start concurrently without relying on fragile timing assertions.
