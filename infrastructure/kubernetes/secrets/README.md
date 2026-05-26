# Secrets Management — boltchats

⚠️ **NEVER commit real secrets to Git**

## Local Development (Minikube/Kind)
```bash
kubectl create secret generic boltchats-secrets \
  --namespace=boltchats \
  --from-literal=mongodb-root-username=admin \
  --from-literal=mongodb-root-password=localdev123 \
  --from-literal=redis-password=localredis123 \
  --from-literal=jwt-secret=local-jwt-secret-min-32-characters-long \
  --from-literal=refresh-token-secret=local-refresh-secret-min-32-chars
```

## Production (Sealed Secrets)

### 1. Install Sealed Secrets Controller
```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml
```

### 2. Install kubeseal CLI
```bash
# macOS
brew install kubeseal

# Linux
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-0.24.0-linux-amd64.tar.gz
tar -xvzf kubeseal-0.24.0-linux-amd64.tar.gz
sudo install -m 755 kubeseal /usr/local/bin/kubeseal
```

### 3. Create Sealed Secret
```bash
# Create temp secret file
kubectl create secret generic boltchats-secrets \
  --namespace=boltchats \
  --from-literal=mongodb-root-username=prod-admin \
  --from-literal=mongodb-root-password='STRONG_RANDOM_PASSWORD' \
  --from-literal=redis-password='STRONG_RANDOM_PASSWORD' \
  --from-literal=jwt-secret='STRONG_RANDOM_32_CHAR_STRING' \
  --from-literal=refresh-token-secret='STRONG_RANDOM_32_CHAR_STRING' \
  --dry-run=client -o yaml > /tmp/secret.yaml

# Seal it (encrypted, safe to commit)
kubeseal --format=yaml --cert=pub-cert.pem < /tmp/secret.yaml > sealed-secret.yaml

# Clean up temp file
rm /tmp/secret.yaml

# Apply sealed secret
kubectl apply -f sealed-secret.yaml
```

## Alternative: External Secrets Operator

### 1. Install ESO
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

### 2. Configure AWS Secrets Manager Backend
See `external-secret-aws.yaml` for example.

### 3. Configure HashiCorp Vault Backend
See `external-secret-vault.yaml` for example.

---

## Required Secret Keys

| Key | Used By | Min Length |
|-----|---------|------------|
| `mongodb-root-username` | MongoDB StatefulSet | — |
| `mongodb-root-password` | MongoDB StatefulSet | 12+ chars |
| `redis-password` | Redis StatefulSet | 12+ chars |
| `jwt-secret` | api, ws services | 32+ chars |
| `refresh-token-secret` | api service | 32+ chars |

---

## Security Best Practices

✅ Use different secrets per environment (dev/staging/prod)  
✅ Rotate secrets every 90 days  
✅ Use strong random generators: `openssl rand -base64 32`  
✅ Store production secrets in external secret manager (AWS SM, Vault, GCP SM)  
✅ Never log secret values  
✅ Restrict RBAC access to secrets  

❌ Never commit secrets to Git  
❌ Never hardcode secrets in ConfigMap  
❌ Never share secrets via Slack/email  
