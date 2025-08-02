from langgraph.types import Command
from src.state import DealEngineState
from src.model import model
from src.prompts import MEETING_PREPARATION_PROMPT
from langgraph.graph import StateGraph, START, END
from typing import Literal
from langchain_core.messages import SystemMessage

meeting_preparation_tools = []
tools_by_name = {tool.name: tool for tool in meeting_preparation_tools}
model_with_tools = model.bind_tools(meeting_preparation_tools)


async def tool_handler(state: DealEngineState):
    """Performs the tool call."""

    result = []
    # Iterate through tool calls
    for tool_call in state["messages"][-1].tool_calls:
        # Get the tool
        tool = tools_by_name[tool_call["name"]]
        # Run it
        observation = tool.invoke(tool_call["args"])
        # Create a tool message
        result.append(
            {"role": "tool", "content": observation, "tool_call_id": tool_call["id"]}
        )

    # Add it to our messages
    return {"messages": result}


async def llm(state: DealEngineState):
    messages = state["messages"]
    messages_with_system = [
        SystemMessage(content=MEETING_PREPARATION_PROMPT)
    ] + messages
    response = await model.ainvoke(messages_with_system)
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

meeting_preparation_agent = graph.compile()
