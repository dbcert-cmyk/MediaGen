"""
Agent 1: Transaction Monitor
This agent monitors the transaction stream and flags suspicious activity.
"""
from typing import Dict, List
import structlog
from google import genai
from google.genai import types

from fraud_detection.config.settings import settings
from fraud_detection.database.models import TransactionData, FraudAssessment
from fraud_detection.tools.fraud_patterns import FraudPatternDetector

logger = structlog.get_logger()


class TransactionMonitorAgent:
    """
    Agent responsible for monitoring transactions and flagging suspicious activity.
    
    This agent:
    - Receives transaction data from the stream
    - Runs initial fraud checks
    - Decides if the transaction should be flagged for investigation
    """

    def __init__(self):
        self.name = "TransactionMonitor"
        self.fraud_detector = FraudPatternDetector()
        
        # Initialize Gemini client
        if settings.google_api_key:
            self.client = genai.Client(api_key=settings.google_api_key)
            self.model_id = settings.transaction_monitor_model
        else:
            self.client = None
            logger.warning("No Google API key found - running in limited mode")

    def analyze_transaction(self, transaction: TransactionData) -> FraudAssessment:
        """
        Analyze a transaction for suspicious patterns.
        
        Args:
            transaction: The transaction to analyze
            
        Returns:
            FraudAssessment with the analysis results
        """
        logger.info(
            "Analyzing transaction",
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            amount=transaction.amount
        )
        
        # Run automated fraud checks
        analysis = self.fraud_detector.analyze_transaction(transaction)
        
        # Use AI to make final determination
        if self.client:
            ai_assessment = self._ai_analysis(transaction, analysis)
        else:
            # Fallback to rule-based assessment
            ai_assessment = self._rule_based_analysis(transaction, analysis)
        
        return ai_assessment

    def _ai_analysis(self, transaction: TransactionData, analysis: Dict) -> FraudAssessment:
        """Use Gemini AI to analyze the transaction with context."""
        
        prompt = f"""You are a fraud detection specialist monitoring financial transactions in real-time.

Transaction Details:
- Transaction ID: {transaction.transaction_id}
- User ID: {transaction.user_id}
- Amount: ${transaction.amount} {transaction.currency}
- Merchant: {transaction.merchant}
- Category: {transaction.category}
- Location: {transaction.location}
- Device: {transaction.device_id}

Automated Analysis Results:
- Suspicion Score: {analysis['suspicion_score']}/100
- Is Suspicious: {analysis['is_suspicious']}
- User Risk Score: {analysis['user_risk_score']}
- Risk Factors Detected: {', '.join(analysis['risk_factors']) if analysis['risk_factors'] else 'None'}

Detailed Checks:
- Velocity Check: {analysis['checks']['velocity']}
- Amount Check: {analysis['checks']['unusual_amount']}
- Location Check: {analysis['checks']['geographic_anomaly']}
- Device Check: {analysis['checks']['device']}
- Round Amount Check: {analysis['checks']['round_amount']}

Based on this information, assess whether this transaction should be flagged for investigation.
Consider:
1. The combination of risk factors
2. The severity of each factor
3. The user's historical risk score
4. Any patterns that suggest fraud

Respond with your assessment in this exact JSON format:
{{
  "is_suspicious": true/false,
  "confidence_score": 0-100,
  "severity": "low/medium/high/critical",
  "risk_factors": ["factor1", "factor2"],
  "recommended_action": "approve/monitor/investigate/decline",
  "reasoning": "Brief explanation of your decision"
}}"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for more consistent decisions
                    response_mime_type="application/json"
                )
            )
            
            # Parse AI response
            import json
            ai_result = json.loads(response.text)
            
            return FraudAssessment(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                is_suspicious=ai_result.get('is_suspicious', analysis['is_suspicious']),
                confidence_score=ai_result.get('confidence_score', analysis['suspicion_score']),
                risk_factors=ai_result.get('risk_factors', analysis['risk_factors']),
                severity=ai_result.get('severity', 'medium'),
                recommended_action=ai_result.get('recommended_action', 'monitor'),
                agent_name=self.name,
                reasoning=ai_result.get('reasoning')
            )
            
        except Exception as e:
            logger.error("AI analysis failed, falling back to rules", error=str(e))
            return self._rule_based_analysis(transaction, analysis)

    def _rule_based_analysis(self, transaction: TransactionData, analysis: Dict) -> FraudAssessment:
        """Fallback rule-based analysis when AI is unavailable."""
        
        suspicion_score = analysis['suspicion_score']
        risk_factors = analysis['risk_factors']
        
        # Determine severity
        if suspicion_score >= 80:
            severity = 'critical'
            recommended_action = 'investigate'
        elif suspicion_score >= 60:
            severity = 'high'
            recommended_action = 'investigate'
        elif suspicion_score >= 40:
            severity = 'medium'
            recommended_action = 'monitor'
        else:
            severity = 'low'
            recommended_action = 'approve'
        
        return FraudAssessment(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            is_suspicious=analysis['is_suspicious'],
            confidence_score=suspicion_score,
            risk_factors=risk_factors,
            severity=severity,
            recommended_action=recommended_action,
            agent_name=self.name,
            reasoning=f"Automated analysis detected {len(risk_factors)} risk factors"
        )

    def should_escalate(self, assessment: FraudAssessment) -> bool:
        """Determine if this transaction should be escalated to the Investigator."""
        return assessment.is_suspicious and assessment.recommended_action in ['investigate', 'decline']
