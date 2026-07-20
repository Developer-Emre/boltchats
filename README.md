<div align="center">

# 💬 boltchats

**Real-time chat platform built with a modern microservices architecture.**

[![CI](https://github.com/Developer-Emre/boltchats/actions/workflows/ci.yml/badge.svg)](https://github.com/Developer-Emre/boltchats/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Next.js](https://img.shields.io/badge/Next.js-16.2.6-black?logo=next.js)
![MongoDB](https://img.shields.io/badge/MongoDB-7-green?logo=mongodb)
![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis)

</div>

---

## 📖 Overview

boltchats is a scalable, production-ready real-time chat application. It is designed around a clean microservices architecture where each service is independently deployable, testable, and maintainable.

Key design principles:
- **No shared library** — services communicate via OpenAPI contract, not shared code
- **Each service owns its own JWT verification** — no central auth dependency
- **Secrets never in plain text** — Sealed Secrets / External Secrets only

---

## 🏗️ Architecture

```
┌─────────────────┐     REST      ┌─────────────────┐
│  boltchats-web  │ ────────────► │  boltchats-api  │
│ (Next.js 16.2.6)│               │   (FastAPI)     │
│                 │  WebSocket    ├─────────────────┤
│                 │ ────────────► │  boltchats-ws   │
└─────────────────┘               │   (FastAPI WS)  │
                                  └────────┬────────┘
                                           │ Redis Pub/Sub
                                  ┌────────▼────────┐
                                  │boltchats-storage│
                                  │  (Async Worker) │
                                  └────────┬────────┘
                                           │
                              ┌────────────▼────────────┐
                              │  MongoDB 7  │  Redis 7  │
                              └─────────────────────────┘
```

---

## 📦 Services

| Service | Description | Port | Tech |
|---------|-------------|------|------|
| `boltchats-api` | REST API — auth, users, rooms, message history | `8000` | FastAPI, Motor, JWT |
| `boltchats-ws` | WebSocket server — real-time messaging | `8001` | FastAPI WS, Redis Pub/Sub |
| `boltchats-storage` | Async message persistence worker | — | Redis Consumer, Motor |
| `boltchats-web` | Frontend application | `3000` | Next.js 16.2.6, TypeScript |

---

## 🗂️ Project Structure

```
boltchats/
├── .github/                    # CI/CD workflows, CODEOWNERS, PR template
├── services/
│   ├── boltchats-api/          # REST API service
│   ├── boltchats-ws/           # WebSocket service
│   ├── boltchats-storage/      # Storage worker service
│   └── boltchats-web/          # Frontend (Next.js)
├── infrastructure/
│   ├── kubernetes/             # K8s manifests (Kustomize)
│   ├── terraform/              # IaC — EKS, VPC, MongoDB Atlas
│   ├── monitoring/             # Helm values for Prometheus, Grafana, Loki, Tempo
│   ├── configs/                # Nginx, Prometheus, Loki, OTel configs
│   ├── logging/                # Fluent Bit, Vector
│   └── service-mesh/           # Istio
├── load-test/                  # k6 load test scripts
├── scripts/                    # Infra/ops shell scripts
├── docs/                       # API spec, architecture, ADRs, runbooks
├── docker-compose.yml          # Local dev
├── docker-compose.test.yml     # CI test environment
├── docker-compose.monitoring.yml
└── Makefile
```

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/) & Docker Compose
- [Make](https://www.gnu.org/software/make/)

### 1. Clone the repository

```bash
git clone https://github.com/Developer-Emre/boltchats.git
cd boltchats
```

### 2. Set up environment variables

```bash
cp services/boltchats-api/.env.example services/boltchats-api/.env
cp services/boltchats-ws/.env.example services/boltchats-ws/.env
cp services/boltchats-storage/.env.example services/boltchats-storage/.env
cp services/boltchats-web/.env.example services/boltchats-web/.env
```

### 3. Start all services

```bash
make up
```

### 4. Access

| Service | URL |
|---------|-----|
| Web App | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| WebSocket | ws://localhost:8001/ws |

---

## 🧪 Testing

```bash
# Run all tests (all services)
make test

# Run per service
make test-api
make test-ws
make test-storage
```

---

## 🔍 Code Quality

```bash
# Lint all services
make lint
```

Pre-commit hooks are configured via `.pre-commit-config.yaml`:
- **black** — code formatting
- **ruff** — fast linting
- **mypy** — type checking
- **hadolint** — Dockerfile linting
- **terraform fmt** — Terraform formatting

```bash
# Install hooks
pip install pre-commit
pre-commit install
```

---

## 📊 Monitoring (Local)

```bash
make monitoring-up
```

| Tool | URL |
|------|-----|
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Loki | http://localhost:3100 |

---

## 🏋️ Load Testing

```bash
# Quick health check
make load-test-smoke

# Gradual load increase
make load-test-stress

# Sudden traffic spike
make load-test-spike
```

---

## ☁️ Infrastructure

Infrastructure is managed with **Terraform** (EKS, VPC, MongoDB Atlas) and deployed via **Kustomize** overlays:

```
dev → staging → prod
```

See [infrastructure/](./infrastructure/) for details.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/api/openapi.yaml) | OpenAPI 3.0 spec |
| [WebSocket Protocol](docs/websocket/protocol.md) | WS message format & events |
| [Architecture (C4)](docs/architecture/c4-model.md) | System context & containers |
| [ADR-001](docs/architecture/decision-records/ADR-001-ws-redis-pubsub.md) | Why Redis Pub/Sub for WS |
| [ADR-002](docs/architecture/decision-records/ADR-002-kustomize-over-helm.md) | Why Kustomize over Helm |
| [ADR-003](docs/architecture/decision-records/ADR-003-no-shared-library.md) | Why no shared library |
| [Runbook](docs/operations/runbook.md) | Operations guide |

---

## 🛠️ Makefile Commands

```bash
make up                 # Start all services (local dev)
make down               # Stop and remove containers
make test               # Run full test suite
make lint               # Lint all services
make monitoring-up      # Start Prometheus + Grafana + Loki
make deploy-staging     # Deploy to staging (EKS)
make deploy-prod        # Deploy to production (EKS)
make load-test-smoke    # Run smoke load test
make load-test-stress   # Run stress load test
```

---

## 📄 License

[MIT](./LICENSE)
