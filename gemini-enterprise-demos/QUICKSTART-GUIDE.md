# Gemini Enterprise Demos - Quick Start Guide

**Fast-track guide to get either demo running in under 5 minutes (setup) + automated deployment time**

---

## Choose Your Demo

| Demo | Use Case | Setup Time | Best For |
|------|----------|------------|----------|
| **#3: Email & Calendar Assistant** | Productivity automation with Gmail & Calendar | 2-3 hours | Quick wins, productivity demos |
| **#4: Customer Data Platform** | Multi-database analytics with BigQuery, AlloyDB | 3-4 hours | Technical depth, enterprise scale |

---

## Prerequisites (5 minutes)

### Required Tools
```bash
# Check if installed
gcloud --version
python3 --version  # Need 3.10+
node --version     # Need 16+ (for Demo #4)
terraform --version  # Optional, for IaC approach
```

### Install Missing Tools
```bash
# gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Python 3.10+
# macOS: brew install python@3.10
# Linux: sudo apt install python3.10

# Node.js (Demo #4 only)
# macOS: brew install node
# Linux: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install -y nodejs
```

### Google Cloud Setup
```bash
# Authenticate
gcloud auth login
gcloud auth application-default login

# Create project (or use existing)
export PROJECT_ID="gemini-demo-$(date +%s)"
gcloud projects create $PROJECT_ID --name="Gemini Enterprise Demo"

# Set project
gcloud config set project $PROJECT_ID

# Enable billing (REQUIRED - no free tier for these demos)
# Go to: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID
```

---

## Demo #3: Email & Calendar Assistant

### 🚀 Fastest Start (Bash Script)

```bash
# Clone repository
git clone https://github.com/dbcert-cmyk/dxb.git
cd dxb/gemini-enterprise-demos/demo-3-email-calendar-assistant/setup

# Run automated setup
./quickstart.sh $PROJECT_ID us-central1

# Follow prompts for manual steps:
# 1. Create Gemini Enterprise data stores (15 min)
# 2. Deploy ADK agents to Vertex AI (30 min)

# Total time: 2-3 hours
```

### What Gets Created
- ✅ Firestore database with mock emails, calendar events, user preferences
- ✅ 4 ADK agents: Email Agent, Calendar Agent, Meeting Prep, Follow-up
- ✅ Gemini Enterprise data stores (manual): Gmail, Google Calendar
- ✅ Python environment with all dependencies

### Test the Demo
```bash
# Open Gemini Enterprise
# https://console.cloud.google.com/ai/gemini-enterprise?project=$PROJECT_ID

# Try these queries:
1. "Summarize my unread emails from today"
2. "Find me a time to meet with John for 30 minutes this week"
3. "Prepare me for my 2pm meeting with the product team"
4. "What action items do I have from yesterday's meetings?"
```

### Cost
- **$355/month** for 10 users (estimated)
- Breakdown: Gemini Enterprise ($300) + Vertex AI ($50) + Firestore ($5)

---

## Demo #4: Customer Data Platform

### 🚀 Fastest Start (Bash Script)

```bash
# Clone repository
git clone https://github.com/dbcert-cmyk/dxb.git
cd dxb/gemini-enterprise-demos/demo-4-customer-data-platform/setup

# Run automated setup
./quickstart.sh $PROJECT_ID us-central1

# Wait for AlloyDB cluster (20-30 minutes - grab coffee!)
# Script handles everything automatically

# Total time: 3-4 hours
```

### Alternative: Terraform (Infrastructure as Code)

```bash
cd demo-4-customer-data-platform/setup/terraform

# Initialize
terraform init

# Review what will be created
terraform plan -var="project_id=$PROJECT_ID"

# Deploy
terraform apply -var="project_id=$PROJECT_ID"

# Get connection details
terraform output

# Later: Destroy everything
terraform destroy -var="project_id=$PROJECT_ID"
```

