#!/bin/bash
#
# Demo #4 Cleanup Script
# Removes all resources created by quickstart.sh
#
# Usage: ./cleanup.sh PROJECT_ID [--yes]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ID="${1}"
AUTO_CONFIRM="${2}"
REGION="us-central1"

# AlloyDB Configuration (must match quickstart.sh)
CLUSTER_NAME="customer-db-cluster"
INSTANCE_NAME="customer-db-primary"
VPC_NAME="alloydb-network"

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: PROJECT_ID is required${NC}"
    echo "Usage: $0 PROJECT_ID [--yes]"
    exit 1
fi

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Warning banner
echo ""
echo "=========================================="
echo "  ⚠️  DESTRUCTIVE OPERATION  ⚠️"
echo "=========================================="
echo ""
log_warning "This will DELETE all resources for Demo #4:"
echo "  - AlloyDB cluster and instance"
echo "  - BigQuery dataset (customer_analytics)"
echo "  - Firestore database"
echo "  - Cloud Storage buckets"
echo "  - VPC network"
echo ""
log_warning "Project: $PROJECT_ID"
echo ""

if [ "$AUTO_CONFIRM" != "--yes" ]; then
    read -p "Are you sure you want to continue? Type 'DELETE' to confirm: " CONFIRM
    if [ "$CONFIRM" != "DELETE" ]; then
        log_info "Cleanup cancelled"
        exit 0
    fi
fi

gcloud config set project $PROJECT_ID

# Delete AlloyDB instance
log_info "Deleting AlloyDB instance..."
if gcloud alloydb instances describe $INSTANCE_NAME \
    --cluster=$CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID &>/dev/null; then
    gcloud alloydb instances delete $INSTANCE_NAME \
        --cluster=$CLUSTER_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --quiet
    log_success "AlloyDB instance deleted"
else
    log_info "AlloyDB instance not found, skipping"
fi

# Delete AlloyDB cluster
log_info "Deleting AlloyDB cluster..."
if gcloud alloydb clusters describe $CLUSTER_NAME \
    --region=$REGION \
    --project=$PROJECT_ID &>/dev/null; then
    gcloud alloydb clusters delete $CLUSTER_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --quiet
    log_success "AlloyDB cluster deleted"
else
    log_info "AlloyDB cluster not found, skipping"
fi

# Delete BigQuery dataset
log_info "Deleting BigQuery dataset..."
if bq ls -d --project_id=$PROJECT_ID | grep -q "customer_analytics"; then
    bq rm -r -f -d $PROJECT_ID:customer_analytics
    log_success "BigQuery dataset deleted"
else
    log_info "BigQuery dataset not found, skipping"
fi

# Delete Cloud Storage buckets
log_info "Deleting Cloud Storage buckets..."
BUCKETS=("customer-docs" "support-calls")
for bucket in "${BUCKETS[@]}"; do
    BUCKET_NAME="$PROJECT_ID-$bucket"
    if gsutil ls -p $PROJECT_ID | grep -q "gs://$BUCKET_NAME/"; then
        gsutil -m rm -r gs://$BUCKET_NAME/
        log_success "  Deleted bucket: $BUCKET_NAME"
    else
        log_info "  Bucket $BUCKET_NAME not found, skipping"
    fi
done

# Delete VPC peering
log_info "Deleting VPC service connection..."
if gcloud services vpc-peerings list \
    --network=$VPC_NAME \
    --project=$PROJECT_ID 2>/dev/null | grep -q "servicenetworking"; then
    gcloud services vpc-peerings delete \
        --service=servicenetworking.googleapis.com \
        --network=$VPC_NAME \
        --project=$PROJECT_ID \
        --quiet || true
    log_success "VPC peering deleted"
fi

# Delete IP range
log_info "Deleting allocated IP range..."
if gcloud compute addresses list --global --project=$PROJECT_ID | grep -q "alloydb-ip-range"; then
    gcloud compute addresses delete alloydb-ip-range \
        --global \
        --project=$PROJECT_ID \
        --quiet
    log_success "IP range deleted"
fi

# Delete VPC network
log_info "Deleting VPC network..."
if gcloud compute networks list --project=$PROJECT_ID | grep -q "$VPC_NAME"; then
    # Delete subnet first
    if gcloud compute networks subnets list --project=$PROJECT_ID | grep -q "alloydb-subnet"; then
        gcloud compute networks subnets delete alloydb-subnet \
            --region=$REGION \
            --project=$PROJECT_ID \
            --quiet
    fi

    # Then delete network
    gcloud compute networks delete $VPC_NAME \
        --project=$PROJECT_ID \
        --quiet
    log_success "VPC network deleted"
fi

# Note about Firestore
log_warning "Firestore database cannot be deleted via CLI"
log_info "To delete Firestore, go to:"
log_info "  https://console.firebase.google.com/project/$PROJECT_ID/firestore"

# Note about Gemini Enterprise
log_warning "Gemini Enterprise data stores must be deleted via Console"
log_info "To delete data stores, go to:"
log_info "  https://console.cloud.google.com/gen-app-builder/engines"

# Clean up local files
log_info "Cleaning up local configuration files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -f "$SCRIPT_DIR/.credentials"
rm -f "$SCRIPT_DIR/mcp-server/.env"
log_success "Local files cleaned"

echo ""
echo "=========================================="
echo "  Cleanup Complete!"
echo "=========================================="
echo ""
log_success "Most resources have been deleted"
echo ""
log_info "Manual cleanup required for:"
echo "  - Firestore database (via Firebase Console)"
echo "  - Gemini Enterprise data stores (via Cloud Console)"
echo ""
log_info "Verify all resources are deleted:"
echo "  https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
echo ""
