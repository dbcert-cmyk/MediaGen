"""
Fraud pattern detection tools for agents.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import structlog
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from fraud_detection.config.settings import settings
from fraud_detection.database.models import (
    User, UserTransaction, FraudPattern, TransactionData
)

logger = structlog.get_logger()


class FraudPatternDetector:
    """Tools for detecting fraud patterns in transactions."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def check_velocity(self, user_id: str, window_seconds: int = 300) -> Dict:
        """
        Check transaction velocity - multiple transactions in short time.
        
        Returns:
            Dict with is_suspicious, count, and threshold_exceeded
        """
        session = self.SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
            
            count = session.query(UserTransaction).filter(
                UserTransaction.user_id == user_id,
                UserTransaction.created_at >= cutoff_time
            ).count()
            
            threshold_exceeded = count > settings.max_transactions_per_window
            
            return {
                'is_suspicious': threshold_exceeded,
                'count': count,
                'threshold': settings.max_transactions_per_window,
                'window_seconds': window_seconds,
                'severity': 'high' if threshold_exceeded else 'low'
            }
        finally:
            session.close()

    def check_unusual_amount(self, transaction: TransactionData) -> Dict:
        """
        Check if transaction amount is unusual for the user.
        
        Returns:
            Dict with is_suspicious, amount, and average_amount
        """
        session = self.SessionLocal()
        try:
            # Get user's average transaction amount
            avg_amount = session.query(
                func.avg(UserTransaction.amount)
            ).filter(
                UserTransaction.user_id == transaction.user_id,
                UserTransaction.status == 'approved'
            ).scalar() or 0
            
            # Check if current amount is significantly higher
            is_suspicious = (
                transaction.amount > settings.suspicious_amount_threshold or
                (avg_amount > 0 and transaction.amount > avg_amount * 5)
            )
            
            return {
                'is_suspicious': is_suspicious,
                'amount': transaction.amount,
                'average_amount': float(avg_amount),
                'threshold': settings.suspicious_amount_threshold,
                'severity': 'high' if transaction.amount > avg_amount * 10 else 'medium'
            }
        finally:
            session.close()

    def check_geographic_anomaly(self, transaction: TransactionData) -> Dict:
        """
        Check for geographic anomalies in transaction location.
        
        Returns:
            Dict with is_suspicious and location info
        """
        session = self.SessionLocal()
        try:
            # Get user's recent locations (last 30 days)
            recent_locations = session.query(
                UserTransaction.location
            ).filter(
                UserTransaction.user_id == transaction.user_id,
                UserTransaction.created_at >= datetime.utcnow() - timedelta(days=30),
                UserTransaction.location.isnot(None)
            ).distinct().all()
            
            recent_locations = [loc[0] for loc in recent_locations if loc[0]]
            
            # Simple check: is this location new?
            is_new_location = transaction.location not in recent_locations if transaction.location else False
            
            return {
                'is_suspicious': is_new_location,
                'current_location': transaction.location,
                'known_locations': recent_locations,
                'severity': 'medium' if is_new_location else 'low'
            }
        finally:
            session.close()

    def check_device_fingerprint(self, transaction: TransactionData) -> Dict:
        """
        Check if device is recognized.
        
        Returns:
            Dict with is_suspicious and device info
        """
        session = self.SessionLocal()
        try:
            # Get user's known devices
            known_devices = session.query(
                UserTransaction.device_id
            ).filter(
                UserTransaction.user_id == transaction.user_id,
                UserTransaction.device_id.isnot(None)
            ).distinct().all()
            
            known_devices = [dev[0] for dev in known_devices if dev[0]]
            
            is_new_device = transaction.device_id not in known_devices if transaction.device_id else False
            
            return {
                'is_suspicious': is_new_device,
                'current_device': transaction.device_id,
                'known_devices': known_devices,
                'severity': 'low' if is_new_device else 'low'
            }
        finally:
            session.close()

    def check_round_amount(self, transaction: TransactionData) -> Dict:
        """
        Check for suspiciously round amounts (common in fraud).
        
        Returns:
            Dict with is_suspicious
        """
        # Check if amount is a round number (e.g., 1000, 2000, 5000)
        is_round = transaction.amount % 1000 == 0 and transaction.amount >= 1000
        
        return {
            'is_suspicious': is_round,
            'amount': transaction.amount,
            'severity': 'low'
        }

    def get_user_risk_score(self, user_id: str) -> float:
        """Get user's current risk score."""
        session = self.SessionLocal()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            return float(user.risk_score) if user else 0.0
        finally:
            session.close()

    def get_user_transaction_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get user's recent transaction history."""
        session = self.SessionLocal()
        try:
            transactions = session.query(UserTransaction).filter(
                UserTransaction.user_id == user_id
            ).order_by(
                UserTransaction.created_at.desc()
            ).limit(limit).all()
            
            return [{
                'transaction_id': txn.transaction_id,
                'amount': float(txn.amount),
                'merchant': txn.merchant,
                'status': txn.status,
                'created_at': txn.created_at.isoformat() if txn.created_at else None
            } for txn in transactions]
        finally:
            session.close()

    def analyze_transaction(self, transaction: TransactionData) -> Dict:
        """
        Run all fraud checks on a transaction.
        
        Returns:
            Comprehensive analysis with all check results
        """
        velocity_check = self.check_velocity(transaction.user_id)
        amount_check = self.check_unusual_amount(transaction)
        location_check = self.check_geographic_anomaly(transaction)
        device_check = self.check_device_fingerprint(transaction)
        round_check = self.check_round_amount(transaction)
        
        # Determine if any checks are suspicious
        checks = [velocity_check, amount_check, location_check, device_check, round_check]
        suspicious_checks = [c for c in checks if c.get('is_suspicious')]
        
        # Calculate overall suspicion score
        suspicion_score = len(suspicious_checks) * 20  # 0-100 scale
        
        return {
            'transaction_id': transaction.transaction_id,
            'user_id': transaction.user_id,
            'is_suspicious': len(suspicious_checks) > 0,
            'suspicion_score': min(suspicion_score, 100),
            'checks': {
                'velocity': velocity_check,
                'unusual_amount': amount_check,
                'geographic_anomaly': location_check,
                'device': device_check,
                'round_amount': round_check
            },
            'risk_factors': [k for k in ['velocity', 'unusual_amount', 'geographic_anomaly', 'device', 'round_amount'] 
                           if checks[['velocity', 'unusual_amount', 'geographic_anomaly', 'device', 'round_amount'].index(k)].get('is_suspicious')],
            'user_risk_score': self.get_user_risk_score(transaction.user_id)
        }
