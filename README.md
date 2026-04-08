---
title: Email Triage OpenEnv
emoji: 📬
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
---



<<<<<<< HEAD
# 📬 Email Triage OpenEnv

> A real-world email triage environment for evaluating AI agents — built for the Meta OpenEnv Hackathon.

[![openenv](https://img.shields.io/badge/openenv-compliant-blue)](https://huggingface.co/spaces)
[![Python](https://img.shields.io/badge/python-3.11+-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)](https://fastapi.tiangolo.com)

---

## Overview & Motivation

Email triage is one of the most universal real-world tasks performed by knowledge workers. It requires:
- **Reading comprehension** to understand email intent and urgency
- **Contextual judgment** to distinguish VIP from routine senders
- **Policy adherence** to follow organizational rules (don't reply to legal threats without counsel)
- **Risk awareness** to detect social engineering (suspicious wire transfers)
- **Prioritization** under time pressure with competing high-stakes demands

Unlike toy problems or games, email triage produces immediate, measurable business impact. It's a perfect benchmark for agent capabilities that generalize to real enterprise workflows.

---

## Environment Architecture

```
openenv-email-triage/
├── app.py                      # FastAPI REST API (HF Spaces entry point)
├── openenv.yaml                # OpenEnv specification metadata
├── Dockerfile                  # Container definition
├── requirements.txt
├── env/
│   ├── email_triage_env.py     # EmailTriageEnv — main environment class
│   ├── models.py               # Pydantic typed models (Observation, Action, Reward)
│   └── email_fixtures.py       # Realistic email dataset for all tasks
├── graders/
│   └── task_graders.py         # Deterministic per-task graders (0.0–1.0)
├── scripts/
│   └── run_baseline.py         # Inference script (rule-based + LLM)
└── tests/
    └── test_env.py             # Pytest test suite
```

---

## Action Space

Actions are submitted as JSON objects with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_type` | enum | ✅ | One of: `label`, `reply`, `escalate`, `archive`, `delete`, `move`, `summarize`, `flag`, `done` |
| `email_id` | string | Most actions | The ID of the email to act on |
| `label` | string | For `label`, `flag` | Label to apply (e.g. `"urgent"`, `"spam"`, `"vip"`) |
| `reply_body` | string | For `reply` | Text of the reply |
| `reason` | string | Optional | Reason for escalation or flagging |
| `destination` | string | For `move` | Target folder |

**Terminal action**: `{"action_type": "done"}` — ends the episode and triggers final scoring.

---

## Observation Space

Each step returns an `Observation` object:

| Field | Type | Description |
|-------|------|-------------|
| `inbox` | List[Email] | All emails currently in the inbox |
| `current_email` | Email \| null | The first unprocessed email |
| `task_description` | string | Natural language task instructions |
| `step_count` | int | Steps taken so far |
| `context` | dict | Task-specific context (policy notes, VIP lists) |
| `done` | bool | Whether the episode is complete |
| `message` | string | Feedback from the last action |

**Email object fields**: `id`, `sender`, `sender_email`, `subject`, `body`, `timestamp`, `is_read`, `labels`, `is_vip`, `thread_id`, `attachments`

---

## Tasks

### Task 1: Single Email Classification (`task_easy`)
**Difficulty**: 🟢 Easy | **Max Steps**: 8 | **Emails**: 1

The agent receives a single urgent email reporting a production database outage. The agent must:
1. Label the email as `"urgent"`
2. Escalate it

**Scoring**:
- +0.5 for correct urgent label
- +0.5 for escalation
- -0.3 for deleting the email
- -0.2 for archiving without escalating
- -0.05 per unnecessary action

**Baseline score (rule-based)**: **1.00**

---

### Task 2: Inbox Triage (`task_medium`)
**Difficulty**: 🟡 Medium | **Max Steps**: 25 | **Emails**: 10

A realistic 10-email inbox containing:
- Newsletter → archive
- VIP contract renewal → flag as VIP
- GitHub notification → archive
- Overdue invoice final notice → escalate as urgent
- HR enrollment deadline → flag as action-required
- Sales lead inquiry → label as sales-lead
- Server CPU alert → escalate
- Personal lunch invite → archive
- Legal document signature required → flag as action-required
- Phishing/spam → delete

Each email is worth 0.1 points. Partial credit is awarded for close-but-not-perfect actions (e.g., flagging instead of escalating).

**Baseline score (rule-based)**: **1.00**

---

### Task 3: Escalation Workflow Under Ambiguity (`task_hard`)
**Difficulty**: 🔴 Hard | **Max Steps**: 30 | **Emails**: 10

A high-pressure crisis day with 10 emails featuring:
- **Conflicting executive instructions** (CEO vs CTO on board deck — must escalate, not choose)
- **Legal threat** from angry customer (must NOT reply without legal review)
- **Potential data breach** (highest-stakes email — deletion is severely penalized)
- **GDPR regulatory deadline** (72-hour response window)
- **PR crisis** (TechCrunch comment deadline)
- **$2.4M client threatening churn**
- **Suspicious wire transfer** ($240k without CFO) — social engineering risk
- **Anonymous HR complaint**
- **Competitor acquisition inquiry**

Scoring is weighted by email criticality. Forbidden actions (deleting breach/legal emails, replying to legal threats) incur severe penalties.

**Policy notes** are provided in the observation context to guide correct behavior.

**Baseline score (rule-based)**: **~0.95**

---

## Reward Function

Rewards are **incremental** — the agent receives feedback after every action, not just at episode end.

- **Positive deltas**: Correct actions yield immediate reward proportional to their importance
- **Negative deltas**: Wrong actions, forbidden actions, and redundant actions incur penalties
- **Step budget penalty**: Exceeding the step budget deducts 0.05 from the final score
- **Final score**: Computed via task-specific grader on `done` action, bounded to [0.0, 1.0]

---

## Setup & Usage

### Prerequisites
- Python 3.11+
- Docker (for containerized deployment)

### Local Installation

```bash
git clone https://huggingface.co/spaces/your-username/email-triage-openenv
cd email-triage-openenv
pip install -r requirements.txt
```

### Run the API Server

```bash
python app.py
# Server starts at http://localhost:7860
# API docs at http://localhost:7860/docs
```

### Validate with OpenEnv

```bash
openenv validate .
```

### Run the Baseline

```bash
# Rule-based baseline (no API key needed)
python scripts/run_baseline.py --task all --mode rule_based

# LLM baseline (requires HF_TOKEN)
HF_TOKEN=your_token python scripts/run_baseline.py --task all --mode llm
```

### Run Tests

```bash
python -m pytest tests/ -v
```

---

## Docker Deployment

### Build

```bash
docker build -t email-triage-openenv .
```

### Run

```bash
docker run -p 7860:7860 email-triage-openenv
```

### Run with HF Token (for LLM baseline inside container)

```bash
docker run -p 7860:7860 -e HF_TOKEN=your_token email-triage-openenv
```

---

## API Usage Example

```python
import requests

BASE = "http://localhost:7860"

# 1. Reset environment
obs = requests.post(f"{BASE}/reset", json={"task_id": "task_medium", "session_id": "s1"}).json()
print(f"Task: {obs['observation']['task_description'][:80]}...")

# 2. Take actions
result = requests.post(f"{BASE}/step", json={
    "session_id": "s1",
    "action_type": "archive",
    "email_id": "m001"
}).json()
print(f"Reward: {result['reward']['value']} — {result['reward']['explanation']}")

# 3. Signal done
result = requests.post(f"{BASE}/step", json={
    "session_id": "s1",
    "action_type": "done"
}).json()
print(f"Final Score: {result['info']['final_score']}")
```

---

## Baseline Performance Scores

| Task | Difficulty | Rule-Based Baseline | Random Baseline |
|------|-----------|---------------------|-----------------|
| `task_easy` | 🟢 Easy | **1.00** | ~0.15 |
| `task_medium` | 🟡 Medium | **1.00** | ~0.20 |
| `task_hard` | 🔴 Hard | **~0.95** | ~0.05 |

The gap between random and rule-based baselines demonstrates that the tasks require genuine reasoning. The hard task's ~0.95 ceiling (vs 1.0) reflects realistic ambiguity where even a perfect rule set can't achieve full marks without nuanced contextual judgment.

---

## Hugging Face Deployment

This environment is tagged with `openenv` and deployed as a Hugging Face Space with Docker runtime. The Space runs the FastAPI server on port 7860, which is HF's default.

---

## License

MIT
=======
---
title: Email Triage Openenv
emoji: 🌍
colorFrom: gray
colorTo: pink
sdk: docker
pinned: false
license: mit
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
>>>>>>> a23806b1722024deb7c158d2ac394ab2dcdfdd49
