"""
Realistic email fixtures used across tasks.
"""
from env.models import Email

# ─── EASY TASK EMAILS ────────────────────────────────────────────────────────

EASY_EMAILS = [
    Email(
        id="e001",
        sender="Alice Johnson",
        sender_email="alice.johnson@bigcorp.com",
        subject="URGENT: Production database is down",
        body=(
            "Hi team,\n\n"
            "Our production database went down at 2:47 PM UTC. Customers cannot log in. "
            "Revenue is being impacted. We need an immediate response from the on-call engineer.\n\n"
            "Please escalate ASAP.\n\nAlice"
        ),
        timestamp="2024-01-15T14:52:00Z",
        is_vip=True,
    ),
]

# ─── MEDIUM TASK EMAILS ──────────────────────────────────────────────────────

MEDIUM_EMAILS = [
    Email(
        id="m001",
        sender="Bob Smith",
        sender_email="bob.smith@newsletter.io",
        subject="Your weekly digest is ready",
        body="Hi there! Here's your curated weekly digest of top articles in tech...",
        timestamp="2024-01-15T08:00:00Z",
    ),
    Email(
        id="m002",
        sender="Sarah Chen",
        sender_email="sarah.chen@enterprise-client.com",
        subject="Contract renewal - Q2 2024",
        body=(
            "Hello,\n\nOur contract expires on March 31st and we'd like to begin renewal discussions. "
            "We're generally happy with the service but have a few requests regarding SLA terms. "
            "Could we schedule a call this week?\n\nBest,\nSarah Chen\nVP Procurement"
        ),
        timestamp="2024-01-15T09:15:00Z",
        is_vip=True,
    ),
    Email(
        id="m003",
        sender="Noreply",
        sender_email="noreply@github.com",
        subject="[GitHub] Your pull request was merged",
        body="Your pull request #482 'Fix pagination bug' was successfully merged into main.",
        timestamp="2024-01-15T09:45:00Z",
    ),
    Email(
        id="m004",
        sender="Mark Torres",
        sender_email="mark.torres@acmeinc.com",
        subject="Invoice #2024-0112 overdue - FINAL NOTICE",
        body=(
            "This is a final notice that Invoice #2024-0112 for $14,500 is now 30 days overdue. "
            "Please remit payment immediately or contact us to discuss payment arrangements. "
            "Failure to respond may result in account suspension."
        ),
        timestamp="2024-01-15T10:00:00Z",
    ),
    Email(
        id="m005",
        sender="HR Team",
        sender_email="hr@yourcompany.com",
        subject="Action required: Benefits enrollment closes Friday",
        body=(
            "Reminder: Open enrollment for 2024 benefits closes this Friday at 5 PM. "
            "If you do not enroll, you will be defaulted to last year's plan. "
            "Please log in to the HR portal to review your options."
        ),
        timestamp="2024-01-15T10:30:00Z",
    ),
    Email(
        id="m006",
        sender="Jennifer Park",
        sender_email="jpark@potential-lead.com",
        subject="Interested in your enterprise plan",
        body=(
            "Hi,\n\nI came across your platform and I'm interested in learning more about your enterprise offerings. "
            "We're a 500-person company looking for a solution like yours. "
            "Do you have time for a 30-minute intro call?\n\nJen"
        ),
        timestamp="2024-01-15T11:00:00Z",
    ),
    Email(
        id="m007",
        sender="System Alert",
        sender_email="alerts@monitoring.internal",
        subject="[ALERT] High CPU usage on prod-server-03",
        body=(
            "ALERT: prod-server-03 CPU usage has exceeded 90% for the past 15 minutes. "
            "Current usage: 94%. Please investigate immediately."
        ),
        timestamp="2024-01-15T11:20:00Z",
    ),
    Email(
        id="m008",
        sender="Tom Bradley",
        sender_email="tom.bradley@colleague.com",
        subject="Lunch tomorrow?",
        body="Hey! Are you free for lunch tomorrow around 12:30? That new Thai place just opened.",
        timestamp="2024-01-15T12:00:00Z",
    ),
    Email(
        id="m009",
        sender="Legal Team",
        sender_email="legal@yourcompany.com",
        subject="New data processing agreement - signature required",
        body=(
            "Please review and sign the attached Data Processing Agreement (DPA) with CloudVendor Inc. "
            "This is required before we can proceed with the integration. "
            "Deadline: end of business today."
        ),
        timestamp="2024-01-15T13:00:00Z",
    ),
    Email(
        id="m010",
        sender="Promo Bot",
        sender_email="deals@shopdeals.xyz",
        subject="You won a $500 gift card! Click now!",
        body=(
            "Congratulations! You've been selected as our lucky winner! "
            "Click the link below to claim your $500 gift card. Limited time offer! "
            "http://totally-legit-deals.xyz/claim"
        ),
        timestamp="2024-01-15T13:30:00Z",
    ),
]

