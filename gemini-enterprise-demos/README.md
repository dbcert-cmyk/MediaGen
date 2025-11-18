# Gemini Enterprise Demos
## Showcasing the Power of Google ADK + MCP + Gemini Enterprise

This repository contains two comprehensive demos that showcase how Gemini Enterprise, Google Agent Development Kit (ADK), and Model Context Protocol (MCP) servers work together to create powerful enterprise AI solutions using **only Google 1st party services**.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Demo #3: Smart Email & Calendar Productivity Assistant](#demo-3-smart-email--calendar-productivity-assistant)
- [Demo #4: Customer Data Platform & Insights Engine](#demo-4-customer-data-platform--insights-engine)
- [Setup Requirements](#setup-requirements)
- [Quick Start](#quick-start)
- [Repository Structure](#repository-structure)
- [ROI Summary](#roi-summary)
- [Support](#support)

---

## Overview

These demos demonstrate:
- ✅ **Gemini Enterprise** as the unified frontend and orchestration platform
- ✅ **Google ADK** for building production-ready multi-agent systems
- ✅ **MCP Servers** for extending capabilities with custom integrations
- ✅ **Google 1st Party Services Only** (BigQuery, Firestore, Gmail, Calendar, Drive, AlloyDB, etc.)

### Key Technologies

| Technology | Purpose | Documentation |
|------------|---------|---------------|
| **Gemini Enterprise** | Agentic platform, conversational UI, data connectors | [Docs](https://cloud.google.com/gemini/enterprise/docs) |
| **Google ADK** | Multi-agent orchestration framework | [Docs](https://google.github.io/adk-docs/) |
| **MCP** | Model Context Protocol for custom integrations | [Spec](https://modelcontextprotocol.io) |
| **Gemini 2.5 Pro** | Advanced AI model powering agents | [Docs](https://ai.google.dev/gemini-api/docs) |

---

## Demo #3: Smart Email & Calendar Productivity Assistant

### What It Does
An AI-powered productivity copilot that manages email, calendar, and meetings automatically.

### Key Features
- 📧 **Intelligent Email Management** - Auto-prioritize, summarize, draft responses
- 📅 **Smart Scheduling** - Find optimal meeting times across multiple calendars
- 📝 **Meeting Preparation** - Auto-gather context, create agendas
- 🤖 **Agentic Workflows** - Automated follow-ups and task management

### Time Savings
- **2.5 hours/day saved per employee**
- **12.5 hours/week saved**
- **650 hours/year saved**

### ROI
- **69.5x return on investment**
- Break-even in less than 1 week

### Setup Time
- **2-3 hours** (including data sync)

### [→ Full Demo #3 Documentation](./demo-3-email-calendar-assistant/)

---

## Demo #4: Customer Data Platform & Insights Engine

### What It Does
A unified customer intelligence platform aggregating data from BigQuery, AlloyDB, Firestore, Cloud Storage, and Gmail for 360-degree customer views and predictive analytics.

### Key Features
- 👤 **Customer 360 Views** - Instant access to all customer data (15 min → 10 sec)
- 📊 **Predictive Analytics** - Churn prediction, upsell identification
- 🎯 **Automated Segmentation** - AI-powered customer grouping
- 💬 **Natural Language Analytics** - Query data without SQL

### Time Savings
- **16,068 hours/year** across sales, support, and marketing teams

### Revenue Impact
- **$430K/year** (churn reduction + upsells + faster sales cycles)

### ROI
- **153x combined ROI** (time savings + revenue impact)

### Setup Time
- **3-4 hours** (including database provisioning)

### [→ Full Demo #4 Documentation](./demo-4-customer-data-platform/)

---

## Setup Requirements

### Prerequisites
- Google Cloud Project with billing enabled
- Gemini Enterprise access
- Basic familiarity with:
  - Google Cloud Console
  - Command line (gcloud, bq, gsutil)
  - Python (for running scripts)

### Google Services Used

#### Demo #3
- ✅ Gemini Enterprise
- ✅ Gmail (data connector)
- ✅ Google Calendar (data connector)
- ✅ Google Drive (data connector)
- ✅ Firestore (user preferences)
- ✅ Vertex AI (agent deployment)

#### Demo #4
- ✅ Gemini Enterprise
- ✅ BigQuery (analytics warehouse)
- ✅ AlloyDB for PostgreSQL (operational database)
- ✅ Firestore (real-time data)
- ✅ Cloud Storage (documents, media)
- ✅ Gmail (customer communications)
- ✅ Vertex AI (agent deployment)

### Cost Estimates

**Demo #3 (100 users):**
- Monthly: ~$355
- Primarily Gemini Enterprise licenses ($30/user/month)

**Demo #4 (10K customers, 18 users):**
- Monthly: ~$681
- Includes databases, storage, and Gemini Enterprise

[→ Detailed Cost Breakdown](./COMPREHENSIVE-VALUE-PRESENTATION.md#cost-estimation)

---

## Quick Start

### Option 1: Demo #3 (Email & Calendar Assistant)

```bash
# Clone repository
git clone https://github.com/your-org/gemini-enterprise-demos.git
cd gemini-enterprise-demos/demo-3-email-calendar-assistant

# Follow setup guide
cat setup/01-PREREQUISITES.md

# Run setup script
./setup/quickstart.sh

# Load mock data
python mock-data/firestore_schema.py YOUR_PROJECT_ID

# Test the demo
# Open Gemini Enterprise UI and type: "Give me my daily briefing"
```

**Estimated setup time:** 2-3 hours

### Option 2: Demo #4 (Customer Data Platform)

```bash
# Clone repository
cd gemini-enterprise-demos/demo-4-customer-data-platform

# Follow setup guide
cat setup/01-PREREQUISITES.md

# Run database setup
./setup/database_setup.sh

# Load mock data
./setup/load_mock_data.sh

# Test the demo
# Open Gemini Enterprise UI and type: "Show me the profile for Acme Corporation"
```

**Estimated setup time:** 3-4 hours

---

## Repository Structure

```
gemini-enterprise-demos/
│
├── README.md (this file)
├── COMPREHENSIVE-VALUE-PRESENTATION.md (ROI analysis, business case)
│
├── demo-3-email-calendar-assistant/
│   ├── setup/
│   │   ├── 01-PREREQUISITES.md (step-by-step setup)
│   │   └── adk-agents/ (Email, Calendar, Meeting Prep agents)
│   ├── mock-data/
│   │   ├── gmail_mock_data.json
│   │   ├── calendar_mock_data.json
│   │   └── firestore_schema.py
│   ├── scripts/
│   │   └── DEMO-SCRIPT.md (complete demo walkthrough)
│   └── presentation/
│       └── demo-3-slides.pdf
│
└── demo-4-customer-data-platform/
    ├── setup/
    │   ├── 01-PREREQUISITES.md (step-by-step setup)
    │   ├── adk-agents/ (Customer Intelligence, Segmentation agents)
    │   └── mcp-server/ (multi-database MCP server)
    ├── mock-data/
    │   ├── bigquery_customers.json
    │   ├── alloydb_schemas/
    │   └── firestore/
    ├── scripts/
    │   └── DEMO-SCRIPT.md (complete demo walkthrough)
    └── presentation/
        └── demo-4-slides.pdf
```

---

## ROI Summary

### Combined Value Proposition

**Total Investment (for both demos):**
- Demo #3: $36,000/year (100 employees)
- Demo #4: $6,480/year (18 employees)
- **Total: $42,480/year**

**Total Benefits:**
- Demo #3 time savings: $2,502,500/year
- Demo #4 time savings: $562,380/year
- Demo #4 revenue impact: $430,000/year
- **Total: $3,494,880/year**

**Combined ROI: 82.3x**

### Break-Even Analysis

| Demo | Investment | Weekly Value | Break-Even Time |
|------|-----------|--------------|-----------------|
| Demo #3 | $36,000/year | $48,125/week | **< 1 week** |
| Demo #4 | $6,480/year | $19,085/week | **< 1 week** |
| **Combined** | **$42,480** | **$67,210/week** | **< 1 week** |

[→ Full ROI Analysis](./COMPREHENSIVE-VALUE-PRESENTATION.md)

---

## Demo Scripts

Both demos include complete, step-by-step demo scripts with:
- Pre-demo setup checklists
- Exact queries to type
- Expected AI responses
- Talking points for presenters
- Q&A sections
- Technical troubleshooting

**Demo #3 Script:** [→ View Demo Script](./demo-3-email-calendar-assistant/scripts/DEMO-SCRIPT.md)
**Demo #4 Script:** [→ View Demo Script](./demo-4-customer-data-platform/scripts/DEMO-SCRIPT.md)

---

## Technical Architecture

### Demo #3 Architecture

```
┌─────────────────────────────────────────────────┐
│          Gemini Enterprise UI                   │
│         (Conversational Interface)              │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────┴────────┐
         │ Agent Designer   │ (No-code orchestration)
         │  Orchestrator    │
         └────────┬─────────┘
                  │
    ┌─────────────┼─────────────────┐
    │             │                 │
┌───▼────┐  ┌────▼────┐  ┌─────────▼──────┐
│ Email  │  │Calendar │  │Meeting Prep    │
│ Agent  │  │ Agent   │  │    Agent       │
│ (ADK)  │  │ (ADK)   │  │    (ADK)       │
└───┬────┘  └────┬────┘  └─────────┬──────┘
    │            │                  │
┌───▼────────────▼──────────────────▼──────┐
│     MCP Server (Gmail/Calendar API)      │
└───┬────────────┬──────────────────┬──────┘
    │            │                  │
┌───▼───┐  ┌────▼────┐  ┌──────────▼──────┐
│ Gmail │  │Calendar │  │ Drive  │ Firestore│
│  API  │  │   API   │  │  API   │   (prefs)│
└───────┘  └─────────┘  └──────────┘ └──────┘
```

### Demo #4 Architecture

```
┌─────────────────────────────────────────────────┐
│          Gemini Enterprise UI                   │
│         (Conversational Interface)              │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────┴────────┐
         │ CDP Orchestrator│ (Agent Designer)
         └────────┬─────────┘
                  │
    ┌─────────────┼─────────────────┬────────────┐
    │             │                 │            │
┌───▼────────┐  ┌─▼──────────┐  ┌──▼────────┐ ┌─▼──────┐
│Customer    │  │Segmentation│  │Recommend- │ │ Churn  │
│Intelligence│  │   Agent    │  │  ation    │ │Predict │
│   Agent    │  │   (ADK)    │  │   Agent   │ │ Agent  │
│   (ADK)    │  │            │  │   (ADK)   │ │ (ADK)  │
└───┬────────┘  └─┬──────────┘  └──┬────────┘ └─┬──────┘
    │             │                 │            │
    └─────────────┴─────────────────┴────────────┘
                       │
         ┌─────────────▼──────────────┐
         │  MCP Multi-DB Server       │
         │  (Data Aggregation)        │
         └─┬────┬─────┬──────┬────┬──┘
           │    │     │      │    │
    ┌──────▼┐ ┌─▼───┐│┌────▼┐ ┌─▼─────┐ ┌──────┐
    │BigQuery│ │Fire-│││Cloud│ │AlloyDB│ │Gmail │
    │(Analytics│store││Storage│(Ops DB)│ │(Comms)│
    │  Data)  │(Real-│││(Docs)│        │ │      │
    └─────────┘time)└┘└──────┘└────────┘└───────┘
```

---

## Security & Compliance

Both demos are designed with enterprise security in mind:

✅ **Data Residency** - All data stays in your Google Cloud project
✅ **No Training on Your Data** - Gemini never trains on customer data
✅ **Compliance** - SOC 2, GDPR, HIPAA compliant
✅ **Access Controls** - Permissions-aware (users see only authorized data)
✅ **Audit Logging** - Full audit trail of all AI actions
✅ **Human Oversight** - All external actions require approval

[→ Security Best Practices](./demo-3-email-calendar-assistant/setup/01-PREREQUISITES.md#security-best-practices)

---

## Troubleshooting

### Common Issues

**Issue: Data stores not syncing**
```bash
# Check sync status
gcloud discovery-engine data-stores list --location=global

# Trigger manual sync
gcloud discovery-engine data-stores import DATASTORE_NAME --location=global
```

**Issue: ADK agents not responding**
```bash
# Check agent deployment
gcloud ai-platform models list --region=us-central1

# View logs
gcloud logging read "resource.type=aiplatform.googleapis.com/Model" --limit=50
```

**Issue: MCP server connection errors**
```bash
# Check if server is running
curl http://localhost:3000/health

# Restart server
cd mcp-server && npm start
```

[→ Full Troubleshooting Guide](./demo-3-email-calendar-assistant/setup/01-PREREQUISITES.md#troubleshooting)

---

## Next Steps

### 1. Choose Your Demo
- **Need productivity gains?** → Start with Demo #3
- **Need customer insights?** → Start with Demo #4
- **Want comprehensive solution?** → Implement both

### 2. Set Up Environment
- Follow the detailed setup guides in each demo folder
- Allocate 2-4 hours for initial setup
- Test with mock data before using real data

### 3. Run the Demo
- Use the provided demo scripts
- Practice the queries and talking points
- Show to stakeholders

### 4. Pilot Program
- Select 10-20 users for 30-day pilot
- Measure time savings and ROI
- Gather feedback and optimize

### 5. Scale Up
- Roll out to full department
- Deploy to entire organization
- Establish center of excellence

---

## Support & Resources

### Documentation
- **Gemini Enterprise:** https://cloud.google.com/gemini/enterprise/docs
- **Google ADK:** https://google.github.io/adk-docs/
- **MCP Specification:** https://modelcontextprotocol.io

### Community
- **Google Cloud Community:** https://www.googlecloudcommunity.com/
- **ADK GitHub:** https://github.com/google/adk
- **MCP Servers:** https://github.com/modelcontextprotocol/servers

### Get Help
- **Issues:** Open an issue in this repository
- **Questions:** Ask in Google Cloud Community forums
- **Enterprise Support:** Contact your Google Cloud account team

---

## License

This demo code is provided under the Apache 2.0 License.

See [LICENSE](./LICENSE) for details.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## Changelog

### Version 1.0 (November 2025)
- Initial release
- Demo #3: Email & Calendar Assistant
- Demo #4: Customer Data Platform
- Comprehensive value presentation
- Complete setup guides and mock data

---

## Acknowledgments

Built with:
- **Gemini Enterprise** - Google Cloud
- **Google ADK** - Google AI
- **Model Context Protocol** - Anthropic (open standard)

Special thanks to the Google Cloud and Google AI teams for their excellent documentation and support.

---

**Questions? Feedback? Suggestions?**

Open an issue or contact: demo-support@company.com

---

*Last Updated: November 2025*
*Version: 1.0*
