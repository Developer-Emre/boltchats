# VPC Module

Creates a multi-AZ VPC for Kubernetes (EKS) with:
- Public subnets (for load balancers, NAT gateways)
- Private subnets (for EKS worker nodes, databases)
- NAT gateways (one per AZ for HA)
- VPC endpoints (S3, ECR — to reduce NAT costs)

## Usage

```hcl
module "vpc" {
  source = "../../modules/vpc"
  
  cluster_name       = "boltchats-dev"
  vpc_cidr           = "10.0.0.0/16"
  azs_count          = 2
  aws_region         = "eu-central-1"
  enable_nat_gateway = true
  
  tags = {
    Environment = "dev"
    Project     = "boltchats"
  }
}
```

## Subnet Allocation

For `vpc_cidr = "10.0.0.0/16"` and `azs_count = 2`:
- Public subnets: `10.0.0.0/20`, `10.0.16.0/20`
- Private subnets: `10.0.32.0/20`, `10.0.48.0/20`

Each subnet supports ~4000 IPs.

## Outputs

- `vpc_id` → VPC ID
- `public_subnet_ids` → List of public subnet IDs
- `private_subnet_ids` → List of private subnet IDs
- `nat_gateway_ids` → NAT Gateway IDs (one per AZ)

## Cost Optimization

Set `enable_ecr_endpoints = true` to reduce NAT gateway data transfer costs when pulling container images from ECR.
