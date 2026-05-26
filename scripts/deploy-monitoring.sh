#!/usr/bin/env bash
set -euo pipefail

# Monitoring Stack Deployment Script
# Deploys Prometheus, Grafana, and Loki using Helm

NAMESPACE="monitoring"
KUBECTL="kubectl"
HELM="helm"

echo "🚀 Deploying Monitoring Stack"
echo "================================"

# Create namespace
echo "📦 Creating namespace: $NAMESPACE"
$KUBECTL create namespace $NAMESPACE --dry-run=client -o yaml | $KUBECTL apply -f -

# Add Helm repos
echo "📚 Adding Helm repositories"
$HELM repo add prometheus-community https://prometheus-community.github.io/helm-charts
$HELM repo add grafana https://grafana.github.io/helm-charts
$HELM repo update

# Deploy Prometheus (kube-prometheus-stack)
echo "📊 Deploying Prometheus Operator + Prometheus"
$HELM upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace $NAMESPACE \
  --values infrastructure/monitoring/prometheus-values.yaml \
  --wait \
  --timeout 10m

# Deploy Loki
echo "📝 Deploying Loki"
$HELM upgrade --install loki grafana/loki \
  --namespace $NAMESPACE \
  --values infrastructure/monitoring/loki-values.yaml \
  --wait \
  --timeout 5m

# Deploy Grafana
echo "📈 Deploying Grafana"
$HELM upgrade --install grafana grafana/grafana \
  --namespace $NAMESPACE \
  --values infrastructure/monitoring/grafana-values.yaml \
  --wait \
  --timeout 5m

# Get Grafana password
echo ""
echo "✅ Monitoring Stack Deployed!"
echo "================================"
echo ""
echo "📊 Prometheus: http://prometheus-kube-prometheus-prometheus.monitoring:9090"
echo "📈 Grafana: http://grafana.monitoring"
echo ""
echo "🔑 Grafana Admin Password:"
$KUBECTL get secret --namespace $NAMESPACE grafana -o jsonpath="{.data.admin-password}" | base64 --decode
echo ""
echo ""
echo "🌐 Port Forward Grafana:"
echo "   kubectl port-forward -n monitoring svc/grafana 3000:80"
echo ""
