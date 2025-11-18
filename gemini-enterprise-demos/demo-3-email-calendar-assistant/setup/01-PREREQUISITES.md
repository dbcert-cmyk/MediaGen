# Demo #3: Smart Email & Calendar Productivity Assistant
## Prerequisites and Setup Instructions

### Overview
This demo showcases how Gemini Enterprise, Google ADK, and MCP servers work together to create an intelligent productivity assistant that manages email, calendar, and documents automatically.

---

## 1. Google Cloud Project Setup

### 1.1 Create or Select a Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID="your-gemini-enterprise-demo"
export REGION="us-central1"

# Create a new project (or use existing)
gcloud projects create $PROJECT_ID --name="Gemini Enterprise Demo"

# Set the project as default
gcloud config set project $PROJECT_ID
```

### 1.2 Enable Required APIs

```bash
# Enable all required Google Cloud APIs
gcloud services enable \
  aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  gmail.googleapis.com \
  calendar-json.googleapis.com \
  drive.googleapis.com \
  firestore.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  cloudbuild.googleapis.com
```

**Estimated time:** 3-5 minutes

---

## 2. Gemini Enterprise Setup

### 2.1 Enable Gemini Enterprise

1. Navigate to [Google Cloud Console](https://console.cloud.google.com)
2. Go to **Gemini Enterprise** (search in top bar)
3. Click **"Enable Gemini Enterprise"**
4. Accept the terms of service
5. Choose your organization settings:
   - **Organization ID:** Your Google Workspace organization
   - **Region:** us-central1 (recommended)
   - **Data residency:** United States

**Estimated time:** 5-10 minutes (includes review)

### 2.2 Configure User Access

```bash
# Grant Gemini Enterprise User role to demo users
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:demo-user@yourdomain.com" \
  --role="roles/discoveryengine.user"

# Grant Gemini Enterprise Admin role (for setup)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:admin@yourdomain.com" \
  --role="roles/discoveryengine.admin"
```

---

## 3. Data Store Configuration

### 3.1 Create Gmail Data Store

1. In Google Cloud Console → **Gemini Enterprise** → **Data Stores**
2. Click **"Create Data Store"**
3. Select **"Gmail"** as the data source
4. Configure:
   - **Name:** `demo-gmail-datastore`
   - **Sync frequency:** Daily
   - **Entities to sync:**
     - ✅ Messages
     - ✅ Threads
     - ✅ Labels
   - **Date range:** Last 90 days
5. Click **"Create"**

**First sync time:** ~1 hour for initial ingestion

### 3.2 Create Google Calendar Data Store

1. Click **"Create Data Store"** again
2. Select **"Google Calendar"** as the data source
3. Configure:
   - **Name:** `demo-calendar-datastore`
   - **Sync frequency:** Daily
   - **Entities to sync:**
     - ✅ Events
     - ✅ Attendees
   - **Calendars:** Select all calendars
   - **Date range:** Next 365 days + Past 90 days
4. Click **"Create"**

### 3.3 Create Google Drive Data Store

1. Click **"Create Data Store"**
2. Select **"Google Drive"** as the data source
3. Configure:
   - **Name:** `demo-drive-datastore`
   - **Sync frequency:** Daily
   - **File types:**
     - ✅ Google Docs
     - ✅ Google Sheets
     - ✅ Google Slides
     - ✅ PDFs
   - **Folders:** Select relevant folders (or entire Drive)
   - **File size limit:** 10 MB per file
4. Click **"Create"**

### 3.4 Create Firestore Data Store (User Preferences)

```bash
# Create Firestore database
gcloud firestore databases create --region=$REGION --type=firestore-native

# Navigate to Gemini Enterprise console
# Create Data Store → Select "Firestore"
# Configure:
#   - Name: demo-user-preferences
#   - Database: (default)
#   - Collection: user_preferences
#   - Sync frequency: Daily
```

---

## 4. Google ADK (Agent Development Kit) Setup

### 4.1 Install ADK

```bash
# Install Python 3.10+ (required)
python3 --version  # Should be 3.10 or higher

# Create virtual environment
python3 -m venv adk-env
source adk-env/bin/activate  # On Windows: adk-env\Scripts\activate

# Install ADK
pip install google-adk
pip install google-cloud-aiplatform
pip install google-cloud-discoveryengine
```

### 4.2 Configure ADK Authentication

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set up ADK configuration
export ADK_PROJECT_ID=$PROJECT_ID
export ADK_LOCATION=$REGION
export GEMINI_MODEL="gemini-2.5-pro"
```

### 4.3 Initialize Vertex AI for Agent Deployment

