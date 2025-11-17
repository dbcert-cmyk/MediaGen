# Quick Start Guide

Get the Agent Data Flow Visualizer running in 5 minutes!

## Step 1: Get Your Google API Key (2 minutes)

1. Open https://aistudio.google.com in your browser
2. Sign in with your Google account
3. Click **"Get API Key"** (top right)
4. Click **"Create API Key"**
5. Copy the key (starts with `AIza...`)

**Free tier includes:**
- 15 requests/minute
- 1,500 requests/day
- Perfect for this demo!

## Step 2: Set Up Environment (1 minute)

```bash
cd /home/user/agent-demo

# Create .env file
cp .env.example .env

# Edit .env and add your API key
nano .env
# Change: GOOGLE_API_KEY=your_api_key_here
# To: GOOGLE_API_KEY=AIza... (your actual key)
# Save and exit: Ctrl+X, Y, Enter
```

## Step 3: Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

## Step 4: Initialize Sample Data (30 seconds)

```bash
python setup_data.py
```

You should see:
```
✓ Created directories
✓ Created tables
✓ Inserted 8 customers
✓ Inserted 12 products
✓ Inserted 150 orders
... etc
```

## Step 5: Run the Application (30 seconds)

```bash
python app.py
```

You should see:
```
✓ Agent service initialized
Server starting on http://localhost:5000
```

## Step 6: Open in Browser

Go to: **http://localhost:5000**

## Try These Queries:

1. **"How many orders are in the database?"**
   - Watch: Agent → MCP Database → SQLite

2. **"List all JSON files"**
   - Watch: Agent → MCP Filesystem → Files

3. **"What's the weather in San Francisco?"**
   - Watch: Agent → MCP API → Mock Weather API

4. **"Find all orders over $100"**
   - Watch: Multi-step query with database operations

## What to Watch:

- **Service Map**: Boxes light up and pulse when active
- **Activity Log**: See each step the agent takes
- **Data Flow**: Animated lines show data moving between services
- **Response**: Agent's natural language response

## Troubleshooting:

**"GOOGLE_API_KEY not found"**
- Make sure you created `.env` and added your API key

**"Module not found"**
- Run: `pip install -r requirements.txt`

**"Database not found"**
- Run: `python setup_data.py`

**Port 5000 already in use**
- Change PORT in `.env` to another port (e.g., 8000)

## Next Steps:

- Try the "Run Demo" button for an automated demo
- Modify sample data in `setup_data.py`
- Add your own MCP servers
- Connect to real GCP services (see README.md)

## Need Help?

Check the full README.md for:
- Architecture details
- GCP migration path
- Custom MCP server creation
- Advanced configuration

---

**Enjoy the demo! 🚀**
