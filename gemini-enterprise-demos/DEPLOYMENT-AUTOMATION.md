# Deployment Automation Guide
## Automated Setup for Gemini Enterprise Demos

This guide covers all automated deployment options for both Demo #3 and Demo #4.

---

## 🚀 Quick Start Options

### Option 1: Bash Scripts (Fastest)
Simple shell scripts that automate manual steps.

**Demo #3:**
```bash
cd demo-3-email-calendar-assistant/setup
./quickstart.sh YOUR_PROJECT_ID
```

**Demo #4:**
```bash
cd demo-4-customer-data-platform/setup
./quickstart.sh YOUR_PROJECT_ID
```

### Option 2: Terraform (Infrastructure as Code)
Full infrastructure automation with state management.

**Demo #4:**
```bash
cd demo-4-customer-data-platform/setup/terraform
terraform init
terraform apply -var="project_id=YOUR_PROJECT"
```

### Option 3: Docker (Containerized)
Run MCP server in containers.

**Demo #4:**
```bash
cd demo-4-customer-data-platform/setup/mcp-server
docker-compose up -d
```

### Option 4: CI/CD Pipelines
Automated deployment on git commits.

**GitHub Actions or Cloud Build** - see sections below

---

## 📋 Deployment Methods Comparison

| Method | Setup Time | Complexity | Best For | State Management |
|--------|-----------|------------|----------|------------------|
| **Bash Scripts** | 2-3 hours | Low | Quick demos, learning | Manual |
| **Terraform** | 3-4 hours | Medium | Production, teams | Automated |
| **Docker** | 30 min | Low | Local dev, testing | N/A |
| **CI/CD** | 1 hour setup | High | Production, automation | Automated |

---

## Demo #3: Email & Calendar Assistant

### Quickstart Script

**Location:** `demo-3-email-calendar-assistant/setup/quickstart.sh`

**What it does:**
- ✅ Enables required Google Cloud APIs
- ✅ Creates Firestore database
- ✅ Loads mock data (emails, calendar, preferences)
- ✅ Sets up Python environment
- ⚠️ Prompts for manual data store creation
- ⚠️ Prompts for manual ADK agent deployment

**Usage:**
```bash
./quickstart.sh PROJECT_ID [REGION]

# Example
./quickstart.sh my-gemini-demo us-central1
```

**Time:** ~2-3 hours (including data sync)

**Prerequisites:**
- `gcloud` CLI installed and authenticated
- Python 3.10+
- pip3

**Outputs:**
- `.env` file with project configuration
- Populated Firestore collections
- Setup verification report

---

## Demo #4: Customer Data Platform

### 1. Quickstart Script

**Location:** `demo-4-customer-data-platform/setup/quickstart.sh`

**What it does:**
- ✅ Enables all required APIs (11 services)
- ✅ Creates BigQuery dataset and tables
- ✅ Creates AlloyDB cluster and instance (20-30 min)
- ✅ Creates Firestore database
- ✅ Creates Cloud Storage buckets
- ✅ Sets up VPC network for AlloyDB
- ✅ Configures MCP server
- ✅ Loads mock data to BigQuery
- ⚠️ Prompts for Gemini Enterprise data stores (manual)

**Usage:**
```bash
./quickstart.sh PROJECT_ID [REGION]

# Example
./quickstart.sh my-gemini-cdp-demo us-west1
```

**Time:** ~3-4 hours (AlloyDB cluster creation is slow)

**Cost Warning:** This creates billable resources (~$600/month)

**Credentials Saved:**
- `.credentials` file with AlloyDB password
- `mcp-server/.env` with connection details

### 2. Terraform Configuration

**Location:** `demo-4-customer-data-platform/setup/terraform/`

**Advantages over Bash:**
- ✅ Infrastructure as Code (version controlled)
- ✅ Idempotent (can run multiple times safely)
- ✅ State management
- ✅ Easy to destroy all resources
- ✅ Better for teams

**Usage:**
```bash
cd demo-4-customer-data-platform/setup/terraform

# Initialize
terraform init

# Review plan
terraform plan -var="project_id=YOUR_PROJECT"

# Apply
terraform apply -var="project_id=YOUR_PROJECT"

# View outputs
terraform output

# Destroy (when done)
terraform destroy -var="project_id=YOUR_PROJECT"
```

**Configuration Options:**

Create `terraform.tfvars`:
```hcl
project_id          = "my-project"
region              = "us-central1"
environment         = "dev"
alloydb_cpu_count   = 2
```

**Variables:**
- `project_id` (required) - GCP project ID
- `region` (optional) - Region for resources (default: us-central1)
- `environment` (optional) - dev/staging/prod (default: dev)
- `alloydb_cpu_count` (optional) - 2-64 vCPUs (default: 2)

