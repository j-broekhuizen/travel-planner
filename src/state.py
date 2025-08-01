from typing import Annotated, Dict, List, Literal, Optional
from typing_extensions import TypedDict, NotRequired
from langgraph.graph.message import AnyMessage, add_messages
from src.model import Opportunity


class DealEngineState(TypedDict):
    """State for the deal engine"""

    messages: Annotated[list[AnyMessage], add_messages]

    # Opportunity data
    opportunity_id: NotRequired[Optional[str]]
    opportunity_data: NotRequired[Optional[Opportunity]]
    opportunity_analysis: NotRequired[Optional[str]]

    # Next best actions
    next_best_actions: NotRequired[Optional[list[str]]]
    best_action: NotRequired[Optional[str]]
    reasoning: NotRequired[Optional[str]]

    # Meeting preparation
    meeting_prep_doc: NotRequired[Optional[str]]

    # Email generation
    email_content: NotRequired[Optional[str]]

    # Routing & control
    current_step: NotRequired[
        Literal[
            "start",
            "opportunity_analysis",
            "meeting_preparation",
            "email_generation",
            "complete",
        ]
    ]
    requested_agents: NotRequired[
        Optional[List[str]]
    ]  # Track which agents have been called
