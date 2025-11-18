"""
Agent 2: Investigator
This agent conducts deep investigation of flagged transactions.
"""
from typing import Dict, List
import structlog
from google import genai
from google.genai import types

from fraud_detection.config.settings import settings
from fraud_detection.database.models import TransactionData, FraudAssessment, InvestigationResult
from fraud_detection.tools.fraud_patterns import FraudPatternDetector

logger = structlog.get_logger()


class InvestigatorAgent:
    """
    Agent responsible for deep investigation of flagged transactions.
    
    This agent:
    - Receives flagged transactions from the Monitor
    - Analyzes user history and patterns
    - Determines if fraud is confirmed
    - Recommends specific actions
    """

    def __init__(self):
        self.name = "Investigator"
        self.fraud_detector = FraudPatternDetector()
        
        # Initialize Gemini client
        if settings.google_api_key:
            self.client = genai.Client(api_key=settings.google_api_key)
            self.model_id = settings.investigator_model
        else:
            self.client = None
            logger.warning("No Google API key found - running in limited mode")

    def investigate(
        self, 
        transaction: TransactionData, 
        initial_assessment: FraudAssessment
    ) -> InvestigationResult:
        """
        Conduct a deep investigation of a flagged transaction.
        
        Args:
            transaction: The transaction under investigation
            initial_assessment: The initial assessment from the Monitor
            
        Returns:
            InvestigationResult with detailed findings
        """
        logger.info(
            "Investigating transaction",
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            initial_severity=initial_assessment.severity
        )
        
        # Gather comprehensive user data
        user_history = self.fraud_detector.get_user_transaction_history(
            transaction.user_id, 
            limit=20
        )
        user_risk_score = self.fraud_detector.get_user_risk_score(transaction.user_id)
        
        # Re-run fraud checks with deeper analysis
        detailed_analysis = self.fraud_detector.analyze_transaction(transaction)
        
        # Use AI for investigation
        if self.client:
            investigation_result = self._ai_investigation(
                transaction,
                initial_assessment,
                user_history,
                user_risk_score,
                detailed_analysis
            )
        else:
            investigation_result = self._rule_based_investigation(
                transaction,
                initial_assessment,
                user_history,
                user_risk_score,
                detailed_analysis
            )
        
        logger.info(
            "Investigation complete",
            transaction_id=transaction.transaction_id,
            is_fraudulent=investigation_result.is_fraudulent,
            confidence=investigation_result.confidence_score,
            action=investigation_result.recommended_action
        )
        
        return investigation_result

    def _ai_investigation(
        self,
        transaction: TransactionData,
        initial_assessment: FraudAssessment,
        user_history: List[Dict],
        user_risk_score: float,
        detailed_analysis: Dict
    ) -> InvestigationResult:
        """Use Gemini AI to conduct thorough investigation."""
        
        prompt = f"""You are a senior fraud investigator reviewing a flagged transaction.

FLAGGED TRANSACTION:
- Transaction ID: {transaction.transaction_id}
- User ID: {transaction.user_id}
- Amount: ${transaction.amount} {transaction.currency}
- Merchant: {transaction.merchant}
- Category: {transaction.category}
- Location: {transaction.location}
- Device: {transaction.device_id}

INITIAL ASSESSMENT:
- Flagged by: {initial_assessment.agent_name}
- Severity: {initial_assessment.severity}
- Confidence: {initial_assessment.confidence_score}%
- Risk Factors: {', '.join(initial_assessment.risk_factors)}
- Initial Reasoning: {initial_assessment.reasoning}

USER PROFILE:
- User Risk Score: {user_risk_score}/100
- Transaction History (last 20 transactions):
{self._format_history(user_history)}

DETAILED FRAUD ANALYSIS:
- Suspicion Score: {detailed_analysis['suspicion_score']}/100
- Velocity Check: {detailed_analysis['checks']['velocity']}
- Amount Analysis: {detailed_analysis['checks']['unusual_amount']}
- Geographic Analysis: {detailed_analysis['checks']['geographic_anomaly']}
- Device Analysis: {detailed_analysis['checks']['device']}

YOUR TASK:
Conduct a thorough investigation and determine:
1. Is this transaction fraudulent? (Consider false positive rate)
2. What is your confidence level?
3. What evidence supports your conclusion?
4. What action should be taken?

Respond in this exact JSON format:
{{
  "is_fraudulent": true/false,
  "confidence_score": 0-100,
  "evidence": ["evidence point 1", "evidence point 2"],
  "historical_patterns": {{
    "average_transaction": float,
    "typical_categories": ["cat1", "cat2"],
    "usual_locations": ["loc1", "loc2"]
  }},
  "recommended_action": "approve/decline/lock_account/alert",
  "priority": "low/medium/high/urgent",
  "investigation_notes": "Detailed reasoning for your decision"
}}"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,  # Very low temperature for investigation
                    response_mime_type="application/json"
                )
            )
            
            import json
            result = json.loads(response.text)
            
            return InvestigationResult(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                is_fraudulent=result.get('is_fraudulent', False),
                confidence_score=result.get('confidence_score', 50.0),
                evidence=result.get('evidence', []),
                historical_patterns=result.get('historical_patterns', {}),
                recommended_action=result.get('recommended_action', 'alert'),
                priority=result.get('priority', 'medium')
            )
            
        except Exception as e:
            logger.error("AI investigation failed, using rule-based approach", error=str(e))
            return self._rule_based_investigation(
                transaction,
                initial_assessment,
                user_history,
                user_risk_score,
                detailed_analysis
            )

    def _rule_based_investigation(
        self,
        transaction: TransactionData,
        initial_assessment: FraudAssessment,
        user_history: List[Dict],
        user_risk_score: float,
        detailed_analysis: Dict
    ) -> InvestigationResult:
        """Fallback rule-based investigation."""
        
        # Calculate evidence
        evidence = []
        risk_factors = detailed_analysis['risk_factors']
        
        if 'velocity' in risk_factors:
            evidence.append("High transaction velocity detected")
        if 'unusual_amount' in risk_factors:
            evidence.append(f"Transaction amount (${transaction.amount}) is unusually high")
        if 'geographic_anomaly' in risk_factors:
            evidence.append(f"Transaction from new location: {transaction.location}")
        if 'device' in risk_factors:
            evidence.append(f"New device detected: {transaction.device_id}")
        
        # Determine if fraudulent based on confidence and risk factors
        confidence = initial_assessment.confidence_score
        is_fraudulent = confidence >= 70 and len(risk_factors) >= 2
        
        # Determine action
        if is_fraudulent and confidence >= 90:
            action = 'lock_account'
            priority = 'urgent'
        elif is_fraudulent and confidence >= 70:
            action = 'decline'
            priority = 'high'
        elif confidence >= 50:
            action = 'alert'
            priority = 'medium'
        else:
            action = 'approve'
            priority = 'low'
        
        # Calculate historical patterns
        if user_history:
            avg_amount = sum(t['amount'] for t in user_history) / len(user_history)
        else:
            avg_amount = 0.0
        
        return InvestigationResult(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            is_fraudulent=is_fraudulent,
            confidence_score=confidence,
            evidence=evidence,
            historical_patterns={
                'average_transaction': avg_amount,
                'transaction_count': len(user_history)
            },
            recommended_action=action,
            priority=priority
        )

    def _format_history(self, history: List[Dict]) -> str:
        """Format transaction history for the prompt."""
        if not history:
            return "No previous transactions"
        
        lines = []
        for txn in history[:10]:  # Limit to 10 for context window
            lines.append(
                f"  - ${txn['amount']:.2f} at {txn['merchant']} ({txn['status']})"
            )
        
        if len(history) > 10:
            lines.append(f"  ... and {len(history) - 10} more transactions")
        
        return '\n'.join(lines)
