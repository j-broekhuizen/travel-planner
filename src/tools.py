import sqlite3
import re
from typing import Annotated, Optional, Dict, Any, List
from datetime import datetime
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from src.model import Opportunity
from src.state import DealEngineState
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage
from langgraph_supervisor.handoff import METADATA_KEY_HANDOFF_DESTINATION
from langgraph.graph import MessagesState
from langchain_core.tools import InjectedToolCallId
from src.model import model

DB_PATH = "src/db/opportunities.db"

## SUPERVISOR TOOLS
## ----------------------------------------------------------------------------


def create_handoff_tool(agent_name: str, description: str):
    """
    Creates a handoff tool that transfers control to a specific agent.

    Args:
        agent_name: The name of the agent to hand off to
        description: Description of when to use this handoff

    Returns:
        A tool function that can be used by the supervisor
    """
    tool_name = f"transfer_to_{agent_name}"

    @tool(tool_name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """
        Execute the handoff to the specified agent.

        This function:
        1. Creates a confirmation message
        2. Returns a Command to navigate to the target agent
        3. Passes along the current state
        """
        # Create a confirmation message for the handoff
        tool_message = ToolMessage(
            content=f"Successfully transferred your request to {agent_name.replace('_', ' ').title()}.",
            name=tool_name,
            tool_call_id=tool_call_id,
        )

        return Command(
            goto=agent_name,  # Which agent to transfer to
            update={
                **state,
                "messages": state["messages"] + [tool_message],
            },  # Update state
            graph=Command.PARENT,  # Work in the parent graph context
        )

    handoff_tool.metadata = {METADATA_KEY_HANDOFF_DESTINATION: agent_name}
    return handoff_tool


## OPPORTUNITY ANALYSIS TOOLS
## ----------------------------------------------------------------------------


@tool("get_opportunity", description="Fetch opportunity by ID")
def get_opportunity(opportunity_id: str) -> Optional[Opportunity]:
    """
    Fetch opportunity by ID

    Args:
        opportunity_id: ID of the opportunity to fetch

    Returns:
        Opportunity object if found, None otherwise
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM opportunities WHERE id = ?
        """,
            (opportunity_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        return Opportunity(
            opportunity_id=row[0],
            account_name=row[1],
            description=row[2],
            deal_value=row[3],
            stage=row[4],
            close_date=datetime.strptime(row[5], "%m/%d/%Y") if row[5] else None,
        )


@tool("list_opportunities", description="List all opportunities")
def list_opportunities(limit: int = 10) -> List[Opportunity]:
    """
    List all opportunities and return as a string

    Args:
        limit: Number of opportunities to list (default: 10)

    Returns:
        String representation of all opportunities
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM opportunities LIMIT ?", (limit,))

        opportunities = []
        for row in cursor.fetchall():
            opportunities.append(
                Opportunity(
                    opportunity_id=row[0],
                    account_name=row[1],
                    description=row[2],
                    deal_value=row[3],
                    stage=row[4],
                    close_date=(
                        datetime.strptime(row[5], "%m/%d/%Y") if row[5] else None
                    ),
                )
            )

        return str(opportunities)


@tool("extract_opportunity_id", description="Extract opportunity ID from text")
def extract_opportunity_id(text: str) -> Optional[str]:
    """
    Extract opportunity ID from text using regex

    Args:
        text: Text to extract opportunity ID from

    Returns:
        Opportunity ID if found, None otherwise
    """
    pattern = r"OPTY\d{4,}"
    match = re.search(pattern, text.upper())
    return match.group(0) if match else None


# NEXT BEST ACTION TOOLS
## ----------------------------------------------------------------------------


# MEETING PREP TOOLS
## ----------------------------------------------------------------------------


# EMAIL GENERATION TOOLS
## ----------------------------------------------------------------------------
