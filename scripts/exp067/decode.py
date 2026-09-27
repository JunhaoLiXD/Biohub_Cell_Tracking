"""The joint decoder: program assembly, exact per-component decomposition, ``scipy.optimize.milp``.

Decomposition (codex_challenge_v1 item 5). Components are derived from the **actual constraint
incidence** — two variables are adjacent only when some constraint row contains both — never from
"these variables share a node". That distinction matters: node ``v`` appears in the in-degree
constraint of transition ``t-1 -> t`` and in the out-degree constraint of ``t -> t+1``, so a
node-identity rule would chain every transition of a movie into one component, exceed
``max_component_vars`` and force a movie-wide fallback on every movie. With a fixed node set and
adjacency-only edges every constraint lives inside a single transition, so the program decomposes
exactly by transition and then by competitor component — and the test asserts that rather than
assuming it.

Fixed edges are modelled as variables with ``lb == ub == 1``. That keeps the constraint algebra
uniform, makes them consume in/out-degree capacity automatically, and — importantly — does **not**
freeze the free competitors at their endpoints.

The only solver is ``scipy.optimize.milp``. There is no custom production branch-and-bound.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from . import audit
from .config import Exp067Config
from .errors import Exp067Deadline
from .features import MovieContext
from .hypotheses import Hypotheses
from .runtime import Deadline, Receipt

CON_IN = "in_degree"
CON_OUT = "out_degree"
CON_ONE_EVENT = "one_event_per_source"
CON_REALIZE = "division_realizes_edge"
CON_FORK = "fork_requires_event"


@dataclass
class Constraint:
    kind: str
    variables: tuple[int, ...]
    coefficients: tuple[float, ...]
    upper: float
    anchor: int  # the node row the row is about, for diagnostics


@dataclass
class Program:
    """A whole movie's integer program. ``n_edges`` edge vars first, then event vars."""

    hyp: Hypotheses
    ctx: MovieContext
    weights: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    constraints: list[Constraint]
    parent_assignment: np.ndarray
    var_transition: np.ndarray
    components: list[list[int]] = field(default_factory=list)
    component_rows: list[list[int]] = field(default_factory=list)

    @property
    def n_edge_vars(self) -> int:
        return self.hyp.n_edges

    @property
    def n_vars(self) -> int:
        return self.hyp.n_edges + self.hyp.n_events

    def event_var(self, j: int) -> int:
        return self.hyp.n_edges + int(j)


def build_program(
    hyp: Hypotheses,
    ctx: MovieContext,
    link_scores: np.ndarray,
    event_scores: np.ndarray,
    config: Exp067Config,
) -> Program:
    """Assemble the movie-wide program. ``link_scores`` / ``event_scores`` are calibrated log-odds."""
    obj = config.objective
    n_e, n_v = hyp.n_edges, hyp.n_events
    n = n_e + n_v

    weights = np.zeros(n, dtype=np.float64)
    lower = np.zeros(n, dtype=np.float64)
    upper = np.ones(n, dtype=np.float64)
    parent_assignment = np.zeros(n, dtype=np.float64)
    var_transition = np.zeros(n, dtype=np.int64)

    for k in range(n_e):
        fixed = bool(hyp.e_fixed[k])
        score = float(link_scores[k]) if ctx.free_edge[k] else obj.tau0
        weights[k] = score - obj.tau0 + (obj.beta0 if hyp.e_is_parent[k] else 0.0)
        if fixed:
            lower[k] = 1.0
            upper[k] = 1.0
        parent_assignment[k] = 1.0 if hyp.e_is_parent[k] else 0.0
        var_transition[k] = int(hyp.e_t[k])

    for j in range(n_v):
        var = n_e + j
        score = float(event_scores[j]) if ctx.scored_event[j] else obj.mu0
        weights[var] = score - obj.mu0
        parent_assignment[var] = 1.0 if hyp.v_is_parent_fork[j] else 0.0
        var_transition[var] = int(hyp.v_t[j])

    constraints: list[Constraint] = []

    # C1 in-degree at every target of at least one candidate edge.
    for target, keys in sorted(hyp.edges_of_target.items()):
        constraints.append(
            Constraint(CON_IN, tuple(int(k) for k in keys), tuple(1.0 for _ in keys), 1.0, int(target))
        )

    # C2 out-degree coupled to the division events of the same source; C3 one event per source.
    for source, keys in sorted(hyp.edges_of_source.items()):
        events = hyp.events_of_source.get(source, [])
        variables = [int(k) for k in keys] + [n_e + int(j) for j in events]
        coefficients = [1.0] * len(keys) + [-1.0] * len(events)
        constraints.append(Constraint(CON_OUT, tuple(variables), tuple(coefficients), 1.0, int(source)))
        if len(events) > 1:
            constraints.append(
                Constraint(
                    CON_ONE_EVENT,
                    tuple(n_e + int(j) for j in events),
                    tuple(1.0 for _ in events),
                    1.0,
                    int(source),
                )
            )

    # C4 a declared division must realise both of its edges.
    for j in range(n_v):
        u, a, b = int(hyp.v_src[j]), int(hyp.v_a[j]), int(hyp.v_b[j])
        for member in (a, b):
            k = hyp.index_of_edge.get((u, member))
            if k is None:  # cannot happen: events are generated from H, but never assume it
                raise AssertionError(f"event {j} references missing edge ({u}, {member})")
            constraints.append(
                Constraint(CON_REALIZE, (n_e + j, int(k)), (1.0, -1.0), 0.0, u)
            )

    # C5 a fork at u is legal only through a declared division event for that exact pair.
    for source, keys in sorted(hyp.edges_of_source.items()):
        targets = sorted({int(hyp.e_tgt[k]) for k in keys})
        if len(targets) < 2:
            continue
        events_by_pair: dict[tuple[int, int], list[int]] = {}
        for j in hyp.events_of_source.get(source, []):
            events_by_pair.setdefault((int(hyp.v_a[j]), int(hyp.v_b[j])), []).append(int(j))
        for i in range(len(targets)):
            for jj in range(i + 1, len(targets)):
                a, b = targets[i], targets[jj]
                ka = hyp.index_of_edge[(source, a)]
                kb = hyp.index_of_edge[(source, b)]
                matching = events_by_pair.get((a, b), [])
                variables = [int(ka), int(kb)] + [n_e + j for j in matching]
                coefficients = [1.0, 1.0] + [-1.0 for _ in matching]
                constraints.append(
                    Constraint(CON_FORK, tuple(variables), tuple(coefficients), 1.0, int(source))
                )

    program = Program(
        hyp=hyp,
        ctx=ctx,
        weights=weights,
        lower=lower,
        upper=upper,
        constraints=constraints,
        parent_assignment=parent_assignment,
        var_transition=var_transition,
    )
    split_components(program)
    return program


