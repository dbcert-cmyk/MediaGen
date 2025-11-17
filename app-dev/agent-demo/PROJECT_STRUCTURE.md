# Project Structure

## Complete File Tree

```
agent-demo/
├── README.md                   # Main documentation
├── QUICKSTART.md              # 5-minute setup guide
├── PROJECT_STRUCTURE.md       # This file
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
│
├── app.py                    # Flask backend + WebSocket (360 lines)
├── agent_service.py          # Google Agent Kit integration (270 lines)
├── setup_data.py             # Sample data generator (300 lines)
│
├── mcp_servers/              # MCP Protocol Servers
│   ├── __init__.py          # Package init
│   ├── database_server.py   # SQLite MCP server (350 lines)
│   ├── filesystem_server.py # File search MCP server (290 lines)
│   └── api_server.py        # Mock API MCP server (280 lines)
│
├── templates/                # HTML templates
│   └── index.html           # Main dashboard (200 lines)
│
├── static/                   # Frontend assets
│   ├── styles.css           # Styling (400 lines)
│   ├── service-map.js       # SVG visualization (300 lines)
│   └── dashboard.js         # Main UI logic (280 lines)
│
└── data/                     # Runtime data (created by setup_data.py)
    ├── demo.db              # SQLite database
    └── sample_files/        # Sample JSON/CSV files
        ├── sensor_data.json
        ├── user_analytics.json
        ├── api_logs.json
        ├── sales_report.csv
        └── server_logs.csv
```

## Total Lines of Code: ~2,800

## Architecture Overview

### Backend (Python)

**app.py** - Flask Application
- HTTP endpoints for REST API
- WebSocket server for real-time updates
- Coordinates between frontend and agent

**agent_service.py** - Agent Orchestrator
- Initializes Google Gemini with function calling
- Registers MCP server tools
- Processes natural language queries
- Tracks activity logs

**MCP Servers** (3 servers)
- Each exposes 5+ tools to the agent
- Database: Query, schema, statistics
- Filesystem: Search, read, list files
- API: Weather, stocks, sensors (mock)

### Frontend (JavaScript)

**dashboard.js** - Main Controller
- WebSocket client
- Handles user input
- Updates statistics
- Manages activity log

**service-map.js** - Visualization
- SVG-based service architecture map
- Animated connections
- Real-time status updates
- Flowing particle effects

**styles.css** - Modern UI
- Gradient backgrounds
- Card-based layout
- Responsive design
- Smooth animations

### Data Layer

**SQLite Database**
- 4 tables: customers, products, orders, analytics_events
- 670+ total records
- E-commerce themed data

**Sample Files**
- JSON: Sensor data, analytics, API logs
- CSV: Sales reports, server logs
- Total: ~700 records across files

## Data Flow

```
User Input (Dashboard)
    ↓
WebSocket Connection
    ↓
Flask Backend (app.py)
    ↓
Agent Service (agent_service.py)
    ↓
Google Gemini (Function Calling)
    ↓
MCP Servers (database/filesystem/api)
    ↓
Data Sources (SQLite/Files/Mock API)
    ↓
Results back through chain
    ↓
Dashboard (Real-time visualization)
```

## Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend Framework** | Flask | Web server & API |
| **Real-time** | Flask-SocketIO | WebSocket communication |
| **Agent** | Google Gemini 2.0 Flash | AI orchestration |
| **Protocol** | MCP (Model Context Protocol) | Tool integration |
| **Database** | SQLite | Local data storage |
| **Frontend** | Vanilla JavaScript | No framework dependencies |
| **Visualization** | SVG | Animated service map |
| **Styling** | CSS3 | Modern gradients & animations |

## File Sizes

- **Python code**: ~1,500 lines
- **JavaScript code**: ~580 lines
- **HTML**: ~200 lines
- **CSS**: ~400 lines
- **Documentation**: ~500 lines

## Scalability Path

### Current (Local/Free)
- SQLite database
- Local file system
- Mock APIs
- Single server

### Future (GCP Production)
- Cloud SQL / Firestore
- Cloud Storage
- Real APIs (BigQuery, etc.)
- Load balanced
- Auto-scaling

### Migration Effort
- **Low**: Just change MCP server backends
- **Agent code**: No changes needed
- **Frontend**: No changes needed
- **Time estimate**: 2-4 hours

