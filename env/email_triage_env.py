"""
EmailTriageEnv — A real-world email triage environment implementing the OpenEnv interface.

Tasks:
  task_easy   — Single email classification and escalation
  task_medium — 10-email inbox triage
  task_hard   — High-stakes inbox with conflicting signals and time pressure
"""
from __future__ import annotations

import json
import copy
from typing import Any, Dict, List, Optional, Tuple

from env.models import (
    Observation, Action, ActionType, Reward, StepResult, Email
)
from env.email_fixtures import EASY_EMAILS, MEDIUM_EMAILS, HARD_EMAILS
from graders.task_graders import EasyTaskGrader, MediumTaskGrader, HardTaskGrader


TASK_IDS = ("task_easy", "task_medium", "task_hard")

TASK_DESCRIPTIONS = {
    "task_easy": (
        "You have received one email in your inbox. Your job is to:\n"
        "1. Label it with the appropriate priority ('urgent', 'high', 'normal', 'low', or 'spam').\n"
        "2. Escalate it if it requires immediate human attention.\n"
        "When finished, use action_type='done'."
    ),
    "task_medium": (
        "You have a 10-email inbox. Triage every email by:\n"
        "- Archiving newsletters, automated notifications, and personal non-work emails.\n"
        "- Labeling sales leads as 'sales-lead'.\n"
        "- Flagging emails that require action from you ('action-required').\n"
        "- Escalating urgent operational issues.\n"
        "- Deleting spam.\n"
        "- Flagging VIP client emails.\n"
        "Process all 10 emails, then use action_type='done'."
    ),
    "task_hard": (
        "You are managing a high-stakes inbox with 10 critical emails arriving during a crisis day.\n"
        "Emails include conflicting executive instructions, legal threats, a potential data breach,\n"
        "regulatory deadlines, and a major client threatening churn.\n"
        "Your priorities:\n"
        "1. Never delete emails that may have legal, compliance, or financial consequences.\n"
        "2. Escalate anything that requires executive decision-making.\n"
        "3. Flag VIP and time-sensitive items.\n"
        "4. Do NOT reply to legal threats without authorization.\n"
        "5. Be suspicious of requests for large financial transactions without proper approvals.\n"
        "Process all 10 emails appropriately, then use action_type='done'."
    ),
}

MAX_STEPS = {
    "task_easy": 8,
    "task_medium": 25,
    "task_hard": 30,
}

INBOX_MAP = {
    "task_easy": EASY_EMAILS,
    "task_medium": MEDIUM_EMAILS,
    "task_hard": HARD_EMAILS,
}

GRADER_MAP = {
    "task_easy": EasyTaskGrader,
    "task_medium": MediumTaskGrader,
    "task_hard": HardTaskGrader,
}


