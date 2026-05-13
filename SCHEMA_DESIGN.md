# Part 2 — Schema Design Decisions

---

## Table Overview

| Table | Purpose |
|-------|---------|
| `properties` | Each villa that the Nistula manages |
| `guests` | One record per real human, across all channels |
| `reservations` | One record per booking, linked to guest + property |
| `conversations` | Groups messages into threads per guest per topic |
| `messages` | Every message from every channel, with full AI lifecycle |
| `guest_channel_identities` | Bonus: maps guests to their IDs on each platform |

---

## Design Decisions

#1. one unified column for all channels .

instead of adding columns in the table as the channel number grew per person i have decided to add rows instead .there is a `channel` column .This makes unified inbox 
queries trivial — one SELECT with no JOINs across tables.it makes the system scalable 

#2. `conversations` sits between guests and messages.

it is different from messages as it holds a link between each interaction making it a thread to keep track .it can exist before a reservation is made (reservation_id is 
nullable). This models reality accurately.

#3.  Both `ai_drafted_reply` and `message_text` stored on outbound messages.

ai_drafted_reply is what Claude drafted as a reply to send to the guest. message_text is what was actually sent sometimes an agent edits Claude's draft before sending. Storing both lets ,Nistula compare them over time and improve the AI. to make it better by learning what is changed later.

#4.`raw_payload JSONB` on messages.

Webhook JSON payload is kept as is in its original form. This is your audit trail: in case a bug 
misidentifies any messages or removes any fields, you can re-process everything using the original payload.

#5.`reply_status` tracks the full AI lifecycle

Five metrics encompass everything that is needed: `ai_drafted` → `agent_edited` or `auto_sent` or 
`agent_sent` or `escalated`. From there, you will know exactly what proportion of 
Nistula’s messages is automatically generated as opposed to being manually edited.



---

## The Hardest Design Decision

**How to identify that two messages from different channels are the same guest.**

A guest called "Rahul Sharma" may make inquiries through WhatsApp via his contact number,
book through Airbnb via another email address, and communicate with Instagram via another username,
which has nothing to do with either. All these platforms provide you with unique identification.
When you create new guest accounts each time, you will have three Rahuls — none of whom is
recognized or tracked for revenue purposes or loyalty programs.

I solved it in two tiers. First, the database contains a nullable unique 
field for each type of identifier (e.g., `whatsapp_id`, `airbnb_guest_id`) 
along with `email` and `phone` as the main de-duplication fields. When a new 
message is received, a query is made to see whether such a phone number/
email/channel id exists already, and if it does, it's matched; otherwise, 
it's created.

Second, I introduced the `guest_channel_identities` table as an extra normalized option. The latter represents a more elegant solution for the future – to create a new channel (such as Expedia), you need only insert a row into the database, rather than modify the `guests` table. Although in production I would transition to the latter approach, discarding the channel-specific columns from the `guests` table, keeping both options demonstrates my awareness of both approaches.

The truth of the matter is that this issue doesn’t have an optimal solution at the data layer by itself— 
it’s something that would eventually involve implementing a probabilistic matching algorithm (fuzzy name + phone + email matching), which is a typical identity resolution challenge 
solved by platforms such as Segment and Salesforce.