```bash
# Initialize Vertex AI Agent Engine
gcloud ai-platform models list --region=$REGION

# Verify Vertex AI is enabled
gcloud services list --enabled | grep aiplatform
```

---

## 5. MCP Server Setup (Gmail & Calendar Integration)

### 5.1 Install MCP Server for Google Workspace

```bash
# Clone the Google Workspace MCP Server
git clone https://github.com/aaronsb/google-workspace-mcp.git
cd google-workspace-mcp

# Install dependencies
npm install
```

### 5.2 Configure OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: `MCP-Gmail-Calendar-Integration`
5. Download JSON credentials as `credentials.json`

6. Configure scopes in OAuth consent screen:
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
   - `https://www.googleapis.com/auth/drive.readonly`

### 5.3 Initialize MCP Server

```bash
# Copy credentials to MCP server directory
cp /path/to/credentials.json google-workspace-mcp/

# Start MCP server
cd google-workspace-mcp
node server.js

# On first run, you'll get an OAuth URL - visit it to authorize
# After authorization, the server will start on port 3000
```

### 5.4 Configure MCP Server for Gemini CLI

```bash
# Install Gemini CLI (if not already installed)
npm install -g @google/generative-ai-cli

# Configure MCP server in Gemini CLI
gemini mcp add google-workspace http://localhost:3000
```

---

## 6. Gmail and Calendar Actions Configuration

### 6.1 Enable Gmail Actions in Gemini Enterprise

1. Go to **Gemini Enterprise Console** → **Settings** → **Actions**
2. Find **"Gmail Actions"** section
3. Toggle **"Enable Gmail Actions"** to ON
4. Configure permissions:
   - ✅ Send email
   - ✅ Draft email
   - ✅ Search email
   - ✅ Modify email (labels, read/unread)

5. Click **"Save"**

### 6.2 Enable Calendar Actions in Gemini Enterprise

1. In the same **Actions** settings page
2. Find **"Google Calendar Actions"** section
3. Toggle **"Enable Calendar Actions"** to ON
4. Configure permissions:
   - ✅ Create events
   - ✅ Update events
   - ✅ List events
   - ✅ Invite attendees

4. Click **"Save"**

### 6.3 Test Actions

```bash
# Test Gmail action via Gemini Enterprise UI
# Navigate to Gemini Enterprise web interface
# Type: "Send an email to test@example.com with subject 'Test' and body 'This is a test'"

# First-time authorization:
# - You'll be prompted to authorize Gmail access
# - Click "Authorize" and complete OAuth flow
# - After authorization, the email will be sent
```

---

## 7. Deploy ADK Agents to Vertex AI

### 7.1 Prepare Agent Code

Create the following directory structure:
```
adk-agents/
├── email_agent/
│   ├── agent.py
│   └── requirements.txt
├── calendar_agent/
│   ├── agent.py
│   └── requirements.txt
├── meeting_prep_agent/
│   ├── agent.py
│   └── requirements.txt
└── followup_agent/
    ├── agent.py
    └── requirements.txt
```

### 7.2 Deploy Agents

```bash
# Navigate to agent directory
cd adk-agents/email_agent

# Deploy to Vertex AI Agent Engine
adk deploy \
  --agent-name=email-agent \
  --project=$PROJECT_ID \
  --location=$REGION \
  --source=agent.py \
  --model=gemini-2.5-pro

# Repeat for other agents
cd ../calendar_agent
adk deploy --agent-name=calendar-agent --project=$PROJECT_ID --location=$REGION --source=agent.py

cd ../meeting_prep_agent
adk deploy --agent-name=meeting-prep-agent --project=$PROJECT_ID --location=$REGION --source=agent.py

cd ../followup_agent
adk deploy --agent-name=followup-agent --project=$PROJECT_ID --location=$REGION --source=agent.py
```

**Deployment time:** 5-10 minutes per agent

---

## 8. Connect ADK Agents to Gemini Enterprise

### 8.1 Register Agents in Gemini Enterprise

1. Go to **Gemini Enterprise Console** → **Agents**
2. Click **"Add Agent"**
3. Select **"Vertex AI Agent"**
4. Fill in details:
   - **Name:** Email Agent
   - **Agent ID:** `projects/{PROJECT_ID}/locations/{REGION}/agents/email-agent`
   - **Description:** Handles email summarization, drafting, and management
5. Click **"Add"**

Repeat for all 4 agents:
- Email Agent
- Calendar Agent
- Meeting Prep Agent
- Follow-up Agent

### 8.2 Create Agent Orchestration

