# Agent Data Flow Visualizer

An interactive dashboard that demonstrates Google Agent Development Kit orchestrating data movement across MCP (Model Context Protocol) servers with real-time visual feedback.

## 🎯 What This Demo Shows

- **Google Agent Kit (Gemini)** intelligently routing queries across multiple data sources
- **MCP Servers** exposing different data backends (Database, Filesystem, APIs)
- **Real-time visualization** of data flowing through services
- **Animated service map** showing active connections and processing states

## 🏗️ Architecture

```
User Query → Agent Kit → MCP Servers → Data Sources
                ↓
         Visual Dashboard (animated service map)
```

**Data Sources (all local/free):**
- SQLite database (e-commerce data)
- Local filesystem (sample JSON/CSV files)
- Mock REST API (weather, stocks, sensors)

## 📋 Prerequisites

- Python 3.8+
- Google API Key (Gemini) - **Free tier available**

## 🔑 Getting Your Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **"Get API Key"** in the top right
4. Click **"Create API Key"**
5. Copy the API key (starts with `AIza...`)

**Note:** The free tier includes:
- 15 requests per minute
- 1,500 requests per day
- More than enough for this demo!

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/user/agent-demo
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Google API key
nano .env  # or use your favorite editor
```

Add this line to `.env`:
```
GOOGLE_API_KEY=your_api_key_here
```

### 3. Initialize Sample Data

```bash
python setup_data.py
```

This creates:
- SQLite database with sample e-commerce data (orders, products, customers)
- Sample JSON files (IoT sensor data, user analytics)
- Sample CSV files (sales reports, logs)

### 4. Run the Application

```bash
python app.py
```

Open your browser to: **http://localhost:5000**

## 🎬 Demo Scenarios

Try these queries in the dashboard:

### Basic Queries
- `"How many orders are in the database?"`
- `"Find all JSON files in the data folder"`
- `"What's the weather in San Francisco?"` (mock API)

### Cross-Service Data Flow
- `"Find all orders over $100 and list them"`
- `"Search for sensor data files and tell me how many temperature readings we have"`
- `"Get the stock price for GOOGL"` (mock data)

### Multi-Step Workflows
- `"Find all high-value orders (>$500) and export to a CSV file"`
- `"Search for error logs and count how many errors occurred today"`
- `"Get weather data for New York and save it to the database"`

Watch the service map light up as the agent orchestrates data movement!

## 📊 What You'll See

- **Animated service boxes** that pulse when active
- **Data flow lines** with particles showing direction
- **Activity log** showing each step the agent takes
- **Real-time metrics** (latency, success rate, query count)
- **Color-coded status** (green=success, blue=processing, red=error)

## 🔧 Project Structure

```
agent-demo/
├── app.py                      # Flask backend + WebSocket
├── agent_service.py            # Google Agent Kit integration
├── setup_data.py               # Creates sample data
├── mcp_servers/
│   ├── __init__.py
│   ├── database_server.py      # SQLite MCP server
│   ├── filesystem_server.py    # File search MCP server
│   └── api_server.py           # Mock API MCP server
├── data/
│   ├── demo.db                 # SQLite database
│   └── sample_files/           # Sample JSON/CSV files
├── static/
│   ├── dashboard.js            # Frontend logic
│   ├── service-map.js          # Animated visualization
│   └── styles.css              # Styling
├── templates/
│   └── index.html              # Dashboard UI
├── requirements.txt
├── .env.example
└── README.md
```

## 🎨 Customization

### Add Your Own Data Source

Create a new MCP server in `mcp_servers/`:

```python
# mcp_servers/my_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-data-source")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="fetch_data",
            description="Fetch data from my source",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "fetch_data":
        # Your logic here
        return [TextContent(type="text", text="Result")]
```

Then add it to `app.py` and update the service map in `static/service-map.js`.

## 🔄 Migration to GCP (Future)

This demo uses local/free tools, but can easily migrate to GCP:

| Current (Local) | Future (GCP) | Effort |
|----------------|--------------|--------|
| SQLite | Cloud SQL / Firestore | Low |
| Local files | Cloud Storage | Low |
| Mock API | BigQuery / Real APIs | Medium |

The agent code and dashboard remain the same - just update MCP server backends!

## 🐛 Troubleshooting

**Issue:** "Invalid API key"
- Make sure your `.env` file has the correct `GOOGLE_API_KEY`
- Verify the key works at https://aistudio.google.com

**Issue:** "Module not found"
- Run `pip install -r requirements.txt` again
- Check you're in the correct directory

**Issue:** WebSocket connection failed
- Check if port 5000 is available
- Try `python app.py` and look for error messages

## 📚 Learn More

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Google AI Studio](https://aistudio.google.com)
- [Google GenAI SDK Docs](https://ai.google.dev/gemini-api/docs)

## 🎉 What's Next?

After running this demo, you can:
1. Add more MCP servers (Redis, MongoDB, etc.)
2. Connect to real GCP services
3. Implement custom workflows
4. Add authentication and multi-user support
5. Deploy to production

---

**Built with:** Flask, Google Gemini 2.0 Flash, MCP Protocol, SQLite, Vanilla JS, SVG

**License:** MIT
