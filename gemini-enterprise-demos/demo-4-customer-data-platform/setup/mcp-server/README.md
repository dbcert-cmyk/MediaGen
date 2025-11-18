# Multi-Database MCP Server
## Unified access layer for Gemini Enterprise Customer Data Platform

This MCP (Model Context Protocol) server provides a unified API for accessing customer data across multiple Google Cloud databases:
- **BigQuery** - Analytics and transaction history
- **AlloyDB** - Operational customer database
- **Firestore** - Real-time activity and sessions
- **Cloud Storage** - Documents and media files

---

## Features

- ✅ Unified query interface across 4 databases
- ✅ Customer 360 view aggregation
- ✅ Parallel query execution for performance
- ✅ RESTful API + MCP tool definitions
- ✅ Connection pooling for AlloyDB
- ✅ Error handling and logging
- ✅ Graceful shutdown

---

## Prerequisites

- Node.js 18+
- Google Cloud Project with:
  - BigQuery dataset: `customer_analytics`
  - AlloyDB cluster running
  - Firestore database
  - Cloud Storage buckets
- Service account with permissions:
  - `roles/bigquery.dataViewer`
  - `roles/cloudsql.client`
  - `roles/datastore.user`
  - `roles/storage.objectViewer`

---

## Installation

```bash
# Install dependencies
npm install

# Or if using the parent demo repo
cd gemini-enterprise-demos/demo-4-customer-data-platform/setup/mcp-server
npm install
```

---

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required
PROJECT_ID=your-gcp-project-id
ALLOYDB_HOST=10.x.x.x  # AlloyDB private IP
ALLOYDB_PASSWORD=your-alloydb-password

# Optional
PORT=3100
LOG_LEVEL=info
```

### Service Account

```bash
# Set up application default credentials
gcloud auth application-default login

# Or use a service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

---

## Usage

### Start the Server

```bash
# Production
npm start

# Development (with auto-reload)
npm run dev

# With environment variables inline
PROJECT_ID=my-project ALLOYDB_HOST=10.0.0.5 npm start
```

Server will start on port 3100 (configurable via PORT env var).

---

## API Endpoints

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T10:00:00.000Z"
}
```

### Execute Database Query

```bash
POST /query
Content-Type: application/json

{
  "database": "bigquery|alloydb|firestore|storage",
  "query": "SELECT * FROM ...",  // For BigQuery/AlloyDB
  "collection": "collection_name",  // For Firestore
  "limit": 100
}
```

**Examples:**

**BigQuery:**
```bash
curl -X POST http://localhost:3100/query \
  -H "Content-Type: application/json" \
  -d '{
    "database": "bigquery",
    "query": "SELECT * FROM customer_analytics.customers LIMIT 10"
  }'
```

**AlloyDB:**
```bash
curl -X POST http://localhost:3100/query \
  -H "Content-Type: application/json" \
  -d '{
    "database": "alloydb",
    "query": "SELECT * FROM customer_profiles WHERE account_tier = '\''Enterprise'\''"
  }'
```

**Firestore:**
```bash
curl -X POST http://localhost:3100/query \
  -H "Content-Type: application/json" \
  -d '{
    "database": "firestore",
    "collection": "customer_sessions",
    "limit": 10
  }'
```

### Customer 360 View

```bash
POST /customer360
Content-Type: application/json

{
  "customerId": "CUST-001"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "customerId": "CUST-001",
    "timestamp": "2025-11-18T10:00:00.000Z",
    "profile": {
      "company_name": "Acme Corporation",
      "primary_contact_email": "john.smith@acmecorp.com",
      ...
    },
    "analytics": {
      "lifetime_value_usd": 485000,
      "total_transactions": 147,
      "churn_risk_score": 0.12,
      ...
    },
    "transactions": {
      "recent": [...],
      "total_count": 147
    },
    "realtime_activity": {
      "recent_sessions": [...],
      "last_active": "2025-11-17T22:30:00Z"
    },
    "support": {
      "open_tickets": [...],
      "ticket_count": 2
    },
    "documents": {
      "files": [...],
      "total_count": 15
    },
    "health_metrics": {
      "churn_risk": 0.12,
      "health_score": 92,
      "lifetime_value": 485000
    }
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:3100/customer360 \
  -H "Content-Type: application/json" \
  -d '{"customerId": "CUST-001"}'
```

### Aggregate Queries

Execute multiple queries across databases in parallel:

```bash
POST /aggregate
Content-Type: application/json

{
  "queries": {
    "customers": {
      "database": "bigquery",
      "query": "SELECT COUNT(*) as total FROM customer_analytics.customers"
    },
    "active_sessions": {
      "database": "firestore",
      "collection": "customer_sessions"
    },
    "profiles": {
      "database": "alloydb",
      "query": "SELECT account_tier, COUNT(*) as count FROM customer_profiles GROUP BY account_tier"
    }
  }
}
```

---

## MCP Tool Definitions

For integration with Gemini Enterprise, the server exposes these MCP tools:

### 1. query_customer_data

```json
{
  "name": "query_customer_data",
  "description": "Query customer data across all databases",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customerId": { "type": "string" },
      "includeTransactions": { "type": "boolean" },
      "includeActivity": { "type": "boolean" }
    },
    "required": ["customerId"]
  }
}
```

### 2. analyze_customer_behavior

```json
{
  "name": "analyze_customer_behavior",
  "description": "Analyze customer behavior patterns",
  "inputSchema": {
    "type": "object",
    "properties": {
      "customerId": { "type": "string" },
      "timeframe": { "type": "string", "enum": ["30d", "90d", "1y"] }
    },
    "required": ["customerId"]
  }
}
```

### 3. segment_customers

```json
{
  "name": "segment_customers",
  "description": "Segment customers by criteria",
  "inputSchema": {
    "type": "object",
    "properties": {
      "criteria": { "type": "object" },
      "limit": { "type": "number" }
    },
    "required": ["criteria"]
  }
}
```

---

## Performance Considerations

### Connection Pooling

AlloyDB uses connection pooling (max 20 connections) for optimal performance:

```javascript
max: 20,
idleTimeoutMillis: 30000,
connectionTimeoutMillis: 2000,
```

### Parallel Execution

Customer 360 queries execute in parallel for ~5x speedup:

```javascript
const [profile, analytics, transactions, ...] = await Promise.all([
  this.getCustomerProfile(customerId),
  this.getCustomerAnalytics(customerId),
  ...
]);
```

### Query Optimization

- BigQuery: Uses parameterized queries
- AlloyDB: Connection pooling + prepared statements
- Firestore: Indexed queries with limits
- Cloud Storage: Prefix filtering for faster lookups

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": "Error message details"
}
```

