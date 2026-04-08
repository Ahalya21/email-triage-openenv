"""
Programmatic graders for each task.
Each grader returns a score between 0.0 and 1.0 and a breakdown dict.
Graders are deterministic and reproducible.
"""
from __future__ import annotations
from typing import Dict, List, Any, Tuple
from env.models import Action, ActionType, Email


def _normalize(score: float) -> float:
    return max(0.0, min(1.0, score))


# ─── EASY TASK GRADER ────────────────────────────────────────────────────────

class EasyTaskGrader:
    """
    Task: Given a single urgent email, the agent must:
      1. Label it 'urgent'
      2. Escalate it
    Score breakdown:
      - 0.5 for correct label
      - 0.5 for escalation
    Penalties:
      - -0.2 for deleting or archiving without reading
      - -0.1 per unnecessary action
    """
    TARGET_EMAIL_ID = "e001"
    MAX_STEPS = 5

    def __init__(self):
        self.reset()

    def reset(self):
        self._labeled_urgent = False
        self._escalated = False
        self._deleted = False
        self._archived = False
        self._extra_actions = 0
        self._steps = 0

    def score_action(self, action: Action) -> Tuple[float, str]:
        self._steps += 1
        delta = 0.0
        explanation = ""

        if action.action_type == ActionType.DONE:
            return 0.0, "Agent signaled done."

        if action.email_id != self.TARGET_EMAIL_ID:
            self._extra_actions += 1
            return 0.0, "Action on wrong email."

        if action.action_type == ActionType.LABEL:
            if action.label and action.label.lower() in ("urgent", "high-priority", "critical"):
                if not self._labeled_urgent:
                    self._labeled_urgent = True
                    delta = 0.5
                    explanation = "Correct urgent label applied."
                else:
                    explanation = "Already labeled; no additional score."
            else:
                delta = -0.1
                explanation = f"Wrong label '{action.label}' applied."

        elif action.action_type == ActionType.ESCALATE:
            if not self._escalated:
                self._escalated = True
                delta = 0.5
                explanation = "Correct escalation."
            else:
                explanation = "Already escalated."

        elif action.action_type == ActionType.DELETE:
            self._deleted = True
            delta = -0.3
            explanation = "Deleted an urgent email — severe penalty."

        elif action.action_type == ActionType.ARCHIVE:
            self._archived = True
            delta = -0.2
            explanation = "Archived urgent email without escalating."

        else:
            self._extra_actions += 1
            delta = -0.05
            explanation = "Unnecessary action taken."

        if self._steps > self.MAX_STEPS:
            delta -= 0.05
            explanation += " (exceeded step budget)"

        return delta, explanation

    def final_score(self) -> Tuple[float, Dict[str, float], str]:
        score = (0.5 if self._labeled_urgent else 0.0) + (0.5 if self._escalated else 0.0)
        score -= 0.3 if self._deleted else 0.0
        score -= 0.2 if self._archived and not self._escalated else 0.0
        score -= min(self._extra_actions * 0.05, 0.2)
        breakdown = {
            "labeled_urgent": 0.5 if self._labeled_urgent else 0.0,
            "escalated": 0.5 if self._escalated else 0.0,
            "delete_penalty": -0.3 if self._deleted else 0.0,
            "extra_action_penalty": -min(self._extra_actions * 0.05, 0.2),
        }
        return _normalize(score), breakdown, "Final easy task score."


# ─── MEDIUM TASK GRADER ──────────────────────────────────────────────────────

MEDIUM_EXPECTED_ACTIONS = {
    "m001": {"action": ActionType.ARCHIVE, "label": None},           # newsletter → archive
    "m002": {"action": ActionType.FLAG, "label": "vip"},             # VIP contract → flag/vip
    "m003": {"action": ActionType.ARCHIVE, "label": None},           # github notification → archive
    "m004": {"action": ActionType.ESCALATE, "label": "urgent"},      # overdue invoice → escalate
    "m005": {"action": ActionType.FLAG, "label": "action-required"}, # HR deadline → flag
    "m006": {"action": ActionType.LABEL, "label": "sales-lead"},     # sales lead → label
    "m007": {"action": ActionType.ESCALATE, "label": "urgent"},      # server alert → escalate
    "m008": {"action": ActionType.ARCHIVE, "label": None},           # personal → archive
    "m009": {"action": ActionType.FLAG, "label": "action-required"}, # legal signature → flag
    "m010": {"action": ActionType.DELETE, "label": "spam"},          # spam → delete
}


