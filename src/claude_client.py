"""
claude_client.py
────────────────
Sends the normalised message + property context to Claude API
and returns a drafted reply string.
"""

import os
import anthropic
from models import NormalisedMessage


# ── Static property context (mock data as provided in the assessment) ──────── #saves from hallucination 
#context injection / grounding.
PROPERTY_CONTEXT = """
Property: Villa B1, Assagao, North Goa
Bedrooms: 3 | Max guests: 6 | Private pool: Yes
Check-in: 2pm | Check-out: 11am
Base rate: INR 18,000 per night (up to 4 guests)
Extra guest charge: INR 2,000 per night per person
WiFi password: Nistula@2024
Caretaker: Available 8am to 10pm
Chef on call: Yes, pre-booking required
Availability April 20-24: Available
Cancellation policy: Free cancellation up to 7 days before check-in
""".strip()

# ── System prompt: tells Claude who it is and how to behave ─────────────────
SYSTEM_PROMPT = """
You are a warm, professional guest relations assistant for Nistula — a luxury 
private villa brand in Assagao, North Goa. Your job is to draft helpful, 
friendly, and accurate replies to guest enquiries.

Guidelines:
- Always address the guest by their first name
- Be warm but professional — like a five-star concierge, not a chatbot
- Use the property details provided to answer factually
- If something is not in the property details, say you will check and get back shortly
- Keep replies concise but complete (3-6 sentences is ideal)
- Never make up prices, availability, or policies not given to you
- End with an offer to help further
""".strip()


def get_drafted_reply(msg: NormalisedMessage) -> str:
    """
    Calls the Claude API with the message and property context.
    Returns the drafted reply as a plain string.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Build the user prompt with all relevant context
    user_prompt = f"""
Property details:
{PROPERTY_CONTEXT}

Guest name: {msg.guest_name}
Channel: {msg.source}
Query type: {msg.query_type}
Booking reference: {msg.booking_ref or "Not provided"}
Message from guest:
\"{msg.message_text}\"

Please draft a reply to this guest message.
""".strip()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    # Extract the text from Claude's response
    return response.content[0].text.strip()


#Take structured guest data
#        ↓
#Add business context
#        ↓
#Prompt Claude properly
#        ↓
#Get a drafted hospitality reply

