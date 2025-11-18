"""
Notification and remediation action tools.
"""
from datetime import datetime
from typing import Dict, Optional
import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fraud_detection.config.settings import settings
from fraud_detection.database.models import User, UserTransaction, FraudAlert

logger = structlog.get_logger()


class RemediationTools:
    """Tools for taking remediation actions on suspicious transactions."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def lock_account(self, user_id: str, reason: str) -> Dict:
        """
        Lock a user account due to suspected fraud.
        
        Returns:
            Dict with success status and details
        """
        session = self.SessionLocal()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'action': 'lock_account',
                    'user_id': user_id,
                    'error': 'User not found'
                }
            
            # Update account status
            user.account_status = 'locked'
            user.updated_at = datetime.utcnow()
            session.commit()
            
            logger.warning(
                "Account locked",
                user_id=user_id,
                reason=reason
            )
            
            return {
                'success': True,
                'action': 'lock_account',
                'user_id': user_id,
                'previous_status': 'active',
                'new_status': 'locked',
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            session.rollback()
            logger.error("Failed to lock account", user_id=user_id, error=str(e))
            return {
                'success': False,
                'action': 'lock_account',
                'user_id': user_id,
                'error': str(e)
            }
        finally:
            session.close()

    def decline_transaction(self, transaction_id: str, reason: str) -> Dict:
        """
        Decline a suspicious transaction.
        
        Returns:
            Dict with success status and details
        """
        session = self.SessionLocal()
        try:
            transaction = session.query(UserTransaction).filter(
                UserTransaction.transaction_id == transaction_id
            ).first()
            
            if not transaction:
                return {
                    'success': False,
                    'action': 'decline_transaction',
                    'transaction_id': transaction_id,
                    'error': 'Transaction not found'
                }
            
            # Update transaction status
            transaction.status = 'declined'
            session.commit()
            
            logger.info(
                "Transaction declined",
                transaction_id=transaction_id,
                user_id=transaction.user_id,
                reason=reason
            )
            
            return {
                'success': True,
                'action': 'decline_transaction',
                'transaction_id': transaction_id,
                'user_id': transaction.user_id,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            session.rollback()
            logger.error("Failed to decline transaction", transaction_id=transaction_id, error=str(e))
            return {
                'success': False,
                'action': 'decline_transaction',
                'transaction_id': transaction_id,
                'error': str(e)
            }
        finally:
            session.close()

    def send_security_alert(self, user_id: str, transaction_id: str, message: str) -> Dict:
        """
        Send a security alert to the user.
        
        In a real system, this would send an email/SMS.
        For demo, we just log it and create an alert record.
        
        Returns:
            Dict with success status
        """
        logger.warning(
            "SECURITY ALERT",
            user_id=user_id,
            transaction_id=transaction_id,
            message=message
        )
        
        # In production, would send actual email/SMS here
        # For demo, we simulate it
        return {
            'success': True,
            'action': 'send_alert',
            'user_id': user_id,
            'transaction_id': transaction_id,
            'message': message,
            'alert_type': 'email',
            'timestamp': datetime.utcnow().isoformat()
        }

    def create_fraud_alert(
        self,
        transaction_id: str,
        user_id: str,
        alert_type: str,
        severity: str,
        confidence_score: float,
        reason: str,
        assigned_agent: str
    ) -> Dict:
        """
        Create a fraud alert record in the database.
        
        Returns:
            Dict with alert details
        """
        session = self.SessionLocal()
        try:
            alert = FraudAlert(
                transaction_id=transaction_id,
                user_id=user_id,
                alert_type=alert_type,
                severity=severity,
                confidence_score=confidence_score,
                reason=reason,
                investigation_status='pending',
                assigned_agent=assigned_agent
            )
            session.add(alert)
            session.commit()
            
            logger.info(
                "Fraud alert created",
                alert_id=alert.alert_id,
                transaction_id=transaction_id,
                severity=severity
            )
            
            return {
                'success': True,
                'alert_id': alert.alert_id,
                'transaction_id': transaction_id,
                'user_id': user_id,
                'severity': severity,
                'confidence_score': confidence_score
            }
        except Exception as e:
            session.rollback()
            logger.error("Failed to create fraud alert", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            session.close()

    def update_user_risk_score(self, user_id: str, increment: float) -> Dict:
        """
        Update a user's risk score.
        
        Returns:
            Dict with updated risk score
        """
        session = self.SessionLocal()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'user_id': user_id,
                    'error': 'User not found'
                }
            
            old_score = float(user.risk_score)
            user.risk_score = min(max(old_score + increment, 0), 100)  # Keep between 0-100
            session.commit()
            
            logger.info(
                "User risk score updated",
                user_id=user_id,
                old_score=old_score,
                new_score=float(user.risk_score)
            )
            
            return {
                'success': True,
                'user_id': user_id,
                'old_score': old_score,
                'new_score': float(user.risk_score)
            }
        except Exception as e:
            session.rollback()
            logger.error("Failed to update risk score", user_id=user_id, error=str(e))
            return {
                'success': False,
                'user_id': user_id,
                'error': str(e)
            }
        finally:
            session.close()
