import unittest

from vector_scheduler import (
    filter_feasible_nodes,
    calculate_task_risk,
    schedule_task,
    load_config
)
from demo_inputs import nodes, task, reliability_estimates


class TestVectorScheduler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.performance_weights = cls.config["performance_weights"]

    def schedule(self, risk_limit, lambda_value=100):
        return schedule_task(
            nodes,
            task,
            reliability_estimates,
            risk_limit,
            lambda_value,
            self.performance_weights
        )

    def test_infeasible_node_is_removed(self):
        feasible = filter_feasible_nodes(nodes, task)
        names = [node["name"] for node in feasible]

        self.assertEqual(names, ["A", "B"])
        self.assertNotIn("C", names)

    def test_default_decision_selects_a(self):
        result = self.schedule(0.20)

        self.assertEqual(result["status"], "RISK_LIMIT_MET")
        self.assertEqual(result["selected_node"], "A")

    def test_tighter_limit_selects_b(self):
        result = self.schedule(0.10)

        self.assertEqual(result["selected_node"], "B")

    def test_unmet_limit_is_reported(self):
        result = self.schedule(0.05)

        self.assertEqual(result["status"], "RISK_LIMIT_UNMET")
        self.assertEqual(result["selected_node"], "B")

    def test_risk_values(self):
        risk_a = calculate_task_risk(
            nodes[0], task, reliability_estimates
        )
        risk_b = calculate_task_risk(
            nodes[1], task, reliability_estimates
        )

        self.assertAlmostEqual(risk_a, 0.185)
        self.assertAlmostEqual(risk_b, 0.0675)
    

    def test_no_feasible_node(self):
        impossible_task = dict(task)
        impossible_task["required_cpu_pct"] = 100

        result = schedule_task(
            nodes,
            impossible_task,
            reliability_estimates,
            0.20,
            100,
            self.performance_weights
        )

        self.assertEqual(result["status"], "NO_FEASIBLE_NODE")
        self.assertIsNone(result["selected_node"])

    def test_deterministic_tie_breaking(self):
        # Create two identical nodes with different names.
        tie_nodes = [
            dict(nodes[0], name="Z"),
            dict(nodes[0], name="A")
        ]

        # Give both nodes identical reliability estimates.
        tie_estimates = {
            "Z": reliability_estimates["A"],
            "A": reliability_estimates["A"]
        }

        result = schedule_task(
            tie_nodes,
            task,
            tie_estimates,
            0.20,
            100,
            self.performance_weights
        )

        self.assertEqual(result["selected_node"], "A")
    
    def test_missing_reliability_data_raises_clear_error(self):
        incomplete_estimates = dict(reliability_estimates)
        incomplete_estimates.pop("A")

        with self.assertRaisesRegex(
            ValueError,
            "Missing reliability estimates for node 'A'"
        ):
            calculate_task_risk(nodes[0], task, incomplete_estimates)



    def test_invalid_cpu_requirement_raises_error(self):
        invalid_task = dict(task)
        invalid_task["required_cpu_pct"] = 101

        with self.assertRaisesRegex(
            ValueError,
            "CPU requirement must be between 0 and 100"
        ):
            filter_feasible_nodes(nodes, invalid_task)

    def test_invalid_ram_requirement_raises_error(self):
        invalid_task = dict(task)
        invalid_task["required_ram_pct"] = 101

        with self.assertRaisesRegex(
            ValueError,
            "RAM requirement must be between 0 and 100"
        ):
            filter_feasible_nodes(nodes, invalid_task)

    def test_negative_bandwidth_requirement_raises_error(self):
        invalid_task = dict(task)
        invalid_task["min_bandwidth_mbps"] = -1

        with self.assertRaisesRegex(
            ValueError,
            "Minimum bandwidth cannot be negative"
        ):
            filter_feasible_nodes(nodes, invalid_task)

    def test_negative_latency_requirement_raises_error(self):
        invalid_task = dict(task)
        invalid_task["max_latency_ms"] = -1

        with self.assertRaisesRegex(
            ValueError,
            "Maximum latency cannot be negative"
        ):
            filter_feasible_nodes(nodes, invalid_task)


if __name__ == "__main__":
    unittest.main()
    
    def test_invalid_cpu_requirement_raises_error(self):
        invalid_task = dict(task)
        invalid_task["required_cpu_pct"] = 101

        with self.assertRaisesRegex(
            ValueError,
            "CPU requirement must be between 0 and 100"
        ):
            filter_feasible_nodes(nodes, invalid_task)

