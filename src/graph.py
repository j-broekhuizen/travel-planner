from typing import Annotated
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from src.model import model
from src.subagents.opportunity_analysis import opportunity_analysis_agent
from src.subagents.next_best_action import next_best_action_agent
from src.subagents.meeting_preparation import meeting_preparation_agent
from src.subagents.email_generation import email_generation_agent
from src.state import DealEngineState
from src.prompts import SUPERVISOR_PROMPT
from src.tools import create_handoff_tool

# Create handoff tools
transfer_to_opportunity_analysis = create_handoff_tool(
    agent_name="opportunity_analysis_agent",
    description="Transfer to opportunity analysis agent for deal information, status updates, and opportunity insights.",
)

transfer_to_meeting_preparation = create_handoff_tool(
    agent_name="meeting_preparation_agent",
    description="Transfer to meeting preparation agent for generating meeting agendas, prep docs, and meeting materials.",
)

transfer_to_email_generation = create_handoff_tool(
    agent_name="email_generation_agent",
    description="Transfer to email generation agent for crafting follow-up emails, proposals, and client communications.",
)

transfer_to_next_best_action = create_handoff_tool(
    agent_name="next_best_action_agent",
    description="Transfer to next best action agent for generating recommended next steps and actions for a deal.",
)

supervisor_agent = create_react_agent(
    model=model,
    tools=[
        transfer_to_opportunity_analysis,
        transfer_to_next_best_action,
        transfer_to_meeting_preparation,
        transfer_to_email_generation,
    ],
    prompt=SUPERVISOR_PROMPT,
    name="supervisor",
)


def create_deal_engine(checkpointer):
    """Create the main deal engine supervisor graph"""

    builder = StateGraph(DealEngineState)

    # Add supervisor
    builder.add_node(
        supervisor_agent,
        destinations=(
            "opportunity_analysis_agent",
            "next_best_action_agent",
            "meeting_preparation_agent",
            "email_generation_agent",
            END,
        ),
    )

    # Add specialized agents
    builder.add_node("opportunity_analysis_agent", opportunity_analysis_agent)
    builder.add_node("next_best_action_agent", next_best_action_agent)
    builder.add_node("meeting_preparation_agent", meeting_preparation_agent)
    builder.add_node("email_generation_agent", email_generation_agent)

    # Define flow - start with supervisor
    builder.add_edge(START, "supervisor")

    # All agents return to supervisor for continued orchestration
    builder.add_edge("opportunity_analysis_agent", "supervisor")
    builder.add_edge("next_best_action_agent", "supervisor")
    builder.add_edge("meeting_preparation_agent", "supervisor")
    builder.add_edge("email_generation_agent", "supervisor")

    return builder.compile(checkpointer=checkpointer)
