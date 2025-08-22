from langgraph.types import Command
from src.state import DealEngineState
from src.tools import extract_opportunity_id, get_opportunity
from src.model import model
from src.prompts import OPPORTUNITY_ANALYSIS_PROMPT
from langgraph.graph import StateGraph, START, END
from typing import Literal
from langchain_core.messages import SystemMessage

opportunity_analysis_tools = [extract_opportunity_id, get_opportunity]
tools_by_name = {tool.name: tool for tool in opportunity_analysis_tools}
model_with_tools = model.bind_tools(opportunity_analysis_tools)


async def tool_handler(state: DealEngineState):
    """
    Tool-calling node that extracts the arguments from the tool call and invokes the tool.
    Args:
    - state: DealEngineState
    Returns:
    - Command: Command(update={"messages": result})
    """

    result = []
    # Iterate through tool calls
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = await tool.ainvoke(tool_call["args"])
        result.append(
            {
                "role": "tool",
                "content": observation,
                "name": tool_call["name"],
                "tool_call_id": tool_call["id"],
            }
        )

    return {"messages": result}


async def llm(state: DealEngineState):
    messages = state["messages"]
    messages_with_system = [
        SystemMessage(content=OPPORTUNITY_ANALYSIS_PROMPT)
    ] + messages
    response = await model_with_tools.ainvoke(messages_with_system)
    return Command(update={"messages": [response]})


def should_continue(state: DealEngineState) -> Literal["tool_handler", "__end__"]:
    """Route to tool handler, or end if no more tool calls."""

    # Get the last message
    messages = state["messages"]
    last_message = messages[-1]

    if not last_message.tool_calls:
        return END
    else:
        return "tool_handler"


# Build the graph
graph = StateGraph(DealEngineState)
graph.add_node("llm", llm)
graph.add_node("tool_handler", tool_handler)

graph.add_conditional_edges(
    "llm",
    should_continue,
    {
        "tool_handler": "tool_handler",
        "__end__": END,
    },
)

graph.add_edge(START, "llm")
graph.add_edge("tool_handler", "llm")

opportunity_analysis_agent = graph.compile(name="opportunity_analysis_agent")
