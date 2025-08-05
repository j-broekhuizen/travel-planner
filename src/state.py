from typing import Annotated, List
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt.chat_agent_executor import AgentState


class DealEngineState(AgentState):
    """State for the deal engine"""

    messages: Annotated[list[AnyMessage], add_messages]
