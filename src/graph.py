from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from src.model import model
from src.subagents.flight_booking import flight_booking_agent
from src.subagents.hotel_booking import hotel_booking_agent
from src.subagents.car_rental import car_rental_agent
from src.state import TravelPlannerState
from src.prompts import SUPERVISOR_PROMPT
from src.tools import (
    BookFlight,
    BookHotel,
    RentCar,
)
from typing import Literal
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
import asyncio


"""
Supervisor binds Pydantic schema tools. 
These will be used to invoke the subagents as tools and pass an explicit instruction to the subagent as a HumanMessage.
"""
supervisor_tools = [BookFlight, BookHotel, RentCar]
model_with_tools = model.bind_tools(supervisor_tools)


async def supervisor_tools_node(state: TravelPlannerState):
    """
    Execute delegate tools by invoking subagent subgraphs (optionally in parallel) and returning ToolMessages.
    """

    messages = state["messages"]
    last_message = messages[-1]
    if not getattr(last_message, "tool_calls", None):
        return Command(goto=END)

    # Build tasks for each tool call
    async def run_tool(tool_call):
        name = tool_call["name"]
        args = tool_call.get("args", {})

        # Map tool name to subagent invocation with scoped HumanMessage
        try:
            if name == "BookFlight":
                scope_text = args.get("instruction")
                if args.get("origin") and args.get("destination"):
                    scope_text = f"Book flight from {args['origin']} to {args['destination']}. {scope_text}"
                input = {"messages": [HumanMessage(content=scope_text)]}
                subagent_output = await flight_booking_agent.ainvoke(input)
            elif name == "BookHotel":
                scope_text = args.get("instruction")
                input = {"messages": [HumanMessage(content=scope_text)]}
                subagent_output = await hotel_booking_agent.ainvoke(input)
            elif name == "RentCar":
                scope_text = args.get("instruction")
                input = {"messages": [HumanMessage(content=scope_text)]}
                subagent_output = await car_rental_agent.ainvoke(input)
            else:
                raise ValueError(f"Unknown tool: {name}")

            # Extract final content: take the content of the last AI message from the subagent
            content = ""
            if isinstance(subagent_output, dict) and "messages" in subagent_output:
                for m in reversed(subagent_output["messages"]):
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


async def supervisor_llm(state: TravelPlannerState):
    """
    Supervisor LLM node that either generates tool calls to the subagents or responds to the user and ends the conversation.
    """

    messages = state["messages"]
    messages_with_system = [SystemMessage(content=SUPERVISOR_PROMPT)] + messages
    response = await model_with_tools.ainvoke(messages_with_system)
    return Command(update={"messages": [response]})


def supervisor_should_continue(
    state: TravelPlannerState,
) -> Literal["supervisor_tools_node", "__end__"]:
    """Route to tool handler for handoffs, or end if no tool calls."""

    messages = state["messages"]
    last_message = messages[-1]

    if not last_message.tool_calls:
        return END
    else:
        return "supervisor_tools_node"


def create_supervisor(checkpointer):
    """Create the top-level graph."""

    supervisor_graph = StateGraph(TravelPlannerState)
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


def create_travel_planner(checkpointer):
    """Create the main travel planner graph"""

    builder = StateGraph(TravelPlannerState)
    supervisor = create_supervisor(checkpointer)

    builder.add_node(
        "supervisor",
        supervisor,
        destinations=(
            "flight_booking_agent",
            "hotel_booking_agent",
            "car_rental_agent",
            END,
        ),
    )
    builder.add_node("flight_booking_agent", flight_booking_agent)
    builder.add_node("hotel_booking_agent", hotel_booking_agent)
    builder.add_node("car_rental_agent", car_rental_agent)

    builder.add_edge(START, "supervisor")
    builder.add_edge("flight_booking_agent", "supervisor")
    builder.add_edge("hotel_booking_agent", "supervisor")
    builder.add_edge("car_rental_agent", "supervisor")

    return builder.compile(checkpointer=checkpointer)
