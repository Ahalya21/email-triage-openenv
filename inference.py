"""
inference.py — OpenEnv baseline inference script.
Runs a rule-based agent against all three Email Triage tasks
and prints structured logs in the required START/STEP/END format.
"""
from __future__ import annotations

import json
import os
import requests

BASE_URL = os.environ.get("OPENENV_URL", "http://localhost:7860")

TASK_IDS = ["task_easy", "task_medium", "task_hard"]


def rule_based_action(observation: dict) -> dict:
    """Simple rule-based policy for email triage."""
    emails = observation.get("emails", [])
    if not emails:
        return {"action_type": "done"}

    email = emails[0]
    subject = (email.get("subject", "") or "").lower()
    body = (email.get("body", "") or "").lower()
    sender = (email.get("sender", "") or "").lower()

    # Spam detection
    if any(w in subject + body for w in ["lottery", "winner", "prize", "nigerian", "click here", "unsubscribe"]):
        return {"action_type": "delete", "email_id": email.get("id"), "reason": "spam"}

    # Urgent escalation
    if any(w in subject + body for w in ["urgent", "breach", "legal", "lawsuit", "critical", "emergency"]):
        return {"action_type": "escalate", "email_id": email.get("id"), "reason": "urgent issue"}

    # Default: label and archive
    return {"action_type": "label", "email_id": email.get("id"), "label": "inbox"}


def run_task(task_id: str):
    print(f"START task_id={task_id}")

    # Reset
    reset_resp = requests.post(f"{BASE_URL}/reset", json={"task": task_id})
    reset_resp.raise_for_status()
    data = reset_resp.json()
    observation = data.get("observation", {})
    session_id = data.get("session_id", "default")

    total_reward = 0.0
    step = 0
    done = False

    while not done and step < 50:
        action = rule_based_action(observation)
        action["session_id"] = session_id

        step_resp = requests.post(f"{BASE_URL}/step", json=action)
        if step_resp.status_code != 200:
            break

        result = step_resp.json()
        observation = result.get("observation", {})
        reward = result.get("reward", {})
        done = result.get("done", False)

        step_reward = reward.get("value", 0.0) if isinstance(reward, dict) else float(reward)
        total_reward += step_reward

        print(f"STEP {step} action={action.get('action_type')} reward={step_reward:.3f}")
        step += 1

    print(f"END task_id={task_id} total_reward={total_reward:.3f} steps={step}")
    return total_reward


def main():
    results = {}
    for task_id in TASK_IDS:
        try:
            score = run_task(task_id)
            results[task_id] = score
        except Exception as e:
            print(f"END task_id={task_id} error={e}")
            results[task_id] = 0.0

    print("\n=== RESULTS ===")
    for task_id, score in results.items():
        print(f"{task_id}: {score:.3f}")

    with open("baseline_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()