class MediumTaskGrader:
    """
    Task: Process a 10-email inbox correctly.
    Score: Each email worth 0.1. Partial credit for close actions.
    """
    PER_EMAIL = 0.1
    PARTIAL_CREDIT = 0.05

    def __init__(self):
        self.reset()

    def reset(self):
        self._scores: Dict[str, float] = {}
        self._actions_taken: Dict[str, List[ActionType]] = {}
        self._steps = 0
        self._redundant_actions = 0

    def score_action(self, action: Action) -> Tuple[float, str]:
        self._steps += 1

        if action.action_type == ActionType.DONE:
            return 0.0, "Agent signaled done."

        eid = action.email_id
        if eid not in MEDIUM_EXPECTED_ACTIONS:
            return -0.02, f"Unknown email id: {eid}"

        if eid in self._scores:
            self._redundant_actions += 1
            return -0.02, f"Email {eid} already handled."

        expected = MEDIUM_EXPECTED_ACTIONS[eid]
        expected_action = expected["action"]
        expected_label = expected["label"]

        if action.action_type == expected_action:
            # Check label match if needed
            if expected_label:
                if action.label and expected_label.lower() in action.label.lower():
                    score = self.PER_EMAIL
                    explanation = f"Perfect: {eid} correctly handled with right label."
                else:
                    score = self.PARTIAL_CREDIT
                    explanation = f"Correct action for {eid} but missing/wrong label."
            else:
                score = self.PER_EMAIL
                explanation = f"Perfect: {eid} correctly handled."
        else:
            # Partial credit for partially correct actions
            close_pairs = {
                (ActionType.FLAG, ActionType.ESCALATE): 0.04,
                (ActionType.ESCALATE, ActionType.FLAG): 0.04,
                (ActionType.ARCHIVE, ActionType.DELETE): 0.03,
                (ActionType.DELETE, ActionType.ARCHIVE): 0.03,
                (ActionType.LABEL, ActionType.FLAG): 0.03,
            }
            score = close_pairs.get((action.action_type, expected_action), 0.0)
            explanation = f"Wrong action for {eid}. Expected {expected_action}, got {action.action_type}. Partial: {score}"

        self._scores[eid] = score
        return score, explanation

    def final_score(self) -> Tuple[float, Dict[str, float], str]:
        raw = sum(self._scores.values())
        penalty = min(self._redundant_actions * 0.02, 0.1)
        final = _normalize(raw - penalty)
        breakdown = dict(self._scores)
        breakdown["redundant_penalty"] = -penalty
        return final, breakdown, f"Processed {len(self._scores)}/10 emails."


# ─── HARD TASK GRADER ────────────────────────────────────────────────────────

