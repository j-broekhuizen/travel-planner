from langgraph.types import Command
from src.state import DealEngineState
from src.model import model
from src.prompts import MEETING_PREPARATION_PROMPT
from langgraph.graph import StateGraph, START, END


def llm(state: DealEngineState):
    # Get context from state if available, otherwise use defaults
    opportunity_analysis = state.get(
        "opportunity_analysis", "No opportunity analysis available"
    )
    next_best_action = state.get("best_action", "No specific action identified")
    reasoning = state.get("reasoning", "No reasoning provided")

    print(f"Opportunity Analysis: {opportunity_analysis}")
    print(f"Next Best Action: {next_best_action}")
    print(f"Reasoning: {reasoning}")

    prompt = MEETING_PREPARATION_PROMPT.format(
        opportunity_analysis=opportunity_analysis,
        next_best_action=next_best_action,
        reasoning=reasoning,
    )
    response = model.invoke(prompt)
    return Command(
        update={
            "meeting_prep_doc": response,
        }
    )


# Build the graph
graph = StateGraph(DealEngineState)
graph.add_node("llm", llm)
graph.add_edge(START, "llm")
graph.add_edge("llm", END)

meeting_preparation_agent = graph.compile()
