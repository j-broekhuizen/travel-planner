
## Overview

The Deal Engine uses a router-based architecture to intelligently route user requests to specialized AI agents:

- **Opportunity Analysis Agent**: Analyzes deal/opty data and provides insights
- **Next Best Action Agent**: Recommends optimal next steps for deals
- **Meeting Preparation Agent**: Creates meeting agendas and preparation materials
- **Email Generation Agent**: Crafts professional follow-up emails and communications

## Architecture

```
User Input → Router → Specialized Agent → Response
```

Each agent uses a routing pattern with tool integration, allowing for:
- Dynamic tool execution
- Multi-step conversations
- Message-based state management
- Conditional routing between tool handling and AI processing

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd deal-engine
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

The deal engine will be available at the configured endpoint.

## Usage Examples

### Opportunity Analysis
```
"What's the status of deal OPTY1234?"
```

### Next Best Actions
```
"What should I do next with this opportunity?"
```

### Meeting Preparation
```
"Generate a meeting prep document for this deal"
```

### Email Generation
```
"Draft a follow-up email for the client"
```

## Project Structure

```
deal-engine/
├── src/
│   ├── graph.py              # Main router and graph definition
│   ├── state.py              # Shared state management
│   ├── model.py             # AI model and data models
│   ├── prompts.py           # AI prompts and templates
│   ├── tools.py             # Database tools and utilities
│   ├── subagents/           # Specialized agent implementations
│   │   ├── opportunity_analysis.py
│   │   ├── next_best_action.py
│   │   ├── meeting_preparation.py
│   │   └── email_generation.py
│   └── db/
│       └── opportunities.db  # SQLite database with deal data
├── requirements.txt
├── langgraph.json          # LangGraph configuration
└── README.md
```

## Database Schema

The system uses a SQLite database with an `opportunities` table:

| Column    | Type    | Description                   |
| --------- | ------- | ----------------------------- |
| id        | TEXT    | Opportunity ID (OPTYXXXX)     |
| name      | TEXT    | Deal name/description         |
| account   | TEXT    | Client account name           |
| NNACV     | REAL    | Net New Annual Contract Value |
| stage     | INTEGER | Deal stage (1-10)             |
| CloseDate | TEXT    | Expected close date           |


