# 🔍 SPO Analytics Agent

**Conversational Supply Path Optimization Analytics powered by Gemini Enterprise**

A proof-of-concept demonstration showcasing how Google Cloud's Generative AI can transform natural language queries into actionable programmatic advertising insights, enabling self-service root cause analysis for SPO partners.

---

## 🎯 Overview

The SPO Analytics Agent solves a critical pain point in programmatic advertising: **supply path transparency and technical support friction**. Instead of waiting for manual analysis, partners can ask natural language questions and get instant, data-driven insights.

### Key Capabilities

- 🗣️ **Natural Language to SQL**: Convert complex questions into optimized BigQuery SQL
- 📊 **Conversational RCA**: Transform raw data into narrative root cause analysis
- 💰 **Fee Transparency**: Analyze markups, exchange fees, and revenue splits
- 🛡️ **Traffic Quality**: Understand IVT blocks, filtering, and performance drops
- ⚡ **Self-Service Analytics**: Reduce dependency on technical support teams

---

## 🏗️ Architecture

```
┌─────────────────┐
│   User Query    │
│  (Natural Lang) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Flask App API  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│ Gemini Enterprise│◄────►│  BigQuery Data   │
│  (Vertex AI)    │      │  (Mock/Prod)     │
│                 │      └──────────────────┘
│ 1. NLQ→SQL      │
│ 2. Synthesis    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Conversational  │
│   Response      │
└─────────────────┘
```

### Component Stack

| Component | Purpose |
|-----------|---------|
| **Vertex AI (Gemini)** | Core reasoning engine for NLQ-to-SQL and narrative synthesis |
| **BigQuery** | Scalable data warehouse for programmatic logs (100M-500M rows) |
| **Flask** | Lightweight API and web interface |
| **Python** | Application logic and orchestration |

---

## 📋 Prerequisites

### For Mock Mode (Testing - No GCP Required)
- Python 3.8+
- No GCP account needed
- Perfect for UI testing and demos

### For Production Mode (Real AI)
- Python 3.8+
- Google Cloud Platform account
- Vertex AI API enabled
- BigQuery API enabled
- Appropriate IAM permissions

