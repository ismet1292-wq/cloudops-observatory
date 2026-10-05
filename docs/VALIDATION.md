# Validation for v0.4 — October 4, 2026

Executed in the Linux development workspace: `python3 -m unittest -v`.
Result: 12 tests passed.

Verified: HTTP health/failure probes and status API; metrics output; incident
opening, deduplication and recovery; latest-120-sample window; nearest-rank p95;
unsupported endpoint scheme rejection; threshold validation; persisted counters;
concurrent probes; timed demo boundaries; standalone lesson connection failure.

Also executed the actual app.py --demo process with a fresh database and an
automatically assigned local port. Observed healthy at 0 seconds, HTTP outage
at 10 seconds, an open incident at 12 seconds, recovery at 22 seconds, and the
same incident resolved at 24 seconds. Verified dashboard, metrics and health
routes returned HTTP 200. Dashboard JavaScript passed node --check.

Validated on Windows 11: local Python launch, Docker image build, container health endpoint, non-root UID/GID 10001, SQLite persistence through a named volume and container replacement, Minikube deployment, Bound 1 GiB PVC, readiness rollout, non-root pod execution, pod replacement with preserved incident ID 1, and GitHub-hosted CI.


Published the container to the public GitHub Container Registry with latest and immutable commit-SHA tags. Pulled the public latest image, started it locally, received status ok from /healthz, and confirmed non-root UID/GID 10001.
Not executed: AWS deployment, production load testing, or a production security audit.