HARD_RUBRIC = {
    "h001": {
        "desc": "CEO board deck request",
        "correct_actions": [ActionType.FLAG, ActionType.ESCALATE],
        "weight": 0.08,
        "must_not": [ActionType.DELETE, ActionType.ARCHIVE],
        "bonus_condition": "reply",  # reply acknowledging
    },
    "h002": {
        "desc": "Legal threat from angry customer",
        "correct_actions": [ActionType.ESCALATE, ActionType.FLAG],
        "weight": 0.10,
        "must_not": [ActionType.DELETE, ActionType.REPLY],
        "note": "Should not reply without legal review",
    },
    "h003": {
        "desc": "Potential data breach (CONFIDENTIAL)",
        "correct_actions": [ActionType.ESCALATE, ActionType.FLAG],
        "weight": 0.15,
        "must_not": [ActionType.DELETE, ActionType.ARCHIVE],
        "note": "Highest stakes — breach notification is critical",
    },
    "h004": {
        "desc": "CTO contradicting CEO on board deck",
        "correct_actions": [ActionType.FLAG, ActionType.ESCALATE],
        "weight": 0.10,
        "must_not": [ActionType.DELETE],
        "note": "Conflicting exec instructions — should escalate not ignore",
    },
    "h005": {
        "desc": "GDPR compliance deadline",
        "correct_actions": [ActionType.ESCALATE, ActionType.FLAG],
        "weight": 0.12,
        "must_not": [ActionType.DELETE, ActionType.ARCHIVE],
    },
    "h006": {
        "desc": "TechCrunch PR deadline",
        "correct_actions": [ActionType.ESCALATE, ActionType.FLAG],
        "weight": 0.08,
        "must_not": [ActionType.DELETE],
    },
    "h007": {
        "desc": "Top client threatening churn ($2.4M)",
        "correct_actions": [ActionType.ESCALATE, ActionType.FLAG],
        "weight": 0.12,
        "must_not": [ActionType.DELETE, ActionType.ARCHIVE],
    },
    "h008": {
        "desc": "Large wire transfer without CFO approval",
        "correct_actions": [ActionType.FLAG, ActionType.ESCALATE],
        "weight": 0.10,
        "must_not": [ActionType.DELETE],
        "note": "Should flag as suspicious — CFO social engineering risk",
    },
    "h009": {
        "desc": "Anonymous HR complaint",
        "correct_actions": [ActionType.ESCALATE, ActionType.FLAG],
        "weight": 0.08,
        "must_not": [ActionType.DELETE, ActionType.ARCHIVE],
    },
    "h010": {
        "desc": "Competitor acquisition inquiry",
        "correct_actions": [ActionType.FLAG, ActionType.ESCALATE],
        "weight": 0.07,
        "must_not": [ActionType.DELETE],
    },
}


class HardTaskGrader:
    """
    Hard task: 10 high-stakes emails requiring nuanced triage.
    Scoring is weighted by email criticality.
    Penalties for dangerous actions (deleting legal/breach emails).
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._scores: Dict[str, float] = {}
        self._penalties: Dict[str, float] = {}
        self._steps = 0

    def score_action(self, action: Action) -> Tuple[float, str]:
        self._steps += 1

        if action.action_type == ActionType.DONE:
            return 0.0, "Agent signaled done."

        eid = action.email_id
        if eid not in HARD_RUBRIC:
            return -0.02, f"Unknown email id: {eid}"

        rubric = HARD_RUBRIC[eid]
        weight = rubric["weight"]

        # Penalty for forbidden actions
        if action.action_type in rubric.get("must_not", []):
            penalty = weight * 0.8
            self._penalties[eid] = self._penalties.get(eid, 0.0) + penalty
            return -penalty, f"SEVERE: Forbidden action {action.action_type} on {eid} ({rubric['desc']})."

        # Already handled?
        if eid in self._scores:
            return -0.01, f"Email {eid} already scored."

        # Correct action?
        if action.action_type in rubric["correct_actions"]:
            # Bonus for reply on h001 (acknowledging CEO)
            bonus = 0.0
            if eid == "h001" and action.action_type == ActionType.ESCALATE:
                bonus = weight * 0.1
            self._scores[eid] = weight + bonus
            return weight + bonus, f"Correct handling of {eid} ({rubric['desc']})."
        else:
            # Partial for label/summarize
            partial = weight * 0.3
            self._scores[eid] = partial
            return partial, f"Partial credit for {eid}: not optimal action."

    def final_score(self) -> Tuple[float, Dict[str, float], str]:
        raw = sum(self._scores.values())
        total_penalty = sum(self._penalties.values())
        final = _normalize(raw - total_penalty)
        breakdown = dict(self._scores)
        breakdown["penalties"] = -total_penalty
        missing = [eid for eid in HARD_RUBRIC if eid not in self._scores]
        return final, breakdown, f"Hard task complete. Missed: {missing}. Penalties: {total_penalty:.2f}"
