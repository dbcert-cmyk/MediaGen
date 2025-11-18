# 🛡️ Multi-Agent Fraud Detection System

A sophisticated, **agentic workflow** where a team of AI agents collaborates in real-time to detect and act on fraudulent financial transactions.

## 🌟 Concept

This isn't one "god" agent. It's a **team of specialized agents** built with **Google ADK** (Agentic Development Kit) that communicate using an **Agent-to-Agent (A2A)** pattern, orchestrated by **LangGraph**.

## 🤖 The Agent Team

### Agent 1: Transaction Monitor
- **Role**: Real-time transaction surveillance
- **Responsibilities**:
  - Monitors transaction stream from Kafka/Redpanda
  - Runs initial fraud pattern detection
  - Flags suspicious activity for investigation
- **Technology**: Google Gemini with fraud detection tools

### Agent 2: The Investigator  
- **Role**: Deep fraud investigation
- **Responsibilities**:
  - Analyzes flagged transactions
  - Queries user history from PostgreSQL
  - Checks against known fraud patterns
  - Confirms if threat is real
- **Technology**: Google Gemini with historical analysis capabilities

### Agent 3: The Remediation Agent
- **Role**: Automated response and action
- **Responsibilities**:
  - Executes actions on confirmed fraud
  - Locks accounts or sends security alerts
  - Updates user risk scores
  - Logs all actions taken
- **Technology**: Direct action execution with notification system

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Transaction Stream                         │
│              (Kafka/Redpanda - Real-time)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent 1: Transaction Monitor                    │
│  • Receives transactions from stream                        │
│  • Runs fraud pattern detection                             │
│  • Flags suspicious activity                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │   Suspicious?       │
         └─────────┬───────────┘
                   │ YES
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent 2: The Investigator                       │
│  • Deep analysis of flagged transactions                    │
│  • Queries user history (PostgreSQL)                        │
│  • Checks fraud patterns                                    │
│  • Confirms fraud determination                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │   Fraud Confirmed?  │
         └─────────┬───────────┘
                   │ YES
                   ▼
┌─────────────────────────────────────────────────────────────┐
│            Agent 3: Remediation Agent                        │
│  • Lock account                                             │
│  • Decline transaction                                      │
│  • Send security alert                                      │
│  • Update risk score                                        │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

All tools are **FREE** and **open-source**:

- **Google ADK** - Agentic Development Kit (Open-source)
- **LangGraph** - Stateful multi-agent orchestration (Open-source)
- **Google Gemini** - AI model for agents
- **Redpanda/Kafka** - Real-time data streaming (Open-source)
- **PostgreSQL** - User history database (Open-source)
- **FastAPI** - Web API and demo interface (Open-source)
- **Docker** - Containerization (Free)
- **Python** - Core programming language (Free)

## 🚀 Quick Start

### Prerequisites

1. **Docker & Docker Compose** installed
2. **Python 3.10+** installed
3. **Google API Key** for Gemini (free tier available)

### Installation

1. **Clone and navigate to the fraud detection directory**:
```bash
cd fraud_detection
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env and add your Google API key
```

5. **Start infrastructure** (PostgreSQL, Redpanda, Redis):
```bash
docker-compose up -d
```

6. **Wait for services to be healthy**:
```bash
docker-compose ps
```

### Running the System

#### Option 1: Web Demo (Recommended for First-Time Users)

Start the interactive web demo:
```bash
python demo_app.py
```

Then open http://localhost:8000 in your browser to:
- See the agent architecture
- Test transactions through the workflow
- View real-time agent decisions

#### Option 2: Real-time Streaming Mode

**Terminal 1** - Start the fraud detection system:
```bash
python -m fraud_detection.main
```

**Terminal 2** - Generate mock transactions:
```bash
python -m fraud_detection.streaming.producer
```

Watch as transactions flow through all three agents in real-time!

## 📊 Demo Features

### Web Interface (http://localhost:8000)

- **Interactive Dashboard**: See all three agents in action
- **Transaction Testing**: Submit test transactions with different risk levels
- **Real-time Analysis**: Watch agents collaborate to detect fraud
- **Visual Results**: Clear display of each agent's decision

### Real-time Streaming

- **Continuous Monitoring**: 24/7 transaction surveillance
- **Automatic Fraud Detection**: No human intervention needed
- **Scalable Architecture**: Handle thousands of transactions per second

## 🔧 Configuration

Edit `.env` file to customize:

```env
# Google AI
GOOGLE_API_KEY=your-api-key-here

# Fraud Detection Thresholds
SUSPICIOUS_AMOUNT_THRESHOLD=5000.00
VELOCITY_CHECK_WINDOW_SECONDS=300
MAX_TRANSACTIONS_PER_WINDOW=10

# Agent Models
TRANSACTION_MONITOR_MODEL=gemini-2.0-flash-exp
INVESTIGATOR_MODEL=gemini-2.0-flash-exp
REMEDIATION_MODEL=gemini-2.0-flash-exp
```

