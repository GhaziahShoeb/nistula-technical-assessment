# Nistula Guest Message Handler
### Part 1 — Technical Assessment | Summer Internship 2026

---

## What This Builds

A production-style backend webhook system that:
- Receives guest messages from any of Nistula's 5 channels
- Normalises them into a unified schema
- Classifies the query type automatically
- Gets a warm, accurate AI-drafted reply via Claude API
- Returns a confidence score and recommended action

---

## Project Structure

```
nistula-assessment/
├── main.py            ← FastAPI app + /webhook/message endpoint
├── classifier.py      ← Keyword-based query type classifier
├── claude_client.py   ← Claude API integration + property context
├── scorer.py          ← Confidence scoring logic
├── models.py          ← Pydantic data models (schemas)
├── .env               ← API key (not committed to git)
├── requirements.txt   ← Python dependencies
└── README.md          ← This file
```

---

## How to Run

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key to .env
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 4. Start the server
uvicorn main:app --reload

# Server runs at: http://localhost:8000
# API docs at:    http://localhost:8000/docs
```

---

## Confidence Scoring Logic

The confidence score (0.0 to 1.0) is calculated in `scorer.py` using 4 signals:

### Base Score: 0.75

| Signal | Condition | Adjustment |
|--------|-----------|------------|
| **Query type** | Complaint | -0.30 |
| | Special request | -0.10 |
| | Availability or Pricing | +0.10 |
| | Post-sales check-in | +0.08 |
| **Reply length** | < 50 characters | -0.20 |
| | > 150 characters | +0.08 |
| **Personalisation** | Guest name in reply | +0.04 |
| | Property details in reply | +0.04 |
| **Uncertainty signals** | "I'm not sure", "please contact" etc. | -0.15 |

### Action Mapping

| Score | Action |
|-------|--------|
| ≥ 0.85 | `auto_send` — reply is confident, send automatically |
| 0.60 – 0.84 | `agent_review` — human should check before sending |
| < 0.60 | `escalate` — needs human handling |
| *Any complaint* | `escalate` — always, regardless of score |

**Rationale:** Complaints are always escalated because they carry reputational risk — even a perfect AI reply can feel dismissive to an unhappy guest. Straightforward factual queries (availability, pricing) score higher because the property context fully covers them. Uncertainty signals in Claude's reply are penalised because they suggest the AI couldn't answer confidently.

---

## API Usage

### Endpoint
```
POST http://localhost:8000/webhook/message
Content-Type: application/json
```

### Request Body
```json
{
  "source": "whatsapp",
  "guest_name": "Rahul Sharma",
  "message": "Is the villa available from April 20 to 24? What is the rate for 2 adults?",
  "timestamp": "2026-05-05T10:30:00Z",
  "booking_ref": "NIS-2024-0891",
  "property_id": "villa-b1"
}
```

### Response
```json
{
  "message_id": "3f7a1c2e-...",
  "query_type": "pre_sales_availability",
  "drafted_reply": "Hi Rahul! Great news — Villa B1 is available from April 20 to 24...",
  "confidence_score": 0.91,
  "action": "auto_send"
}
```

---

## Test Cases

Three different inputs tested (run via Swagger UI at `/docs`):

**Test 1 — Availability + Pricing (WhatsApp)**
```json
{ "source": "whatsapp", "guest_name": "Rahul Sharma",
  "message": "Is the villa available from April 20 to 24? Rate for 2 adults?",
  "timestamp": "2026-05-05T10:30:00Z", "booking_ref": "NIS-2024-0891", "property_id": "villa-b1" }
```

**Test 2 — Check-in Query (Airbnb)**
```json
{ "source": "airbnb", "guest_name": "Priya Mehta",
  "message": "What time can we check in? Also what is the WiFi password?",
  "timestamp": "2026-05-06T08:00:00Z", "booking_ref": "NIS-2024-0902", "property_id": "villa-b1" }
```

**Test 3 — Complaint (Booking.com)**
```json
{ "source": "booking_com", "guest_name": "James Wilson",
  "message": "The AC in the master bedroom is not working. I am very unhappy.",
  "timestamp": "2026-05-07T14:00:00Z", "booking_ref": "NIS-2024-0910", "property_id": "villa-b1" }
```

---

## Architecture Notes

- **No hardcoded secrets** — API key loaded from `.env` via `python-dotenv`
- **Graceful error handling** — Claude API errors return 502 with clear message; invalid source returns 400
- **Extensible classifier** — keyword lists can be swapped for an ML classifier later
- **Stateless design** — each request is fully self-contained; easy to scale horizontally
- **FastAPI auto-docs** — visit `/docs` to test interactively in browser


for making the server live 

uvicorn main:app --reload

## Testing

Run all three test cases in a new terminal tab while the server is running.

**Test 1 — Availability + Pricing (WhatsApp)**
```bash
curl -X POST http://localhost:8000/webhook/message \
  -H "Content-Type: application/json" \
  -d '{
    "source": "whatsapp",
    "guest_name": "Rahul Sharma",
    "message": "Is the villa available from April 20 to 24? What is the rate for 2 adults?",
    "timestamp": "2026-05-05T10:30:00Z",
    "booking_ref": "NIS-2024-0891",
    "property_id": "villa-b1"
  }'
```

**Test 2 — Check-in Query (Airbnb)**
```bash
curl -X POST http://localhost:8000/webhook/message \
  -H "Content-Type: application/json" \
  -d '{
    "source": "airbnb",
    "guest_name": "Priya Mehta",
    "message": "What time can we check in? Also what is the WiFi password?",
    "timestamp": "2026-05-06T08:00:00Z",
    "booking_ref": "NIS-2024-0902",
    "property_id": "villa-b1"
  }'
```

**Test 3 — Complaint (Booking.com)**
```bash
curl -X POST http://localhost:8000/webhook/message \
  -H "Content-Type: application/json" \
  -d '{
    "source": "booking_com",
    "guest_name": "James Wilson",
    "message": "The AC in the master bedroom is not working. I am very unhappy.",
    "timestamp": "2026-05-07T14:00:00Z",
    "booking_ref": "NIS-2024-0910",
    "property_id": "villa-b1"
  }'
```

**Expected results:**
- Test 1 → `query_type: pre_sales_pricing`, `action: auto_send`
- Test 2 → `query_type: post_sales_checkin`, `action: auto_send`  
- Test 3 → `query_type: complaint`, `action: escalate`# nistula-technical-assessment