def split_components(program: Program) -> None:
    """Union-find over the ACTUAL constraint incidence, not over node identity."""
    n = program.n_vars
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for constraint in program.constraints:
        variables = constraint.variables
        for var in variables[1:]:
            union(variables[0], var)

    groups: dict[int, list[int]] = {}
    for var in range(n):
        groups.setdefault(find(var), []).append(var)
    # Deterministic order: by the smallest variable index each component contains.
    ordered = sorted(groups.values(), key=lambda vars_: vars_[0])
    program.components = ordered
    index_of_component = {var: ci for ci, vars_ in enumerate(ordered) for var in vars_}
    rows: list[list[int]] = [[] for _ in ordered]
    for ri, constraint in enumerate(program.constraints):
        rows[index_of_component[constraint.variables[0]]].append(ri)
    program.component_rows = rows


def component_transitions(program: Program, component: list[int]) -> set[int]:
    return {int(program.var_transition[v]) for v in component}


# --------------------------------------------------------------------------------- solving

def _solve_component(
    program: Program, component: list[int], rows: list[int], config: Exp067Config, time_limit: float
) -> tuple[np.ndarray | None, str | None]:
    from scipy.optimize import Bounds, LinearConstraint, milp

    local_of_var = {var: i for i, var in enumerate(component)}
    size = len(component)
    if size > config.solve.max_component_vars:
        return None, "component_too_large"

    from scipy.sparse import coo_matrix
    rr, cc, vv = [], [], []
    upper_bounds = np.zeros(len(rows), dtype=np.float64)
    for r, ri in enumerate(rows):
        constraint = program.constraints[ri]
        for var, coefficient in zip(constraint.variables, constraint.coefficients):
            rr.append(r)
            cc.append(local_of_var[var])
            vv.append(coefficient)
        upper_bounds[r] = constraint.upper

    a_matrix = coo_matrix((vv, (rr, cc)), shape=(len(rows), size)).tocsc()
    cost = -program.weights[component]
    bounds = Bounds(lb=program.lower[component], ub=program.upper[component])
    constraints = LinearConstraint(a_matrix, -np.inf, upper_bounds) if len(rows) else None
    options = {"time_limit": max(time_limit, 0.05), "mip_rel_gap": config.solve.milp_mip_rel_gap}
    result = milp(
        c=cost,
        constraints=constraints,
        integrality=np.ones(size, dtype=np.int64),
        bounds=bounds,
        options=options,
    )
    if result.x is None or not result.success:
        return None, f"no_incumbent:{getattr(result, 'status', 'unknown')}"
    x = np.asarray(result.x, dtype=np.float64)
    if not np.isfinite(x).all():
        return None, "incumbent_nonfinite"
    rounded = np.rint(x)
    if np.max(np.abs(x - rounded)) > 1e-6:
        return None, "incumbent_not_integral"
    return rounded, None


