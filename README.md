
## Overview

The Travel Planner uses a supervisor-based architecture to intelligently coordinate and route user requests across specialized AI agents:

- **Flight Booking Agent**: Searches and books flights, handles airline preferences and scheduling
- **Hotel Booking Agent**: Finds and reserves accommodations based on preferences and budget
- **Car Rental Agent**: Manages vehicle rentals, pickup/dropoff logistics, and transportation needs

## Architecture

```
User Input → Supervisor → Specialized Agent → Supervisor → Response
```

The supervisor orchestrates intelligent delegation and coordination, enabling:
- Multi-agent collaboration and context sharing
- Dynamic tool execution across specialized travel domains
- Comprehensive trip planning from multiple booking agents
- Intelligent routing based on travel request analysis and conversation history
- Quality control and booking coordination

## Quick Start

### Prerequisites

- Python 3.8+
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

The system uses a SQLite database with travel-related tables:

### Destinations Table
| Column      | Type    | Description                |
| ----------- | ------- | -------------------------- |
| id          | TEXT    | Destination ID (DEST001)   |
| city        | TEXT    | City name                  |
| country     | TEXT    | Country name               |
| airport_code| TEXT    | Primary airport code       |
| description | TEXT    | Destination description    |

### Sample Bookings Table  
| Column     | Type    | Description              |
| ---------- | ------- | ------------------------ |
| id         | TEXT    | Booking ID (TRV001)      |
| destination| TEXT    | Destination city         |
| type       | TEXT    | flight/hotel/car         |
| details    | TEXT    | Booking specifics        |
| price      | REAL    | Price in USD             |


