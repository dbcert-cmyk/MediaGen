# Demo #4: Customer Data Platform & Insights Engine
## Prerequisites and Setup Instructions

### Overview
This demo showcases how Gemini Enterprise integrates multiple Google Cloud databases (BigQuery, Firestore, AlloyDB, Cloud Storage) with ADK and MCP servers to create a unified customer intelligence platform with 360-degree customer views and predictive analytics.

---

## 1. Google Cloud Project Setup

### 1.1 Create or Select a Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID="gemini-cdp-demo"
export REGION="us-central1"

# Create a new project (or use existing)
gcloud projects create $PROJECT_ID --name="Gemini CDP Demo"

# Set the project as default
gcloud config set project $PROJECT_ID

# Enable billing (required for AlloyDB, BigQuery)
gcloud beta billing projects link $PROJECT_ID \
  --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### 1.2 Enable Required APIs

```bash
# Enable all required Google Cloud APIs
gcloud services enable \
  aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  bigquery.googleapis.com \
  alloydb.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  gmail.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  cloudbuilds.googleapis.com
```

**Estimated time:** 5-10 minutes

---

## 2. Gemini Enterprise Setup

### 2.1 Enable Gemini Enterprise

1. Navigate to [Google Cloud Console](https://console.cloud.google.com)
2. Go to **Gemini Enterprise** (search in top bar)
3. Click **"Enable Gemini Enterprise"**
4. Accept the terms of service
5. Configure settings:
   - **Organization ID:** Your Google Workspace organization
   - **Region:** us-central1
   - **Data residency:** United States

**Estimated time:** 5 minutes

### 2.2 Configure User Access

```bash
# Grant Gemini Enterprise User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:demo-user@company.com" \
  --role="roles/discoveryengine.user"

# Grant Gemini Enterprise Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:admin@company.com" \
  --role="roles/discoveryengine.admin"
```

---

## 3. Database Setup

### 3.1 Create BigQuery Dataset (Customer Analytics)

```bash
# Create BigQuery dataset
bq mk --dataset \
  --location=$REGION \
  --description="Customer analytics data warehouse" \
  $PROJECT_ID:customer_analytics

# Create tables (schemas defined in mock-data/)
bq mk --table \
  $PROJECT_ID:customer_analytics.customers \
  mock-data/bigquery_schemas/customers_schema.json

bq mk --table \
  $PROJECT_ID:customer_analytics.transactions \
  mock-data/bigquery_schemas/transactions_schema.json

bq mk --table \
  $PROJECT_ID:customer_analytics.customer_interactions \
  mock-data/bigquery_schemas/interactions_schema.json

bq mk --table \
  $PROJECT_ID:customer_analytics.product_catalog \
  mock-data/bigquery_schemas/products_schema.json
```

### 3.2 Create AlloyDB Cluster (Operational Customer Database)

```bash
# Create VPC network for AlloyDB
gcloud compute networks create alloydb-network \
  --subnet-mode=custom

# Create subnet
gcloud compute networks subnets create alloydb-subnet \
  --network=alloydb-network \
  --region=$REGION \
  --range=10.0.0.0/24

# Allocate IP range for private service connection
gcloud compute addresses create alloydb-ip-range \
  --global \
  --purpose=VPC_PEERING \
  --prefix-length=16 \
  --network=alloydb-network

# Create private connection
gcloud services vpc-peerings connect \
  --service=servicenetworking.googleapis.com \
  --ranges=alloydb-ip-range \
  --network=alloydb-network

# Create AlloyDB cluster
gcloud alloydb clusters create customer-db-cluster \
  --password=CHANGE_ME_STRONG_PASSWORD \
  --network=alloydb-network \
  --region=$REGION \
  --project=$PROJECT_ID

# Create primary instance
gcloud alloydb instances create customer-db-primary \
  --instance-type=PRIMARY \
  --cpu-count=2 \
  --region=$REGION \
  --cluster=customer-db-cluster \
  --project=$PROJECT_ID
```

**Estimated time:** 15-20 minutes (AlloyDB cluster creation)

### 3.3 Load AlloyDB Schema

```bash
# Get AlloyDB connection string
export ALLOYDB_IP=$(gcloud alloydb instances describe customer-db-primary \
  --cluster=customer-db-cluster \
  --region=$REGION \
  --format="value(ipAddress)")

# Connect and create schema (from cloud shell or compute instance)
psql "host=$ALLOYDB_IP user=postgres dbname=postgres" \
  -f setup/alloydb_schemas/customer_profile_schema.sql
```

### 3.4 Create Firestore Database (Real-time Customer Data)

```bash
# Create Firestore database
gcloud firestore databases create \
  --location=$REGION \
  --type=firestore-native

# Create indexes for efficient queries
gcloud firestore indexes composite create \
  --collection-group=customer_sessions \
  --query-scope=COLLECTION \
  --field-config field-path=user_id,order=ASCENDING \
  --field-config field-path=timestamp,order=DESCENDING
```

### 3.5 Create Cloud Storage Buckets (Documents & Media)

```bash
# Create bucket for customer support documents
gcloud storage buckets create gs://$PROJECT_ID-customer-docs \
  --location=$REGION \
  --uniform-bucket-level-access

# Create bucket for call recordings
gcloud storage buckets create gs://$PROJECT_ID-support-calls \
  --location=$REGION \
  --uniform-bucket-level-access

# Set lifecycle policy (delete after 90 days)
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [{
      "action": {"type": "Delete"},
      "condition": {"age": 90}
    }]
  }
}
EOF

gcloud storage buckets update gs://$PROJECT_ID-customer-docs \
  --lifecycle-file=lifecycle.json
```

---

## 4. Gemini Enterprise Data Store Configuration

### 4.1 Create BigQuery Data Store

1. In Google Cloud Console → **Gemini Enterprise** → **Data Stores**
2. Click **"Create Data Store"**
3. Select **"BigQuery"** as the data source
4. Configure:
   - **Name:** `customer-analytics-datastore`
   - **Dataset:** `customer_analytics`
   - **Tables to sync:**
     - ✅ customers
     - ✅ transactions
     - ✅ customer_interactions
     - ✅ product_catalog
   - **Sync frequency:** Daily
   - **Reconciliation mode:** INCREMENTAL
5. Click **"Create"**

**First sync time:** ~30-60 minutes for initial ingestion

### 4.2 Create Firestore Data Store

1. Click **"Create Data Store"**
2. Select **"Firestore"** as the data source
3. Configure:
   - **Name:** `customer-realtime-datastore`
   - **Database:** (default)
   - **Collections to sync:**
     - ✅ customer_sessions
     - ✅ support_tickets
     - ✅ customer_preferences
     - ✅ behavioral_events
   - **Sync frequency:** Daily
4. Click **"Create"**

### 4.3 Create Cloud Storage Data Store

1. Click **"Create Data Store"**
2. Select **"Cloud Storage"** as the data source
3. Configure for customer documents:
   - **Name:** `customer-documents-datastore`
   - **Bucket:** `gs://$PROJECT_ID-customer-docs`
   - **File types:**
     - ✅ PDF
     - ✅ Text files
     - ✅ CSV
   - **Sync frequency:** Daily
   - **Reconciliation mode:** FULL
4. Create another for support calls:
   - **Name:** `support-calls-datastore`
   - **Bucket:** `gs://$PROJECT_ID-support-calls`
   - **File types:**
     - ✅ Audio files (MP3, WAV)
   - **Sync frequency:** Daily

### 4.4 Create Gmail Data Store (Customer Communications)

1. Click **"Create Data Store"**
2. Select **"Gmail"** as the data source
3. Configure:
   - **Name:** `customer-emails-datastore`
   - **Label filter:** "CUSTOMERS" (create this label in Gmail)
   - **Date range:** Last 365 days
   - **Sync frequency:** Daily
4. Click **"Create"**

---

## 5. Google ADK (Agent Development Kit) Setup

### 5.1 Install ADK

```bash
# Create virtual environment
python3 -m venv cdp-adk-env
source cdp-adk-env/bin/activate

# Install ADK and dependencies
pip install google-adk
pip install google-cloud-aiplatform
pip install google-cloud-discoveryengine
pip install google-cloud-bigquery
pip install google-cloud-alloydb-connectors
pip install google-cloud-firestore
pip install google-cloud-storage
```

### 5.2 Configure ADK Authentication

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set environment variables
export ADK_PROJECT_ID=$PROJECT_ID
export ADK_LOCATION=$REGION
export GEMINI_MODEL="gemini-2.5-pro"
```

### 5.3 Deploy ADK Agents

```bash
# Navigate to agents directory
cd setup/adk-agents

# Deploy Customer Intelligence Agent
cd customer_intelligence_agent
adk deploy \
  --agent-name=customer-intelligence-agent \
  --project=$PROJECT_ID \
  --location=$REGION \
  --source=agent.py \
  --model=gemini-2.5-pro

# Deploy Segmentation Agent
cd ../segmentation_agent
adk deploy \
  --agent-name=segmentation-agent \
  --project=$PROJECT_ID \
  --location=$REGION \
  --source=agent.py

# Deploy Recommendation Agent
cd ../recommendation_agent
adk deploy \
  --agent-name=recommendation-agent \
  --project=$PROJECT_ID \
  --location=$REGION \
  --source=agent.py

# Deploy Churn Prediction Agent
cd ../churn_prediction_agent
adk deploy \
  --agent-name=churn-prediction-agent \
  --project=$PROJECT_ID \
  --location=$REGION \
  --source=agent.py
```

**Deployment time:** 5-10 minutes per agent

---

## 6. MCP Server Setup (Multi-Database Connector)

### 6.1 Install MCP Server for Multi-DB Access

```bash
# Clone or create MCP server for multi-database access
mkdir mcp-multi-db-server
cd mcp-multi-db-server

# Initialize Node.js project
npm init -y

# Install dependencies
npm install @modelcontextprotocol/sdk
npm install @google-cloud/bigquery
npm install @google-cloud/firestore
npm install pg  # PostgreSQL client for AlloyDB
npm install @google-cloud/storage
```

### 6.2 Configure MCP Server

Create `server.js` (see setup/mcp-server/server.js)

```bash
# Start MCP server
node server.js

# Server will start on port 3100
```

### 6.3 Test MCP Server Connection

```bash
# Test BigQuery connection
curl http://localhost:3100/query \
  -H "Content-Type: application/json" \
  -d '{"database": "bigquery", "query": "SELECT COUNT(*) FROM customer_analytics.customers"}'

# Test Firestore connection
curl http://localhost:3100/query \
  -H "Content-Type: application/json" \
  -d '{"database": "firestore", "collection": "customer_sessions", "limit": 10}'

# Test AlloyDB connection
curl http://localhost:3100/query \
  -H "Content-Type: application/json" \
  -d '{"database": "alloydb", "query": "SELECT * FROM customer_profiles LIMIT 10"}'
```

---

## 7. Connect ADK Agents to Gemini Enterprise

### 7.1 Register Agents in Gemini Enterprise

1. Go to **Gemini Enterprise Console** → **Agents**
2. Click **"Add Agent"** for each deployed agent:

**Customer Intelligence Agent:**
- **Name:** Customer Intelligence Agent
- **Agent ID:** `projects/{PROJECT_ID}/locations/{REGION}/agents/customer-intelligence-agent`
- **Description:** Provides 360-degree customer views and insights

**Segmentation Agent:**
- **Name:** Customer Segmentation Agent
- **Agent ID:** `projects/{PROJECT_ID}/locations/{REGION}/agents/segmentation-agent`
- **Description:** Segments customers for targeted campaigns

**Recommendation Agent:**
- **Name:** Recommendation Agent
- **Agent ID:** `projects/{PROJECT_ID}/locations/{REGION}/agents/recommendation-agent`
- **Description:** Generates personalized product recommendations

**Churn Prediction Agent:**
- **Name:** Churn Prediction Agent
- **Agent ID:** `projects/{PROJECT_ID}/locations/{REGION}/agents/churn-prediction-agent`
- **Description:** Predicts customer churn risk

### 7.2 Create Orchestration Agent (No-Code Agent Designer)

1. Open **Agent Designer** in Gemini Enterprise
2. Click **"Create New Agent"**
3. Name: **"Customer Data Platform Orchestrator"**
4. Configure workflow:

```
User Query → Route to appropriate agent:
  - "customer profile" → Customer Intelligence Agent
  - "segment" OR "group" → Segmentation Agent
  - "recommend" OR "suggest" → Recommendation Agent
  - "churn" OR "at-risk" → Churn Prediction Agent

Data Sources (all selected):
  ✓ customer-analytics-datastore (BigQuery)
  ✓ customer-realtime-datastore (Firestore)
  ✓ customer-documents-datastore (Cloud Storage)
  ✓ support-calls-datastore (Cloud Storage)
  ✓ customer-emails-datastore (Gmail)
```

5. Click **"Publish"**

---

## 8. Load Mock Data

### 8.1 Load BigQuery Data

```bash
# Navigate to mock data directory
cd mock-data/bigquery

# Load customers table
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  $PROJECT_ID:customer_analytics.customers \
  customers.json

# Load transactions table
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  $PROJECT_ID:customer_analytics.transactions \
  transactions.json

# Load interactions table
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  $PROJECT_ID:customer_analytics.customer_interactions \
  interactions.json

# Load products table
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  $PROJECT_ID:customer_analytics.product_catalog \
  products.json
```

### 8.2 Load AlloyDB Data

```bash
# Load customer profiles
psql "host=$ALLOYDB_IP user=postgres dbname=postgres" \
  -f mock-data/alloydb/customer_profiles.sql
```

### 8.3 Load Firestore Data

```bash
# Run Firestore loader script
python mock-data/firestore/load_firestore_data.py $PROJECT_ID
```

### 8.4 Upload Documents to Cloud Storage

```bash
# Upload customer documents
gcloud storage cp mock-data/documents/* \
  gs://$PROJECT_ID-customer-docs/

# Upload support call recordings
gcloud storage cp mock-data/support-calls/* \
  gs://$PROJECT_ID-support-calls/
```

---

## 9. Verify Setup

### 9.1 Check Data Store Sync Status

```bash
# List all data stores
gcloud discovery-engine data-stores list \
  --location=global \
  --project=$PROJECT_ID

# Check BigQuery data store sync
gcloud discovery-engine data-stores describe customer-analytics-datastore \
  --location=global \
  --project=$PROJECT_ID
```

Expected: `state: ACTIVE`, `lastSyncTime: <recent>`

### 9.2 Test End-to-End Query

Open **Gemini Enterprise** UI and test:

```
Show me the customer profile for Acme Corporation
```

Expected response should include data from:
- BigQuery (transaction history, LTV)
- AlloyDB (current profile info)
- Firestore (recent activity)
- Cloud Storage (support documents)
- Gmail (email communications)

---

## 10. Troubleshooting

### Common Issues

**Issue 1: AlloyDB connection timeout**
```bash
# Check if you're connecting from authorized network
gcloud compute instances create alloydb-proxy \
  --zone=us-central1-a \
  --network=alloydb-network

# SSH into instance and connect from there
```

**Issue 2: BigQuery data store not syncing**
```bash
# Trigger manual sync
gcloud discovery-engine data-stores import customer-analytics-datastore \
  --location=global \
  --bigquery-dataset=$PROJECT_ID.customer_analytics
```

**Issue 3: MCP server can't connect to databases**
```bash
# Check service account permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:mcp-server@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

---

## 11. Security Best Practices

1. **Enable VPC Service Controls** for AlloyDB
2. **Set up BigQuery column-level security** for PII data
3. **Enable Cloud Storage bucket-level IAM** with principle of least privilege
4. **Configure Firestore security rules** to restrict access
5. **Enable audit logging** for all data access:

```bash
gcloud logging sinks create customer-data-audit \
  storage.googleapis.com/audit-logs-bucket \
  --log-filter='protoPayload.serviceName=("bigquery.googleapis.com" OR "alloydb.googleapis.com" OR "firestore.googleapis.com")'
```

---

## 12. Cost Estimation

### Monthly Costs (Demo Environment with 10K customers)

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Gemini Enterprise | 10 users × $30 | $300 |
| BigQuery | 100GB storage, 1TB queries | $25 |
| AlloyDB | 2 vCPU primary instance | $290 |
| Firestore | 10GB storage, 1M ops | $15 |
| Cloud Storage | 50GB | $1 |
| Vertex AI (Agents) | 100K requests | $50 |
| **Total** | | **~$681/month** |

**Production (100K customers):**
- BigQuery: $150
- AlloyDB: $580 (4 vCPU)
- Firestore: $75
- Total: **~$1,455/month**

---

## Setup Complete! ✅

Your Demo #4 environment is now ready. Proceed to:
- **Mock Data:** Already loaded via scripts above
- **Demo Scripts:** See `scripts/DEMO-SCRIPT.md`
- **Presentation:** See `presentation/CDP-VALUE-PRESENTATION.md`

**Estimated total setup time:** 3-4 hours (including database provisioning)
