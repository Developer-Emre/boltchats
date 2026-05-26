# Global Terraform Backend Setup

⚠️ **Run this ONCE before creating environments**

## Prerequisites
```bash
aws configure  # Set AWS credentials
```

## Bootstrap Backend

```bash
cd terraform/global

# Initialize (no backend yet — state stored locally)
terraform init

# Plan
terraform plan -out=backend.tfplan

# Apply
terraform apply backend.tfplan
```

This creates:
- S3 bucket: `boltchats-terraform-state` (versioned, encrypted)
- DynamoDB table: `boltchats-terraform-locks` (for state locking)
- IAM policy: `TerraformBackendAccess`

## After Bootstrap

Copy the output values to each environment's `backend.tf`:
```hcl
terraform {
  backend "s3" {
    bucket         = "boltchats-terraform-state"
    key            = "dev/terraform.tfstate"  # Change per env
    region         = "eu-central-1"
    dynamodb_table = "boltchats-terraform-locks"
    encrypt        = true
  }
}
```

## Cleanup (Danger!)

⚠️ **This destroys all Terraform state — only run if you're sure**

```bash
# First destroy all environments
cd ../environments/dev && terraform destroy
cd ../staging && terraform destroy
cd ../prod && terraform destroy

# Then destroy backend (requires manual S3 bucket deletion)
cd ../../global
terraform destroy

# Manually empty and delete S3 bucket if needed
aws s3 rm s3://boltchats-terraform-state --recursive
aws s3 rb s3://boltchats-terraform-state
```