# ─── HARD TASK EMAILS ────────────────────────────────────────────────────────

HARD_EMAILS = [
    Email(
        id="h001",
        sender="CEO Office",
        sender_email="ceo@yourcompany.com",
        subject="Board deck - need by 4 PM TODAY",
        body=(
            "I need the updated Q4 board presentation by 4 PM today without fail. "
            "The board call is at 5 PM. This is your highest priority right now.\n\nDavid"
        ),
        timestamp="2024-01-15T10:00:00Z",
        is_vip=True,
    ),
    Email(
        id="h002",
        sender="Angry Customer",
        sender_email="john.doe@customer.com",
        subject="Your service ruined my business - I'm suing",
        body=(
            "Your platform went down during our product launch and we lost over $50,000 in sales. "
            "I have screenshots, logs, and my lawyer is already involved. "
            "I expect a personal call from your CEO by end of day or I will be going to the press."
        ),
        timestamp="2024-01-15T10:15:00Z",
    ),
    Email(
        id="h003",
        sender="Security Team",
        sender_email="security@yourcompany.com",
        subject="Possible data breach detected - CONFIDENTIAL",
        body=(
            "CONFIDENTIAL - Do not forward.\n\n"
            "Our intrusion detection system flagged unusual data export activity from user account #88423 "
            "at 3 AM UTC. Approximately 12,000 customer records may have been accessed. "
            "We are investigating but need guidance on whether to notify affected customers now "
            "and whether to loop in legal and PR. Please advise."
        ),
        timestamp="2024-01-15T10:30:00Z",
        is_vip=True,
    ),
    Email(
        id="h004",
        sender="CTO",
        sender_email="cto@yourcompany.com",
        subject="Re: Board deck - use last month's numbers",
        body=(
            "Ignore David's email - the board deck is already handled. "
            "Use the Q3 numbers, NOT Q4. I'll explain later. Don't reply to David directly."
        ),
        timestamp="2024-01-15T10:35:00Z",
        is_vip=True,
        thread_id="board-deck-thread",
    ),
    Email(
        id="h005",
        sender="Regulatory Body",
        sender_email="compliance@gdpr-authority.eu",
        subject="Data Subject Access Request - Response required within 72 hours",
        body=(
            "We have received a complaint from a data subject regarding your handling of personal data. "
            "Under GDPR Article 15, you are required to respond within 72 hours. "
            "Reference: GDPR-2024-00892. Please confirm receipt and provide a timeline for resolution."
        ),
        timestamp="2024-01-15T11:00:00Z",
    ),
    Email(
        id="h006",
        sender="PR Agency",
        sender_email="contact@prfirm.com",
        subject="TechCrunch wants a comment on the outage - 2 hour deadline",
        body=(
            "TechCrunch is running a story on yesterday's outage and has reached out for comment. "
            "They need a response by 1 PM. Do you want us to handle this or will your comms team respond directly? "
            "We recommend a brief acknowledgment + commitment to a postmortem."
        ),
        timestamp="2024-01-15T11:15:00Z",
    ),
    Email(
        id="h007",
        sender="Top Client",
        sender_email="procurement@mega-client.com",
        subject="Considering switching providers",
        body=(
            "Given yesterday's outage and the lack of proactive communication from your team, "
            "we are formally evaluating alternative providers. Our contract is worth $2.4M annually. "
            "We expect a call with your account executive and VP of Engineering today."
        ),
        timestamp="2024-01-15T11:30:00Z",
        is_vip=True,
    ),
    Email(
        id="h008",
        sender="Finance",
        sender_email="finance@yourcompany.com",
        subject="Wire transfer approval needed - $240,000",
        body=(
            "We need approval for a wire transfer of $240,000 to vendor CloudInfra Ltd by EOD. "
            "This is for the annual infrastructure contract. The CFO is traveling and unreachable. "
            "Can you authorize?"
        ),
        timestamp="2024-01-15T12:00:00Z",
    ),
    Email(
        id="h009",
        sender="Employee",
        sender_email="anon.report@yourcompany.com",
        subject="Anonymous HR complaint",
        body=(
            "I am submitting this anonymously. My manager has been creating a hostile work environment "
            "and I have witnessed behavior that may violate company policy. "
            "I am afraid of retaliation if I go through normal channels. Please advise on next steps."
        ),
        timestamp="2024-01-15T12:30:00Z",
    ),
    Email(
        id="h010",
        sender="Competitor",
        sender_email="bd@competitor-corp.com",
        subject="Acquisition conversation?",
        body=(
            "Hi, I'm the VP of Business Development at CompetitorCorp. "
            "Our leadership has been watching your growth and we'd like to explore whether "
            "there's a conversation to be had about a potential acquisition or strategic partnership. "
            "Happy to sign an NDA first. Would you be open to a call?"
        ),
        timestamp="2024-01-15T13:00:00Z",
    ),
]
