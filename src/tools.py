import aiosqlite
import re
from typing import Annotated, Optional, Dict, Any, List
from datetime import datetime
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.model import Destination, TravelBooking
from src.model import model

DB_PATH = "src/db/travel_data.db"

## SUPERVISOR TOOLS
## ----------------------------------------------------------------------------


class BookFlight(BaseModel):
    """Search and book flights based on travel requirements."""

    origin: Optional[str] = Field(
        default=None,
        description=(
            "Departure city, airport code, or location (e.g., 'NYC', 'JFK', 'New York'). If provided, the agent will use it to "
            "search flights; if omitted, the agent will attempt to extract origin from the instruction text."
        ),
    )
    destination: Optional[str] = Field(
        default=None,
        description=(
            "Arrival city, airport code, or location (e.g., 'Paris', 'CDG', 'London'). If provided, the agent will use it to "
            "search flights; if omitted, the agent will attempt to extract destination from the instruction text."
        ),
    )
    instruction: str = Field(
        description=(
            "Natural-language flight booking request including dates, preferences, passenger count, "
            "class preferences, airline preferences, budget constraints, and any special requirements."
        ),
    )


class BookHotel(BaseModel):
    """Search and book hotel accommodations based on travel requirements."""

    instruction: str = Field(
        description=(
            "Describe the hotel booking request, including destination, check-in/check-out dates, guest count, "
            "room preferences, amenities desired, budget range, location preferences (downtown, airport, etc.), "
            "and any special requirements or accessibility needs."
        ),
    )


class RentCar(BaseModel):
    """Search and book rental cars based on transportation needs."""

    instruction: str = Field(
        description=(
            "Provide car rental context including pickup/dropoff locations and dates, vehicle type preferences, "
            "driver information, insurance needs, budget constraints, and any special equipment requirements. "
            "Specify if pickup is at airport, hotel, or other location."
        ),
    )


@tool(
    "search_flights",
    description=(
        "Search for available flights by origin city and destination city. "
        "Returns flight options with aircraft type and route information."
    ),
)
async def search_flights(origin_city: str, destination_city: str) -> List[dict]:
    """
    Search for flights between two cities

    Args:
        origin_city: Departure city name
        destination_city: Arrival city name

    Returns:
        List of flight options with details
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()

        # Query database for flights matching origin and destination
        await cursor.execute(
            """
            SELECT id, origin_city, destination_city, plane_type
            FROM flights 
            WHERE origin_city = ? AND destination_city = ?
        """,
            (origin_city, destination_city),
        )

        rows = await cursor.fetchall()

        flights = []
        for row in rows:
            flights.append(
                {
                    "flight_id": row[0],
                    "origin_city": row[1],
                    "destination_city": row[2],
                    "plane_type": row[3],
                }
            )

        return str(flights)


@tool(
    "search_cars",
    description=(
        "Search for available rental cars. If the user mentions a city, use that as the pickup city. "
        "Returns car options with make and color information."
    ),
)
async def search_cars(pickup_city: str) -> List[dict]:
    """
    Search for rental cars in a specific city

    Args:
        pickup_city: City where car will be picked up

    Returns:
        List of car rental options with details
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()

        # Query database for cars available in the pickup city
        await cursor.execute(
            """
            SELECT id, pickup_city, make, color
            FROM cars 
            WHERE pickup_city = ?
        """,
            (pickup_city,),
        )

        rows = await cursor.fetchall()

        cars = []
        for row in rows:
            cars.append(
                {
                    "car_id": row[0],
                    "pickup_city": row[1],
                    "make": row[2],
                    "color": row[3],
                }
            )

        return str(cars)


@tool(
    "search_hotels",
    description=(
        "Search for hotel accommodations by location city. "
        "Returns hotel options with name and description information."
    ),
)
async def search_hotels(location_city: str) -> List[dict]:
    """
    Search for hotels in a specific city

    Args:
        location_city: City where hotels are located

    Returns:
        List of hotel options with details
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()

        # Query database for hotels in the specified city
        await cursor.execute(
            """
            SELECT id, location_city, name, description
            FROM hotels 
            WHERE location_city = ?
        """,
            (location_city,),
        )

        rows = await cursor.fetchall()

        hotels = []
        for row in rows:
            hotels.append(
                {
                    "hotel_id": row[0],
                    "location_city": row[1],
                    "name": row[2],
                    "description": row[3],
                }
            )

        return str(hotels)