### What Gets Created
- ✅ BigQuery dataset with customer analytics tables
- ✅ AlloyDB PostgreSQL cluster (2 vCPU instance)
- ✅ Firestore database for real-time activity
- ✅ Cloud Storage buckets for customer documents
- ✅ VPC network with private connectivity
- ✅ MCP Server (Node.js) deployed to Cloud Run
- ✅ Mock customer data loaded

### Test the Demo
```bash
# Get MCP Server URL
gcloud run services describe mcp-server \
  --region=us-central1 \
  --format='value(status.url)'

# Test API
curl https://mcp-server-xxx.run.app/health
curl https://mcp-server-xxx.run.app/api/customer/C001

# Open Gemini Enterprise
# https://console.cloud.google.com/ai/gemini-enterprise?project=$PROJECT_ID

# Try these queries:
1. "Give me a 360-degree view of customer C001"
2. "What customers are at risk of churning?"
3. "Show me high-value customers with recent support tickets"
4. "Analyze customer lifetime value trends"
```

### Cost
- **$641/month** (estimated)
- Breakdown: Gemini Enterprise ($300) + AlloyDB ($290) + BigQuery ($25) + Other ($26)

### Cost Optimization
```bash
# Use smaller AlloyDB instance
terraform apply -var="project_id=$PROJECT_ID" -var="alloydb_cpu_count=2"

# Destroy when not in use
./cleanup.sh $PROJECT_ID
```

---

## Docker Deployment (Demo #4 Local Development)

```bash
cd demo-4-customer-data-platform/setup/mcp-server

# Create .env file
cat > .env <<EOF
PROJECT_ID=$PROJECT_ID
ALLOYDB_HOST=10.x.x.x  # Get from terraform output
ALLOYDB_PASSWORD=<password>  # Saved in .credentials
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
EOF

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Test
curl http://localhost:3100/health

# Stop
docker-compose down
```

---

## CI/CD Deployment (Production)

### GitHub Actions

```bash
# 1. Add GitHub Secrets
# Go to: Settings → Secrets → Actions
# Add:
#   - GCP_PROJECT_ID: your-project-id
#   - GCP_SA_KEY: <service-account-key-json>

# 2. Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/editor"

# 3. Push to main branch
git push origin main

# 4. Monitor deployment
# GitHub → Actions → Deploy Demo #4
```

### Cloud Build

```bash
# 1. Create trigger
gcloud builds triggers create github \
  --repo-name=dxb \
  --repo-owner=dbcert-cmyk \
  --branch-pattern=^main$ \
  --build-config=gemini-enterprise-demos/demo-4-customer-data-platform/setup/cloudbuild.yaml

# 2. Grant permissions
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/editor"

# 3. Trigger build
git push origin main

# Or manual trigger:
gcloud builds submit \
  --config=gemini-enterprise-demos/demo-4-customer-data-platform/setup/cloudbuild.yaml \
  --substitutions=_PROJECT_ID=$PROJECT_ID
```

---

## Manual Steps (Required for Both Demos)

### Create Gemini Enterprise Data Stores

**Why manual?** Google Cloud Console UI required - no API available yet.

**Time:** 15-20 minutes per data store

**Steps:**

1. **Go to Gemini Enterprise Console**
   ```
   https://console.cloud.google.com/ai/gemini-enterprise?project=$PROJECT_ID
   ```

2. **Create Data Store**
   - Click "Data Stores" → "Create Data Store"
   - Select connector type:
     - Demo #3: Gmail, Google Calendar
     - Demo #4: BigQuery, Cloud Storage, Firestore

3. **Configure Sync**
   - Demo #3:
     - Gmail: Sync last 30 days, all folders
     - Calendar: Sync last 90 days, all calendars
   - Demo #4:
     - BigQuery: Dataset `customer_analytics`, all tables
     - Cloud Storage: Buckets created by script
     - Firestore: Database `customer-activity`

4. **Wait for Initial Sync**
   - Small datasets: 10-15 minutes
   - Large datasets: 1-2 hours

5. **Create Agent (Optional)**
   - Go to "Agent Designer"
   - Create new agent
   - Connect data stores
   - Configure tools (ADK agents deployed earlier)

