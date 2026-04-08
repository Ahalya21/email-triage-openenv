"""
Typed Pydantic models for the Email Triage OpenEnv environment.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


# ─── Email Data Model ────────────────────────────────────────────────────────

class EmailPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    SPAM = "spam"


class Email(BaseModel):
    id: str
    sender: str
    sender_email: str
    subject: str
    body: str
    timestamp: str
    is_read: bool = False
    labels: List[str] = Field(default_factory=list)
    is_vip: bool = False
    thread_id: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)


# ─── Observation Model ───────────────────────────────────────────────────────

class Observation(BaseModel):
    inbox: List[Email]
    current_email: Optional[Email]
    task_description: str
    step_count: int = 0
    context: Dict[str, Any] = Field(default_factory=dict)
    done: bool = False
    message: str = ""


# ─── Action Model ────────────────────────────────────────────────────────────

class ActionType(str, Enum):
    LABEL = "label"
    REPLY = "reply"
    ESCALATE = "escalate"
    ARCHIVE = "archive"
    DELETE = "delete"
    MOVE = "move"
    SUMMARIZE = "summarize"
    FLAG = "flag"
    DONE = "done"


class Action(BaseModel):
    action_type: ActionType
    email_id: Optional[str] = None
    label: Optional[str] = None
    reply_body: Optional[str] = None
    summary: Optional[str] = None
    destination: Optional[str] = None
    reason: Optional[str] = None


# ─── Reward Model ────────────────────────────────────────────────────────────

class Reward(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    explanation: str = ""


# ─── Step Result ─────────────────────────────────────────────────────────────

class StepResult(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)
