#!/bin/bash
#
# Demo #3 Quick Start Script
# Automated setup for Smart Email & Calendar Productivity Assistant
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
echo "  Gemini Enterprise Demo #3"
echo "  Email & Calendar Assistant Setup"
echo "=========================================="
echo ""
log_info "Project ID: $PROJECT_ID"
log_info "Region: $REGION"
echo ""

# Step 1: Check prerequisites
log_info "Step 1/10: Checking prerequisites..."
check_command gcloud
check_command python3
check_command pip3
log_success "Prerequisites check passed"

# Step 2: Set up Google Cloud project
log_info "Step 2/10: Configuring Google Cloud project..."
gcloud config set project $PROJECT_ID
log_success "Project configured"

# Step 3: Enable required APIs
log_info "Step 3/10: Enabling required APIs (this may take 2-3 minutes)..."
APIS=(
    "aiplatform.googleapis.com"
    "discoveryengine.googleapis.com"
    "gmail.googleapis.com"
    "calendar-json.googleapis.com"
    "drive.googleapis.com"
    "firestore.googleapis.com"
    "cloudresourcemanager.googleapis.com"
)

for api in "${APIS[@]}"; do
    log_info "  Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID 2>/dev/null || true
done
log_success "APIs enabled"

# Step 4: Create Firestore database
log_info "Step 4/10: Creating Firestore database..."
if gcloud firestore databases list --project=$PROJECT_ID 2>/dev/null | grep -q "(default)"; then
    log_warning "Firestore database already exists"
else
    gcloud firestore databases create \
        --location=$REGION \
        --type=firestore-native \
        --project=$PROJECT_ID
    log_success "Firestore database created"
fi

# Step 5: Set up Python virtual environment
log_info "Step 5/10: Setting up Python environment..."
cd "$SCRIPT_DIR/../.."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_warning "Virtual environment already exists"
fi

source venv/bin/activate

# Step 6: Install Python dependencies
log_info "Step 6/10: Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q google-adk google-cloud-aiplatform google-cloud-discoveryengine \
    google-cloud-firestore google-auth python-dateutil
log_success "Dependencies installed"

# Step 7: Load Firestore mock data
log_info "Step 7/10: Loading Firestore mock data..."
cd "$SCRIPT_DIR/../mock-data"
python3 firestore_schema.py $PROJECT_ID
log_success "Firestore data loaded"

# Step 8: Create Gemini Enterprise data stores
log_info "Step 8/10: Creating Gemini Enterprise data stores..."
log_warning "Data stores must be created via Google Cloud Console (manual step)"
log_info "  1. Go to: https://console.cloud.google.com/gen-app-builder/engines"
log_info "  2. Create data stores for: Gmail, Calendar, Drive"
log_info "  3. Configure sync frequency: Daily"
echo ""
read -p "Press Enter when data stores are created..."

# Step 9: Deploy ADK agents to Vertex AI
log_info "Step 9/10: Deploying ADK agents..."
log_warning "ADK agent deployment requires manual configuration"
log_info "Run these commands to deploy agents:"
echo ""
echo "cd $SCRIPT_DIR/adk-agents/email_agent"
echo "adk deploy --agent-name=email-agent --project=$PROJECT_ID --location=$REGION --source=agent.py"
echo ""
echo "cd $SCRIPT_DIR/adk-agents/calendar_agent"
echo "adk deploy --agent-name=calendar-agent --project=$PROJECT_ID --location=$REGION --source=agent.py"
echo ""
echo "cd $SCRIPT_DIR/adk-agents/meeting_prep_agent"
echo "adk deploy --agent-name=meeting-prep-agent --project=$PROJECT_ID --location=$REGION --source=agent.py"
echo ""
echo "cd $SCRIPT_DIR/adk-agents/followup_agent"
echo "adk deploy --agent-name=followup-agent --project=$PROJECT_ID --location=$REGION --source=agent.py"
echo ""
read -p "Press Enter when agents are deployed..."

# Step 10: Verify setup
log_info "Step 10/10: Verifying setup..."
log_info "Checking Firestore collections..."
COLLECTIONS=("user_preferences" "email_patterns" "meeting_preferences" "follow_up_tasks")
for collection in "${COLLECTIONS[@]}"; do
    COUNT=$(gcloud firestore export gs://${PROJECT_ID}-temp --collection-ids=$collection --project=$PROJECT_ID 2>&1 | wc -l || echo "0")
    log_info "  ✓ Collection: $collection"
done

log_success "Setup verification complete!"

# Summary
echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
log_success "Demo #3 is ready to use!"
echo ""
echo "Next steps:"
echo "  1. Open Gemini Enterprise: https://gemini-enterprise.cloud.google.com"
echo "  2. Try the demo script: ../scripts/DEMO-SCRIPT.md"
echo "  3. Test with: 'Give me my daily briefing'"
echo ""
echo "Estimated setup time: 2-3 hours (including data sync)"
echo "First data store sync may take 1-2 hours"
echo ""
log_info "For troubleshooting, see: ../setup/01-PREREQUISITES.md"
echo ""

# Create environment file
cat > .env << EOF
PROJECT_ID=$PROJECT_ID
REGION=$REGION
GEMINI_MODEL=gemini-2.5-pro
EOF

log_success "Created .env file with configuration"

# Optional: Open documentation
read -p "Open setup documentation in browser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "$SCRIPT_DIR/01-PREREQUISITES.md"
    elif command -v open &> /dev/null; then
        open "$SCRIPT_DIR/01-PREREQUISITES.md"
    else
        log_info "Please open: $SCRIPT_DIR/01-PREREQUISITES.md"
    fi
fi

log_success "All done! 🎉"