**Outputs:**
- AlloyDB IP address and connection string
- BigQuery dataset path
- Storage bucket names
- Service account email
- Complete setup summary

See [Terraform README](demo-4-customer-data-platform/setup/terraform/README.md) for details.

### 3. Docker Deployment

**Location:** `demo-4-customer-data-platform/setup/mcp-server/`

**For:** Local development and testing

**Files:**
- `Dockerfile` - Multi-stage build for production
- `docker-compose.yml` - Local orchestration
- `.dockerignore` - Excludes unnecessary files

**Usage:**
```bash
cd demo-4-customer-data-platform/setup/mcp-server

# Build image
docker build -t mcp-server .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Environment Variables Required:**
```bash
# .env file
PROJECT_ID=your-project
ALLOYDB_HOST=10.x.x.x
ALLOYDB_PASSWORD=your-password
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

**Production Deployment to Cloud Run:**
```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/mcp-server

# Deploy to Cloud Run
gcloud run deploy mcp-server \
  --image gcr.io/PROJECT_ID/mcp-server \
  --region us-central1 \
  --set-env-vars PROJECT_ID=PROJECT_ID,ALLOYDB_HOST=IP \
  --set-secrets ALLOYDB_PASSWORD=alloydb-password:latest
```

---

## CI/CD Pipelines

### GitHub Actions

**Location:** `.github/workflows/demo4-deploy.yml`

**Triggers:**
- Push to `main` branch (paths: `demo-4-customer-data-platform/**`)
- Pull requests to `main`
- Manual workflow dispatch

**Jobs:**
1. **terraform-plan** - Plans infrastructure changes
2. **terraform-apply** - Applies changes (main branch only)
3. **build-mcp-server** - Builds Docker image
4. **deploy-mcp-server** - Deploys to Cloud Run
5. **load-mock-data** - Loads BigQuery data
6. **notify** - Reports deployment status

**Setup:**

1. Add GitHub Secrets:
   - `GCP_PROJECT_ID` - Your Google Cloud project ID
   - `GCP_SA_KEY` - Service account key JSON

2. Grant permissions to service account:
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:github-actions@PROJECT.iam.gserviceaccount.com" \
     --role="roles/editor"
   ```

3. Push to main branch to trigger deployment

**Manual Trigger:**
```bash
# Via GitHub UI: Actions → Deploy Demo #4 → Run workflow
# Select environment: dev/staging/prod
```

**Monitoring:**
- View progress in GitHub Actions tab
- Artifacts saved: Terraform plan, outputs
- Automatic rollback on failure

### Cloud Build

**Location:** `demo-4-customer-data-platform/setup/cloudbuild.yaml`

**Advantages:**
- ✅ Native to Google Cloud
- ✅ No GitHub Actions minutes used
- ✅ Direct access to GCP resources
- ✅ Build artifacts stored in GCS

**Setup:**

1. Create Cloud Build trigger:
   ```bash
   gcloud builds triggers create github \
     --repo-name=YOUR_REPO \
     --repo-owner=YOUR_ORG \
     --branch-pattern=^main$ \
     --build-config=gemini-enterprise-demos/demo-4-customer-data-platform/setup/cloudbuild.yaml
   ```

2. Grant permissions to Cloud Build:
   ```bash
   PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format="value(projectNumber)")

   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
     --role="roles/editor"
   ```

3. Push to main branch

**Substitution Variables:**
```yaml
_PROJECT_ID: ${PROJECT_ID}
_REGION: us-central1
_ENVIRONMENT: dev
_ALLOYDB_CPU: 2
```

**Manual Trigger:**
```bash
gcloud builds submit \
  --config=gemini-enterprise-demos/demo-4-customer-data-platform/setup/cloudbuild.yaml \
  --substitutions=_PROJECT_ID=PROJECT,_ENVIRONMENT=prod
```

**Build Steps:**
1. Terraform init/plan/apply
2. Build Docker image
3. Push to GCR
4. Deploy to Cloud Run
5. Load mock data
6. Test deployment
7. Generate summary

**Artifacts:** Saved to `gs://PROJECT-build-artifacts/demo-4/BUILD_ID/`

---

## Cleanup Scripts

### Demo #4 Cleanup

**Location:** `demo-4-customer-data-platform/setup/cleanup.sh`

**Removes:**
- AlloyDB cluster and instance
- BigQuery dataset
- Cloud Storage buckets
- VPC network and subnets
- Local configuration files

**Usage:**
```bash
# Interactive mode (prompts for confirmation)
./cleanup.sh PROJECT_ID

# Auto-confirm mode (dangerous!)
./cleanup.sh PROJECT_ID --yes
```

