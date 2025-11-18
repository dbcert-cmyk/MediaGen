-- Multi-Agent Fraud Detection System Database Schema

-- Drop existing tables if they exist
DROP TABLE IF EXISTS fraud_alerts CASCADE;
DROP TABLE IF EXISTS user_transactions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS fraud_patterns CASCADE;

-- Users table
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    account_status VARCHAR(20) DEFAULT 'active' CHECK (account_status IN ('active', 'locked', 'suspended', 'closed')),
    risk_score DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User transactions table
CREATE TABLE user_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id),
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    merchant VARCHAR(255),
    category VARCHAR(100),
    location VARCHAR(255),
    ip_address INET,
    device_id VARCHAR(100),
    transaction_type VARCHAR(50) CHECK (transaction_type IN ('purchase', 'withdrawal', 'transfer', 'deposit')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'declined', 'flagged')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fraud patterns table (known fraud indicators)
CREATE TABLE fraud_patterns (
    pattern_id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(100) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    description TEXT,
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fraud alerts table
CREATE TABLE fraud_alerts (
    alert_id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) REFERENCES user_transactions(transaction_id),
    user_id VARCHAR(50) NOT NULL REFERENCES users(user_id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence_score DECIMAL(5,2),
    reason TEXT,
    investigation_status VARCHAR(50) DEFAULT 'pending' CHECK (investigation_status IN ('pending', 'investigating', 'confirmed', 'false_positive', 'resolved')),
    assigned_agent VARCHAR(50),
    action_taken VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX idx_transactions_user_id ON user_transactions(user_id);
CREATE INDEX idx_transactions_created_at ON user_transactions(created_at);
CREATE INDEX idx_transactions_status ON user_transactions(status);
CREATE INDEX idx_alerts_user_id ON fraud_alerts(user_id);
CREATE INDEX idx_alerts_status ON fraud_alerts(investigation_status);
CREATE INDEX idx_alerts_created_at ON fraud_alerts(created_at);

-- Insert some known fraud patterns
INSERT INTO fraud_patterns (pattern_name, pattern_type, description, severity) VALUES
('High Velocity Transactions', 'velocity', 'Multiple transactions in a short time window', 'high'),
('Unusual Amount', 'amount', 'Transaction amount significantly higher than user average', 'medium'),
('Geographic Anomaly', 'location', 'Transaction from unusual geographic location', 'medium'),
('Rapid Location Change', 'location', 'Transactions from distant locations in short time', 'high'),
('New Device', 'device', 'Transaction from previously unseen device', 'low'),
('Unusual Time', 'temporal', 'Transaction at unusual time for user', 'low'),
('Round Amount', 'amount', 'Suspiciously round transaction amount', 'low'),
('High-Risk Merchant', 'merchant', 'Transaction with known high-risk merchant category', 'medium'),
('Account Takeover Pattern', 'behavioral', 'Pattern consistent with account takeover', 'critical'),
('Card Testing', 'behavioral', 'Multiple small transactions testing card validity', 'high');

-- Insert some sample users for testing
INSERT INTO users (user_id, name, email, account_status, risk_score) VALUES
('user_001', 'Alice Johnson', 'alice@example.com', 'active', 15.50),
('user_002', 'Bob Smith', 'bob@example.com', 'active', 8.20),
('user_003', 'Charlie Brown', 'charlie@example.com', 'active', 32.75),
('user_004', 'Diana Prince', 'diana@example.com', 'active', 5.00),
('user_005', 'Eve Wilson', 'eve@example.com', 'active', 42.80);

-- Insert some sample historical transactions
INSERT INTO user_transactions (transaction_id, user_id, amount, merchant, category, location, transaction_type, status) VALUES
('txn_001', 'user_001', 45.99, 'Amazon', 'shopping', 'New York, NY', 'purchase', 'approved'),
('txn_002', 'user_001', 12.50, 'Starbucks', 'food', 'New York, NY', 'purchase', 'approved'),
('txn_003', 'user_002', 250.00, 'Best Buy', 'electronics', 'Los Angeles, CA', 'purchase', 'approved'),
('txn_004', 'user_003', 5000.00, 'Luxury Cars Inc', 'automotive', 'Miami, FL', 'purchase', 'approved'),
('txn_005', 'user_004', 89.99, 'Target', 'shopping', 'Chicago, IL', 'purchase', 'approved');

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at on users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
