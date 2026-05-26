# EKS Module

Production-ready Amazon EKS cluster with:
- Managed node groups with auto-scaling
- IRSA (IAM Roles for Service Accounts) via OIDC provider
- AWS Load Balancer Controller IAM role
- EBS CSI driver for persistent volumes
- EKS add-ons (VPC CNI, CoreDNS, kube-proxy)

## Usage

```hcl
module "eks" {
  source = "../../modules/eks"
  
  cluster_name       = "boltchats-dev"
  kubernetes_version = "1.31"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids
  
  node_groups = {
    general = {
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
      disk_size      = 50
      desired_size   = 2
      min_size       = 1
      max_size       = 4
      labels         = { workload = "general" }
      taints         = []
    }
  }
  
  enable_aws_load_balancer_controller = true
  enable_ebs_csi_driver               = true
  
  tags = {
    Environment = "dev"
    Project     = "boltchats"
  }
}
```

## Node Group Configuration

Each node group supports:
- **instance_types**: List of EC2 instance types (e.g., `["t3.medium", "t3a.medium"]`)
- **capacity_type**: `ON_DEMAND` or `SPOT`
- **disk_size**: Root volume size in GB
- **desired_size**: Initial number of nodes
- **min_size** / **max_size**: Auto-scaling bounds
- **labels**: Kubernetes node labels
- **taints**: Kubernetes taints for workload isolation

## Outputs

- `cluster_endpoint` → Kubernetes API endpoint
- `cluster_certificate_authority_data` → CA cert for kubectl config
- `oidc_provider_arn` → For creating IRSA IAM roles
- `aws_load_balancer_controller_role_arn` → Annotate ServiceAccount with this

## Post-Deployment

### 1. Configure kubectl
```bash
aws eks update-kubeconfig --region eu-central-1 --name boltchats-dev
kubectl get nodes
```

### 2. Install AWS Load Balancer Controller
```bash
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=boltchats-dev \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=<role_arn>
```

### 3. Deploy StorageClass for EBS
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  fsType: ext4
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```
