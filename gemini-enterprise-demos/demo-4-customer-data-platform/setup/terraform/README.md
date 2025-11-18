# Terraform Configuration for Demo #4
## Infrastructure as Code for Customer Data Platform

This Terraform configuration automates the deployment of all infrastructure for Demo #4.

---

## What Gets Created

### Databases
- **BigQuery Dataset**: `customer_analytics` with tables for customers and transactions
- **AlloyDB Cluster**: PostgreSQL-compatible database with 2 vCPU primary instance
- **Firestore Database**: NoSQL database for real-time data

### Storage
- **Cloud Storage Buckets**:
  - `{PROJECT_ID}-customer-docs` - Customer documents
  - `{PROJECT_ID}-support-calls` - Support call recordings

### Networking
- **VPC Network**: Private network for AlloyDB
- **Subnet**: 10.0.0.0/24 CIDR range
- **Private Service Connection**: For AlloyDB access

### Security
- **Service Account**: For MCP server with appropriate permissions
- **Secret Manager**: Stores AlloyDB password securely

---

## Prerequisites

1. **Terraform** 1.5+ installed
2. **gcloud CLI** authenticated and configured
3. **Google Cloud Project** with billing enabled
4. **IAM Permissions**:
   - `roles/owner` or equivalent permissions to create resources

---

## Quick Start

### 1. Initialize Terraform

```bash
cd setup/terraform
terraform init
```

### 2. Review the Plan

```bash
terraform plan -var="project_id=YOUR_PROJECT_ID"
```

### 3. Deploy Infrastructure

```bash
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

**Note:** This will take 20-30 minutes due to AlloyDB cluster creation.

### 4. View Outputs

```bash
terraform output
```

---

## Configuration Options

### Using a terraform.tfvars File

Create `terraform.tfvars`:

```hcl
project_id          = "your-project-id"
region              = "us-central1"
environment         = "dev"
alloydb_cpu_count   = 2
```

Then deploy:

```bash
terraform apply
```

### Command Line Variables

```bash
terraform apply \
  -var="project_id=my-project" \
  -var="region=us-west1" \
  -var="alloydb_cpu_count=4"
```

---

## Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `project_id` | Google Cloud Project ID | - | Yes |
| `region` | GCP region for resources | `us-central1` | No |
| `environment` | Environment (dev/staging/prod) | `dev` | No |
| `alloydb_cpu_count` | AlloyDB vCPU count (2-64) | `2` | No |
| `enable_deletion_protection` | Protect AlloyDB from deletion | `false` | No |
| `bigquery_location` | BigQuery dataset location | `US` | No |

---

## Outputs Reference

### Key Outputs

```bash
# Get AlloyDB IP
terraform output alloydb_ip_address

# Get AlloyDB password from Secret Manager
gcloud secrets versions access latest \
  --secret=$(terraform output -raw alloydb_password_secret)

# Get BigQuery dataset
terraform output bigquery_dataset_full

# Get full setup summary
terraform output setup_summary
```

### Example Output

```json
{
  "alloydb_ip_address": "10.0.0.3",
  "bigquery_dataset": "customer_analytics",
  "customer_docs_bucket": "my-project-customer-docs",
  "mcp_server_service_account": "mcp-server@my-project.iam.gserviceaccount.com"
}
```

---

## Cost Estimation

Run Terraform with cost estimation tools:

```bash
# Using Infracost (https://www.infracost.io/)
infracost breakdown --path .

# Example monthly cost breakdown:
# - AlloyDB (2 vCPU):     ~$290
# - BigQuery (10GB):       ~$5
# - Cloud Storage (50GB):  ~$1
# - VPC (standard):        Free
# - Firestore (1M ops):    ~$15
# Total:                   ~$311/month
```

---

## State Management

### Local State (Default)

Terraform state is stored locally in `terraform.tfstate`.

**⚠️ Warning:** Do not commit state files to version control!

### Remote State (Recommended for Teams)

Configure GCS backend:

```hcl
# backend.tf
terraform {
  backend "gcs" {
    bucket = "my-terraform-state-bucket"
    prefix = "demo-4/terraform/state"
  }
}
```

Initialize:

```bash
terraform init -backend-config="bucket=YOUR_BUCKET"
```

---

## Common Operations

### View Current State

```bash
terraform show
```

### Refresh State

```bash
terraform refresh -var="project_id=YOUR_PROJECT"
```

### Target Specific Resources

```bash
# Only create BigQuery resources
terraform apply -target=google_bigquery_dataset.customer_analytics

