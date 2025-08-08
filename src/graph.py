from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send
from src.model import model
from src.subagents.opportunity_analysis import opportunity_analysis_agent
from src.subagents.next_best_action import next_best_action_agent
from src.subagents.meeting_preparation import meeting_preparation_agent
from src.subagents.email_generation import email_generation_agent
from src.state import DealEngineState
from src.tools import (
    AnalyzeOpportunity,
    GenerateEmail,
    NextBestAction,
    PrepareMeeting,
)
from src.prompts import (
    OPPORTUNITY_ANALYSIS_TOOL_DESCRIPTION,
    NEXT_BEST_ACTION_TOOL_DESCRIPTION,
    MEETING_PREPARATION_TOOL_DESCRIPTION,
    EMAIL_GENERATION_TOOL_DESCRIPTION,
    SUPERVISOR_PROMPT,
)
from typing import Literal
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage, HumanMessage
from uuid import uuid4
import asyncio


"""Supervisor binds Pydantic schema tools. Execution happens in supervisor_tools node."""
supervisor_tools = [AnalyzeOpportunity, NextBestAction, PrepareMeeting, GenerateEmail]
model_with_tools = model.bind_tools(supervisor_tools)


async def supervisor_tools_node(state: DealEngineState):
    """Execute delegate tools by invoking subagent subgraphs in parallel and returning ToolMessages."""

    messages = state["messages"]
    last_message = messages[-1]
    if not getattr(last_message, "tool_calls", None):
        return Command(goto=END)

    # Helper to get last human text for fallback context
    def last_human_text(msgs):
        for m in reversed(msgs):
            if (
                getattr(m, "type", None) == "human"
                or m.__class__.__name__ == "HumanMessage"
            ):
                return m.content
        return ""

    original_human = last_human_text(messages)

    # Build async tasks for each tool call
    async def run_tool(tool_call):
        name = tool_call["name"]
        args = tool_call.get("args", {})

        # Map tool name to subagent invocation with scoped HumanMessage
        try:
            if name == "AnalyzeOpportunity":
                scope_text = args.get("instruction") or original_human
                if args.get("opportunity_id"):
                    scope_text = f"Analyze opportunity {args['opportunity_id']}. Context: {scope_text}"
                oa_input = {"messages": [HumanMessage(content=scope_text)]}
                observation = await opportunity_analysis_agent.ainvoke(oa_input)
            elif name == "GenerateEmail":
                scope_text = args.get("instruction") or original_human
                eg_input = {"messages": [HumanMessage(content=scope_text)]}
                observation = await email_generation_agent.ainvoke(eg_input)
            elif name == "NextBestAction":
                scope_text = args.get("instruction") or original_human
                nba_input = {"messages": [HumanMessage(content=scope_text)]}
                observation = await next_best_action_agent.ainvoke(nba_input)
            elif name == "PrepareMeeting":
                scope_text = args.get("instruction") or original_human
                mp_input = {"messages": [HumanMessage(content=scope_text)]}
                observation = await meeting_preparation_agent.ainvoke(mp_input)
            else:
                return ToolMessage(
                    content=f"Unknown tool '{name}'.",
                    name=name,
                    tool_call_id=tool_call["id"],
                )

            # Extract final content: take the content of the last AI message from the subagent
            content = ""
            if isinstance(observation, dict) and "messages" in observation:
                for m in reversed(observation["messages"]):
                    if (
                        getattr(m, "type", None) == "ai"
                        or m.__class__.__name__ == "AIMessage"
                    ):
                        content = str(m.content)
                        break

            return ToolMessage(
                content=content or "No result produced.",
                name=name,
                tool_call_id=tool_call["id"],
            )
        except Exception as e:
            return ToolMessage(
                content=f"Error executing {name}: {e}",
                name=name,
                tool_call_id=tool_call["id"],
            )

    tasks = [run_tool(tc) for tc in last_message.tool_calls]
    results = await asyncio.gather(*tasks)

    return Command(goto="supervisor_llm", update={"messages": results})


async def supervisor_llm(state: DealEngineState):
    """Supervisor LLM node for routing and coordination."""

    messages = state["messages"]
    print(f"Supervisor LLM State: {messages}")
    messages_with_system = [SystemMessage(content=SUPERVISOR_PROMPT)] + messages
    response = await model_with_tools.ainvoke(messages_with_system)
    return Command(update={"messages": [response]})


def supervisor_should_continue(
    state: DealEngineState,
) -> Literal["supervisor_tools_node", "__end__"]:
    """Route to tool handler for handoffs, or end if no tool calls."""

    # Get the last message
    messages = state["messages"]
    last_message = messages[-1]

    if not last_message.tool_calls:
        return END
    else:
        return "supervisor_tools_node"


def create_supervisor(checkpointer):
    """Create the custom supervisor agent following subagent pattern."""

    # Build the supervisor graph
    supervisor_graph = StateGraph(DealEngineState)
    supervisor_graph.add_node("supervisor_llm", supervisor_llm)
    supervisor_graph.add_node("supervisor_tools_node", supervisor_tools_node)

    supervisor_graph.add_conditional_edges(
        "supervisor_llm",
        supervisor_should_continue,
        {
            "supervisor_tools_node": "supervisor_tools_node",
            "__end__": END,
        },
    )

    supervisor_graph.add_edge(START, "supervisor_llm")
    supervisor_graph.add_edge("supervisor_tools_node", "supervisor_llm")

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
