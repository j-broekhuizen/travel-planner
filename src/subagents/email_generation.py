from typing import Literal
from langgraph.types import Command
from src.state import DealEngineState


def email_generation_agent(state: DealEngineState) -> Command[Literal["supervisor"]]:
    """
    Enhanced email generation agent that uses opportunity and meeting context
    """
    # Get context from previous agents
    analysis = state.get("opportunity_analysis", {})
    opty_id = state.get("opportunity_id")
    deal_data = state.get("deal_data", {})
    completed_tasks = state.get("completed_tasks", [])

    if analysis and opty_id and "meeting_preparation" in completed_tasks:
        # Full context email
        account = deal_data.get("account_name", "Client")
        next_action = analysis.get("next_best_action", "Continue our discussion")

        response_content = f"""📧 **Follow-up Email for {opty_id}**

**Subject**: Great meeting today - Next steps for {account}

**Email Draft**:

Hi [Stakeholder Name],

Thank you for the productive conversation today regarding {account}. I wanted to recap our key discussion points and confirm next steps:

**Meeting Summary**:
• Reviewed current deal status and timeline
• Discussed solution alignment with your requirements  
• Addressed questions about implementation approach

**Agreed Next Steps**:
• {next_action}
• I'll follow up with additional materials by [DATE]
• Schedule next meeting for [DATE/TIME]

**Value Proposition Reminder**:
Our solution will help {account} achieve [key benefits discussed]. Based on today's conversation, I'm confident we can deliver the outcomes you're looking for.

Please let me know if you have any questions or need clarification on anything we discussed.

Best regards,
[Your Name]

**Email Tone**: Professional and follow-up focused
**Call to Action**: Confirm next meeting and review materials"""

    elif analysis and opty_id:
        # Opportunity context only
        account = deal_data.get("account_name", "Client")

        response_content = f"""📧 **Email Template for {opty_id}**

**Subject**: Following up on {account} opportunity

**Email Draft**:

Hi [Stakeholder Name],

I wanted to follow up on our {account} opportunity and share some insights from my recent analysis.

**Current Status**: 
Based on my review, I believe the next best step is to {analysis.get('next_best_action', 'schedule a follow-up discussion')}.

**Next Steps**:
I'd love to schedule time to discuss this further and answer any questions you might have.

Would you be available for a brief call this week?

Best regards,
[Your Name]

**Personalization Notes**: 
• Customize based on previous interactions
• Include relevant case studies or materials
• Adjust tone based on relationship level"""
    else:
        # Generic email
        response_content = """📧 **Email Generation Agent**

I can help craft professional emails! For better personalization:
1. First analyze an opportunity 
2. Optionally prepare meeting materials
3. Then I can create highly customized follow-up emails

**Generic Email Template**:

Subject: Following up on our conversation

Hi [Name],

Thank you for your time today. I wanted to follow up on our discussion about [topic].

Key points from our conversation:
• [Point 1]
• [Point 2]  
• [Point 3]

Next steps:
• [Action 1]
• [Action 2]

Please let me know if you have any questions.

Best regards,
[Your Name]

What type of email would you like me to help with?"""

    response_message = {
        "role": "assistant",
        "content": response_content,
        "name": "email_generation_agent",
    }

    # Update completed tasks
    completed = state.get("completed_tasks", [])
    if "email_generation" not in completed:
        completed = completed + ["email_generation"]

    return Command(
        goto="supervisor",
        update={"messages": [response_message], "completed_tasks": completed},
    )
