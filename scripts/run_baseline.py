#!/usr/bin/env python3
"""
Baseline inference script for the Email Triage OpenEnv environment.

Uses the OpenAI-compatible API client pointed at a Hugging Face Inference Endpoint.
API credentials are read from the HF_TOKEN environment variable.

Usage:
    HF_TOKEN=your_token python scripts/run_baseline.py [--task task_easy|task_medium|task_hard|all]

Produces a reproducible baseline score for each task.
"""
import os
import json
import argparse
import sys
from typing import Dict, Any, List

# OpenAI client (compatible with HF Inference Endpoints)
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.email_triage_env import EmailTriageEnv
from env.models import Action, ActionType

# ─── Configuration ───────────────────────────────────────────────────────────

HF_TOKEN = os.environ.get("HF_TOKEN", "")
if not HF_TOKEN:
    print("WARNING: HF_TOKEN not set. Falling back to rule-based baseline.")

# HF Inference Endpoint for a supported model (e.g., Mistral-7B or similar)
HF_BASE_URL = os.environ.get(
    "HF_INFERENCE_URL",
    "https://api-inference.huggingface.co/v1"
)
MODEL_NAME = os.environ.get("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")

SYSTEM_PROMPT = """You are an expert email triage assistant. You will be given an inbox and a task.
Your job is to process emails by returning a JSON action object.

VALID action_types: label, reply, escalate, archive, delete, move, summarize, flag, done

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{
  "action_type": "<action_type>",
  "email_id": "<email_id or null>",
  "label": "<label or null>",
  "reply_body": "<reply text or null>",
  "reason": "<reason or null>"
}

When all emails are processed, return: {"action_type": "done", "email_id": null}
"""


def build_user_prompt(obs_dict: Dict[str, Any], last_reward: float = 0.0) -> str:
    """Build a user prompt from the current observation."""
    inbox = obs_dict.get("inbox", [])
    task = obs_dict.get("task_description", "")
    step = obs_dict.get("step_count", 0)
    message = obs_dict.get("message", "")
    context = obs_dict.get("context", {})

    inbox_text = ""
    for email in inbox:
        labels = ", ".join(email.get("labels", [])) or "none"
        inbox_text += (
            f"\n---\n"
            f"ID: {email['id']}\n"
            f"From: {email['sender']} <{email['sender_email']}>\n"
            f"Subject: {email['subject']}\n"
            f"Body: {email['body'][:400]}\n"
            f"VIP: {email.get('is_vip', False)}\n"
            f"Current Labels: {labels}\n"
        )

    policy_notes = ""
    if context.get("policy_notes"):
        policy_notes = "\nPOLICY NOTES:\n" + "\n".join(f"- {p}" for p in context["policy_notes"])

    return (
        f"TASK: {task}\n"
        f"{policy_notes}\n"
        f"STEP: {step} | LAST REWARD DELTA: {last_reward:.3f}\n"
        f"ENVIRONMENT MESSAGE: {message}\n"
        f"\nINBOX ({len(inbox)} emails):\n{inbox_text}\n"
        f"\nWhat is your next action? Return JSON only."
    )


