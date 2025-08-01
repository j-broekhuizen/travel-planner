from langgraph.types import Command
from src.state import DealEngineState
from src.tools import extract_opportunity_id, get_opportunity
from src.model import model
from src.prompts import NEXT_BEST_ACTION_PROMPT
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import List


class NextBestActionSchema(BaseModel):
    """
    A schema for deciding the next best action for a deal based on the opportunity analysis.
    """

    next_best_actions: List[str] = Field(
        description="A list of 5 next best actions for the deal"
    )
    best_action: str = Field(description="The best action to take for the deal")
    reasoning: str = Field(description="The reasoning for the best action")


def llm(state: DealEngineState):
    opportunity_analysis = state.get("opportunity_analysis", "No opportunity analysis available")
    prompt = NEXT_BEST_ACTION_PROMPT.format(opportunity_analysis=opportunity_analysis)
    structured_model = model.with_structured_output(NextBestActionSchema)
    response = structured_model.invoke(prompt)
    return Command(
        update={
            "next_best_actions": response.next_best_actions,
            "best_action": response.best_action,
            "reasoning": response.reasoning,
        }
    )


# Build the graph
graph = StateGraph(DealEngineState)
graph.add_node("llm", llm)

graph.add_edge(START, "llm")
graph.add_edge("llm", END)

next_best_action_agent = graph.compile()
