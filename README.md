
## Overview

The Travel Planner uses a supervisor/reAct architecture that calls specialized sub-agents as tools:

- **Flight Booking Agent**: Searches and books flights, handles airline preferences and scheduling
- **Hotel Booking Agent**: Finds and reserves accommodations based on preferences and budget
- **Car Rental Agent**: Manages vehicle rentals, pickup/dropoff logistics, and transportation needs


The supervisor orchestrates intelligent delegation and coordination, enabling:
- Multi-agent collaboration and context sharing via calling agents as tools
- Dynamic tool execution across specialized travel domains
- Routing based on travel request analysis and conversation history


## Quick Start

### Prerequisites

- Python 3.13+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd travel-planner
```

2. Install dependencies:
```bash
uv pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### Running the Application

Start the LangGraph server:
```bash
langgraph dev
```

The travel planner will be available at the configured endpoint.

## Usage Examples

### Flight Booking
```
"Find me flights from NYC to Paris for next week"
```

### Hotel Reservations
```
"Book a hotel in downtown Paris for 3 nights"
```

### Car Rental
```
"I need a rental car in Paris for my trip"
```

### Complete Trip Planning
```
"Plan a 5-day trip to Paris including flights, hotel, and car rental"
```

## Project Structure

```
travel-planner/
├── src/
│   ├── graph.py              # Main supervisor and graph definition
│   ├── state.py              # Shared state management
│   ├── model.py             # AI model and data models
│   ├── prompts.py           # AI prompts and templates
│   ├── tools.py             # Booking tools and utilities
│   ├── subagents/           # Specialized agent implementations
│   │   ├── flight_booking.py
│   │   ├── hotel_booking.py
│   │   └── car_rental.py
│   └── db/
│       └── travel_data.db    # SQLite database with travel options
├── requirements.txt
├── langgraph.json          # LangGraph configuration
└── README.md
```

## Database Schema

The system uses a SQLite database (`src/db/travel_data.db`) with comprehensive travel inventory:

### Flights Table
| Column           | Type | Description                 |
| ---------------- | ---- | --------------------------- |
| id               | TEXT | Flight ID (FL001)           |
| origin_city      | TEXT | Departure city              |
| destination_city | TEXT | Arrival city                |
| plane_type       | TEXT | Aircraft model (Boeing 777) |

**Available Routes (3 aircraft types each):**
- New York → Paris, Los Angeles → Tokyo, Chicago → London
- Miami → Barcelona, Seattle → Amsterdam, Boston → Rome  
- San Francisco → Sydney, Denver → Dubai, Atlanta → Bangkok, Houston → Frankfurt

### Hotels Table
| Column        | Type | Description                     |
| ------------- | ---- | ------------------------------- |
| id            | TEXT | Hotel ID (HTL001)               |
| location_city | TEXT | Hotel city location             |
| name          | TEXT | Hotel name                      |
| description   | TEXT | Hotel description and amenities |

**Available Cities (3 hotels each):**
Paris, Tokyo, London, Barcelona, Amsterdam, Rome, Sydney, Dubai, Bangkok, Frankfurt

### Cars Table  
| Column      | Type | Description                |
| ----------- | ---- | -------------------------- |
| id          | TEXT | Car ID (CAR001)            |
| pickup_city | TEXT | Car rental pickup city     |
| make        | TEXT | Vehicle make (Toyota, BMW) |
| color       | TEXT | Vehicle color              |

**Available Cities (6 car makes each):**
Paris, Tokyo, London, Barcelona, Amsterdam, Rome, Sydney, Dubai, Bangkok, Frankfurt