HTTP status codes:
- `200` - Success
- `400` - Bad request (invalid parameters)
- `500` - Server error (database connection, query errors)

---

## Monitoring & Logging

### Logs

Server logs to console with timestamps:

```
2025-11-18T10:00:00.000Z [INFO] Multi-Database MCP Server running on port 3100
2025-11-18T10:00:01.000Z [INFO] Customer 360 query for CUST-001 completed in 342ms
2025-11-18T10:00:02.000Z [ERROR] BigQuery query failed: Table not found
```

### Health Monitoring

Use the `/health` endpoint for liveness/readiness probes:

```bash
# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 3100
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## Deployment

### Local Development

```bash
npm run dev
```

### Production (Docker)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3100
CMD ["npm", "start"]
```

Build and run:
```bash
docker build -t mcp-server .
docker run -p 3100:3100 \
  -e PROJECT_ID=my-project \
  -e ALLOYDB_HOST=10.0.0.5 \
  -e ALLOYDB_PASSWORD=secret \
  mcp-server
```

### Cloud Run

```bash
gcloud run deploy mcp-server \
  --source . \
  --region us-central1 \
  --set-env-vars PROJECT_ID=my-project,ALLOYDB_HOST=10.0.0.5 \
  --set-secrets ALLOYDB_PASSWORD=alloydb-password:latest
```

---

## Testing

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:3100/health

# Test BigQuery
curl -X POST http://localhost:3100/query \
  -H "Content-Type: application/json" \
  -d '{"database": "bigquery", "query": "SELECT 1"}'

# Test Customer 360
curl -X POST http://localhost:3100/customer360 \
  -H "Content-Type: application/json" \
  -d '{"customerId": "CUST-001"}'
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test 1000 requests with 10 concurrent
ab -n 1000 -c 10 -p customer360.json \
  -T application/json \
  http://localhost:3100/customer360
```

---

## Troubleshooting

### AlloyDB Connection Fails

```
Error: connect ETIMEDOUT
```

**Solution:**
- Check AlloyDB private IP is correct
- Ensure server is running in same VPC as AlloyDB
- Verify firewall rules allow port 5432
- Check AlloyDB password is correct

```bash
# Test connection manually
psql "host=$ALLOYDB_HOST user=postgres dbname=postgres"
```

### BigQuery Permission Denied

```
Error: User does not have permission to query table
```

**Solution:**
```bash
# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

### Firestore Index Missing

```
Error: The query requires an index
```

**Solution:**
```bash
# Create composite index
gcloud firestore indexes composite create \
  --collection-group=customer_sessions \
  --query-scope=COLLECTION \
  --field-config field-path=customer_id,order=ASCENDING \
  --field-config field-path=timestamp,order=DESCENDING
```

---

## Security Best Practices

1. **Never commit credentials** - Use environment variables or Secret Manager
2. **Use least privilege** - Grant minimum required IAM roles
3. **Enable VPC Service Controls** - For additional data protection
4. **Rotate credentials** - Regularly rotate AlloyDB password
5. **Use Cloud Armor** - If exposing publicly, add DDoS protection
6. **Enable audit logging** - Track all data access

---

## License

Apache 2.0 - See LICENSE file

---

## Support

For issues and questions:
- Open an issue in the main demo repository
- Consult the [Demo #4 Setup Guide](../01-PREREQUISITES.md)
- Review [Gemini Enterprise Docs](https://cloud.google.com/gemini/enterprise/docs)

---

**Last Updated:** November 2025
**Version:** 1.0.0
