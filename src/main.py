"""
main.py
───────
Nistula Guest Message Handler — Part 1 Assessment
FastAPI webhook endpoint that receives guest messages, normalises them,
classifies them, gets a Claude-drafted reply, and returns a confidence score.

Run with:  uvicorn main:app --reload
"""

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from models import InboundMessage, NormalisedMessage, WebhookResponse
from classifier import classify_message
from claude_client import get_drafted_reply
from scorer import calculate_confidence, get_action

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Nistula Guest Message Handler",
    description="Unified AI-powered guest messaging backend for Nistula villas",
    version="1.0.0"
)


# ── Health check endpoint ────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "Nistula Message Handler is running"}


# ── Main webhook endpoint ────────────────────────────────────────────────────
@app.post("/webhook/message", response_model=WebhookResponse)
async def handle_message(payload: InboundMessage):
    """
    Receives an inbound guest message from any channel.
    Steps:
      1. Validate and normalise into unified schema
      2. Classify the query type
      3. Send to Claude API for a drafted reply
      4. Score the reply and decide the action
      5. Return the full response
    """

    # ── Step 1: Validate source channel ─────────────────────────────────────
    valid_sources = {"whatsapp", "booking_com", "airbnb", "instagram", "direct"}
    if payload.source not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source '{payload.source}'. Must be one of: {valid_sources}"
        )

    # ── Step 2: Classify the message ────────────────────────────────────────
    query_type = classify_message(payload.message)

    # ── Step 3: Normalise into unified schema ────────────────────────────────
    normalised = NormalisedMessage(
        message_id=str(uuid.uuid4()),    # generate a unique ID
        source=payload.source,
        guest_name=payload.guest_name,
        message_text=payload.message,
        timestamp=payload.timestamp,
        booking_ref=payload.booking_ref,
        property_id=payload.property_id,
        query_type=query_type
    )

    # ── Step 4: Get Claude's drafted reply ───────────────────────────────────
    try:
        drafted_reply = get_drafted_reply(normalised)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Claude API error: {str(e)}"
        )

    # ── Step 5: Score the reply and decide action ────────────────────────────
    confidence_score = calculate_confidence(
        query_type=query_type,
        drafted_reply=drafted_reply,
        guest_name=payload.guest_name
    )
    action = get_action(confidence_score, query_type)

    # ── Step 6: Return the response ──────────────────────────────────────────
    return WebhookResponse(

        message_id=normalised.message_id,
        query_type=query_type,
        drafted_reply=drafted_reply,
        confidence_score=confidence_score,
        action=action
    )


# ── Global error handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )