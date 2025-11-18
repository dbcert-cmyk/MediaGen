#!/bin/bash
#
# Demo #4 Quick Start Script
# Automated setup for Customer Data Platform & Insights Engine
#
# Usage: ./quickstart.sh PROJECT_ID [REGION]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${1}"
REGION="${2:-us-central1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# AlloyDB Configuration
ALLOYDB_PASSWORD="${ALLOYDB_PASSWORD:-$(openssl rand -base64 32)}"
VPC_NAME="alloydb-network"
SUBNET_NAME="alloydb-subnet"
CLUSTER_NAME="customer-db-cluster"
INSTANCE_NAME="customer-db-primary"

# Validation
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: PROJECT_ID is required${NC}"
    echo "Usage: $0 PROJECT_ID [REGION]"
    exit 1
fi

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# Banner
echo "=========================================="
echo "  Gemini Enterprise Demo #4"
echo "  Customer Data Platform Setup"
echo "=========================================="
echo ""
log_info "Project ID: $PROJECT_ID"
log_info "Region: $REGION"
log_warning "This setup will create billable resources!"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Setup cancelled"
    exit 0
fi

# Step 1: Check prerequisites
log_info "Step 1/15: Checking prerequisites..."
check_command gcloud
check_command bq
check_command python3
check_command node
check_command npm
log_success "Prerequisites check passed"

# Step 2: Configure Google Cloud project
log_info "Step 2/15: Configuring Google Cloud project..."
gcloud config set project $PROJECT_ID
log_success "Project configured"

# Step 3: Enable required APIs
log_info "Step 3/15: Enabling required APIs (this may take 3-5 minutes)..."
APIS=(
    "aiplatform.googleapis.com"
    "discoveryengine.googleapis.com"
    "bigquery.googleapis.com"
    "alloydb.googleapis.com"
    "firestore.googleapis.com"
    "storage.googleapis.com"
    "compute.googleapis.com"
    "servicenetworking.googleapis.com"
    "cloudresourcemanager.googleapis.com"
)

for api in "${APIS[@]}"; do
    log_info "  Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID 2>/dev/null || true
done
log_success "APIs enabled"

# Step 4: Create BigQuery dataset
log_info "Step 4/15: Creating BigQuery dataset..."
if bq ls -d --project_id=$PROJECT_ID | grep -q "customer_analytics"; then
    log_warning "BigQuery dataset already exists"
else
    bq mk --dataset \
        --location=$REGION \
        --description="Customer analytics data warehouse" \
        $PROJECT_ID:customer_analytics
    log_success "BigQuery dataset created"
fi

# Step 5: Create BigQuery tables
log_info "Step 5/15: Creating BigQuery tables..."
TABLES=("customers" "transactions" "customer_interactions" "product_catalog")
for table in "${TABLES[@]}"; do
    if bq ls --project_id=$PROJECT_ID customer_analytics | grep -q "$table"; then
        log_warning "  Table $table already exists"
    else
        log_info "  Creating table: $table"
        # Simple schema - in production use schema files
        case $table in
            "customers")
                bq mk --table \
                    $PROJECT_ID:customer_analytics.$table \
                    customer_id:STRING,company_name:STRING,industry:STRING,employee_count:INTEGER,annual_revenue_usd:FLOAT,account_tier:STRING,customer_since:DATE,lifetime_value_usd:FLOAT,total_transactions:INTEGER,last_transaction_date:DATE,churn_risk_score:FLOAT,health_score:INTEGER,primary_contact_email:STRING,geographic_region:STRING
                ;;
            "transactions")
                bq mk --table \
                    $PROJECT_ID:customer_analytics.$table \
                    transaction_id:STRING,customer_id:STRING,transaction_date:TIMESTAMP,amount_usd:FLOAT,product_id:STRING,transaction_type:STRING
                ;;
            *)
                log_info "  Skipping $table - create manually if needed"
                ;;
        esac
    fi
done
log_success "BigQuery tables created"

# Step 6: Load BigQuery mock data
log_info "Step 6/15: Loading BigQuery mock data..."
if [ -f "$SCRIPT_DIR/../../mock-data/bigquery_customers.json" ]; then
    bq load \
        --source_format=NEWLINE_DELIMITED_JSON \
        --project_id=$PROJECT_ID \
        customer_analytics.customers \
        "$SCRIPT_DIR/../../mock-data/bigquery_customers.json"
    log_success "Mock data loaded to BigQuery"
else
    log_warning "Mock data file not found, skipping data load"
fi

# Step 7: Create Firestore database
log_info "Step 7/15: Creating Firestore database..."
if gcloud firestore databases list --project=$PROJECT_ID 2>/dev/null | grep -q "(default)"; then
    log_warning "Firestore database already exists"
else
    gcloud firestore databases create \
        --location=$REGION \
        --type=firestore-native \
        --project=$PROJECT_ID
    log_success "Firestore database created"
fi

# Step 8: Create Cloud Storage buckets
log_info "Step 8/15: Creating Cloud Storage buckets..."
BUCKETS=("customer-docs" "support-calls")
for bucket in "${BUCKETS[@]}"; do
    BUCKET_NAME="$PROJECT_ID-$bucket"
    if gsutil ls -p $PROJECT_ID | grep -q "gs://$BUCKET_NAME/"; then
        log_warning "  Bucket $BUCKET_NAME already exists"
    else
        gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME/
        log_success "  Created bucket: $BUCKET_NAME"
    fi
done

# Step 9: Create VPC network for AlloyDB
log_info "Step 9/15: Creating VPC network for AlloyDB..."
if gcloud compute networks list --project=$PROJECT_ID | grep -q "$VPC_NAME"; then
    log_warning "VPC network already exists"
else
    gcloud compute networks create $VPC_NAME \
        --subnet-mode=custom \
        --project=$PROJECT_ID

    gcloud compute networks subnets create $SUBNET_NAME \
        --network=$VPC_NAME \
        --region=$REGION \
        --range=10.0.0.0/24 \
        --project=$PROJECT_ID

    log_success "VPC network created"
fi

# Step 10: Allocate IP range for private service connection
log_info "Step 10/15: Setting up private service connection..."
if gcloud compute addresses list --global --project=$PROJECT_ID | grep -q "alloydb-ip-range"; then
    log_warning "IP range already allocated"
else
    gcloud compute addresses create alloydb-ip-range \
        --global \
        --purpose=VPC_PEERING \
        --prefix-length=16 \
        --network=$VPC_NAME \
        --project=$PROJECT_ID

    gcloud services vpc-peerings connect \
        --service=servicenetworking.googleapis.com \
        --ranges=alloydb-ip-range \
        --network=$VPC_NAME \
        --project=$PROJECT_ID

    log_success "Private service connection created"
fi

# Step 11: Create AlloyDB cluster
log_info "Step 11/15: Creating AlloyDB cluster (this takes 15-20 minutes)..."
if gcloud alloydb clusters describe $CLUSTER_NAME --region=$REGION --project=$PROJECT_ID &>/dev/null; then
    log_warning "AlloyDB cluster already exists"
else
    log_info "  This is the longest step - creating cluster..."
    gcloud alloydb clusters create $CLUSTER_NAME \
        --password=$ALLOYDB_PASSWORD \
        --network=$VPC_NAME \
        --region=$REGION \
        --project=$PROJECT_ID

    log_success "AlloyDB cluster created"
fi

# Step 12: Create AlloyDB primary instance
log_info "Step 12/15: Creating AlloyDB primary instance (5-10 minutes)..."
if gcloud alloydb instances describe $INSTANCE_NAME \
    --cluster=$CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID &>/dev/null; then
    log_warning "AlloyDB instance already exists"