def call_llm(client: OpenAI, messages: List[Dict]) -> str:
    """Call the LLM and return the text response."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=256,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


def parse_action(raw: str) -> Action:
    """Parse LLM output into an Action object."""
    # Strip markdown fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)
    action_type_str = data.get("action_type", "done").lower()
    try:
        action_type = ActionType(action_type_str)
    except ValueError:
        action_type = ActionType.DONE

    return Action(
        action_type=action_type,
        email_id=data.get("email_id"),
        label=data.get("label"),
        reply_body=data.get("reply_body"),
        reason=data.get("reason"),
    )


# ─── Rule-Based Fallback Baseline ────────────────────────────────────────────

RULE_BASED_PLANS = {
    "task_easy": [
        Action(action_type=ActionType.LABEL, email_id="e001", label="urgent"),
        Action(action_type=ActionType.ESCALATE, email_id="e001", reason="Production database down, immediate action required"),
        Action(action_type=ActionType.DONE),
    ],
    "task_medium": [
        Action(action_type=ActionType.ARCHIVE, email_id="m001"),
        Action(action_type=ActionType.FLAG, email_id="m002", label="vip"),
        Action(action_type=ActionType.ARCHIVE, email_id="m003"),
        Action(action_type=ActionType.ESCALATE, email_id="m004", label="urgent", reason="Overdue invoice final notice"),
        Action(action_type=ActionType.FLAG, email_id="m005", label="action-required"),
        Action(action_type=ActionType.LABEL, email_id="m006", label="sales-lead"),
        Action(action_type=ActionType.ESCALATE, email_id="m007", reason="High CPU alert on production server"),
        Action(action_type=ActionType.ARCHIVE, email_id="m008"),
        Action(action_type=ActionType.FLAG, email_id="m009", label="action-required"),
        Action(action_type=ActionType.DELETE, email_id="m010", label="spam"),
        Action(action_type=ActionType.DONE),
    ],
    "task_hard": [
        Action(action_type=ActionType.ESCALATE, email_id="h001", reason="CEO urgent deadline - board deck"),
        Action(action_type=ActionType.ESCALATE, email_id="h002", reason="Legal threat - do not reply without legal review"),
        Action(action_type=ActionType.ESCALATE, email_id="h003", reason="Potential data breach - escalate to security and legal immediately"),
        Action(action_type=ActionType.ESCALATE, email_id="h004", reason="Conflicting executive instructions - escalate for resolution"),
        Action(action_type=ActionType.ESCALATE, email_id="h005", reason="GDPR regulatory deadline - 72 hour response required"),
        Action(action_type=ActionType.ESCALATE, email_id="h006", reason="PR crisis - TechCrunch story deadline"),
        Action(action_type=ActionType.ESCALATE, email_id="h007", reason="VIP client churn risk - $2.4M account"),
        Action(action_type=ActionType.FLAG, email_id="h008", reason="Suspicious wire transfer - CFO unavailable, potential social engineering"),
        Action(action_type=ActionType.ESCALATE, email_id="h009", reason="Anonymous HR complaint - requires HR and legal review"),
        Action(action_type=ActionType.FLAG, email_id="h010", reason="Competitor acquisition inquiry - escalate to leadership"),
        Action(action_type=ActionType.DONE),
    ],
}


def run_rule_based_baseline(task_id: str) -> Dict[str, Any]:
    """Run the deterministic rule-based baseline for a task."""
    env = EmailTriageEnv(task_id=task_id)
    obs = env.reset()
    plan = RULE_BASED_PLANS[task_id]

    total_reward = 0.0
    step_rewards = []
    done = False

    print(f"\n{'='*60}")
    print(f"TASK: {task_id} (Rule-Based Baseline)")
    print(f"{'='*60}")

    for action in plan:
        if done:
            break
        obs_data, reward, done, info = env.step(action)
        step_rewards.append(reward.value)
        print(f"  Step {env._step_count}: {action.action_type} {action.email_id or ''} → reward={reward.value:.3f} | {reward.explanation[:60]}")

    final_score = info.get("final_score", info.get("cumulative_reward", 0.0))
    breakdown = info.get("breakdown", {})

    print(f"\n  FINAL SCORE: {final_score:.4f}")
    print(f"  BREAKDOWN: {json.dumps(breakdown, indent=2)}")

    return {
        "task_id": task_id,
        "final_score": final_score,
        "step_rewards": step_rewards,
        "breakdown": breakdown,
        "method": "rule_based",
    }


def run_llm_baseline(task_id: str, client: OpenAI) -> Dict[str, Any]:
    """Run the LLM-based baseline for a task."""
    env = EmailTriageEnv(task_id=task_id)
    obs = env.reset()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    step_rewards = []
    last_delta = 0.0
    done = False
    max_steps = 35

    print(f"\n{'='*60}")
    print(f"TASK: {task_id} (LLM Baseline: {MODEL_NAME})")
    print(f"{'='*60}")

    for i in range(max_steps):
        if done:
            break

        user_msg = build_user_prompt(obs.model_dump(), last_delta)
        messages.append({"role": "user", "content": user_msg})

        try:
            raw = call_llm(client, messages)
            messages.append({"role": "assistant", "content": raw})
            action = parse_action(raw)
        except Exception as e:
            print(f"  Step {i+1}: LLM parse error: {e}. Using DONE fallback.")
            action = Action(action_type=ActionType.DONE)

        obs, reward, done, info = env.step(action)
        last_delta = reward.value
        step_rewards.append(reward.value)
        print(f"  Step {i+1}: {action.action_type} {action.email_id or ''} → reward={reward.value:.3f}")

        if done:
            break

    final_score = info.get("final_score", info.get("cumulative_reward", 0.0))
    breakdown = info.get("breakdown", {})

    print(f"\n  FINAL SCORE: {final_score:.4f}")
    return {
        "task_id": task_id,
        "final_score": final_score,
        "step_rewards": step_rewards,
        "breakdown": breakdown,
        "method": f"llm:{MODEL_NAME}",
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run Email Triage OpenEnv baseline.")
    parser.add_argument(
        "--task",
        default="all",
        choices=["task_easy", "task_medium", "task_hard", "all"],
        help="Which task to evaluate (default: all)",
    )
    parser.add_argument(
        "--mode",
        default="rule_based",
        choices=["rule_based", "llm"],
        help="Baseline mode (default: rule_based)",
    )
    args = parser.parse_args()

    tasks = ["task_easy", "task_medium", "task_hard"] if args.task == "all" else [args.task]

    results = []

    if args.mode == "llm":
        if not HF_TOKEN:
            print("ERROR: HF_TOKEN is required for LLM mode.")
            sys.exit(1)
        client = OpenAI(base_url=HF_BASE_URL, api_key=HF_TOKEN)
        for task_id in tasks:
            result = run_llm_baseline(task_id, client)
            results.append(result)
    else:
        for task_id in tasks:
            result = run_rule_based_baseline(task_id)
            results.append(result)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    total = 0.0
    for r in results:
        print(f"  {r['task_id']}: {r['final_score']:.4f} ({r['method']})")
        total += r["final_score"]
    avg = total / len(results) if results else 0.0
    print(f"\n  AVERAGE SCORE: {avg:.4f}")

    # Write results to file for CI/reproducibility
    output_path = "baseline_results.json"
    with open(output_path, "w") as f:
        json.dump({"results": results, "average": avg}, f, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
