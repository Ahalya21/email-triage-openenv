"""
FastAPI application exposing the Email Triage OpenEnv environment via REST API.
Deployable as a Hugging Face Space with the openenv tag.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from env.email_triage_env import EmailTriageEnv, TASK_IDS
from env.models import Action, ActionType

app = FastAPI(
    title="Email Triage OpenEnv",
    description=(
        "A real-world email triage environment for evaluating AI agents. "
        "Implements the OpenEnv interface with three tasks spanning easy to hard."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (one env per session_id)
_sessions: Dict[str, EmailTriageEnv] = {}


class ResetRequest(BaseModel):
    task_id: str = "task_easy"
    session_id: str = "default"


class StepRequest(BaseModel):
    session_id: str = "default"
    action_type: str
    email_id: Optional[str] = None
    label: Optional[str] = None
    reply_body: Optional[str] = None
    summary: Optional[str] = None
    destination: Optional[str] = None
    reason: Optional[str] = None


@app.get("/")
def root():
    return {
        "name": "Email Triage OpenEnv",
        "version": "1.0.0",
        "tasks": list(TASK_IDS),
        "endpoints": ["/reset", "/step", "/state", "/health", "/docs"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset")
def reset(req: ResetRequest):
    if req.task_id not in TASK_IDS:
        raise HTTPException(status_code=400, detail=f"Unknown task_id. Choose from: {TASK_IDS}")
    env = EmailTriageEnv(task_id=req.task_id)
    obs = env.reset()
    _sessions[req.session_id] = env
    return {"observation": obs.model_dump(), "session_id": req.session_id}


@app.post("/step")
def step(req: StepRequest):
    env = _sessions.get(req.session_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"No session '{req.session_id}'. Call /reset first.")

    try:
        action_type = ActionType(req.action_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid action_type: {req.action_type}")

    action = Action(
        action_type=action_type,
        email_id=req.email_id,
        label=req.label,
        reply_body=req.reply_body,
        summary=req.summary,
        destination=req.destination,
        reason=req.reason,
    )

    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    }


@app.get("/state")
def state(session_id: str = "default"):
    env = _sessions.get(session_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"No session '{session_id}'. Call /reset first.")
    return env.state()


@app.get("/tasks")
def tasks():
    from env.email_triage_env import TASK_DESCRIPTIONS, MAX_STEPS, INBOX_MAP
    return {
        task_id: {
            "description": TASK_DESCRIPTIONS[task_id],
            "max_steps": MAX_STEPS[task_id],
            "num_emails": len(INBOX_MAP[task_id]),
        }
        for task_id in TASK_IDS
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