# Only create AlloyDB
terraform apply -target=google_alloydb_cluster.customer_db
```

### Import Existing Resources

```bash
terraform import google_bigquery_dataset.customer_analytics \
  projects/PROJECT_ID/datasets/customer_analytics
```

---

## Destroy Infrastructure

### Destroy Everything

```bash
terraform destroy -var="project_id=YOUR_PROJECT"
```

**⚠️ Warning:** This will delete ALL resources including data!

### Destroy Specific Resources

```bash
# Destroy only AlloyDB
terraform destroy -target=google_alloydb_instance.customer_db_primary
terraform destroy -target=google_alloydb_cluster.customer_db
```

---

## Troubleshooting

### AlloyDB Timeout

**Issue:** AlloyDB cluster creation times out

**Solution:**
```bash
# Increase timeout
terraform apply -var="project_id=YOUR_PROJECT" \
  -timeout=60m
```

### API Not Enabled

**Issue:** `Error 403: ... API has not been used`

**Solution:**
```bash
# Enable APIs manually first
gcloud services enable alloydb.googleapis.com
terraform apply
```

### Quota Exceeded

**Issue:** `Quota 'CPUS_ALL_REGIONS' exceeded`

**Solution:**
```bash
# Request quota increase or reduce CPU count
terraform apply -var="alloydb_cpu_count=2"
```

### VPC Peering Already Exists

**Issue:** `Private service connection already exists`

**Solution:**
```bash
# Import existing connection
terraform import google_service_networking_connection.private_vpc_connection \
  YOUR_PROJECT:servicenetworking.googleapis.com
```

---

## Advanced Configuration

### Different CPU Sizes per Environment

```hcl
# terraform.tfvars
alloydb_cpu_count = {
  dev     = 2
  staging = 4
  prod    = 8
}
```

### Multiple Regions

```hcl
# Deploy to multiple regions
module "us_central" {
  source     = "./modules/cdp"
  region     = "us-central1"
  project_id = var.project_id
}

module "us_west" {
  source     = "./modules/cdp"
  region     = "us-west1"
  project_id = var.project_id
}
```

### Custom Firestore Indexes

Add to `main.tf`:

```hcl
resource "google_firestore_index" "customer_sessions" {
  collection = "customer_sessions"

  fields {
    field_path = "customer_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "timestamp"
    order      = "DESCENDING"
  }
}
```

---

## Terraform Modules (Optional)

Organize into modules:

```
terraform/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── bigquery/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── alloydb/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── storage/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
```

---

## CI/CD Integration

### GitHub Actions

```.yaml
name: Terraform Deploy

on:
  push:
    branches: [main]
    paths: ['terraform/**']

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: terraform plan -var="project_id=${{ secrets.GCP_PROJECT_ID }}"

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        run: terraform apply -auto-approve \
          -var="project_id=${{ secrets.GCP_PROJECT_ID }}"
```

---

## Security Best Practices

1. **State File Security**
   - Use remote backend with encryption
   - Enable versioning
   - Restrict access with IAM

2. **Secrets Management**
   - Never commit secrets
   - Use Secret Manager for sensitive data
   - Rotate passwords regularly

3. **IAM Least Privilege**
   - Service accounts have minimum required permissions
   - Review IAM bindings regularly

4. **Network Security**
   - AlloyDB in private VPC
   - No public IPs exposed
   - VPC Service Controls (optional)

---

## Next Steps After Deployment

1. **Retrieve AlloyDB Password**:
   ```bash
   gcloud secrets versions access latest \
     --secret=$(terraform output -raw alloydb_password_secret)
   ```

2. **Configure MCP Server**:
   ```bash
   cd ../mcp-server
   terraform output -raw alloydb_connection_string
   ```

3. **Load Mock Data**:
   ```bash
   cd ../../mock-data
   ./load_data.sh $(terraform -chdir=../setup/terraform output -raw project_id)
   ```

4. **Create Gemini Enterprise Data Stores** (manual):
   - Visit Cloud Console
   - Create data stores for BigQuery, Firestore, Cloud Storage

---

## Support

For issues:
- Review [main setup guide](../01-PREREQUISITES.md)
- Check [Terraform documentation](https://www.terraform.io/docs)
- Open issue in demo repository

---

**Last Updated:** November 2025
**Terraform Version:** 1.5+
