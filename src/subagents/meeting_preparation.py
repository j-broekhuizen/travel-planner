from typing import Literal
from langgraph.types import Command
from src.state import DealEngineState


def meeting_preparation_agent(state: DealEngineState) -> Command[Literal["supervisor"]]:
    """
    Enhanced meeting prep agent that uses opportunity context
    """
    # Get opportunity context if available
    analysis = state.get("opportunity_analysis", {})
    opty_id = state.get("opportunity_id")
    deal_data = state.get("deal_data", {})

    if analysis and opty_id:
        # Context-aware meeting prep
        stage = deal_data.get("stage", "Unknown")
        account = deal_data.get("account_name", "Client")
        next_action = analysis.get("next_best_action", "Continue discussion")

        response_content = f"""📋 **Meeting Preparation for {opty_id}**

**Meeting Title**: {stage} Discussion with {account}

**Agenda**:
1. Welcome & Introductions (5 min)
2. Current State Review (10 min)
3. {next_action} (25 min)
4. Questions & Next Steps (10 min)

**Key Talking Points**:
• Review deal status and progress
• Address any concerns or blockers  
• {next_action.lower()}
• Confirm timeline and next steps

**Stakeholder Prep**:
• Review previous meeting notes
• Prepare relevant materials and demos
• Confirm attendee list and meeting logistics

**Success Metrics**:
• Clear next steps defined
• Stakeholder alignment confirmed
• Timeline agreed upon

Would you like me to draft a follow-up email template for after this meeting?"""
    else:
        # Generic meeting prep
        response_content = """📋 **Meeting Preparation Agent**

I can help prepare meeting materials! For better customization, please:
1. First analyze an opportunity with the Opportunity Analysis Agent
2. Then I can create context-specific meeting materials

**Generic Meeting Template**:
• Welcome & Introductions (5 min)
• Current State Assessment (15 min) 
• Solution Overview (20 min)
• Q&A and Next Steps (10 min)

What type of meeting would you like to prepare for?"""

    response_message = {
        "role": "assistant",
        "content": response_content,
        "name": "meeting_preparation_agent",
    }

    # Update completed tasks
    completed = state.get("completed_tasks", [])
    if "meeting_preparation" not in completed:
        completed = completed + ["meeting_preparation"]

    return Command(
        goto="supervisor",
        update={"messages": [response_message], "completed_tasks": completed},
    )
