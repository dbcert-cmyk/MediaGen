"""
FastAPI Demo Application for Multi-Agent Fraud Detection System.
Provides a web interface and REST API to interact with the system.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import structlog

from fraud_detection.database.models import TransactionData
from fraud_detection.workflows.orchestrator import FraudDetectionOrchestrator
from fraud_detection.streaming.producer import TransactionProducer
from fraud_detection.config.settings import settings

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Fraud Detection System",
    description="A sophisticated, agentic workflow for detecting and acting on fraudulent transactions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
orchestrator = FraudDetectionOrchestrator()
producer = TransactionProducer() if settings.kafka_bootstrap_servers else None


# Pydantic models for API
class AnalyzeTransactionRequest(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    merchant: Optional[str] = "Demo Merchant"
    category: Optional[str] = "shopping"
    location: Optional[str] = "New York, NY"
    device_id: Optional[str] = "device_1"


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the home page with demo interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Agent Fraud Detection System</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
            }
            .container {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
                text-align: center;
                margin-bottom: 10px;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
            }
            .agents {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin: 30px 0;
            }
            .agent {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            .agent h3 {
                color: #667eea;
                margin-top: 0;
            }
            .demo-form {
                background: #f8f9fa;
                padding: 25px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #555;
            }
            input, select {
                width: 100%;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            input:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                background: #667eea;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
            }
            button:hover {
                background: #5568d3;
            }
            .result {
                margin-top: 20px;
                padding: 20px;
                background: #e8f5e9;
                border-left: 4px solid #4caf50;
                border-radius: 5px;
                display: none;
            }
            .result.fraud {
                background: #ffebee;
                border-left-color: #f44336;
            }
            .loading {
                text-align: center;
                padding: 20px;
                display: none;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ Multi-Agent Fraud Detection System</h1>
            <p class="subtitle">A sophisticated, agentic workflow powered by Google ADK & LangGraph</p>
            
            <div class="agents">
                <div class="agent">
                    <h3>🔍 Agent 1: Monitor</h3>
                    <p>Monitors transaction stream and flags suspicious activity using AI-powered pattern detection.</p>
                </div>
                <div class="agent">
                    <h3>🕵️ Agent 2: Investigator</h3>
                    <p>Conducts deep investigation of flagged transactions, analyzing user history and patterns.</p>
                </div>
                <div class="agent">
                    <h3>⚡ Agent 3: Remediation</h3>
                    <p>Takes action on confirmed fraud: locks accounts, declines transactions, sends alerts.</p>
                </div>
            </div>

            <div class="demo-form">
                <h2>Test Transaction Analysis</h2>
                <form id="transactionForm">
                    <div class="form-group">
                        <label>User ID</label>
                        <select id="userId">
                            <option value="user_001">user_001 (Alice Johnson)</option>
                            <option value="user_002">user_002 (Bob Smith)</option>
                            <option value="user_003">user_003 (Charlie Brown)</option>
                            <option value="user_004">user_004 (Diana Prince)</option>
                            <option value="user_005">user_005 (Eve Wilson)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Amount ($)</label>
                        <input type="number" id="amount" value="1250.00" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label>Merchant</label>
                        <input type="text" id="merchant" value="Online Store XYZ" required>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select id="category">
                            <option value="shopping">Shopping</option>
                            <option value="electronics">Electronics</option>
                            <option value="food">Food & Dining</option>
                            <option value="travel">Travel</option>
                            <option value="entertainment">Entertainment</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Location</label>
                        <input type="text" id="location" value="New York, NY" required>
                    </div>
                    <button type="submit">Analyze Transaction</button>
                </form>

                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Agents are analyzing the transaction...</p>
                </div>

                <div class="result" id="result"></div>
            </div>
        </div>

        <script>
            document.getElementById('transactionForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const loading = document.getElementById('loading');
                const result = document.getElementById('result');
                
                loading.style.display = 'block';
                result.style.display = 'none';
                
                const data = {
                    transaction_id: 'txn_' + Date.now(),
                    user_id: document.getElementById('userId').value,
                    amount: parseFloat(document.getElementById('amount').value),
                    merchant: document.getElementById('merchant').value,
                    category: document.getElementById('category').value,
                    location: document.getElementById('location').value,
                    device_id: 'device_web'
                };
                
                try {
                    const response = await fetch('/api/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    const analysis = await response.json();
                    
                    loading.style.display = 'none';
                    result.style.display = 'block';
                    
                    const isFraud = analysis.investigation?.is_fraudulent || false;
                    result.className = 'result ' + (isFraud ? 'fraud' : '');
                    
                    result.innerHTML = `
                        <h3>Analysis Results</h3>
                        <p><strong>Transaction ID:</strong> ${analysis.transaction_id}</p>
                        <p><strong>Monitor Assessment:</strong> ${analysis.monitor?.is_suspicious ? '⚠️ SUSPICIOUS' : '✅ CLEAN'} 
                           (Confidence: ${analysis.monitor?.confidence || 0}%)</p>
                        ${analysis.investigation ? `
                            <p><strong>Investigation:</strong> ${isFraud ? '🚨 FRAUD DETECTED' : '✅ NO FRAUD'} 
                               (Confidence: ${analysis.investigation.confidence}%)</p>
                            <p><strong>Recommended Action:</strong> ${analysis.investigation.recommended_action}</p>
                        ` : ''}
                        ${analysis.remediation ? `
                            <p><strong>Remediation:</strong> ${analysis.remediation.action_type} 
                               ${analysis.remediation.success ? '✅' : '❌'}</p>
                            <p><strong>Details:</strong> ${analysis.remediation.details}</p>
                        ` : ''}
                    `;
                } catch (error) {
                    loading.style.display = 'none';
                    result.style.display = 'block';
                    result.className = 'result fraud';
                    result.innerHTML = `<h3>Error</h3><p>${error.message}</p>`;
                }
            });
        </script>
    </body>
    </html>
    """


@app.post("/api/analyze")
async def analyze_transaction(request: AnalyzeTransactionRequest):
    """
    Analyze a transaction through the multi-agent workflow.
    
    This endpoint processes a transaction through all three agents
    and returns the complete analysis results.
    """
    try:
        # Create transaction data
        transaction = TransactionData(
            transaction_id=request.transaction_id,
            user_id=request.user_id,
            amount=request.amount,
            merchant=request.merchant,
            category=request.category,
            location=request.location,
            device_id=request.device_id,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            "API: Analyzing transaction",
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id
        )
        
        # Process through the workflow
        final_state = orchestrator.process_transaction(transaction)
        
        # Get summary
        summary = orchestrator.get_workflow_summary(final_state)
        
        return JSONResponse(content=summary)
        
    except Exception as e:
        logger.error("API: Analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "multi-agent-fraud-detection",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*80)
    print("MULTI-AGENT FRAUD DETECTION SYSTEM - DEMO APPLICATION")
    print("="*80)
    print("\nStarting web server...")
    print("Open http://localhost:8000 in your browser to access the demo\n")
    print("="*80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
