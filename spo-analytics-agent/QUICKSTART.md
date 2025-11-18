# 🚀 Quick Start Guide - SPO Analytics Agent

Get started with the SPO Analytics Agent in under 5 minutes!

## ⚡ Fastest Start (Mock Mode - No GCP)

Perfect for testing the UI and functionality without any GCP setup.

```bash
# 1. Navigate to the project
cd spo-analytics-agent

# 2. Install dependencies
pip install flask python-dotenv

# 3. Verify the .env file has MOCK_MODE=true
cat .env | grep MOCK_MODE
# Should show: MOCK_MODE=true

# 4. Run tests (optional but recommended)
python test_app.py

# 5. Start the application
python app.py

# 6. Open your browser to:
http://localhost:5001
```

That's it! You now have a working SPO Analytics Agent in mock mode.

## 📊 Try These Queries

Once the app is running, try asking:

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

## 🔧 Production Mode (Real GCP)

To use real Vertex AI and BigQuery:

```bash
# 1. Set up GCP authentication
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable required APIs
gcloud services enable aiplatform.googleapis.com bigquery.googleapis.com

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Update .env file
# Change MOCK_MODE=false
# Add GCP_PROJECT_ID=your-project-id

# 5. Create BigQuery tables
python -c "from bigquery_service import BigQueryService; BigQueryService().create_all_tables()"

# 6. Generate mock data (start with 100K rows for testing)
python data_generator.py --rows 100000

# 7. Start the application
python app.py
```

## 🧪 Testing

Run the test suite to verify everything works:

```bash
python test_app.py
```

Expected output:
```
🎉 All tests passed! The SPO Analytics Agent is ready to use.
```

## 📡 API Usage

### Query Endpoint

```bash
curl -X POST http://localhost:5001/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my fill rate for the last 7 days?"}'
```

### Health Check

```bash
curl http://localhost:5001/health
```

### Get Examples

```bash
curl http://localhost:5001/api/examples
```

## 🐛 Troubleshooting

### "Module not found" errors
```bash
pip install flask python-dotenv
```

### Port already in use
Edit `.env` and change `PORT=5001` to another port like `PORT=5002`

### Cannot connect to BigQuery (Production mode)
- Verify `gcloud auth application-default login` was run
- Check that your GCP project ID is correct in `.env`
- Ensure BigQuery API is enabled

## 📚 Next Steps

- Read the [full README](README.md) for detailed documentation
- Review the [TRD](../TRD.md) to understand the architecture
- Explore the code in `spo_agent.py` to see how NLQ-to-SQL works
- Generate larger datasets with `data_generator.py`

## 🎯 Project Structure Overview

```
spo-analytics-agent/
├── app.py                 # Flask web application
├── spo_agent.py           # Core NLQ-to-SQL agent
├── bigquery_service.py    # BigQuery operations
├── data_generator.py      # Mock data generation
├── test_app.py            # Test suite
├── templates/index.html   # Web UI
└── static/                # CSS and JavaScript
```

## 💡 Tips

- **Mock Mode** is great for UI testing and demos
- **Production Mode** shows the real power of Gemini + BigQuery
- Start with small datasets (100K-1M rows) before scaling to 100M+
- The agent learns from your schema - more complex schemas = more capabilities
- Check logs for debugging: `LOG_LEVEL=DEBUG` in `.env`

---

**Need help?** Check the main [README](README.md) or review the code comments.

**Ready to deploy?** See the deployment guide in the README.
