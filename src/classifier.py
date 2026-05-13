"""
classifier.py(query classification engine.)
─────────────
Classifies a guest message into one of 6 query types using keyword matching.
Simple, transparent, and easy to extend later with ML if needed.
"""

def classify_message(message: str) -> str:
    """
    Returns one of:
      pre_sales_availability | pre_sales_pricing | post_sales_checkin
      special_request        | complaint         | general_enquiry
    """
    text = message.lower()

    # ── Complaint signals ────────────────────────────────────────────────────
    complaint_keywords = [
        "not working", "broken", "unhappy", "disappointed", "terrible",
        "horrible", "bad experience", "worst", "unacceptable", "dirty",
        "disgusting", "noisy", "refund", "complain", "complaint", "issue",
        "problem", "fault", "damaged"
    ]
    if any(kw in text for kw in complaint_keywords):
        return "complaint"

    # ── Special request signals ──────────────────────────────────────────────
    special_keywords = [
        "early check", "late check", "airport", "transfer", "pickup",
        "cab", "taxi", "birthday", "anniversary", "decoration", "surprise",
        "special arrangement", "extra bed", "crib", "baby"
    ]
    if any(kw in text for kw in special_keywords):
        return "special_request"

    # ── Post-sales check-in signals ──────────────────────────────────────────
    checkin_keywords = [
        "check in", "check-in", "check out", "checkout", "wifi", "wi-fi",
        "password", "access code", "key", "directions", "address", "how to get",
        "caretaker", "contact", "arrival", "parking"
    ]
    if any(kw in text for kw in checkin_keywords):
        return "post_sales_checkin"

    # ── Pre-sales pricing signals ────────────────────────────────────────────
    pricing_keywords = [
        "rate", "price", "cost", "charge", "how much", "per night",
        "tariff", "fee", "pricing", "quote", "discount", "offer"
    ]
    if any(kw in text for kw in pricing_keywords):
        return "pre_sales_pricing"

    # ── Pre-sales availability signals ──────────────────────────────────────
    availability_keywords = [
        "available", "availability", "dates", "from", "to", "book",
        "reserve", "vacancy", "open", "free", "slot"
    ]
    if any(kw in text for kw in availability_keywords):
        return "pre_sales_availability"

    # ── Default: general enquiry ─────────────────────────────────────────────
    return "general_enquiry"


#The classifier is single-label. A message can contain both a complaint and a special request.
#  I'd improve it by either allowing multiple labels, or using a Claude API call to classify instead of keyword matching — which handles nuance much better.