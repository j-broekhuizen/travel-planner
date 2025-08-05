from langgraph.graph import StateGraph, START, END
from src.model import model
from src.subagents.opportunity_analysis import opportunity_analysis_agent
from src.subagents.next_best_action import next_best_action_agent
from src.subagents.meeting_preparation import meeting_preparation_agent
from src.subagents.email_generation import email_generation_agent
from src.state import DealEngineState
from langgraph.prebuilt import create_react_agent
from src.tools import create_handoff_tool
from src.prompts import (
    OPPORTUNITY_ANALYSIS_TOOL_DESCRIPTION,
    NEXT_BEST_ACTION_TOOL_DESCRIPTION,
    MEETING_PREPARATION_TOOL_DESCRIPTION,
    EMAIL_GENERATION_TOOL_DESCRIPTION,
    SUPERVISOR_PROMPT,
)


def create_supervisor(checkpointer):
    """Create the supervisor agent."""

    opportunity_handoff_tool = create_handoff_tool(
        "opportunity_analysis_agent", OPPORTUNITY_ANALYSIS_TOOL_DESCRIPTION
    )
    next_best_action_handoff_tool = create_handoff_tool(
        "next_best_action_agent", NEXT_BEST_ACTION_TOOL_DESCRIPTION
    )
    meeting_preparation_handoff_tool = create_handoff_tool(
        "meeting_preparation_agent", MEETING_PREPARATION_TOOL_DESCRIPTION
    )
    email_generation_handoff_tool = create_handoff_tool(
        "email_generation_agent", EMAIL_GENERATION_TOOL_DESCRIPTION
    )

    supervisor_tools = [
        opportunity_handoff_tool,
        next_best_action_handoff_tool,
        meeting_preparation_handoff_tool,
        email_generation_handoff_tool,
    ]
    return create_react_agent(
        name="supervisor",
        model=model,
        tools=supervisor_tools,
        prompt=SUPERVISOR_PROMPT,
        state_schema=DealEngineState,
        checkpointer=checkpointer,
    )


def create_deal_engine(checkpointer):
    """Create the main deal engine supervisor graph"""

    builder = StateGraph(DealEngineState)

    supervisor = create_supervisor(checkpointer)

    builder.add_node(
        "supervisor",
        supervisor,
        destinations=(
            "opportunity_analysis_agent",
            "next_best_action_agent",
            "meeting_preparation_agent",
            "email_generation_agent",
            END,
        ),
    )
    builder.add_node("opportunity_analysis_agent", opportunity_analysis_agent)
    builder.add_node("next_best_action_agent", next_best_action_agent)
    builder.add_node("meeting_preparation_agent", meeting_preparation_agent)
    builder.add_node("email_generation_agent", email_generation_agent)

    builder.add_edge(START, "supervisor")

    builder.add_edge("opportunity_analysis_agent", "supervisor")
    builder.add_edge("next_best_action_agent", "supervisor")
    builder.add_edge("meeting_preparation_agent", "supervisor")
    builder.add_edge("email_generation_agent", "supervisor")

    return builder.compile(checkpointer=checkpointer)