## 📈 Viewing Results

### Redpanda Console

Monitor Kafka topics in real-time:
```bash
# Open http://localhost:8080
```

View:
- Transaction stream
- Fraud alerts
- Topic throughput

### Database

Connect to PostgreSQL to view:
```bash
docker exec -it fraud_detection_postgres psql -U fraud_user -d fraud_detection
```

Query examples:
```sql
-- View all fraud alerts
SELECT * FROM fraud_alerts ORDER BY created_at DESC LIMIT 10;

-- View user risk scores
SELECT user_id, name, risk_score, account_status FROM users;

-- View recent transactions
SELECT * FROM user_transactions ORDER BY created_at DESC LIMIT 10;
```

## 🧪 Testing Fraud Patterns

The system can detect various fraud patterns:

1. **High Velocity** - Multiple transactions in short time
2. **Unusual Amount** - Transactions much higher than user average
3. **Geographic Anomaly** - Transactions from new/unusual locations
4. **New Device** - Transactions from unrecognized devices
5. **Round Amounts** - Suspiciously round transaction amounts

### Test via Web Interface

Use the demo at http://localhost:8000 and try:
- Amount: $15,000 → Unusual amount pattern
- User: user_001 with multiple quick submissions → Velocity pattern

### Test via API

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test_123",
    "user_id": "user_001",
    "amount": 15000.00,
    "merchant": "Suspicious Store",
    "category": "electronics",
    "location": "Unknown City, XX"
  }'
```

## 🏛️ Project Structure

```
fraud_detection/
├── agents/
│   ├── transaction_monitor.py  # Agent 1: Monitor
│   ├── investigator.py         # Agent 2: Investigator
│   └── remediation.py          # Agent 3: Remediation
├── workflows/
│   └── orchestrator.py         # LangGraph workflow
├── streaming/
│   ├── producer.py             # Kafka producer
│   └── consumer.py             # Kafka consumer
├── database/
│   ├── models.py               # SQLAlchemy & Pydantic models
│   └── schema.sql              # Database schema
├── tools/
│   ├── fraud_patterns.py       # Fraud detection tools
│   └── notification.py         # Remediation tools
├── config/
│   └── settings.py             # Configuration
├── main.py                     # CLI entry point
├── demo_app.py                 # Web demo
├── docker-compose.yml          # Infrastructure
└── requirements.txt            # Dependencies
```

## 🎯 Key Concepts Demonstrated

### 1. Agent Specialization
Each agent has a **single, well-defined purpose**. This makes them:
- More reliable
- Easier to test
- Simpler to improve

### 2. Agent-to-Agent Communication
Agents pass structured data between each other:
```python
TransactionData → Monitor → FraudAssessment
FraudAssessment → Investigator → InvestigationResult
InvestigationResult → Remediation → RemediationAction
```

### 3. Stateful Workflow (LangGraph)
The workflow maintains state across agent interactions:
- Tracks which agents have processed the transaction
- Routes to appropriate next agent based on decisions
- Preserves all intermediate results

### 4. Tool Usage
Agents use tools to interact with external systems:
- Database queries (user history)
- Pattern detection (fraud rules)
- Actions (lock account, send alert)

## 🔒 Security & Compliance

- **Audit Trail**: All actions logged to database
- **Explainable AI**: Each decision includes reasoning
- **Human Review**: Alerts can be reviewed before final action
- **Privacy**: Sensitive data handled according to best practices

## 🚀 Production Considerations

To make this production-ready:

1. **Add Authentication**: Secure API endpoints
2. **Scale Kafka**: Use managed Kafka (Confluent Cloud)
3. **Database Replication**: Set up PostgreSQL replicas
4. **Monitoring**: Add Prometheus/Grafana
5. **Rate Limiting**: Protect API from abuse
6. **Error Recovery**: Implement retry logic and circuit breakers
7. **Load Balancing**: Deploy multiple instances

## 📚 Learn More

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [Redpanda Documentation](https://docs.redpanda.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🤝 Contributing

This is a demo project showcasing multi-agent architecture. Feel free to:
- Add more fraud patterns
- Improve agent prompts
- Add new agents (e.g., Appeals Agent)
- Enhance the UI

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🎉 Acknowledgments

Built with:
- Google ADK (Agentic Development Kit)
- LangGraph for orchestration
- Redpanda for streaming
- PostgreSQL for persistence
- Love for AI agents ❤️

---

**Ready to see agents in action?** Run `python demo_app.py` and visit http://localhost:8000!
