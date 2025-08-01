from typing import Annotated
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from src.model import model
from src.subagents.opportunity_analysis import opportunity_analysis_agent
from src.subagents.next_best_action import next_best_action_agent
from src.subagents.meeting_preparation import meeting_preparation_agent
from src.subagents.email_generation import email_generation_agent
from src.state import DealEngineState
from src.prompts import ROUTER_PROMPT
from pydantic import BaseModel, Field
from typing import Literal


class DealEngineRouter(BaseModel):
    """A router for the deal engine."""

    reasoning: str = Field(
        description="Step-by-step reasoning behind the routing decision."
    )
    routing_decision: Literal[
        "opportunity_analysis_agent",
        "next_best_action_agent",
        "meeting_preparation_agent",
        "email_generation_agent",
    ] = Field(description="The agent to route the user's request to.")


router_model = model.with_structured_output(DealEngineRouter)


async def router(state: DealEngineState):
    """Route the user's request to the appropriate agent."""
    user_message = state["messages"][-1].content
    messages = [SystemMessage(content=ROUTER_PROMPT)] + state["messages"]
    response = await router_model.ainvoke(messages)
    return Command(
        goto=response.routing_decision,
        update={
            "routing_reasoning": {
                "user_message": user_message,
                "reasoning": response.reasoning,
            },
        },
    )


def create_deal_engine(checkpointer):
    """Create the main deal engine supervisor graph"""

    builder = StateGraph(DealEngineState)

    # Add router
    builder.add_node("deal_engine_router", router)

    # Add specialized agents
    builder.add_node("opportunity_analysis_agent", opportunity_analysis_agent)
    builder.add_node("next_best_action_agent", next_best_action_agent)
    builder.add_node("meeting_preparation_agent", meeting_preparation_agent)
    builder.add_node("email_generation_agent", email_generation_agent)

    # Define flow - start with router
    builder.add_edge(START, "deal_engine_router")

    # All agents return to END for continued orchestration
    builder.add_edge("opportunity_analysis_agent", END)
    builder.add_edge("next_best_action_agent", END)
    builder.add_edge("meeting_preparation_agent", END)
    builder.add_edge("email_generation_agent", END)

    return builder.compile(checkpointer=checkpointer)
