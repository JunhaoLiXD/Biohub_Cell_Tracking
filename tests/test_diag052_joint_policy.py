import json
from pathlib import Path

from scripts.diag052_joint_policy import Candidate, difference_components, motion_features, solve_policy, persistent_original_ids

PARAMS = json.loads((Path(__file__).resolve().parents[1]/'configs/local_052_joint_graph_pilot_v1.json').read_text())['parameters']


def test_recovered_numeric_id_does_not_reuse_old_detection_features():
    ids = [1, 2, 3]
    coords = [(99, 0, 0, 0), (5, 0, 0, 0), (7, 0, 0, 0)]
    final = {1: (4, 0, 0, 0), 2: (5, 0, 0, 0), 3: (7, 0, 0, 0)}
    stages = [{1: {'t': 99}, 2: {'t': 5}, 3: {'t': 7}},
              {2: {'t': 5}}, {1: {'t': 4}, 2: {'t': 5}, 3: {'t': 7}}]
    assert persistent_original_ids(ids, coords, final, stages) == {2}


def c(p, motion=None, cosine=0, best=False):
    return Candidate(p, .5, cosine, motion, best)


def test_joint_swap_handles_two_occupied_endpoints_and_is_order_invariant():
    nodes = {1: (0, 0, 0, 0), 2: (0, 0, 0, 1), 3: (1, 0, 0, 0), 4: (1, 0, 0, 1)}
    old = {(1, 3), (2, 4)}
    pool = {(1, 3): c(.6), (2, 4): c(.6), (1, 4): c(.85), (2, 3): c(.85)}
    result, actions, _ = solve_policy(nodes, old, pool, PARAMS, 'original_score')
    assert result == {(1, 4), (2, 3)}
    assert len(actions) == 1
    assert set(actions[0]['removed']) == old
    again = solve_policy(dict(reversed(list(nodes.items()))), old,
                         dict(reversed(list(pool.items()))), PARAMS, 'original_score')
    assert again[0] == result and again[1] == actions


def test_keep_option_and_no_change_control_preserve_graph():
    nodes = {1: (0, 0, 0, 0), 2: (1, 0, 0, 0), 3: (1, 0, 0, 1)}
    old = {(1, 2)}
    pool = {(1, 2): c(.6), (1, 3): c(.61)}
    assert solve_policy(nodes, old, pool, PARAMS, 'original_score')[0] == old
    assert solve_policy(nodes, old, pool, PARAMS, 'no_change')[0] == old


def test_high_confidence_and_uncached_links_are_protected():
    nodes = {1: (0, 0, 0, 0), 2: (1, 0, 0, 0), 3: (1, 0, 0, 1)}
    old = {(1, 2)}
    for pool in [{(1, 3): c(.999)}, {(1, 2): c(.95, best=True), (1, 3): c(.999)}]:
        assert solve_policy(nodes, old, pool, PARAMS, 'original_score')[0] == old


def test_forks_and_adjacent_edges_cannot_be_rewired():
    nodes = {1: (0, 0, 0, 0), 2: (1, 0, 0, 0), 3: (1, 0, 0, 1),
             4: (2, 0, 0, 0), 5: (2, 0, 0, 1)}
    old = {(1, 2), (1, 3), (2, 4), (3, 5)}
    pool = {e: c(.6) for e in old}
    pool.update({(2, 5): c(.999), (3, 4): c(.999)})
    assert solve_policy(nodes, old, pool, PARAMS, 'original_score')[0] == old


def test_five_frame_motion_requires_full_unbranched_context():
    nodes = {i: (i, 0, 0, i) for i in range(5)}
    _, past, future = motion_features(nodes, {(0, 1), (1, 2), (2, 3), (3, 4)})
    assert 2 in past and 1 not in past and 3 in future and 4 not in future
    assert tuple(past[2]) == (0, 0, .40625)


def test_context_can_change_choice_with_same_pool_and_preserve_degrees():
    nodes = {1: (0, 0, 0, 0), 2: (1, 0, 0, 0), 3: (1, 0, 0, 1)}
    pool = {(1, 2): c(.6, motion=14, cosine=0), (1, 3): c(.6, motion=0, cosine=1)}
    old = {(1, 2)}
    assert solve_policy(nodes, old, pool, PARAMS, 'original_score')[0] == old
    assert solve_policy(nodes, old, pool, PARAMS, 'context')[0] == {(1, 3)}


def test_only_deletion_is_rejected_even_with_negative_context_utility():
    nodes = {1: (0, 0, 0, 0), 2: (1, 0, 0, 0)}
    old = {(1, 2)}
    assert solve_policy(nodes, old, {(1, 2): c(.1, motion=14)}, PARAMS, 'context')[0] == old


def test_disjoint_difference_components_can_be_reverted_independently():
    components = list(difference_components({(1, 3)}, {(1, 2), (4, 5)}))
    assert ({(1, 3)}, {(1, 2)}) in components
    assert (set(), {(4, 5)}) in components
