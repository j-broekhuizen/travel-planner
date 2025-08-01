from langgraph.types import Command
from src.state import DealEngineState
from src.model import model
from src.prompts import EMAIL_GENERATION_PROMPT
from langgraph.graph import StateGraph, START, END


def llm(state: DealEngineState):
    opportunity_analysis = state.get("opportunity_analysis", "No opportunity analysis available")
    next_best_action = state.get("best_action", "No specific action identified")
    reasoning = state.get("reasoning", "No reasoning provided")
    meeting_prep = state.get("meeting_prep_doc", "No meeting preparation available")
    prompt = EMAIL_GENERATION_PROMPT.format(
        opportunity_analysis=opportunity_analysis,
        next_best_action=next_best_action,
        reasoning=reasoning,
        meeting_prep=meeting_prep,
    )
    response = model.invoke(prompt)
    return Command(
        update={
            "email_content": response,
        }
    )


# Build the graph
graph = StateGraph(DealEngineState)
graph.add_node("llm", llm)
graph.add_edge(START, "llm")
graph.add_edge("llm", END)

email_generation_agent = graph.compile()
