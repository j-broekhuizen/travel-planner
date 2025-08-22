from typing import Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

# Chat model
model = ChatOpenAI(model="gpt-4.1")


class Opportunity(BaseModel):
    """Data model for deal opportunities"""

    opportunity_id: str
    account_name: str
    description: str
    deal_value: float
    stage: int
    close_date: Optional[datetime] = None