def _validate_component(
    program: Program, component: list[int], rows: list[int], values: np.ndarray
) -> str | None:
    """Independent re-check. Nothing is accepted on the solver's word."""
    local_of_var = {var: i for i, var in enumerate(component)}
    for i, var in enumerate(component):
        value = values[i]
        if value not in (0.0, 1.0):
            return "incumbent_not_binary"
        if value < program.lower[var] - 1e-9 or value > program.upper[var] + 1e-9:
            return "incumbent_out_of_bounds"
    for ri in rows:
        constraint = program.constraints[ri]
        total = sum(
            coefficient * values[local_of_var[var]]
            for var, coefficient in zip(constraint.variables, constraint.coefficients)
        )
        if total > constraint.upper + 1e-9:
            return f"constraint_violated:{constraint.kind}"
    return None


@dataclass
class DecodeResult:
    selected_edges: np.ndarray  # bool over hypothesis edges
    selected_events: np.ndarray  # bool over hypothesis events
    receipt: Receipt
    objective: float


def solve(
    program: Program,
    config: Exp067Config,
    deadline: Deadline,
    receipt: Receipt,
) -> DecodeResult:
    """Solve component by component; validate or revert each one atomically, with a receipt."""
    values = program.parent_assignment.copy()
    receipt.n_components = len(program.components)
    receipt.n_free_edge_vars = int(np.count_nonzero(program.ctx.free_edge))
    receipt.n_event_vars = int(program.hyp.n_events)
    receipt.n_fixed_edges = int(np.count_nonzero(program.hyp.e_fixed))
    receipt.n_transitions = len({int(t) for t in program.var_transition}) if program.n_vars else 0

    for component, rows in zip(program.components, program.component_rows):
        try:
            deadline.check("component solve")
        except Exp067Deadline:
            receipt.revert("deadline_exhausted")
            continue
        free_here = [v for v in component if program.lower[v] != program.upper[v]]
        if not free_here:
            receipt.n_components_solved += 1
            continue
        started = time.time()
        budget = min(config.solve.max_component_seconds, max(deadline.remaining_s, 0.05))
        try:
            solution, reason = _solve_component(program, component, rows, config, budget)
        except Exception as exc:  # a solver crash is a revert, never a silent pass
            solution, reason = None, f"solver_exception:{type(exc).__name__}"
        deadline.add_solving(time.time() - started)
        if solution is None:
            receipt.revert(reason or "no_incumbent")
            continue
        problem = _validate_component(program, component, rows, solution)
        if problem is not None:
            receipt.revert(f"incumbent_invalid:{problem}")
            continue
        for i, var in enumerate(component):
            values[var] = solution[i]
        receipt.n_components_solved += 1

    revert_fraction = receipt.n_components_reverted / receipt.n_components if receipt.n_components else 0.0
    if revert_fraction > config.solve.max_revert_fraction:
        receipt.revert("max_revert_fraction_exceeded", count=0)
        receipt.note(
            f"movie-wide fallback: revert fraction {revert_fraction:.4f} exceeds "
            f"{config.solve.max_revert_fraction}"
        )
        values = program.parent_assignment.copy()
        receipt.active = False

    n_e = program.n_edge_vars
    selected_edges = values[:n_e] > 0.5
    selected_events = values[n_e:] > 0.5
    objective = float(np.dot(program.weights, values))
    return DecodeResult(selected_edges, selected_events, receipt, objective)


def parent_objective(program: Program) -> float:
    return float(np.dot(program.weights, program.parent_assignment))


def assert_parent_feasible(program: Program) -> None:
    """The parent assignment must always be feasible, or fallback would be unreachable."""
    for component, rows in zip(program.components, program.component_rows):
        local = {var: i for i, var in enumerate(component)}
        values = program.parent_assignment[component]
        for i, var in enumerate(component):
            if values[i] < program.lower[var] - 1e-9 or values[i] > program.upper[var] + 1e-9:
                raise audit.Exp067AuditFailure(
                    f"parent assignment violates the bounds of variable {var}"
                )
        for ri in rows:
            constraint = program.constraints[ri]
            total = sum(
                coefficient * values[local[var]]
                for var, coefficient in zip(constraint.variables, constraint.coefficients)
            )
            if total > constraint.upper + 1e-9:
                raise audit.Exp067AuditFailure(
                    f"parent assignment violates {constraint.kind} at node row {constraint.anchor}"
                )
