from typing import Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

# Chat model
model = ChatOpenAI(model="gpt-4.1")


class Destination(BaseModel):
    """Data model for travel destinations"""

    destination_id: str
    city: str
    country: str
    airport_code: str
    description: str


class TravelBooking(BaseModel):
    """Data model for travel bookings"""

    booking_id: str
    destination: str
    booking_type: str  # flight, hotel, car
    details: str
    price: float
    booking_date: Optional[datetime] = None
