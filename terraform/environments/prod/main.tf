terraform {
  required_version = ">= 1.6"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "boltchats-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "boltchats-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "prod"
      Project     = "boltchats"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  cluster_name = "boltchats-prod"
  
  common_tags = {
    Environment = "prod"
    Project     = "boltchats"
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"
  
  cluster_name       = local.cluster_name
  vpc_cidr           = var.vpc_cidr
  azs_count          = 2
  aws_region         = var.aws_region
  enable_nat_gateway = true
  enable_ecr_endpoints = false
  
  tags = local.common_tags
}

# EKS Module
module "eks" {
  source = "../../modules/eks"
  
  cluster_name       = local.cluster_name
  kubernetes_version = var.kubernetes_version
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids
  
  cluster_endpoint_public_access = true
  cluster_log_types              = ["api", "audit", "authenticator"]
  
  node_groups = {
    general = {
      instance_types = ["m5.xlarge"]
      capacity_type  = "ON_DEMAND"
      disk_size      = 50
      desired_size   = 5
      min_size       = 3
      max_size       = 10
      labels         = { workload = "general" }
      taints         = []
    }
  }
  
  enable_aws_load_balancer_controller = true
  enable_ebs_csi_driver               = true
  
  tags = local.common_tags
}
