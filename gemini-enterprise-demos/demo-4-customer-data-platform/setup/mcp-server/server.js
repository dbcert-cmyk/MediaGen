/**
 * MCP Multi-Database Server
 * Provides unified access to BigQuery, AlloyDB, Firestore, and Cloud Storage
 * Part of Gemini Enterprise Demo #4
 */

const { MCPServer } = require('@modelcontextprotocol/sdk');
const { BigQuery } = require('@google-cloud/bigquery');
const { Firestore } = require('@google-cloud/firestore');
const { Storage } = require('@google-cloud/storage');
const { Pool } = require('pg');
const express = require('express');

class MultiDatabaseMCPServer {
  constructor(projectId) {
    this.projectId = projectId;

    // Initialize clients
    this.bigquery = new BigQuery({ projectId });
    this.firestore = new Firestore({ projectId });
    this.storage = new Storage({ projectId });

    // AlloyDB connection pool (PostgreSQL)
    this.alloydbPool = new Pool({
      host: process.env.ALLOYDB_HOST,
      port: 5432,
      database: 'postgres',
      user: 'postgres',
      password: process.env.ALLOYDB_PASSWORD,
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    // Initialize Express server
    this.app = express();
    this.app.use(express.json());

    this.setupRoutes();
    this.setupMCPTools();
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ status: 'healthy', timestamp: new Date().toISOString() });
    });

    // Unified query endpoint
    this.app.post('/query', async (req, res) => {
      try {
        const { database, query, collection, limit } = req.body;

        let result;
        switch (database) {
          case 'bigquery':
            result = await this.queryBigQuery(query);
            break;
          case 'alloydb':
            result = await this.queryAlloyDB(query);
            break;
          case 'firestore':
            result = await this.queryFirestore(collection, limit);
            break;
          case 'storage':
            result = await this.listStorageFiles(query);
            break;
          default:
            throw new Error(`Unknown database: ${database}`);
        }

        res.json({ success: true, data: result });
      } catch (error) {
        console.error('Query error:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Customer 360 view endpoint
    this.app.post('/customer360', async (req, res) => {
      try {
        const { customerId } = req.body;
        const customerView = await this.getCustomer360(customerId);
        res.json({ success: true, data: customerView });
      } catch (error) {
        console.error('Customer 360 error:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Aggregate query across databases
    this.app.post('/aggregate', async (req, res) => {
      try {
        const { queries } = req.body;
        const results = await this.executeAggregateQueries(queries);
        res.json({ success: true, data: results });
      } catch (error) {
        console.error('Aggregate query error:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });
  }

  setupMCPTools() {
    // Define MCP tools for Gemini Enterprise integration
    this.mcpTools = [
      {
        name: 'query_customer_data',
        description: 'Query customer data across all databases',
        inputSchema: {
          type: 'object',
          properties: {
            customerId: { type: 'string', description: 'Customer ID' },
            includeTransactions: { type: 'boolean', description: 'Include transaction history' },
            includeActivity: { type: 'boolean', description: 'Include recent activity' },
          },
          required: ['customerId']
        }
      },
      {
        name: 'analyze_customer_behavior',
        description: 'Analyze customer behavior patterns',
        inputSchema: {
          type: 'object',
          properties: {
            customerId: { type: 'string', description: 'Customer ID' },
            timeframe: { type: 'string', description: 'Analysis timeframe (30d, 90d, 1y)' }
          },
          required: ['customerId']
        }
      },
      {
        name: 'segment_customers',
        description: 'Segment customers by criteria',
        inputSchema: {
          type: 'object',
          properties: {
            criteria: { type: 'object', description: 'Segmentation criteria' },
            limit: { type: 'number', description: 'Max results to return' }
          },
          required: ['criteria']
        }
      }
    ];
  }

  // BigQuery operations
  async queryBigQuery(query) {
    const [job] = await this.bigquery.createQueryJob({
      query: query,
      location: 'US',
    });

    const [rows] = await job.getQueryResults();
    return rows;
  }

  async getCustomerTransactions(customerId) {
    const query = `
      SELECT
        transaction_id,
        transaction_date,
        amount_usd,
        product_id,
        transaction_type
      FROM \`${this.projectId}.customer_analytics.transactions\`
      WHERE customer_id = @customerId
      ORDER BY transaction_date DESC
      LIMIT 100
    `;

    const options = {
      query: query,
      location: 'US',
      params: { customerId: customerId }
    };

    const [rows] = await this.bigquery.query(options);
    return rows;
  }

  async getCustomerAnalytics(customerId) {
    const query = `
      SELECT
        c.customer_id,
        c.company_name,
        c.lifetime_value_usd,
        c.total_transactions,
        c.churn_risk_score,
        c.health_score,
        COUNT(DISTINCT t.transaction_id) as transaction_count,
        SUM(t.amount_usd) as total_spent,
        MAX(t.transaction_date) as last_transaction_date
      FROM \`${this.projectId}.customer_analytics.customers\` c
      LEFT JOIN \`${this.projectId}.customer_analytics.transactions\` t
        ON c.customer_id = t.customer_id
      WHERE c.customer_id = @customerId
      GROUP BY 1,2,3,4,5,6
    `;

    const options = {
      query: query,
      location: 'US',
      params: { customerId: customerId }
    };

    const [rows] = await this.bigquery.query(options);
    return rows[0] || null;
  }

  // AlloyDB (PostgreSQL) operations
  async queryAlloyDB(query) {
    const client = await this.alloydbPool.connect();
    try {
      const result = await client.query(query);
      return result.rows;
    } finally {
      client.release();
    }
  }

  async getCustomerProfile(customerId) {
    const client = await this.alloydbPool.connect();
    try {
      const query = `
        SELECT
          customer_id,
          company_name,
          primary_contact_name,
          primary_contact_email,
          phone,
          industry,
          employee_count,
          annual_revenue_usd,
          account_tier,
          customer_success_manager,
          billing_address,
          created_at,
          updated_at
        FROM customer_profiles
        WHERE customer_id = $1
      `;

      const result = await client.query(query, [customerId]);
      return result.rows[0] || null;
    } finally {
      client.release();
    }
  }

  // Firestore operations
  async queryFirestore(collectionName, limit = 100) {
    const snapshot = await this.firestore
      .collection(collectionName)
      .limit(limit)
      .get();

    const documents = [];
    snapshot.forEach(doc => {
      documents.push({ id: doc.id, ...doc.data() });
    });

    return documents;
  }

  async getCustomerRealtimeActivity(customerId) {
    const sessionsSnapshot = await this.firestore
      .collection('customer_sessions')
      .where('customer_id', '==', customerId)
      .orderBy('timestamp', 'desc')
      .limit(10)
      .get();

    const sessions = [];
    sessionsSnapshot.forEach(doc => {
      sessions.push({ id: doc.id, ...doc.data() });
    });

    return sessions;
  }

  async getOpenSupportTickets(customerId) {
    const ticketsSnapshot = await this.firestore
      .collection('support_tickets')
      .where('customer_id', '==', customerId)
      .where('status', 'in', ['open', 'in_progress'])
      .get();

    const tickets = [];
    ticketsSnapshot.forEach(doc => {
      tickets.push({ id: doc.id, ...doc.data() });
    });

    return tickets;
  }

  // Cloud Storage operations
  async listStorageFiles(bucketName) {
    const [files] = await this.storage.bucket(bucketName).getFiles();

    return files.map(file => ({
      name: file.name,
      size: file.metadata.size,
      contentType: file.metadata.contentType,
      created: file.metadata.timeCreated,
      updated: file.metadata.updated
    }));
  }

  async getCustomerDocuments(customerId) {
    const bucketName = `${this.projectId}-customer-docs`;
    const [files] = await this.storage
      .bucket(bucketName)
      .getFiles({ prefix: `${customerId}/` });

    return files.map(file => ({
      name: file.name,
      size: file.metadata.size,
      contentType: file.metadata.contentType,
      created: file.metadata.timeCreated,
      url: file.publicUrl()
    }));
  }

  // Aggregation - Customer 360 View
  async getCustomer360(customerId) {
    try {
      // Execute queries in parallel for better performance
      const [
        profile,
        analytics,
        transactions,
        realtimeActivity,
        supportTickets,
        documents
      ] = await Promise.all([
        this.getCustomerProfile(customerId),
        this.getCustomerAnalytics(customerId),
        this.getCustomerTransactions(customerId),
        this.getCustomerRealtimeActivity(customerId),
        this.getOpenSupportTickets(customerId),
        this.getCustomerDocuments(customerId)
      ]);

      return {
        customerId,
        timestamp: new Date().toISOString(),
        profile: profile || {},
        analytics: analytics || {},
        transactions: {
          recent: transactions.slice(0, 10),
          total_count: transactions.length
        },
        realtime_activity: {
          recent_sessions: realtimeActivity,
          last_active: realtimeActivity[0]?.timestamp || null
        },
        support: {
          open_tickets: supportTickets,
          ticket_count: supportTickets.length
        },
        documents: {
          files: documents,
          total_count: documents.length
        },
        health_metrics: {
          churn_risk: analytics?.churn_risk_score || 0,
          health_score: analytics?.health_score || 0,
          lifetime_value: analytics?.lifetime_value_usd || 0
        }
      };
    } catch (error) {
      console.error('Error building Customer 360 view:', error);
      throw error;
    }
  }

  // Execute multiple queries across databases
  async executeAggregateQueries(queries) {
    const results = {};

    for (const [key, queryConfig] of Object.entries(queries)) {
      const { database, query, collection } = queryConfig;

      try {
        switch (database) {
          case 'bigquery':
            results[key] = await this.queryBigQuery(query);
            break;
          case 'alloydb':
            results[key] = await this.queryAlloyDB(query);
            break;
          case 'firestore':
            results[key] = await this.queryFirestore(collection);
            break;
          default:
            results[key] = { error: `Unknown database: ${database}` };
        }
      } catch (error) {
        results[key] = { error: error.message };
      }
    }

    return results;
  }

  // Start the server
  start(port = 3100) {
    this.server = this.app.listen(port, () => {
      console.log(`Multi-Database MCP Server running on port ${port}`);
      console.log(`Project ID: ${this.projectId}`);
      console.log('\nEndpoints:');
      console.log(`  GET  /health - Health check`);
      console.log(`  POST /query - Execute database query`);
      console.log(`  POST /customer360 - Get Customer 360 view`);
      console.log(`  POST /aggregate - Execute aggregate queries`);
      console.log('\nMCP Tools registered:', this.mcpTools.length);
    });

    return this.server;
  }

  // Graceful shutdown
  async shutdown() {
    console.log('\nShutting down MCP server...');

    // Close AlloyDB pool
    await this.alloydbPool.end();

    // Close Express server
    if (this.server) {
      this.server.close();
    }

    console.log('Shutdown complete');
  }
}

// Main execution
if (require.main === module) {
  const projectId = process.env.PROJECT_ID || process.argv[2];

  if (!projectId) {
    console.error('Error: PROJECT_ID environment variable or command line argument required');
    process.exit(1);
  }

  if (!process.env.ALLOYDB_HOST) {
    console.error('Error: ALLOYDB_HOST environment variable required');
    process.exit(1);
  }

  const server = new MultiDatabaseMCPServer(projectId);
  server.start();

  // Handle graceful shutdown
  process.on('SIGTERM', async () => {
    await server.shutdown();
    process.exit(0);
  });

  process.on('SIGINT', async () => {
    await server.shutdown();
    process.exit(0);
  });
}

module.exports = MultiDatabaseMCPServer;
