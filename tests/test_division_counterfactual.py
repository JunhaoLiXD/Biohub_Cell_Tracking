"""Structural tests for the restricted, GT-assisted diagnostic edit algebra."""
import unittest
from scripts.diagnose_division_counterfactual import repaired_edges
from scripts.exp067.audit import audit_graph


class CounterfactualTests(unittest.TestCase):
    def test_noop_preserves_parent(self):
        parent = {(1, 2), (2, 4), (3, 5)}
        self.assertEqual(repaired_edges(parent, []), parent)

    def test_conflicting_continuation_is_removed_and_unrelated_edge_preserved(self):
        parent = {(1, 4), (2, 3), (3, 6)}
        result = repaired_edges(parent, [{'mother': 1, 'daughters': [3, 5]}])
        self.assertEqual(result, {(1, 3), (1, 5), (3, 6)})
        self.assertEqual(parent, {(1, 4), (2, 3), (3, 6)})
        audit_graph({1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2}, sorted(result))

    def test_subset_order_is_irrelevant(self):
        parent = {(1, 3), (2, 5), (3, 7), (4, 8)}
        selected = [{'mother': 1, 'daughters': [3, 4]}, {'mother': 2, 'daughters': [5, 6]}]
        self.assertEqual(repaired_edges(parent, selected), repaired_edges(parent, selected[::-1]))

    def test_two_mothers_cannot_request_one_daughter(self):
        with self.assertRaises(ValueError):
            repaired_edges(set(), [{'mother': 1, 'daughters': [3, 4]}, {'mother': 2, 'daughters': [4, 5]}])


if __name__ == '__main__':
    unittest.main()
