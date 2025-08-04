from typing import Annotated, Dict, List, Literal, Optional
from typing_extensions import TypedDict, NotRequired
from langgraph.graph.message import AnyMessage, add_messages
from src.model import Opportunity


def add_routing_reasoning(
    existing: List["RoutingReasoning"], new: "RoutingReasoning"
) -> List["RoutingReasoning"]:
    """Reducer: append and deduplicate RoutingReasoning entries."""
    if existing is None:
        existing = []
    if isinstance(new, list):
        combined = existing + new
    else:
        combined = existing + [new]
    # Deduplicate by user_message, routing_decision, and reasoning
    seen = set()
    deduped = []
    for entry in combined:
        key = (entry["user_message"], entry["routing_decision"], entry["reasoning"])
        if key not in seen:
            seen.add(key)
            deduped.append(entry)
    return deduped


class RoutingReasoning(TypedDict):
    user_message: str
    reasoning: str
    routing_decision: str


class DealEngineState(TypedDict):
    """State for the deal engine"""

    messages: Annotated[list[AnyMessage], add_messages]
    routing_reasoning: Annotated[List[RoutingReasoning], add_routing_reasoning]