1. Go to **Agent Designer** (no-code tool)
2. Click **"Create New Agent"**
3. Name: **"Productivity Copilot"**
4. Add workflow:
   ```
   Trigger: User query in Gemini Enterprise
   ↓
   Route to appropriate agent:
   - Email keywords → Email Agent
   - Calendar/meeting keywords → Calendar Agent
   - "Prepare for meeting" → Meeting Prep Agent
   - "Follow up" → Follow-up Agent
   ```

5. Configure data sources:
   - ✅ demo-gmail-datastore
   - ✅ demo-calendar-datastore
   - ✅ demo-drive-datastore
   - ✅ demo-user-preferences

6. Click **"Publish"**

---

## 9. Firestore Schema Setup (User Preferences)

```bash
# Install Firestore SDK
pip install google-cloud-firestore

# Run the schema setup script (provided in mock-data/)
python setup/firestore_schema_setup.py
```

This creates the following collections:
- `user_preferences` - User settings and preferences
- `email_patterns` - Learned email patterns
- `meeting_preferences` - Meeting scheduling preferences
- `follow_up_tasks` - Automated follow-up reminders

---

## 10. Verify Setup

### 10.1 Check Data Store Sync Status

```bash
# List all data stores
gcloud discovery-engine data-stores list \
  --location=global \
  --project=$PROJECT_ID

# Check sync status for Gmail
gcloud discovery-engine data-stores describe demo-gmail-datastore \
  --location=global \
  --project=$PROJECT_ID
```

Expected output: `state: ACTIVE`, `lastSyncTime: <recent timestamp>`

### 10.2 Test End-to-End Flow

1. Open **Gemini Enterprise** web interface
2. Type: **"Give me my daily briefing"**
3. Expected output:
   - Summary of unread emails (from Gmail data store)
   - Today's calendar events (from Calendar data store)
   - Action items from recent meetings (from Drive data store)

4. Type: **"Schedule lunch with Sarah next week"**
5. Expected behavior:
   - Calendar Agent checks both calendars
   - Finds optimal time
   - Asks for confirmation
   - Creates event (via Calendar Actions)
   - Sends invitation (via Gmail Actions)

---

## 11. Troubleshooting

### Common Issues

**Issue 1: Data stores not syncing**
```bash
# Check data store status
gcloud discovery-engine data-stores describe demo-gmail-datastore --location=global

# Trigger manual sync
gcloud discovery-engine data-stores import demo-gmail-datastore \
  --location=global \
  --source=gmail
```

**Issue 2: OAuth authorization failures**
- Ensure OAuth consent screen is configured correctly
- Check that all required scopes are enabled
- Verify credentials.json is in the correct location

**Issue 3: Agents not responding**
```bash
# Check agent deployment status
gcloud ai-platform models list --region=$REGION

# View agent logs
gcloud logging read "resource.type=aiplatform.googleapis.com/Model" --limit=50
```

**Issue 4: MCP server connection issues**
```bash
# Check MCP server status
curl http://localhost:3000/health

# Restart MCP server
cd google-workspace-mcp
node server.js
```

---

## 12. Security Best Practices

1. **Limit OAuth scopes** to minimum required permissions
2. **Enable audit logging** for Gemini Enterprise:
   ```bash
   gcloud logging sinks create gemini-audit-logs \
     storage.googleapis.com/gemini-audit-bucket \
     --log-filter='resource.type="discoveryengine.googleapis.com/DataStore"'
   ```
3. **Set up data access controls** in Firestore:
   ```javascript
   // Firestore security rules
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /user_preferences/{userId} {
         allow read, write: if request.auth.uid == userId;
       }
     }
   }
   ```
4. **Rotate OAuth credentials** every 90 days
5. **Monitor API usage** to detect anomalies

---

## 13. Cost Estimation

### Monthly Costs (for demo with 10 users)

| Service | Usage | Cost |
|---------|-------|------|
| Gemini Enterprise | 10 users × $30/user | $300 |
| Vertex AI (Agent Engine) | ~100k requests | $50 |
| Gmail API | 50k requests | Free (within quota) |
| Calendar API | 20k requests | Free (within quota) |
| Firestore | 10GB storage, 100k reads/writes | $5 |
| Cloud Storage | 5GB | $0.10 |
| **Total** | | **~$355/month** |

**Note:** Costs scale linearly with number of users and API usage.

---

## Setup Complete! ✅

Your Demo #3 environment is now ready. Proceed to:
- **Mock Data Setup:** See `mock-data/` directory
- **Demo Scripts:** See `scripts/` directory
- **Presentation:** See `presentation/` directory

**Next Steps:**
1. Load mock data (see `02-MOCK-DATA-SETUP.md`)
2. Test the demo scenarios (see `demo-scripts/`)
3. Review the presentation materials

**Estimated total setup time:** 2-3 hours (excluding data sync time)
