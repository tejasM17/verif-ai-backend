import json
import logging
from typing import AsyncGenerator, Dict, Any
from app.services.graph.graph_builder import get_app

logger = logging.getLogger(__name__)

async def stream_graph_events(initial_state: dict) -> AsyncGenerator[dict, None]:
    """
    Runs the LangGraph and yields frontend-friendly events.
    """
    app = get_app()
    
    try:
        async for event in app.astream_events(initial_state, version="v3"):
            kind = event["event"]
            name = event["name"]
            
            # 1. Thinking tokens from LLMs
            if kind == "on_chat_model_stream":
                content = event["data"].get("chunk", {}).get("content", "")
                if content:
                    yield {
                        "type": "thinking_token",
                        "data": {
                            "token": content,
                            "node": event.get("metadata", {}).get("langgraph_node", "unknown")
                        }
                    }

            # 2. Tool starts (Research Step Start)
            elif kind == "on_tool_start":
                yield {
                    "type": "research_step_start",
                    "data": {
                        "agent": event.get("metadata", {}).get("langgraph_node", "unknown"),
                        "tool": name,
                        "input": event["data"].get("input", {}),
                        "timestamp": event.get("run_id") # Using run_id as a marker
                    }
                }

            # 3. Tool ends (Research Step Complete)
            elif kind == "on_tool_end":
                yield {
                    "type": "research_step_complete",
                    "data": {
                        "agent": event.get("metadata", {}).get("langgraph_node", "unknown"),
                        "tool": name,
                        "output": str(event["data"].get("output", "")),
                    }
                }

            # 4. Final Result (Analysis Complete)
            elif kind == "on_chain_end" and name == "LangGraph":
                # The final state is in the last on_chain_end event of the graph
                final_output = event["data"].get("output")
                if final_output:
                    yield {
                        "type": "analysis_complete",
                        "data": {
                            "trust_score": final_output.get("overall_trust_score"),
                            "verdict": final_output.get("verdict"),
                            "summary": "Verification analysis finished successfully."
                        }
                    }

    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        yield {
            "type": "error",
            "data": {
                "message": "An unexpected error occurred during analysis.",
                "detail": str(e)
            }
        }
