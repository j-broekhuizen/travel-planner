from langgraph.types import Command
from src.state import DealEngineState
from src.tools import extract_opportunity_id, get_opportunity
from src.model import model
from src.prompts import OPPORTUNITY_ANALYSIS_PROMPT
from langgraph.graph import StateGraph, START, END


def extract_opportunity_id_node(state: DealEngineState):
    messages = state["messages"]
    opportunity_id = None
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content:
            extracted = extract_opportunity_id.invoke(msg.content)
            if extracted:
                opportunity_id = extracted
                break
    print(f"Extracted opportunity ID: {opportunity_id}")
    if opportunity_id is None:
        raise ValueError("No opportunity ID found in messages")
    return Command(update={"opportunity_id": opportunity_id})


def fetch_opportunity_data_node(state: DealEngineState):
    opportunity_id = state["opportunity_id"]
    opportunity = get_opportunity.invoke({"opportunity_id": opportunity_id})
    if opportunity is None:
        return Command(
            update={"opportunity_data": f"Opportunity {opportunity_id} not found"}
        )
    opportunity_dict = (
        opportunity.model_dump()
        if hasattr(opportunity, "model_dump")
        else opportunity.__dict__
    )
    return Command(update={"opportunity_data": opportunity_dict})


def llm(state: DealEngineState):
    opportunity_data = state["opportunity_data"]
    if isinstance(opportunity_data, str) and "not found" in opportunity_data:
        return Command(update={"opportunity_analysis": opportunity_data})
    prompt = OPPORTUNITY_ANALYSIS_PROMPT.format(opportunity_data=opportunity_data)
    response = model.invoke(prompt)
    return Command(update={"opportunity_analysis": response})


# Build the graph
graph = StateGraph(DealEngineState)
graph.add_node("extract_opportunity_id", extract_opportunity_id_node)
graph.add_node("fetch_opportunity_data", fetch_opportunity_data_node)
graph.add_node("llm", llm)

graph.add_edge(START, "extract_opportunity_id")
graph.add_edge("extract_opportunity_id", "fetch_opportunity_data")
graph.add_edge("fetch_opportunity_data", "llm")
graph.add_edge("llm", END)

opportunity_analysis_agent = graph.compile()