**💡 New to GCP?** Get [$300 in free credits](https://cloud.google.com/free) for 90 days!

---

## 🚀 Quick Start

### Option 1: Mock Mode (No GCP, Instant Testing)

```bash
# 1. Navigate to the project directory
cd spo-analytics-agent

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and ensure MOCK_MODE=true

# 5. Run the application
python app.py

# 6. Open your browser
# Navigate to: http://localhost:5001
```

### Option 2: Production Mode (Real Vertex AI & BigQuery)

```bash
# 1. Set up GCP authentication
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com

# 3. Install dependencies
cd spo-analytics-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings:
#   MOCK_MODE=false
#   GCP_PROJECT_ID=your-actual-project-id
#   GCP_LOCATION=us-central1
#   BIGQUERY_DATASET=spo_analytics

# 5. Create BigQuery dataset and tables
python -c "from bigquery_service import BigQueryService; BigQueryService().create_all_tables()"

# 6. Generate mock data (see Data Generation section below)
python data_generator.py --rows 1000000

# 7. Run the application
python app.py

# 8. Open your browser
# Navigate to: http://localhost:5001
```

---

## 📊 Data Schema

The POC uses three core tables to enable full SPO analytics:

### 1. `impression_log_mock`
Bid request and impression data
- **Key Fields**: impression_id, timestamp, publisher_id, inventory_type, country_geo, bid_request_count, bid_response_count
- **Use Cases**: Fill rate analysis, volume trends, geo/device breakdowns

### 2. `transaction_log_mock`
Financial transaction and revenue data
- **Key Fields**: impression_id, dsp_id, winning_bid, publisher_net_revenue, exchange_fee, total_markup
- **Use Cases**: Supply path transparency, markup analysis, fee breakdowns

### 3. `filter_log_mock`
Traffic filtering and blocking events
- **Key Fields**: impression_id, filter_category, filter_reason_code, block_timestamp
- **Use Cases**: Root cause analysis, IVT detection, quality insights

---

## 💬 Example Queries

### Fill Rate Analysis
- "What's my fill rate for the last 7 days?"
- "Compare fill rates between CTV and Mobile inventory"
- "Why did my fill rate drop last week?"

### SPO Transparency
- "What's the average markup across all DSPs?"
- "Compare exchange fees for different inventory types"
- "Which DSP has the highest markup?"

### Root Cause Analysis
- "Why is traffic being blocked?"
- "What's the IVT block rate for US traffic?"
- "Show me the top filter categories from last week"

### Revenue & Performance
- "What's my total revenue for the last 30 days?"
- "Show me the top performing inventory types"
- "What's my average winning bid by geo?"

---

## 🛠️ Data Generation

### Generate Mock Data for Testing

The `data_generator.py` script creates realistic programmatic log data:

```bash
# Generate 1M rows (MVP scale)
python data_generator.py --rows 1000000

# Generate 100M rows (full POC scale)
python data_generator.py --rows 100000000

# Generate with specific date range
python data_generator.py --rows 1000000 --days 90
```

**Note**: Large data generation (100M+ rows) can take several hours and will incur BigQuery storage costs.

---

## 🔧 Configuration

### Environment Variables

See `.env.example` for all configuration options. Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `MOCK_MODE` | Enable mock mode (true/false) | `true` |
| `GCP_PROJECT_ID` | Your GCP project ID | - |
| `GEMINI_MODEL` | Model to use | `gemini-2.0-flash-exp` |
| `GEMINI_TEMPERATURE` | SQL generation temperature | `0.2` |
| `BIGQUERY_DATASET` | BigQuery dataset name | `spo_analytics` |

---

## 📡 API Endpoints

### `POST /api/query`
Submit a natural language query

**Request:**
```json
{
  "query": "What's my fill rate for the last 7 days?"
}
```

**Response:**
```json
{
  "success": true,
  "user_query": "What's my fill rate for the last 7 days?",
  "sql_query": "SELECT ...",
  "narrative": "Your average fill rate is 76.3%...",
  "data": [...],
  "metadata": {
    "row_count": 7
  }
}
```

### `GET /api/dataset/stats`
Get dataset statistics

### `POST /api/dataset/create`
Create BigQuery dataset and tables (admin)

### `GET /api/examples`
Get example queries by category

### `GET /health`
Health check endpoint

---

## 🧪 Testing

### Run in Mock Mode
```bash
# Set MOCK_MODE=true in .env
python app.py
```

Mock mode provides:
- Instant responses without GCP
- Simulated data patterns
- Full UI testing
- No costs

### Test with Real Data
1. Ensure dataset is created and populated
2. Set `MOCK_MODE=false` in `.env`
3. Run the app and try example queries

---

## 📈 Scaling Considerations

### MVP (Current)
- **Data Volume**: 1M-10M rows
- **Response Time**: < 5 seconds
- **Cost**: Minimal (free tier friendly)

### Production POC
- **Data Volume**: 100M-500M rows
- **Response Time**: < 8 seconds
- **Cost**: BigQuery queries + Gemini API calls

### Optimization Tips
- Use BigQuery partitioned tables (already configured)
- Enable query result caching
- Implement SQL query validation before execution
- Monitor Gemini token usage

---

## 💰 Cost Estimation

### GCP Costs (Production Mode)
- **BigQuery Storage**: ~$0.02/GB/month
  - 1M rows ≈ 100MB = $0.002/month
  - 100M rows ≈ 10GB = $0.20/month
- **BigQuery Queries**: $5/TB processed
  - Typical query: 100MB = $0.0005
- **Vertex AI (Gemini)**: Pay per request
  - Input tokens: ~$0.00025/1K tokens
  - Output tokens: ~$0.00075/1K tokens
  - Typical query: ~$0.01-0.05

**Free Tier**: BigQuery offers 1TB/month query processing free!

---

## 🔒 Security Best Practices

1. **Never commit credentials**: Use `.env` files (already in `.gitignore`)
2. **Use service accounts**: Create dedicated service accounts with minimal permissions
3. **Enable audit logs**: Monitor all BigQuery and Vertex AI access
4. **Set billing alerts**: Avoid unexpected costs
5. **Rotate API keys**: Regularly rotate service account keys

---

## 📝 Project Structure

```
spo-analytics-agent/
├── app.py                      # Main Flask application
├── spo_agent.py                # Core NLQ-to-SQL agent
├── bigquery_service.py         # BigQuery operations
├── data_generator.py           # Mock data generation
├── config.py                   # Configuration management
├── schemas/
│   └── bigquery_schemas.py     # Table schemas
├── templates/
│   └── index.html              # Web UI
├── static/
│   ├── css/
│   │   └── style.css           # Styles
│   └── js/
│       └── app.js              # Frontend logic
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
└── README.md                   # This file
```

---

## 🚧 Known Limitations (MVP)

- Query complexity limited to single-agent execution
- No query history or session management
- Basic error handling (will improve in production)
- Mock data uses simple patterns (real data more complex)
- No authentication/authorization (add for production)

---

## 🗺️ Roadmap

### Phase 1: MVP ✅ (Current)
- [x] Core NLQ-to-SQL conversion
- [x] Data synthesis engine
- [x] Basic web UI
- [x] Mock mode for testing
- [x] Three core tables

### Phase 2: Enhanced POC
- [ ] Advanced query patterns (multi-table joins)
- [ ] Query result caching
- [ ] Session management
- [ ] Enhanced error handling
- [ ] Query suggestions based on context

### Phase 3: Production Ready
- [ ] Authentication & authorization
- [ ] Multi-tenancy support
- [ ] Advanced visualizations
- [ ] Query history and favorites
- [ ] Performance monitoring
- [ ] Deployment to Cloud Run

---

## 🤝 Contributing

This is a POC project. For improvements or issues, please create a GitHub issue or submit a pull request.

---

## 📚 Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Guide](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## 📄 License

This project is provided as-is for demonstration and educational purposes.

---

## 💡 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the [Vertex AI docs](https://cloud.google.com/vertex-ai/docs)
3. Review the [BigQuery docs](https://cloud.google.com/bigquery/docs)
4. Open an issue in this repository

---

**Built with Google Cloud Vertex AI, BigQuery, and Flask**

*Demonstrating the future of conversational programmatic analytics* 🚀
