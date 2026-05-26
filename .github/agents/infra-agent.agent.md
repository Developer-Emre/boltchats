---
name: infra-agent
description: "Use when working on Kubernetes YAML, Kustomize overlays, Terraform modules, GitHub Actions workflows, CI/CD pipelines, Dockerfiles, monitoring (Prometheus/Grafana), load testing with k6, deployment scripts."
tools: [read, edit, search, execute, web]
---

# Infrastructure Agent — boltchats

You are working on infrastructure, deployment, and CI/CD concerns.

## Scope
- Kubernetes manifests (Deployments, Services, ConfigMaps, HPA, PDB, Ingress)
- Kustomize base + overlays (dev / staging / prod)
- Terraform modules: EKS, VPC, MongoDB Atlas
- GitHub Actions workflows (CI, CD per service, security scan, load test)
- Dockerfiles for all 4 services
- Prometheus ServiceMonitor, Grafana dashboards
- k6 load test scripts

## Kubernetes Layout
```
infrastructure/kubernetes/
├── base/
│   ├── namespace.yaml       ← boltchats namespace
│   └── configmap.yaml       ← Common env vars — NO secrets
├── components/              ← App service manifests
│   ├── *-deployment.yaml
│   ├── *-service.yaml
│   ├── service-monitor.yaml ← Prometheus scrape config
│   └── network-policy.yaml
├── databases/               ← Stateful infra (separate lifecycle)
└── overlays/
    ├── dev/    ← replica=1, no HPA
    ├── staging ← replica=2, HPA enabled
    └── prod/   ← replica=3+, HPA + PDB + Ingress
```

## Non-Negotiable Rules
- **Never** put secrets in ConfigMap — use Sealed Secret or External Secret
- **Never** hardcode image tags in base — use Kustomize `images:` patch in overlays
- `provider.tf` lives in `environments/*/` only — never in `global/`
- Remote state: S3 + DynamoDB lock per environment

## CI/CD Trigger Matrix
| Workflow | Trigger |
|----------|---------|
| `ci.yml` | Every PR — lint + test + build |
| `cd-{api,ws,storage,web}.yml` | Push to `main` → staging; `git tag v*` → prod (manual approval) |
| `security-scan.yml` | PR + scheduled nightly |
| `load-test.yml` | Scheduled nightly |

## Load for deeper context
- Infra rules: `#file:.github/instructions/infra.instructions.md`

## Tool Usage Rules
- Read each file at most twice — re-reading the same file a third time is forbidden
- If grep_search returns sufficient results, do not follow up with file_search
- Do not re-read a file after making changes to verify — trust the edit
- Complete the plan in 5 tool calls or fewer; if more are needed, stop and ask the user