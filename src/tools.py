import aiosqlite
import re
from typing import Annotated, Optional, Dict, Any, List
from datetime import datetime
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.model import Opportunity
from src.model import model

DB_PATH = "src/db/opportunities.db"

## SUPERVISOR TOOLS
## ----------------------------------------------------------------------------


class AnalyzeOpportunity(BaseModel):
    """Analyze an opportunity. Provide an ID or free-text instruction with context."""

    opportunity_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional CRM opportunity ID (e.g., OPTY12345). If provided, the agent will use it to "
            "retrieve the record; if omitted, the agent will attempt to infer or extract an ID from "
            "the instruction text."
        ),
    )
    instruction: Optional[str] = Field(
        default=None,
        description=(
            "Optional natural-language guidance and context for the analysis (e.g., specific goals, "
            "known risks, questions to answer, constraints, or focus areas)."
        ),
    )


class GenerateEmail(BaseModel):
    """Generate an email per the given instruction (tone, recipient, purpose)."""

    instruction: str = Field(
        description=(
            "Describe the email to draft, including recipient (name/role/title if known), relationship/context, "
            "objective (e.g., follow-up, proposal, scheduling), desired tone/style, and any constraints or details "
            "(e.g., word count, product references, opportunity ID)."
        ),
    )


class NextBestAction(BaseModel):
    """Suggest the next best action for an opportunity or account."""

    instruction: str = Field(
        description=(
            "Provide deal/account context for action planning: current stage, key stakeholders and roles, "
            "recent activity, blockers/risks, desired objectives, and any deadlines. The agent will return five "
            "prioritized actions and one recommended action with reasoning."
        ),
    )


class PrepareMeeting(BaseModel):
    """Prepare a meeting brief/checklist for an upcoming meeting."""

    instruction: str = Field(
        description=(
            "Provide meeting context to generate a brief and agenda: meeting type, attendees and roles, "
            "date/time, objectives/success criteria, logistics/constraints, and relevant opportunity context."
        ),
    )


## OPPORTUNITY ANALYSIS TOOLS
## ----------------------------------------------------------------------------


@tool(
    "get_opportunity",
    description=(
        "Retrieve a single opportunity by its ID (e.g., OPTY12345), including account, description, "
        "deal value, stage, and optional close_date. Returns None if no record is found."
    ),
)
async def get_opportunity(opportunity_id: str) -> Optional[Opportunity]:
    """
    Fetch opportunity by ID

    Args:
        opportunity_id: ID of the opportunity to fetch

    Returns:
        Opportunity object if found, None otherwise
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT * FROM opportunities WHERE id = ?
        """,
            (opportunity_id,),
        )

        row = await cursor.fetchone()
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


@tool(
    "list_opportunities",
    description=(
        "List up to 'limit' opportunities from the database, returning a stringified list of Opportunity "
        "objects (id, account, description, value, stage, close_date). Useful for browsing during analysis."
    ),
)
async def list_opportunities(limit: int = 10) -> List[Opportunity]:
    """
    List all opportunities and return as a string

    Args:
        limit: Number of opportunities to list (default: 10)

    Returns:
        String representation of all opportunities
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM opportunities LIMIT ?", (limit,))

        opportunities = []
        rows = await cursor.fetchall()
        for row in rows:
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


@tool(
    "extract_opportunity_id",
    description=(
        "Parse free text and return a standardized opportunity ID if present (regex pattern: OPTY\\d{4,}). "
        "Useful to normalize user input before database lookups."
    ),
)
async def extract_opportunity_id(text: str) -> Optional[str]:
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
