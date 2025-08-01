from typing import Dict, List, Optional, Any
from datetime import datetime
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

model = ChatOpenAI(model="gpt-4.1")


class Opportunity(BaseModel):
    """Data model for deal opportunities"""

    opportunity_id: str
    account_name: str
    description: str
    deal_value: float
    stage: int  # Changed from str to int to match database
    close_date: Optional[datetime] = None


class MeetingPrepDoc(BaseModel):
    """Structured output from meeting preparation agent"""

    meeting_title: str
    agenda_items: List[str]
    key_talking_points: List[str]
    stakeholder_notes: Dict[str, str]
    prep_checklist: List[str]
    duration_mins: int = 60
    meeting_type: str = "discovery"  # discovery, demo, negotiation, closing


class EmailContent(BaseModel):
    """Structured output from email generation agent"""

    subject: str
    body: str
    tone: str  # professional, friendly, urgent
    call_to_action: str
    template_used: Optional[str] = None
    personalization_notes: List[str] = None

    def __post_init__(self):
        if self.personalization_notes is None:
            self.personalization_notes = []