## Development Time Breakdown

- **Project structure & setup**: 1 hour
- **MCP servers**: 3 hours
- **Agent integration**: 2 hours
- **Backend (Flask)**: 2 hours
- **Frontend (UI)**: 3 hours
- **Visualization**: 2 hours
- **Sample data**: 1 hour
- **Documentation**: 2 hours
- **Total**: ~16 hours (2 days)

## API Endpoints

### REST API
- `GET /` - Dashboard UI
- `GET /health` - Health check
- `GET /api/tools` - List available tools
- `POST /api/query` - Execute query (sync)

### WebSocket Events
- `connect` - Client connection
- `disconnect` - Client disconnection
- `query` - Submit query
- `query_started` - Query processing started
- `progress` - Real-time progress updates
- `query_complete` - Query finished successfully
- `query_error` - Query failed
- `demo_scenario` - Run demo scenario

## MCP Tools Available

### Database Server (5 tools)
1. `query_database` - Execute SELECT queries
2. `get_table_schema` - Get table structure
3. `list_tables` - List all tables
4. `get_statistics` - Database statistics
5. `insert_record` - Insert new records

### Filesystem Server (5 tools)
1. `list_files` - List files with pattern
2. `read_file` - Read file contents
3. `search_files` - Search by filename
4. `get_file_info` - File metadata
5. `count_json_records` - Count JSON records

### API Server (5 tools)
1. `get_weather` - Mock weather data
2. `get_stock_price` - Mock stock prices
3. `get_sensor_reading` - Mock IoT sensors
4. `search_products` - Mock product catalog
5. `get_exchange_rate` - Mock currency rates

**Total: 15 tools** across 3 servers

## Security Considerations

### Current (Demo)
- ✅ SQL injection protection (SELECT only)
- ✅ File path validation
- ✅ No secrets in code
- ✅ Environment variables for API keys
- ⚠️ No authentication (demo only)
- ⚠️ No rate limiting

### Production Requirements
- Add user authentication (JWT/OAuth)
- Implement rate limiting
- Add HTTPS/SSL
- Sanitize all inputs
- Add CORS restrictions
- Audit logging
- Database backup strategy

## Browser Compatibility

- ✅ Chrome/Edge (Chromium) - Full support
- ✅ Firefox - Full support
- ✅ Safari - Full support
- ⚠️ IE11 - Not supported (uses modern JS)

## Performance

### Expected Response Times
- Simple query (1 tool): 1-2 seconds
- Complex query (3+ tools): 3-5 seconds
- Database query: <500ms
- File read: <200ms
- Mock API call: <100ms

### Optimization Opportunities
- Cache frequently accessed data
- Parallel tool execution
- Database indexing
- Connection pooling
- Client-side caching

## Extensibility

### Adding New MCP Server

1. Create new file in `mcp_servers/`
2. Define tools with `@server.list_tools()`
3. Implement handlers with `@server.call_tool()`
4. Register in `agent_service.py`
5. Update service map in `service-map.js`

**Time estimate**: 1-2 hours per server

### Adding New Tool to Existing Server

1. Add tool definition
2. Add handler implementation
3. Test independently

**Time estimate**: 30 minutes per tool

## Testing Strategy

### Manual Testing
- Test each MCP server independently
- Test agent with each tool
- Test WebSocket connection
- Test UI interactions
- Test error handling

### Automated Testing (Future)
- Unit tests for MCP servers
- Integration tests for agent
- E2E tests for workflows
- Performance benchmarks

## Deployment Options

### Local Development
```bash
python app.py
```

### Production (Docker)
```dockerfile
FROM python:3.10
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

### Cloud Run / App Engine
- Package as container
- Set environment variables
- Deploy to GCP
- Configure scaling

## Cost Estimate (GCP Production)

### Google AI (Gemini)
- Free tier: 1,500 requests/day
- Paid: $0.00025 per 1K characters
- Expected: $5-20/month

### Cloud SQL
- db-f1-micro: $7/month
- db-g1-small: $25/month

### Cloud Storage
- $0.02 per GB/month
- Expected: <$1/month

### Cloud Run
- Free tier: 2M requests/month
- Expected: Free or <$5/month

**Total: $0-50/month** depending on usage

---

**Questions? Check README.md or QUICKSTART.md**
