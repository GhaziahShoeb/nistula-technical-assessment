"""
scorer.py
─────────
Calculates a confidence score (0.0 – 1.0) for a drafted reply.

SCORING LOGIC (explained for README):
──────────────────────────────────────
We start at a base of 0.75 and adjust up/down based on 4 signals:

1. QUERY TYPE  (+/-)
   - Complaints always score low (we never auto-send on complaints)
   - Straightforward query types (availability, pricing, checkin) score higher

2. REPLY LENGTH  (+/-)
   - Very short replies (<50 chars) suggest Claude couldn't answer properly → lower
   - Reasonable replies (>150 chars) suggest a complete, helpful answer → higher

3. KEYWORD PRESENCE  (+)
   - If the reply mentions the guest's name → more personalised → higher
   - If the reply contains specific property details (pool, chef, rate) → higher

4. UNCERTAINTY SIGNALS  (-)
   - If Claude's reply contains hedging phrases like "I'm not sure",
     "I don't know", "please contact" → lower score
"""


def calculate_confidence(
    query_type: str,
    drafted_reply: str,
    guest_name: str
) -> float:

    score = 0.75  # base score

    # ── 1. Query type adjustment ─────────────────────────────────────────────
    query_adjustments = {
        "complaint":              -0.30,   # always needs human review
        "special_request":        -0.10,   # usually needs personalisation
        "general_enquiry":         0.00,   # neutral
        "pre_sales_availability":  0.10,   # well-defined, easy to answer
        "pre_sales_pricing":       0.10,   # well-defined, easy to answer
        "post_sales_checkin":      0.08,   # factual info, mostly static
    }
    score += query_adjustments.get(query_type, 0.0)

    # ── 2. Reply length adjustment ───────────────────────────────────────────
    reply_len = len(drafted_reply)
    if reply_len < 50:
        score -= 0.20   # suspiciously short — something went wrong
    elif reply_len > 150:
        score += 0.08   # good, detailed reply

    # ── 3. Personalisation and property detail keywords ──────────────────────
    reply_lower = drafted_reply.lower()
    first_name = guest_name.split()[0].lower()

    if first_name in reply_lower:
        score += 0.04   # addressed guest by name

    property_signals = ["pool", "chef", "caretaker", "inr", "check-in",
                        "check in", "wifi", "nistula", "villa"]
    if any(kw in reply_lower for kw in property_signals):
        score += 0.04   # reply contains specific property info

    # ── 4. Uncertainty / deflection signals ─────────────────────────────────
    uncertainty_signals = [
        "i'm not sure", "i am not sure", "i don't know", "i do not know",
        "please contact", "cannot answer", "unable to provide",
        "not available", "i apologize but"
    ]
    if any(sig in reply_lower for sig in uncertainty_signals):
        score -= 0.15   # Claude hedged — needs human review

    # ── Clamp to [0.0, 1.0] ──────────────────────────────────────────────────
    return round(max(0.0, min(1.0, score)), 2)


def get_action(confidence_score: float, query_type: str) -> str:
    """
    Decide what to do with the drafted reply based on score and type.
    """
    if query_type == "complaint":
        return "escalate"   # complaints always go to a human, regardless of score

    if confidence_score >= 0.85:
        return "auto_send"
    elif confidence_score >= 0.60:
        return "agent_review"
    else:
        return "escalate"
    
#Claude generates reply
#        ↓
#Scorer evaluates quality/risk
#        ↓
#System decides:
#- auto_send
#- agent_review
#a- escalate    