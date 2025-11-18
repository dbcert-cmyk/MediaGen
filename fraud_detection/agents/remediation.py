"""
Agent 3: Remediation Agent
This agent takes action on confirmed fraudulent transactions.
"""
from typing import Dict, List
import structlog

from fraud_detection.database.models import InvestigationResult, RemediationAction
from fraud_detection.tools.notification import RemediationTools

logger = structlog.get_logger()


class RemediationAgent:
    """
    Agent responsible for taking remediation actions on confirmed fraud.
    
    This agent:
    - Receives investigation results
    - Takes appropriate actions (lock account, decline transaction, send alerts)
    - Logs all actions taken
    - Updates user risk scores
    """

    def __init__(self):
        self.name = "RemediationAgent"
        self.remediation_tools = RemediationTools()

    def execute_remediation(
        self,
        transaction_id: str,
        user_id: str,
        investigation_result: InvestigationResult
    ) -> RemediationAction:
        """
        Execute remediation actions based on investigation results.
        
        Args:
            transaction_id: The transaction ID
            user_id: The user ID
            investigation_result: Results from the Investigator
            
        Returns:
            RemediationAction with details of actions taken
        """
        logger.info(
            "Executing remediation",
            transaction_id=transaction_id,
            user_id=user_id,
            action=investigation_result.recommended_action,
            priority=investigation_result.priority
        )
        
        action_type = investigation_result.recommended_action
        actions_taken = []
        success = True
        
        try:
            # Execute the recommended action
            if action_type == 'lock_account':
                result = self._lock_account(user_id, investigation_result)
                actions_taken.append(result)
                
            elif action_type == 'decline':
                result = self._decline_transaction(transaction_id, investigation_result)
                actions_taken.append(result)
                
            elif action_type == 'alert':
                result = self._send_alert(user_id, transaction_id, investigation_result)
                actions_taken.append(result)
                
            elif action_type == 'approve':
                logger.info("Transaction approved after investigation", transaction_id=transaction_id)
                actions_taken.append({
                    'action': 'approve',
                    'success': True,
                    'details': 'Transaction approved after investigation'
                })
            
            # Always create a fraud alert record for suspicious transactions
            if investigation_result.is_fraudulent:
                alert_result = self._create_fraud_alert(
                    transaction_id,
                    user_id,
                    investigation_result
                )
                actions_taken.append(alert_result)
                
                # Update user risk score
                risk_increment = self._calculate_risk_increment(investigation_result)
                score_result = self.remediation_tools.update_user_risk_score(
                    user_id,
                    risk_increment
                )
                actions_taken.append(score_result)
            
            # Format details
            details = self._format_action_details(actions_taken)
            
            logger.info(
                "Remediation completed",
                transaction_id=transaction_id,
                actions_count=len(actions_taken),
                success=success
            )
            
            return RemediationAction(
                transaction_id=transaction_id,
                user_id=user_id,
                action_type=action_type,
                success=success,
                details=details
            )
            
        except Exception as e:
            logger.error(
                "Remediation failed",
                transaction_id=transaction_id,
                error=str(e)
            )
            return RemediationAction(
                transaction_id=transaction_id,
                user_id=user_id,
                action_type=action_type,
                success=False,
                details=f"Remediation failed: {str(e)}"
            )

    def _lock_account(self, user_id: str, investigation: InvestigationResult) -> Dict:
        """Lock the user's account."""
        reason = f"Account locked due to suspected fraud. Evidence: {', '.join(investigation.evidence[:2])}"
        result = self.remediation_tools.lock_account(user_id, reason)
        
        if result['success']:
            # Also send alert to user
            self.remediation_tools.send_security_alert(
                user_id,
                investigation.transaction_id,
                "Your account has been locked due to suspicious activity. Please contact support."
            )
        
        return result

    def _decline_transaction(self, transaction_id: str, investigation: InvestigationResult) -> Dict:
        """Decline the transaction."""
        reason = f"Transaction declined: {', '.join(investigation.evidence[:2])}"
        result = self.remediation_tools.decline_transaction(transaction_id, reason)
        
        if result['success']:
            # Send alert to user
            self.remediation_tools.send_security_alert(
                investigation.user_id,
                transaction_id,
                "A transaction was declined due to security concerns."
            )
        
        return result

    def _send_alert(self, user_id: str, transaction_id: str, investigation: InvestigationResult) -> Dict:
        """Send security alert to user."""
        message = f"Suspicious transaction detected: ${investigation.confidence_score:.0f}% confidence. " \
                 f"Reason: {', '.join(investigation.evidence[:2])}"
        
        return self.remediation_tools.send_security_alert(
            user_id,
            transaction_id,
            message
        )

    def _create_fraud_alert(
        self,
        transaction_id: str,
        user_id: str,
        investigation: InvestigationResult
    ) -> Dict:
        """Create a fraud alert record."""
        severity_map = {
            'urgent': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }
        
        return self.remediation_tools.create_fraud_alert(
            transaction_id=transaction_id,
            user_id=user_id,
            alert_type='fraud_investigation',
            severity=severity_map.get(investigation.priority, 'medium'),
            confidence_score=investigation.confidence_score,
            reason=', '.join(investigation.evidence),
            assigned_agent=self.name
        )

    def _calculate_risk_increment(self, investigation: InvestigationResult) -> float:
        """Calculate how much to increase the user's risk score."""
        # Base increment on confidence and priority
        base_increment = investigation.confidence_score / 10  # 0-10 scale
        
        # Multiply based on priority
        priority_multipliers = {
            'urgent': 2.0,
            'high': 1.5,
            'medium': 1.0,
            'low': 0.5
        }
        
        multiplier = priority_multipliers.get(investigation.priority, 1.0)
        return base_increment * multiplier

    def _format_action_details(self, actions: List[Dict]) -> str:
        """Format the actions taken into a readable string."""
        details = []
        for action in actions:
            if action.get('success'):
                action_type = action.get('action', action.get('action_type', 'unknown'))
                details.append(f"{action_type}: success")
            else:
                details.append(f"failed: {action.get('error', 'unknown error')}")
        
        return '; '.join(details)
