Question A — The Immediate Response
The message:

Hi [Guest Name], I'm so sorry — this is completely unacceptable and I understand how stressful this is with guests arriving in a few hours. I've flagged this as urgent right now and our caretaker will call you within the next 15 minutes to resolve this tonight. Your comfort is our priority and we will make this right.

Why i chose this wording: it Never uses "we'll try to do" or "as soon as we can"; makes a tangible promise of 15 minutes to make the emergency not feel overwhelming anymore. It recognizes the need for a refund without explicitly offering one or refusing one, which means making that decision is left to a person at 3 am.

Question B — The System Design
At the point where the message has been identified as a complaint based on keywords “no hot water” + “refund”, the following sequence occurs automatically:

Confidence score dictates an escalation, which means that there is no automatic sending by AI. Message is composed and queued for human approval but sent instantly considering the time stamp.
Whitelist care taker receives a WhatsApp notification with guest name, villa, and complaint – no generic ping.
Owner is alerted through WhatsApp with all relevant details – guest’s name, reservation ID, issue raised, and an acknowledgment button with just one tap.
Escalated conversation is recorded with the time stamp, complaint text, query type complaint, and the addition of a new tag ‘maintenance_hot_water’ to both guest’s account and property listing.
30-minute timeout begins for no response by any human. In case no human has responded yet, the system escalates further – sends another alert to the owner with ‘URGENT’ tag, and the AI responds to the guest with an assurance that we are working on the issue.


Question C — The Learning
Three cases of hot water complaints within two months is clearly a pattern; not a case of bad luck. The system needs to:

Tag complaints automatically based on keywords and properties. Pattern flag needs to kick in after second complaint.
Generate a maintenance checklist for Villa B1 - this should be done automatically right after the second complaint, and the checklist should need approval.
Block all B1 complaints from being auto-sent till maintenance is marked as resolved.

What I'd build: The first part of the system we call “Property Health Dashboard” – where each property has an active issue log. If there are three similar complaints from guests within a span of 60 days, then a maintenance issue is flagged up for the owner and a vendor is scheduled for visit.