# Stagingelopment Environment — boltchats

## Prerequisites

1. Bootstrap global backend:
   ```bash
   cd ../../global
   terraform init
   terraform apply
   ```

2. Configure AWS credentials:
   ```bash
   aws configure
   ```

## Deploy

```bash
cd terraform/environments/staging

# Initialize
terraform init

# Plan
terraform plan -out=staging.tfplan

# Apply
terraform apply staging.tfplan
```

## Resources Created

- **VPC**: `10.0.0.0/16` across 2 AZs
- **EKS Cluster**: Kubernetes 1.31
- **Node Group**: 2 × t3.large (1-4 auto-scaling)
- **NAT Gateways**: 2 (one per AZ)

## Configure kubectl

```bash
aws eks update-kubeconfig --region eu-central-1 --name boltchats-staging
kubectl get nodes
```

## Deploy Application

```bash
cd ../../../infrastructure/kubernetes

# Deploy databases
kubectl apply -k databases/

# Deploy secrets (create manually first)
kubectl create secret generic boltchats-secrets \
  --namespace=boltchats \
  --from-literal=mongodb-root-username=admin \
  --from-literal=mongodb-root-password=stagingpass123 \
  --from-literal=redis-password=stagingredis123 \
  --from-literal=jwt-secret=staging-jwt-secret-min-32-characters-long \
  --from-literal=refresh-token-secret=staging-refresh-secret-min-32-chars

# Deploy services
kubectl apply -k overlays/staging/
```

## Cleanup

```bash
# Delete Kubernetes resources first
kubectl delete -k overlays/staging/
kubectl delete -k databases/

# Destroy infrastructure
terraform destroy
```

## Cost Estimate (Monthly)

- EKS control plane: $73
- 2 × t3.large nodes (730h): ~$60
- 2 × NAT Gateways: ~$65
- EBS volumes (100GB total): ~$10
- **Total: ~$208/month**