**⚠️ Warning:** This is destructive and cannot be undone!

**Manual cleanup still required:**
- Firestore database (via Firebase Console)
- Gemini Enterprise data stores (via Cloud Console)

---

## Cost Management

### Estimated Monthly Costs

**Demo #3:**
- Gemini Enterprise (10 users): $300
- Vertex AI agents: $50
- Firestore: $5
- **Total:** ~$355/month

**Demo #4:**
- Gemini Enterprise (10 users): $300
- AlloyDB (2 vCPU): $290
- BigQuery: $25
- Firestore: $15
- Cloud Storage: $1
- Cloud Run: $10
- **Total:** ~$641/month

### Cost Optimization Tips

1. **Use smaller AlloyDB instances for demos:**
   ```hcl
   # terraform.tfvars
   alloydb_cpu_count = 2  # Minimum
   ```

2. **Delete resources when not in use:**
   ```bash
   ./cleanup.sh PROJECT_ID --yes
   ```

3. **Use dev environment with shorter data retention:**
   ```hcl
   environment = "dev"  # Enables force_destroy on buckets
   ```

4. **Set up billing alerts:**
   ```bash
   gcloud beta billing budgets create \
     --billing-account=BILLING_ACCOUNT_ID \
     --display-name="Demo Budget" \
     --budget-amount=500 \
     --threshold-rule=percent=50 \
     --threshold-rule=percent=90
   ```

---

## Troubleshooting

### Quickstart Script Issues

**Issue:** "APIs not enabled"
```bash
# Manually enable all APIs
gcloud services enable aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  # ... (see quickstart.sh for full list)
```

**Issue:** "AlloyDB cluster creation timeout"
```bash
# AlloyDB can take 20-30 minutes
# Check status:
gcloud alloydb clusters describe customer-db-cluster --region=REGION

# If stuck, cancel and retry:
./cleanup.sh PROJECT_ID --yes
./quickstart.sh PROJECT_ID
```

### Terraform Issues

**Issue:** "State file locked"
```bash
# Force unlock (use carefully)
terraform force-unlock LOCK_ID
```

**Issue:** "Resource already exists"
```bash
# Import existing resource
terraform import google_bigquery_dataset.customer_analytics \
  projects/PROJECT/datasets/customer_analytics
```

**Issue:** "Quota exceeded"
```bash
# Request quota increase or reduce resources
terraform apply -var="alloydb_cpu_count=2"
```

### Docker Issues

**Issue:** "Cannot connect to AlloyDB"
```bash
# Ensure running in same VPC or use Cloud SQL Proxy
docker run -d \
  -v /cloudsql:/cloudsql \
  gcr.io/cloudsql-docker/gce-proxy:latest \
  /cloud_sql_proxy \
  -instances=PROJECT:REGION:INSTANCE=tcp:0.0.0.0:5432
```

### CI/CD Issues

**Issue:** GitHub Actions failing
```bash
# Check secrets are set correctly
# Check service account has permissions
# View detailed logs in Actions tab
```

**Issue:** Cloud Build permission denied
```bash
# Grant Cloud Build service account permissions
gcloud projects add-iam-policy-binding PROJECT \
  --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/editor"
```

---

## Best Practices

### 1. Version Control
- Commit Terraform state to remote backend (GCS)
- Never commit `.env` files or credentials
- Use `.gitignore` for sensitive files

### 2. Testing
- Test in dev environment first
- Use Terraform plan before apply
- Validate with `terraform validate`

### 3. Security
- Use least privilege IAM roles
- Rotate AlloyDB passwords regularly
- Enable audit logging
- Use Secret Manager for credentials

### 4. Monitoring
- Set up Cloud Monitoring dashboards
- Configure alerting policies
- Enable Cloud Logging
- Review costs weekly

### 5. Documentation
- Document any manual steps
- Update README when changing scripts
- Keep credentials in secure location

---

## Next Steps After Deployment

1. **Create Gemini Enterprise Data Stores** (manual step):
   - Go to Cloud Console
   - Create data stores for each data source
   - Configure sync frequency

2. **Test the Demo**:
   - Follow demo scripts in `scripts/DEMO-SCRIPT.md`
   - Verify all data sources are accessible
   - Test sample queries

3. **Customize for Your Use Case**:
   - Modify mock data with real scenarios
   - Adjust ADK agents for your workflows
   - Configure MCP server for additional databases

---

## Support

For issues:
- Review setup guides in each demo's `setup/` directory
- Check troubleshooting sections above
- Open issue in GitHub repository
- Consult [Gemini Enterprise Docs](https://cloud.google.com/gemini/enterprise/docs)

---

**Last Updated:** November 2025
**Version:** 1.0