**Detailed Instructions:** See `setup/01-PREREQUISITES.md` in each demo folder

---

## Troubleshooting

### Common Issues

**Issue:** "APIs not enabled"
```bash
# Manually enable all required APIs
gcloud services enable aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  firestore.googleapis.com \
  # ... (see quickstart.sh for full list)
```

**Issue:** "AlloyDB cluster creation timeout"
```bash
# Check status
gcloud alloydb clusters describe customer-db-cluster --region=us-central1

# If stuck, cleanup and retry
./cleanup.sh $PROJECT_ID --yes
./quickstart.sh $PROJECT_ID
```

**Issue:** "Permission denied"
```bash
# Grant yourself necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/owner"
```

**Issue:** "Terraform state locked"
```bash
# Force unlock (use carefully)
terraform force-unlock LOCK_ID
```

**Issue:** "Docker can't connect to AlloyDB"
```bash
# Use Cloud SQL Proxy for local development
docker run -d \
  -v /cloudsql:/cloudsql \
  gcr.io/cloudsql-docker/gce-proxy:latest \
  /cloud_sql_proxy \
  -instances=$PROJECT_ID:us-central1:customer-db-instance=tcp:0.0.0.0:5432
```

### Get Help

- **Documentation:** See `README.md` and `DEPLOYMENT-AUTOMATION.md`
- **Setup Issues:** Check `setup/01-PREREQUISITES.md` in each demo
- **Cost Questions:** See `COMPREHENSIVE-VALUE-PRESENTATION.md`
- **API Errors:** Check [Gemini Enterprise Docs](https://cloud.google.com/gemini/enterprise/docs)

---

## Post-Deployment Checklist

### Demo #3
- [ ] Firestore database created
- [ ] Mock data loaded (emails, calendar events)
- [ ] 4 ADK agents deployed to Vertex AI
- [ ] Gemini Enterprise data stores synced (Gmail, Calendar)
- [ ] Test queries work in Gemini Enterprise UI

### Demo #4
- [ ] BigQuery dataset created with mock data
- [ ] AlloyDB cluster running (check: `gcloud alloydb clusters list`)
- [ ] Firestore database created
- [ ] Cloud Storage buckets created
- [ ] MCP Server deployed to Cloud Run
- [ ] Health check passes: `curl MCP_SERVER_URL/health`
- [ ] Gemini Enterprise data stores synced
- [ ] Test queries return data

---

## Demo Scripts

### Demo #3: 20-Minute Walkthrough

**See:** `demo-3-email-calendar-assistant/scripts/DEMO-SCRIPT.md`

**Highlights:**
1. Email Triage (5 min) - "Summarize my unread emails and prioritize"
2. Smart Scheduling (5 min) - "Find time for team standup, 30 min, this week"
3. Meeting Prep (5 min) - "Prepare me for my 2pm product review"
4. Follow-up Automation (3 min) - "What are my action items from yesterday?"
5. Q&A (2 min)

### Demo #4: 25-Minute Walkthrough

**See:** `demo-4-customer-data-platform/scripts/DEMO-SCRIPT.md`

**Highlights:**
1. Customer 360 View (5 min) - "Show me everything about customer C001"
2. Churn Prediction (5 min) - "Which customers are at risk?"
3. Cross-Database Analytics (5 min) - "High LTV customers with support issues"
4. Real-time Insights (5 min) - "Recent customer activity and trends"
5. Q&A (5 min)

---

## Business Value

### Combined ROI: 82.3x

**Demo #3 ROI: 69.5x**
- Time saved: 12.5 hours/week per employee
- Annual value per employee: $31,200
- Cost per employee: $450/year
- Break-even: 2.3 weeks

**Demo #4 ROI: 153x**
- Revenue impact: $430K annually
- Cost savings: $198K annually
- Total value: $628K annually
- Investment: $4,100 annually
- Break-even: 3.2 weeks

**See:** `COMPREHENSIVE-VALUE-PRESENTATION.md` for full business case

---

## Next Steps After Setup

1. **Customize Mock Data**
   - Demo #3: Update `mock-data/gmail_mock_data.json` with realistic scenarios
   - Demo #4: Update `mock-data/bigquery_customers.json` with your customer profiles

2. **Extend with More Data Sources**
   - Demo #3: Add Google Drive, Google Sites
   - Demo #4: Add Cloud SQL, Spanner

3. **Deploy Additional ADK Agents**
   - See `setup/adk-agents/` for more examples
   - Create custom agents for your use cases

4. **Configure Production Security**
   - Enable VPC Service Controls
   - Set up Cloud Armor for MCP Server
   - Rotate AlloyDB passwords
   - Enable audit logging

5. **Schedule Regular Demos**
   - Use demo scripts to maintain consistency
   - Gather feedback for improvements
   - Track engagement metrics

---

## Cleanup (Important!)

### Demo #3 Cleanup
```bash
cd demo-3-email-calendar-assistant/setup

# Delete Firestore collections (manual - Firebase Console)
# Delete Gemini Enterprise data stores (manual - Cloud Console)

# Disable APIs to stop charges
gcloud services disable aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  firestore.googleapis.com
```

### Demo #4 Cleanup
```bash
cd demo-4-customer-data-platform/setup

# Using cleanup script (DESTRUCTIVE!)
./cleanup.sh $PROJECT_ID

# Or using Terraform
cd terraform
terraform destroy -var="project_id=$PROJECT_ID"

# Verify all resources deleted
gcloud alloydb clusters list
gcloud run services list
bq ls
gsutil ls
```

### Cost Alert Setup
```bash
# Set up billing alerts
gcloud beta billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Gemini Demo Budget" \
  --budget-amount=500 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

---

## Resource Links

**Documentation:**
- [Gemini Enterprise Docs](https://cloud.google.com/gemini/enterprise/docs)
- [Google ADK GitHub](https://github.com/google/adk)
- [MCP Protocol Spec](https://spec.modelcontextprotocol.io/)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/docs/agent-engine)

**Repositories:**
- Main Repo: `https://github.com/dbcert-cmyk/dxb`
- Demo #3: `gemini-enterprise-demos/demo-3-email-calendar-assistant/`
- Demo #4: `gemini-enterprise-demos/demo-4-customer-data-platform/`

**Support:**
- GitHub Issues: `https://github.com/dbcert-cmyk/dxb/issues`
- Google Cloud Support: `https://cloud.google.com/support`

---

## Quick Reference Commands

```bash
# Clone repo
git clone https://github.com/dbcert-cmyk/dxb.git
cd dxb/gemini-enterprise-demos

# Demo #3 - Quick Start
cd demo-3-email-calendar-assistant/setup
./quickstart.sh $PROJECT_ID us-central1

# Demo #4 - Quick Start
cd demo-4-customer-data-platform/setup
./quickstart.sh $PROJECT_ID us-central1

# Demo #4 - Terraform
cd demo-4-customer-data-platform/setup/terraform
terraform init
terraform apply -var="project_id=$PROJECT_ID"

# Demo #4 - Docker
cd demo-4-customer-data-platform/setup/mcp-server
docker-compose up -d

# Check deployment status
gcloud alloydb clusters list
gcloud run services list
bq ls
gsutil ls

# Test MCP Server
curl $(gcloud run services describe mcp-server --region=us-central1 --format='value(status.url)')/health

# View logs
gcloud run logs read mcp-server --region=us-central1

# Cleanup
./cleanup.sh $PROJECT_ID  # Demo #4
terraform destroy -var="project_id=$PROJECT_ID"  # Terraform
```

---

**Last Updated:** November 2024
**Version:** 1.0
**Estimated Total Setup Time:** 2-4 hours per demo
**Recommended Path:** Start with Demo #3 (simpler), then Demo #4 (more complex)

---

**Ready to start?** Pick your demo above and run the quickstart script!