else
    log_info "  Creating primary instance..."
    gcloud alloydb instances create $INSTANCE_NAME \
        --instance-type=PRIMARY \
        --cpu-count=2 \
        --region=$REGION \
        --cluster=$CLUSTER_NAME \
        --project=$PROJECT_ID

    log_success "AlloyDB instance created"
fi

# Step 13: Get AlloyDB IP address
log_info "Step 13/15: Retrieving AlloyDB connection details..."
ALLOYDB_IP=$(gcloud alloydb instances describe $INSTANCE_NAME \
    --cluster=$CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(ipAddress)")
log_success "AlloyDB IP: $ALLOYDB_IP"

# Step 14: Set up MCP server
log_info "Step 14/15: Setting up MCP server..."
cd "$SCRIPT_DIR/mcp-server"

if [ ! -d "node_modules" ]; then
    log_info "  Installing Node.js dependencies..."
    npm install
    log_success "  Dependencies installed"
else
    log_warning "  Node modules already installed"
fi

# Create .env file for MCP server
cat > .env << EOF
PROJECT_ID=$PROJECT_ID
ALLOYDB_HOST=$ALLOYDB_IP
ALLOYDB_PASSWORD=$ALLOYDB_PASSWORD
PORT=3100
EOF

log_success "MCP server configured"

# Step 15: Create Gemini Enterprise data stores
log_info "Step 15/15: Gemini Enterprise data store setup..."
log_warning "Data stores must be created via Google Cloud Console"
log_info "Create data stores for:"
log_info "  1. BigQuery (customer_analytics dataset)"
log_info "  2. Firestore (customer_sessions, support_tickets collections)"
log_info "  3. Cloud Storage ($PROJECT_ID-customer-docs bucket)"
echo ""

# Summary
echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
log_success "Demo #4 infrastructure is deployed!"
echo ""
echo "Important Information:"
echo "  AlloyDB IP: $ALLOYDB_IP"
echo "  AlloyDB Password: $ALLOYDB_PASSWORD"
echo ""
log_warning "SAVE THESE CREDENTIALS SECURELY!"
echo ""

# Save credentials
CREDS_FILE="$SCRIPT_DIR/.credentials"
cat > $CREDS_FILE << EOF
# Demo #4 Credentials
# Generated: $(date)

PROJECT_ID=$PROJECT_ID
REGION=$REGION
ALLOYDB_HOST=$ALLOYDB_IP
ALLOYDB_PASSWORD=$ALLOYDB_PASSWORD
ALLOYDB_CLUSTER=$CLUSTER_NAME
ALLOYDB_INSTANCE=$INSTANCE_NAME

# Buckets
CUSTOMER_DOCS_BUCKET=gs://$PROJECT_ID-customer-docs
SUPPORT_CALLS_BUCKET=gs://$PROJECT_ID-support-calls

# BigQuery
BIGQUERY_DATASET=$PROJECT_ID.customer_analytics
EOF

chmod 600 $CREDS_FILE
log_success "Credentials saved to: $CREDS_FILE"

echo ""
echo "Next steps:"
echo "  1. Start MCP server: cd mcp-server && npm start"
echo "  2. Create Gemini Enterprise data stores (manual step)"
echo "  3. Test with: curl http://localhost:3100/health"
echo "  4. Try demo: ../scripts/DEMO-SCRIPT.md"
echo ""
echo "To clean up resources later:"
echo "  ./cleanup.sh $PROJECT_ID"
echo ""

# Cost estimation
echo "Monthly Cost Estimate:"
echo "  - BigQuery: ~$25"
echo "  - AlloyDB (2 vCPU): ~$290"
echo "  - Firestore: ~$15"
echo "  - Cloud Storage: ~$1"
echo "  - Gemini Enterprise (10 users): ~$300"
echo "  Total: ~$631/month"
echo ""

log_success "All done! 🎉"
