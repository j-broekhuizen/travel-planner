from typing import Annotated, Dict, List, Literal, Optional
from typing_extensions import TypedDict, NotRequired
from langgraph.graph.message import AnyMessage, add_messages
from src.model import Opportunity


class DealEngineState(TypedDict):
    """State for the deal engine"""

    messages: Annotated[list[AnyMessage], add_messages]
    routing_reasoning: NotRequired[Optional[Dict[str, str]]]
