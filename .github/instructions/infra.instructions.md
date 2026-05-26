---
applyTo: "infrastructure/**,scripts/**"
---
# Infrastructure Rules — boltchats

## Kubernetes Layout
```
infrastructure/kubernetes/
├── base/
│   ├── namespace.yaml
│   └── configmap.yaml          # Common config — NO secrets here
├── components/                 # App services only
│   ├── api-deployment.yaml / api-service.yaml
│   ├── ws-deployment.yaml  / ws-service.yaml
│   ├── storage-deployment.yaml / storage-service.yaml
│   ├── network-policy.yaml
│   └── service-monitor.yaml    # Prometheus scrape config
├── databases/                  # Different lifecycle/owner
│   ├── mongodb-statefulset.yaml / mongodb-service.yaml
│   └── redis-deployment.yaml   / redis-service.yaml
├── overlays/
│   ├── dev/    → kustomization.yaml + patch.yaml
│   ├── staging → + hpa.yaml + pdb.yaml
│   └── prod/   → + hpa.yaml + pdb.yaml + ingress.yaml
└── secrets/
    ├── sealed-secret.yaml      # kubeseal encrypted
    └── external-secret.yaml    # Vault / AWS SSM reference
```

## Kubernetes Rules
- `localhost`, hardcoded ports, IPs → **forbidden** in service code
- All config via env vars injected through ConfigMap
- Secrets → Sealed Secret or External Secret only. **Never in ConfigMap.**
- `components/` = app services | `databases/` = stateful infra (separate lifecycle)

## Terraform Layout
```
terraform/
├── modules/eks/ · modules/vpc/ · modules/mongodb-atlas/
├── environments/dev/ · staging/ · prod/
│   └── main.tf + provider.tf + variables.tf + terraform.tfvars + backend.tf
└── global/iam.tf   # Cross-env IAM only — no provider here
```

## Terraform Rules
- `provider.tf` lives in each `environments/*/` — never in `global/`
- `global/` contains only cross-environment IAM resources
- Remote state: S3 bucket + DynamoDB lock (defined in each `backend.tf`)

## CI/CD Workflows
| File | Trigger |
|------|---------|
| `ci.yml` | Every PR — test + lint + build |
| `cd-api/ws/storage.yml` | main → staging · git tag → prod |
| `security-scan.yml` | Scheduled + PR — Trivy + Snyk |
| `load-test.yml` | Nightly — k6 |

## Script Responsibility
| Location | Purpose |
|----------|---------|
| `services/*/scripts/` | Service-specific: migrate, seed, admin |
| `scripts/` (root) | Infra/ops: deploy.sh, backup, load-test wrapper |
