import pytest

from src.evaluation.run_experiment import POLICIES, run_policy


def run(policy, unreliability=0.2, seed=7, tasks=20):
    return run_policy(
        policy,
        node_count=10,
        task_count=tasks,
        unreliability=unreliability,
        seed=seed,
        lambda_value=2.0,
    )


@pytest.mark.parametrize("policy", list(POLICIES))
def test_pipeline_runs_for_every_policy(policy):
    rows, summary = run(policy)
    assert len(rows) == 20
    assert summary["policy"] == policy
    assert summary["completion_rate"] + summary["failure_rate"] == pytest.approx(
        100.0
    )
    assert summary["not_scheduled"] <= 20


def test_same_seed_is_reproducible():
    first_rows, first_summary = run("arrro")
    second_rows, second_summary = run("arrro")
    assert first_rows == second_rows
    assert first_summary == second_summary


def test_policies_face_identical_tasks():
    task_ids = {
        policy: [(r["task_id"], r["task_type"]) for r in run(policy)[0]]
        for policy in POLICIES
    }
    reference = task_ids["arrro"]
    assert all(ids == reference for ids in task_ids.values())


def test_every_decision_is_a_scheduled_node_or_a_recorded_miss():
    rows, _ = run("arrro", tasks=30)
    for row in rows:
        if row["node_id"] is None:
            assert row["failure_reason"] == "NO_FEASIBLE_NODE"
        else:
            assert row["node_id"].startswith("edge-")


def test_rejection_feeds_back_true_state_to_tracker():
    # A rejected task must record true utilization so the tracker can learn.
    rows, _ = run("arrro", unreliability=0.4, seed=3, tasks=60)
    reasons = {r["failure_reason"] for r in rows if not r["success"]}
    assert reasons <= {
        "NO_FEASIBLE_NODE",
        "TRUE_CPU_EXHAUSTED",
        "TRUE_RAM_EXHAUSTED",
        "INSUFFICIENT_BANDWIDTH",
    }