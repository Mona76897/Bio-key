# BioKey V2
**An ML-Based Continuous Behavioral Authentication and Cybersecurity Framework for Real-Time Session Protection**

## What this is

BioKey continuously verifies user identity *during* an active session using keystroke
dynamics (Dwell Time and Flight Time), rather than checking identity only once at login.
Keystroke telemetry streams from a client agent into a scoring pipeline that produces a
live Trust Score (0-100%) and triggers graduated responses (AUTHORIZED / WARNING / ISOLATE)
if the typing pattern no longer matches the enrolled user.

## Team

| Role | Owner | Responsible for |
|---|---|---|
| Lead Architect / Cloud & DevSecOps | *(you)* | AWS infra, `backend_service/`, `infrastructure/`, CI/CD |
| ML Lead | *(teammate 1)* | `ml_engine/` — dataset, training, MLflow tracking, ONNX export |
| Frontend & Scoring Logic Lead | *(teammate 2)* | `client/`, `backend_service/app/core/` (buffer, EMA, state machine), dashboard |

## Repo structure

```
biokey-v2/
├── client/               # Keystroke capture agent + lockout UI
│   └── src/
├── ml_engine/             # Training scripts, MLflow experiments, ONNX exports
│   ├── data/               # Dataset download/prep scripts (not raw data — see .gitignore)
│   ├── notebooks/          # EDA and experimentation
│   └── models/             # Exported .onnx model artifacts
├── backend_service/       # FastAPI ingestion + inference + scoring engine
│   └── app/
│       ├── api/             # Ingestion & health endpoints
│       └── core/            # Rolling buffer, EMA smoothing, state machine
├── infrastructure/        # Docker, IaC, CI/CD
│   ├── docker/
│   └── ci/
├── test_harness/           # FAR / FRR / detection-latency evaluation scripts
└── legacy/v1_demo/         # V1 prototype — kept as a working reference/fallback
```

## Build plan (see full roadmap in project docs)

- **Weeks 1-2**: Foundations — infra skeleton, dataset sourcing, capture widget.
- **Weeks 3-4**: Core pipeline working end-to-end (boring path — no Kafka/Vault yet).
  This is the milestone that must work before anything else starts.
- **Weeks 5-6**: Real ONNX model wired in, evaluation harness (`test_harness/`) built.
- **Weeks 7-8**: First tool swap — Terraform (codifying what already works).
- **Weeks 9-10**: Second tool swap — Vault / optional Kafka, only if on schedule.
- **Weeks 11-12**: CI/CD + polish, viva prep.
- **Weeks 13-14**: Buffer.

**Rule:** nothing after week 4 is allowed to break what worked at week 4. Every tool
swap happens on a branch, behind the same interface, with the simpler version still
demo-able as fallback.

## Scope

**In scope:** keyboard timing only (dwell/flight time), FastAPI ingestion pipeline,
ONNX inference, EMA scoring engine, cloud deployment with CI/CD, evaluation harness
producing FAR/FRR/latency.

**Explicitly out of scope (for this project):** other biometric modalities (mouse,
face), enterprise streaming infra (Kafka) and secrets managers (Vault) as *required*
components (allowed as optional stretch swaps once core is solid), formal
penetration/adversarial-evasion testing, SSO/LDAP integration.

## Status

🔧 Week 1 — repo scaffolded, infra and pipeline work starting.