class EmailTriageEnv:
    """
    OpenEnv-compliant email triage environment.
    Implements: reset(), step(), state()
    """

    def __init__(self, task_id: str = "task_easy"):
        if task_id not in TASK_IDS:
            raise ValueError(f"Unknown task_id '{task_id}'. Choose from: {TASK_IDS}")
        self.task_id = task_id
        self._inbox: List[Email] = []
        self._current_index: int = 0
        self._step_count: int = 0
        self._done: bool = False
        self._cumulative_reward: float = 0.0
        self._action_log: List[Dict[str, Any]] = []
        self._grader = None
        self._reward_history: List[float] = []

    # ──────────────────────────────────────────────────────────────────────────
    # OpenEnv Interface
    # ──────────────────────────────────────────────────────────────────────────

    def reset(self) -> Observation:
        """Reset the environment and return the initial observation."""
        self._inbox = copy.deepcopy(INBOX_MAP[self.task_id])
        self._current_index = 0
        self._step_count = 0
        self._done = False
        self._cumulative_reward = 0.0
        self._action_log = []
        self._reward_history = []
        self._grader = GRADER_MAP[self.task_id]()
        return self._build_observation()

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """
        Execute one action in the environment.
        Returns (observation, reward, done, info).
        """
        if self._done:
            obs = self._build_observation(message="Environment is already done. Call reset().")
            reward = Reward(value=0.0, explanation="No-op after done.")
            return obs, reward, True, {"warning": "already_done"}

        self._step_count += 1

        # Check step budget
        max_steps = MAX_STEPS[self.task_id]
        if self._step_count > max_steps:
            self._done = True
            final_score, breakdown, final_msg = self._grader.final_score()
            step_penalty = 0.05
            final_score = max(0.0, final_score - step_penalty)
            reward = Reward(
                value=final_score,
                breakdown={**breakdown, "step_budget_exceeded": -step_penalty},
                explanation=f"Exceeded {max_steps} step budget. {final_msg}",
            )
            self._cumulative_reward = final_score
            obs = self._build_observation(message=f"Step budget exceeded ({max_steps} steps). Task ended.")
            return obs, reward, True, self._build_info(final_score, breakdown, "step_budget_exceeded")

        # Handle 'done' action
        if action.action_type == ActionType.DONE:
            self._done = True
            final_score, breakdown, final_msg = self._grader.final_score()
            self._cumulative_reward = final_score
            reward = Reward(
                value=final_score,
                breakdown=breakdown,
                explanation=f"Task complete. {final_msg}",
            )
            obs = self._build_observation(message="Task complete. Final score computed.", done=True)
            self._action_log.append({"step": self._step_count, "action": "done", "reward": final_score})
            return obs, reward, True, self._build_info(final_score, breakdown, "done")

        # Apply action to environment state
        message = self._apply_action(action)

        # Score the action incrementally
        delta, explanation = self._grader.score_action(action)
        self._cumulative_reward = min(1.0, max(0.0, self._cumulative_reward + delta))
        self._reward_history.append(delta)

        # Log action
        self._action_log.append({
            "step": self._step_count,
            "action_type": action.action_type,
            "email_id": action.email_id,
            "delta": delta,
            "explanation": explanation,
        })

        reward = Reward(
            value=max(0.0, delta),
            breakdown={"step_delta": delta},
            explanation=explanation,
        )

        obs = self._build_observation(message=f"{explanation} {message}".strip())
        return obs, reward, False, self._build_info(self._cumulative_reward, {}, "in_progress")

    def state(self) -> Dict[str, Any]:
        """Return the current environment state (serializable)."""
        return {
            "task_id": self.task_id,
            "step_count": self._step_count,
            "done": self._done,
            "cumulative_reward": self._cumulative_reward,
            "inbox": [e.model_dump() for e in self._inbox],
            "action_log": self._action_log,
            "reward_history": self._reward_history,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Internal Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _apply_action(self, action: Action) -> str:
        """Mutate inbox state based on action. Returns status message."""
        email = self._find_email(action.email_id)
        if email is None:
            return f"Email '{action.email_id}' not found."

        if action.action_type == ActionType.LABEL and action.label:
            if action.label not in email.labels:
                email.labels.append(action.label)
            return f"Labeled '{action.email_id}' as '{action.label}'."

        elif action.action_type == ActionType.ARCHIVE:
            if "archived" not in email.labels:
                email.labels.append("archived")
            return f"Archived '{action.email_id}'."

        elif action.action_type == ActionType.DELETE:
            self._inbox = [e for e in self._inbox if e.id != action.email_id]
            return f"Deleted '{action.email_id}'."

        elif action.action_type == ActionType.ESCALATE:
            if "escalated" not in email.labels:
                email.labels.append("escalated")
            return f"Escalated '{action.email_id}'. Reason: {action.reason or 'none provided'}."

        elif action.action_type == ActionType.FLAG:
            if "flagged" not in email.labels:
                email.labels.append("flagged")
            if action.label and action.label not in email.labels:
                email.labels.append(action.label)
            return f"Flagged '{action.email_id}'."

        elif action.action_type == ActionType.REPLY:
            if "replied" not in email.labels:
                email.labels.append("replied")
            return f"Replied to '{action.email_id}'."

        elif action.action_type == ActionType.MOVE:
            if action.destination:
                email.labels.append(f"moved:{action.destination}")
            return f"Moved '{action.email_id}' to '{action.destination}'."

        elif action.action_type == ActionType.SUMMARIZE:
            return f"Summarized '{action.email_id}'."

        return "Action applied."

    def _find_email(self, email_id: Optional[str]) -> Optional[Email]:
        if not email_id:
            return None
        for e in self._inbox:
            if e.id == email_id:
                return e
        return None

    def _build_observation(self, message: str = "", done: bool = False) -> Observation:
        current = self._inbox[self._current_index] if self._inbox and self._current_index < len(self._inbox) else None
        context = {}
        if self.task_id == "task_hard":
            context = {
                "policy_notes": [
                    "Do NOT reply to legal threats without Legal team review.",
                    "Wire transfers over $10k require CFO signature.",
                    "Data breach incidents must be escalated to Security + Legal immediately.",
                    "Conflicting executive instructions should be escalated, not resolved unilaterally.",
                ],
                "vip_senders": ["ceo@yourcompany.com", "cto@yourcompany.com", "procurement@mega-client.com"],
            }
        return Observation(
            inbox=self._inbox,
            current_email=current,
            task_description=TASK_DESCRIPTIONS[self.task_id],
            step_count=self._step_count,
            context=context,
            done=done or self._done,
            message=message,
        )

    def _build_info(self, score: float, breakdown: Dict, status: str) -> Dict[str, Any]:
        return {
            "cumulative_reward": self._cumulative_reward,
            "final_score": score,
            "breakdown": breakdown,
            "status": status,
            "steps_taken": self._step_count,
            "action_log": self._action_log,
        }
