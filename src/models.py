from pydantic import BaseModel
from typing import Optional

#the raw incoming webhook payload.
# ── What comes IN from the webhook(different sources like stated below ) ──────────────────────────────────────────
class InboundMessage(BaseModel):
    source: str          # "whatsapp", "booking_com", "airbnb", "instagram", "direct"
    guest_name: str    #personalization,crm,ai replies
    message: str         #raw message
    timestamp: str        #Time message was received.Important for:conversation history.ordering messages.analytics.SLA tracking
    booking_ref: Optional[str] = None  #These fields may or may not exist.
    property_id: Optional[str] = None      #Instagram DMs may not have booking references.


# ── The normalised / unified schema (internal use) ───────────────────────────
class NormalisedMessage(BaseModel):
    message_id: str 
    source: str
    guest_name: str #confidence scoring
    message_text: str
    timestamp: str
    booking_ref: Optional[str] = None
    property_id: Optional[str] = None
    query_type: str      # classified category


# ── What goes OUT as the response ───────────────────────────────────────────
class WebhookResponse(BaseModel):
    message_id: str
    query_type: str
    drafted_reply: str #Human may review later.ai drafted 
    confidence_score: float #trust-control mechanism which works on probability scores.Helps decide whether to auto-send, ask for human review, or escalate.
    action: str          # "auto_send", "agent_review", or "escalate"

    #| Score     | Action       |
#| --------- | ------------ |
#| >0.85     | auto_send    |
#| 0.60–0.85 | agent_review |
#| <0.60     | escalate     |

#RAW EXTERNAL DATA
#    ↓
#InboundMessage

#STANDARDIZED INTERNAL DATA
#    ↓
#NormalisedMessage

#FINAL API OUTPUT
#    ↓
#WebhookResponse

## Separate schemas keep external webhook payloads independent from internal processing.
# Normalization creates one consistent format across all channels, making AI handling,
# analytics, and routing easier to scale and maintain.