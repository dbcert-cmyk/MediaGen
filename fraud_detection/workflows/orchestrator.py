"""
LangGraph orchestration workflow for multi-agent fraud detection.
This coordinates the three agents in a stateful workflow.
"""
from typing import TypedDict, Annotated, Literal
from datetime import datetime
import structlog
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from fraud_detection.database.models import (
    TransactionData, 
    FraudAssessment, 
    InvestigationResult,
    RemediationAction
)
from fraud_detection.agents.transaction_monitor import TransactionMonitorAgent
from fraud_detection.agents.investigator import InvestigatorAgent
from fraud_detection.agents.remediation import RemediationAgent

logger = structlog.get_logger()


# Define the state structure for the workflow
class FraudDetectionState(TypedDict):
    """State that flows through the agent workflow."""
    # Input
    transaction: TransactionData
    
    # Agent outputs
    monitor_assessment: FraudAssessment | None
    investigation_result: InvestigationResult | None
    remediation_action: RemediationAction | None
    
    # Workflow metadata
    workflow_status: str  # "monitoring", "investigating", "remediating", "completed"
    timestamp: str
    
    # Messages for logging and tracking
    messages: Annotated[list, add_messages]


class FraudDetectionOrchestrator:
    """
    Orchestrates the multi-agent fraud detection workflow using LangGraph.
    
    Workflow:
    1. Transaction Monitor analyzes the transaction
    2. If suspicious, Investigator conducts deep analysis
    3. If fraud confirmed, Remediation Agent takes action
    """

    def __init__(self):
        self.monitor_agent = TransactionMonitorAgent()
        self.investigator_agent = InvestigatorAgent()
        self.remediation_agent = RemediationAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create the graph
        workflow = StateGraph(FraudDetectionState)
        
        # Add nodes (agent functions)
        workflow.add_node("monitor", self._monitor_node)
        workflow.add_node("investigate", self._investigate_node)
        workflow.add_node("remediate", self._remediate_node)
        workflow.add_node("complete", self._complete_node)
        
        # Set the entry point
        workflow.set_entry_point("monitor")
        
        # Add conditional edges based on agent decisions
        workflow.add_conditional_edges(
            "monitor",
            self._should_investigate,
            {
                "investigate": "investigate",
                "complete": "complete"
            }
        )
        
        workflow.add_conditional_edges(
            "investigate",
            self._should_remediate,
            {
                "remediate": "remediate",
                "complete": "complete"
            }
        )
        
        workflow.add_edge("remediate", "complete")
        workflow.add_edge("complete", END)
        
        return workflow

    # Node functions - each represents an agent's work
    
    def _monitor_node(self, state: FraudDetectionState) -> FraudDetectionState:
        """Transaction Monitor Agent node."""
        logger.info(
            "Monitor Agent analyzing transaction",
            transaction_id=state['transaction'].transaction_id
        )
        
        assessment = self.monitor_agent.analyze_transaction(state['transaction'])
        
        state['monitor_assessment'] = assessment
        state['workflow_status'] = "monitoring_complete"
        state['messages'].append({
            'agent': 'monitor',
            'timestamp': datetime.utcnow().isoformat(),
            'assessment': assessment.model_dump()
        })
        
        logger.info(
            "Monitor assessment complete",
            transaction_id=state['transaction'].transaction_id,
            is_suspicious=assessment.is_suspicious,
            severity=assessment.severity
        )
        
        return state

    def _investigate_node(self, state: FraudDetectionState) -> FraudDetectionState:
        """Investigator Agent node."""
        logger.info(
            "Investigator Agent analyzing transaction",
            transaction_id=state['transaction'].transaction_id
        )
        
        investigation = self.investigator_agent.investigate(
            state['transaction'],
            state['monitor_assessment']
        )
        
        state['investigation_result'] = investigation
        state['workflow_status'] = "investigation_complete"
        state['messages'].append({
            'agent': 'investigator',
            'timestamp': datetime.utcnow().isoformat(),
            'result': investigation.model_dump()
        })
        
        logger.info(
            "Investigation complete",
            transaction_id=state['transaction'].transaction_id,
            is_fraudulent=investigation.is_fraudulent,
            recommended_action=investigation.recommended_action
        )
        
        return state

    def _remediate_node(self, state: FraudDetectionState) -> FraudDetectionState:
        """Remediation Agent node."""
        logger.info(
            "Remediation Agent taking action",
            transaction_id=state['transaction'].transaction_id
        )
        
        action = self.remediation_agent.execute_remediation(
            state['transaction'].transaction_id,
            state['transaction'].user_id,
            state['investigation_result']
        )
        
        state['remediation_action'] = action
        state['workflow_status'] = "remediation_complete"
        state['messages'].append({
            'agent': 'remediation',
            'timestamp': datetime.utcnow().isoformat(),
            'action': action.model_dump()
        })
        
        logger.info(
            "Remediation complete",
            transaction_id=state['transaction'].transaction_id,
            action_type=action.action_type,
            success=action.success
        )
        
        return state

    def _complete_node(self, state: FraudDetectionState) -> FraudDetectionState:
        """Final node to mark workflow as complete."""
        state['workflow_status'] = "completed"
        
        logger.info(
            "Workflow complete",
            transaction_id=state['transaction'].transaction_id,
            final_status=state['workflow_status']
        )
        
        return state

    # Conditional edge functions - determine workflow routing
    
    def _should_investigate(self, state: FraudDetectionState) -> Literal["investigate", "complete"]:
        """Decide if transaction should be investigated."""
        assessment = state.get('monitor_assessment')
        
        if assessment and self.monitor_agent.should_escalate(assessment):
            logger.info(
                "Transaction escalated to investigation",
                transaction_id=state['transaction'].transaction_id
            )
            return "investigate"
        
        logger.info(
            "Transaction approved by monitor",
            transaction_id=state['transaction'].transaction_id
        )
        return "complete"

    def _should_remediate(self, state: FraudDetectionState) -> Literal["remediate", "complete"]:
        """Decide if remediation is needed."""
        investigation = state.get('investigation_result')
        
        if investigation and investigation.is_fraudulent:
            logger.info(
                "Fraud confirmed, proceeding to remediation",
                transaction_id=state['transaction'].transaction_id
            )
            return "remediate"
        
        logger.info(
            "No fraud detected, completing workflow",
            transaction_id=state['transaction'].transaction_id
        )
        return "complete"

    # Public API
    
    def process_transaction(self, transaction: TransactionData) -> FraudDetectionState:
        """
        Process a transaction through the multi-agent workflow.
        
        Args:
            transaction: The transaction to process
            
        Returns:
            Final state with all agent outputs
        """
        logger.info(
            "Starting fraud detection workflow",
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            amount=transaction.amount
        )
        
        # Initialize state
        initial_state: FraudDetectionState = {
            'transaction': transaction,
            'monitor_assessment': None,
            'investigation_result': None,
            'remediation_action': None,
            'workflow_status': 'started',
            'timestamp': datetime.utcnow().isoformat(),
            'messages': []
        }
        
        # Run the workflow
        final_state = self.app.invoke(initial_state)
        
        logger.info(
            "Fraud detection workflow completed",
            transaction_id=transaction.transaction_id,
            workflow_status=final_state['workflow_status']
        )
        
        return final_state

    def get_workflow_summary(self, state: FraudDetectionState) -> dict:
        """Get a summary of the workflow execution."""
        summary = {
            'transaction_id': state['transaction'].transaction_id,
            'user_id': state['transaction'].user_id,
            'amount': state['transaction'].amount,
            'workflow_status': state['workflow_status'],
            'timestamp': state['timestamp']
        }
        
        if state.get('monitor_assessment'):
            summary['monitor'] = {
                'is_suspicious': state['monitor_assessment'].is_suspicious,
                'confidence': state['monitor_assessment'].confidence_score,
                'severity': state['monitor_assessment'].severity
            }
        
        if state.get('investigation_result'):
            summary['investigation'] = {
                'is_fraudulent': state['investigation_result'].is_fraudulent,
                'confidence': state['investigation_result'].confidence_score,
                'recommended_action': state['investigation_result'].recommended_action
            }
        
        if state.get('remediation_action'):
            summary['remediation'] = {
                'action_type': state['remediation_action'].action_type,
                'success': state['remediation_action'].success,
                'details': state['remediation_action'].details
            }
        
        return summary
