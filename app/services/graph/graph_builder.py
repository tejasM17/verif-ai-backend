import logging
from typing import List, Literal, Optional

from langgraph.graph import StateGraph, START, END
from app.services.graph.state import VerificationState
from app.services.graph.supervisor import supervisor_node
from app.services.graph.resume_node import resume_agent_node
from app.services.graph.certificate_node import certificate_agent_node
from app.services.graph.github_node import github_agent_node
from app.services.graph.cross_reference import cross_reference_node
from app.services.graph.final_decision import final_decision_node

logger = logging.getLogger(__name__)

# Singleton for compiled app
_app = None

def get_app():
    """
    Builds and compiles the LangGraph state machine.
    """
    global _app
    if _app is not None:
        return _app

    workflow = StateGraph(VerificationState)

    # Add Nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("resume_agent", resume_agent_node)
    workflow.add_node("cert_agent", certificate_agent_node)
    workflow.add_node("github_agent", github_agent_node)
    workflow.add_node("cross_reference", cross_reference_node)
    workflow.add_node("final_decision", final_decision_node)

    # Define Edges
    workflow.add_edge(START, "supervisor")
    
    # Parallel fan-out from supervisor
    workflow.add_edge("supervisor", "resume_agent")
    workflow.add_edge("supervisor", "cert_agent")
    workflow.add_edge("supervisor", "github_agent")

    # Fan-in to cross_reference
    # LangGraph waits for all parallel branches to reach the same node
    workflow.add_edge("resume_agent", "cross_reference")
    workflow.add_edge("cert_agent", "cross_reference")
    workflow.add_edge("github_agent", "cross_reference")

    # Linear completion
    workflow.add_edge("cross_reference", "final_decision")
    workflow.add_edge("final_decision", END)

    _app = workflow.compile()
    return _app
