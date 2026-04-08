"""
Tests for the Email Triage OpenEnv environment.
Run with: python -m pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from env.email_triage_env import EmailTriageEnv
from env.models import Action, ActionType, Observation, Reward


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def easy_env():
    env = EmailTriageEnv("task_easy")
    env.reset()
    return env

@pytest.fixture
def medium_env():
    env = EmailTriageEnv("task_medium")
    env.reset()
    return env

@pytest.fixture
def hard_env():
    env = EmailTriageEnv("task_hard")
    env.reset()
    return env


# ─── Interface Tests ──────────────────────────────────────────────────────────

def test_reset_returns_observation(easy_env):
    obs = easy_env.reset()
    assert isinstance(obs, Observation)
    assert len(obs.inbox) == 1
    assert obs.step_count == 0
    assert obs.task_description != ""

def test_step_returns_tuple(easy_env):
    action = Action(action_type=ActionType.LABEL, email_id="e001", label="urgent")
    obs, reward, done, info = easy_env.step(action)
    assert isinstance(obs, Observation)
    assert isinstance(reward, Reward)
    assert isinstance(done, bool)
    assert isinstance(info, dict)

def test_state_is_serializable(easy_env):
    state = easy_env.state()
    import json
    json.dumps(state)  # Should not raise

def test_done_action_ends_episode(easy_env):
    _, _, done, _ = easy_env.step(Action(action_type=ActionType.DONE))
    assert done is True

def test_step_after_done_is_noop(easy_env):
    easy_env.step(Action(action_type=ActionType.DONE))
    obs, reward, done, info = easy_env.step(Action(action_type=ActionType.LABEL, email_id="e001", label="urgent"))
    assert done is True
    assert reward.value == 0.0

def test_unknown_task_raises():
    with pytest.raises(ValueError):
        EmailTriageEnv("task_nonexistent")


# ─── Easy Task Tests ──────────────────────────────────────────────────────────

def test_easy_perfect_score():
    env = EmailTriageEnv("task_easy")
    env.reset()
    env.step(Action(action_type=ActionType.LABEL, email_id="e001", label="urgent"))
    _, reward, done, info = env.step(Action(action_type=ActionType.ESCALATE, email_id="e001"))
    env.step(Action(action_type=ActionType.DONE))
    state = env.state()
    assert state["cumulative_reward"] >= 0.9

def test_easy_delete_penalty():
    env = EmailTriageEnv("task_easy")
    env.reset()
    _, reward, _, _ = env.step(Action(action_type=ActionType.DELETE, email_id="e001"))
    assert reward.value == 0.0  # Negative delta doesn't produce positive reward
    # Cumulative should be penalized
    env.step(Action(action_type=ActionType.DONE))
    assert env._cumulative_reward < 0.5

def test_easy_wrong_label_penalty():
    env = EmailTriageEnv("task_easy")
    env.reset()
    _, reward, _, _ = env.step(Action(action_type=ActionType.LABEL, email_id="e001", label="low"))
    env.step(Action(action_type=ActionType.DONE))
    # Score should reflect bad label
    assert env._cumulative_reward < 0.5


# ─── Medium Task Tests ────────────────────────────────────────────────────────

def test_medium_has_10_emails(medium_env):
    obs = medium_env.reset()
    assert len(obs.inbox) == 10

def test_medium_correct_archive():
    env = EmailTriageEnv("task_medium")
    env.reset()
    _, reward, _, _ = env.step(Action(action_type=ActionType.ARCHIVE, email_id="m001"))
    assert reward.value > 0

def test_medium_spam_deletion():
    env = EmailTriageEnv("task_medium")
    env.reset()
    _, reward, _, _ = env.step(Action(action_type=ActionType.DELETE, email_id="m010", label="spam"))
    assert reward.value > 0

def test_medium_vip_flagging():
    env = EmailTriageEnv("task_medium")
    env.reset()
    _, reward, _, _ = env.step(Action(action_type=ActionType.FLAG, email_id="m002", label="vip"))
    assert reward.value > 0

def test_medium_redundant_action_penalty():
    env = EmailTriageEnv("task_medium")
    env.reset()
    env.step(Action(action_type=ActionType.ARCHIVE, email_id="m001"))
    _, reward2, _, _ = env.step(Action(action_type=ActionType.ARCHIVE, email_id="m001"))
    assert reward2.value == 0.0  # Redundant = no positive reward

def test_medium_full_perfect_run():
    from scripts.run_baseline import RULE_BASED_PLANS
    env = EmailTriageEnv("task_medium")
    env.reset()
    plan = RULE_BASED_PLANS["task_medium"]
    done = False
    for action in plan:
        if done:
            break
        _, _, done, info = env.step(action)
    assert info["final_score"] >= 0.85


# ─── Hard Task Tests ──────────────────────────────────────────────────────────

def test_hard_has_10_emails(hard_env):
    obs = hard_env.reset()
    assert len(obs.inbox) == 10

def test_hard_breach_email_delete_severe_penalty():
    env = EmailTriageEnv("task_hard")
    env.reset()
    _, reward, _, _ = env.step(Action(action_type=ActionType.DELETE, email_id="h003"))
    # Negative delta → no positive reward, cumulative goes negative
    assert env._cumulative_reward < 0

def test_hard_legal_reply_penalty():
    env = EmailTriageEnv("task_hard")
    env.reset()
    _, reward, _, _ = env.step(Action(
        action_type=ActionType.REPLY,
        email_id="h002",
        reply_body="Sorry about that, here's compensation."
    ))
    # Replying to legal threat without auth is penalized
    assert env._cumulative_reward < 0

def test_hard_context_has_policy_notes(hard_env):
    obs = hard_env.reset()
    assert "policy_notes" in obs.context
    assert len(obs.context["policy_notes"]) > 0

def test_hard_perfect_run():
    from scripts.run_baseline import RULE_BASED_PLANS
    env = EmailTriageEnv("task_hard")
    env.reset()
    plan = RULE_BASED_PLANS["task_hard"]
    done = False
    for action in plan:
        if done:
            break
        _, _, done, info = env.step(action)
    assert info["final_score"] >= 0.80


# ─── Step Budget Tests ────────────────────────────────────────────────────────

def test_step_budget_exceeded():
    env = EmailTriageEnv("task_easy")
    env.reset()
    # Spam with 9 nonsense actions (budget is 8)
    for i in range(9):
        obs, reward, done, info = env.step(Action(action_type=ActionType.SUMMARIZE, email_id="e001"))
        if done:
            break
    assert done is True


# ─── Reward Sanity Tests ──────────────────────────────────────────────────────

def test_rewards_bounded_0_to_1():
    for task_id in ["task_easy", "task_medium", "task_hard"]:
        env = EmailTriageEnv(task_id)
        env.reset()
        env.step(Action(action_type=ActionType.DONE))
        assert 0.0 <= env._cumulative_reward <= 1.0

def test_reward_increases_with_correct_actions():
    env = EmailTriageEnv("task_easy")
    env.reset()
    _, r1, _, _ = env.step(Action(action_type=ActionType.LABEL, email_id="e001", label="urgent"))
    _, r2, _, _ = env.step(Action(action_type=ActionType.ESCALATE, email_id="e001"))
    assert r1.value > 0
    assert r2.value > 0
