"""
Database models for the Multi-Agent Fraud Detection System.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, DECIMAL, TIMESTAMP, Boolean, Integer, 
    ForeignKey, CheckConstraint, Text, func
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

Base = declarative_base()


# SQLAlchemy Models (Database)
class User(Base):
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    account_status = Column(String(20), default="active")
    risk_score = Column(DECIMAL(5, 2), default=0.00)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    transactions = relationship("UserTransaction", back_populates="user")
    alerts = relationship("FraudAlert", back_populates="user")


class UserTransaction(Base):
    __tablename__ = "user_transactions"

    transaction_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    merchant = Column(String(255))
    category = Column(String(100))
    location = Column(String(255))
    ip_address = Column(INET)
    device_id = Column(String(100))
    transaction_type = Column(String(50))
    status = Column(String(20), default="pending")
    created_at = Column(TIMESTAMP, default=func.now())

    user = relationship("User", back_populates="transactions")
    alerts = relationship("FraudAlert", back_populates="transaction")


class FraudPattern(Base):
    __tablename__ = "fraud_patterns"

    pattern_id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_name = Column(String(100), nullable=False)
    pattern_type = Column(String(50), nullable=False)
    description = Column(Text)
    severity = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=func.now())


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(50), ForeignKey("user_transactions.transaction_id"))
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20))
    confidence_score = Column(DECIMAL(5, 2))
    reason = Column(Text)
    investigation_status = Column(String(50), default="pending")
    assigned_agent = Column(String(50))
    action_taken = Column(String(255))
    created_at = Column(TIMESTAMP, default=func.now())
    resolved_at = Column(TIMESTAMP)

    user = relationship("User", back_populates="alerts")
    transaction = relationship("UserTransaction", back_populates="alerts")


# Pydantic Models (API/Data Transfer)
class TransactionData(BaseModel):
    """Transaction data model for streaming and API."""
    transaction_id: str
    user_id: str
    amount: float
    currency: str = "USD"
    merchant: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    transaction_type: str = "purchase"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_123456",
                "user_id": "user_001",
                "amount": 1250.00,
                "currency": "USD",
                "merchant": "Online Store XYZ",
                "category": "electronics",
                "location": "New York, NY",
                "transaction_type": "purchase"
            }
        }


class FraudAssessment(BaseModel):
    """Fraud assessment result from agents."""
    transaction_id: str
    user_id: str
    is_suspicious: bool
    confidence_score: float = Field(ge=0.0, le=100.0)
    risk_factors: list[str] = []
    severity: str = "low"  # low, medium, high, critical
    recommended_action: str
    agent_name: str
    reasoning: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_123456",
                "user_id": "user_001",
                "is_suspicious": True,
                "confidence_score": 85.5,
                "risk_factors": ["high_velocity", "unusual_amount"],
                "severity": "high",
                "recommended_action": "investigate",
                "agent_name": "TransactionMonitor"
            }
        }


class InvestigationResult(BaseModel):
    """Investigation result from the Investigator agent."""
    transaction_id: str
    user_id: str
    is_fraudulent: bool
    confidence_score: float
    evidence: list[str] = []
    historical_patterns: dict = {}
    recommended_action: str  # approve, decline, lock_account, alert
    priority: str = "medium"  # low, medium, high, urgent

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_123456",
                "user_id": "user_001",
                "is_fraudulent": True,
                "confidence_score": 92.0,
                "evidence": ["Multiple high-value transactions in 5 minutes", "New device", "Geographic anomaly"],
                "recommended_action": "lock_account",
                "priority": "urgent"
            }
        }


class RemediationAction(BaseModel):
    """Remediation action result."""
    transaction_id: str
    user_id: str
    action_type: str  # lock_account, send_alert, decline_transaction, request_verification
    success: bool
    details: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_123456",
                "user_id": "user_001",
                "action_type": "lock_account",
                "success": True,
                "details": "Account locked due to suspected fraudulent activity"
            }
        }
