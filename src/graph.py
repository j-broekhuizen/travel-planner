from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from src.model import model
from src.subagents.opportunity_analysis import opportunity_analysis_agent
from src.subagents.next_best_action import next_best_action_agent
from src.subagents.meeting_preparation import meeting_preparation_agent
from src.subagents.email_generation import email_generation_agent
from src.state import DealEngineState
from src.tools import create_handoff_tool
from src.prompts import (
    OPPORTUNITY_ANALYSIS_TOOL_DESCRIPTION,
    NEXT_BEST_ACTION_TOOL_DESCRIPTION,
    MEETING_PREPARATION_TOOL_DESCRIPTION,
    EMAIL_GENERATION_TOOL_DESCRIPTION,
    SUPERVISOR_PROMPT,
)
from typing import Literal
from langchain_core.messages import SystemMessage, ToolMessage


# Create supervisor tools
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

tools_by_name = {tool.name: tool for tool in supervisor_tools}
model_with_tools = model.bind_tools(supervisor_tools)


async def supervisor_tool_handler(state: DealEngineState):
    """Handle supervisor tool calls for agent handoffs."""

    # Get the last message with tool calls
    last_message = state["messages"][-1]

    # Handle each tool call
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]

        # Create tool message for the handoff
        tool_message = ToolMessage(
            content=f"Successfully transferred your request to {tool_name.replace('transfer_to_', '').replace('_', ' ').title()}.",
            name=tool_name,
            tool_call_id=tool_call["id"],
        )

        # Determine which agent to route to based on tool name
        if "opportunity_analysis" in tool_name:
            agent_name = "opportunity_analysis_agent"
        elif "next_best_action" in tool_name:
            agent_name = "next_best_action_agent"
        elif "meeting_preparation" in tool_name:
            agent_name = "meeting_preparation_agent"
        elif "email_generation" in tool_name:
            agent_name = "email_generation_agent"
        else:
            # Fallback - shouldn't happen
            agent_name = END

        # Return Command to transfer to the appropriate agent
        return Command(
            goto=agent_name,
            update={
                "messages": state["messages"] + [tool_message],
            },
            graph=Command.PARENT,
        )

    # If no tool calls (shouldn't happen), return state unchanged
    return {"messages": []}


async def supervisor_llm(state: DealEngineState):
    """Supervisor LLM node for routing and coordination."""

    messages = state["messages"]
    messages_with_system = [SystemMessage(content=SUPERVISOR_PROMPT)] + messages

    response = await model_with_tools.ainvoke(messages_with_system)
    return Command(update={"messages": [response]})


def supervisor_should_continue(
    state: DealEngineState,
) -> Literal["supervisor_tool_handler", "__end__"]:
    """Route to tool handler for handoffs, or end if no tool calls."""

    # Get the last message
    messages = state["messages"]
    last_message = messages[-1]

    if not last_message.tool_calls:
        return END
    else:
        return "supervisor_tool_handler"


def create_supervisor(checkpointer):
    """Create the custom supervisor agent following subagent pattern."""

    # Build the supervisor graph
    supervisor_graph = StateGraph(DealEngineState)
    supervisor_graph.add_node("supervisor_llm", supervisor_llm)
    supervisor_graph.add_node("supervisor_tool_handler", supervisor_tool_handler)

    supervisor_graph.add_conditional_edges(
        "supervisor_llm",
        supervisor_should_continue,
        {
            "supervisor_tool_handler": "supervisor_tool_handler",
            "__end__": END,
        },
    )

    supervisor_graph.add_edge(START, "supervisor_llm")
    supervisor_graph.add_edge("supervisor_tool_handler", "supervisor_llm")

    return supervisor_graph.compile(name="supervisor", checkpointer=checkpointer)


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
