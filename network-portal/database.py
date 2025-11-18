"""
Database configuration and models
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://netportal:netportal@localhost:5432/netportal")

# Create engine
engine = create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Database Models

class Device(Base):
    """Network device model"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    device_type = Column(String(50))  # server, switch, ap, router, etc.
    ip_address = Column(String(45))  # IPv4 or IPv6
    mac_address = Column(String(17))
    vendor = Column(String(100))
    model = Column(String(100))
    location = Column(String(255))
    credentials_id = Column(Integer)  # Reference to encrypted credentials
    status = Column(String(20), default="unknown")  # online, offline, unknown
    last_seen = Column(DateTime)
    metadata = Column(JSON)  # Additional device-specific data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Credential(Base):
    """Encrypted credentials for device access"""
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    credential_type = Column(String(50))  # ssh, snmp, api, etc.
    username = Column(String(255))
    password_encrypted = Column(Text)  # Encrypted password
    private_key_encrypted = Column(Text)  # Encrypted SSH key
    community_string_encrypted = Column(Text)  # Encrypted SNMP community
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class MonitoringMetric(Base):
    """Time-series monitoring metrics"""
    __tablename__ = "monitoring_metrics"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False)
    metric_type = Column(String(50))  # cpu, memory, bandwidth, etc.
    metric_name = Column(String(100))
    value = Column(String(255))
    unit = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class NetworkScan(Base):
    """Network scan results"""
    __tablename__ = "network_scans"

    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String(50))  # discovery, port_scan, vulnerability
    subnet = Column(String(45))
    status = Column(String(20))  # running, completed, failed
    results = Column(JSON)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class AgentTask(Base):
    """AI agent task history"""
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50))
    query = Column(Text)
    response = Column(Text)
    status = Column(String(20))  # pending, running, completed, failed
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
